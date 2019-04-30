# -*- coding: utf-8 -*-

import requests
import pyodbc
import datetime
import json

param = {}
param["servicedescpath"] = "http://172.16.10.252:8081/" 
param["ConnectString"]   = "DRIVER={SQL Server};SERVER=172.16.10.252;DATABASE=IntraService;UID=ETK\SergeySt;PWD=;Trusted_Connection=true"
param["board_name"]      = "IntraService"

param["debug_path"] = "C:\\Projects\\UpdateTrello\\log\\trello_{0}.log"
param["debug_level"] = 10

debugs = {}    
debugs["program"]                   = 10
debugs["error"]                     = 10
debugs["Строка соединения ODBC"]    = 0
debugs["IntraService url"]          = 0
# Запросы ODBC
debugs["Select ODBC"]               = 0
debugs["Execute ODBC"]              = 0
# Задачи ODBC
debugs["Get info for task"]         = 0
debugs["Info for task"]             = 0
# Конструктор trello
debugs["Trello auth info"]          = 0
# Команды работы с API сервера trello
debugs["get api"]                   = 0
debugs["put api"]                   = 0
debugs["post api"]                  = 0
debugs["delete api"]                = 0
debugs["get board"]                 = 0
debugs["get list"]                  = 0
debugs["get label"]                 = 0
debugs["delete card"]               = 0
debugs["update task"]               = 0
debugs["erase old cards"]           = 10
debugs["update free list"]          = 10

def debug(str, str_level = ""):
    level = debugs.get(str_level, 0)
    if level >= param["debug_level"]:
        print(str)
        with open(param["debug_path"].format(datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d")), "a") as f:
            if str_level == "error":
                f.write("{0} : ======================================================================\n".format(datetime.datetime.now())) 
            f.write("{0} : {1}\n".format(datetime.datetime.now(), str))
            if str_level == "error":
                f.write("{0} : ======================================================================\n".format(datetime.datetime.now())) 
    
# Класс работать с ODBC    
class DB_reader():

    # Инициализировать ODBC
    def __init__(self, ConnectString):
        debug("ODBC connect {0}".format(ConnectString), "Строка соединения ODBC")
        self.odbc_connect = pyodbc.connect(ConnectString)
        self.cursor = self.odbc_connect.cursor()
        self.servicedescpath = None
    
    # Получить url IntraService    
    def get_servicedescpath(self, userid):    
        if not self.servicedescpath:
            self.servicedescpath = param["servicedescpath"]
            for user in self.select("select u.ServiceDeskPath from dbo.[User] u where u.id = {0} and u.ServiceDeskPath is not null".format(userid)):
                if user[0]:
                    self.servicedescpath = user[0]
            debug("IntraService url {0}".format(self.servicedescpath), "IntraService url")
            return self.servicedescpath
        
    # Запрос к базе данных    
    def select(self, query_string):    
        debug('Select ODBC "{0}"'.format(query_string), "Select ODBC")
        self.cursor.execute(query_string)
        return self.cursor.fetchall()
        
    def execute(self, query_string):    
        debug('Execute ODBC "{0}"'.format(query_string), "Execute ODBC")
        self.cursor.execute(query_string)
        self.odbc_connect.commit()
        
    def get_task(self, task_id, userid):
    
        debug('Get info for task "{0}"'.format(task_id), "Get info for task")
        # Загрузить информацию об задаче
        for task in self.select("""
            select t.Id           as taskid
                  ,t.StatusId     as statusid
                  ,st.NameXml.value('(/Language/Ru)[1]', 'varchar(100)') as status
            	  ,s.NameXml.value('(/Language/Ru)[1]', 'varchar(100)') as service
                  ,t.Description  as description
                  ,t.Created      as created
                  ,t.DeadLine     as deadline
                  ,t.CreatorId    as creatorid
                  ,t.Executors    as executors
                  ,us.Name        as creatorname
                  ,us.Phone       as creatorphone
                  ,t.Participants as participants
                  ,(select max(1) from dbo.[VisitedTask] vt where vt.NewComments = 1 and vt.UserId = {1} and vt.TaskId = {2}) as newcomment
                  ,(select ViewClosed from dbo.[UserTrello] ut where ut.UserId = {1}) as viewclosed
            from dbo.[Task] t left join dbo.[Status] st on t.StatusId  = st.id
                              left join dbo.[user] us   on t.CreatorId = us.id
                              left join dbo.[Service] s on t.ServiceId = s.id
            where t.id = {0}""".format(task_id, userid, task_id)
            ):
            # Задачи "Закрыта" и "Отменена" -> "Закрыта/Отменена"
            status = task.status
            if (status == "Закрыта") or (status == "Отменена"):
                status = "Закрыта/Отменена"
                
            object = {# Номер задачи целое число
                      "taskid"      : task_id
                     # Наименование статуса задачи. Если нет исполнителя, то статус "Свободная"
                     ,"status"      : status if task.executors else "Свободные"
                     # Наименование задачи - номер, описание, создатель и его телефон
                     ,"description" : "#{0}. {2} {1}".format(task_id, task.description, "{0} ({1}).".format(task.creatorname, task.creatorphone) if task.creatorphone else task.creatorname)
                     # Направление заявления
                     ,"service"     : task.service
                     # Дата создания, строка в ISO формате
                     ,"created"     : task.created.isoformat() if task.created else None
                     # DEADLINE дата, строка в ISO формате
                     ,"deadline"    : task.deadline.isoformat() if task.deadline else None
                     # Создатель и его телефон
                     ,"creator"     : "{0} ({1})".format(task.creatorname, task.creatorphone) if task.creatorphone else task.creatorname
                     # Наблюдатели
                     ,"participants": task.participants
                     # Новые сообщения
                     ,"newcomment"  : task.newcomment
                     }
                     
            if 1:         
                if (object["service"] == "Инциденты") and (object["status"] == "Свободные"):
                    object["status"] = "Инциденты"
            
            if (task.viewclosed == 0) and (status == "Закрыта/Отменена"):
                object["status"] = "Не показывать"
                     
        debug('Info for task "{0}" : "{1}"'.format(task_id, object), "Info for task")
                     
        # Заполнить описание задачи             
        comments = []
        # Ссылка на задачу в IntraService
        comments.append("[#{2}]({0}task/view/{1})".format(self.servicedescpath, task_id, task_id))             
                     
        # Присоединенные файлы
        attachments = []
        for attachment in self.select("""
            select at.id   as id
                  ,at.name as name
            from dbo.[TaskFile] at
            where at.taskid = {0}""".format(task_id)):
            # Добавим в список (не используется)
            attachments.append({"id" : attachment.id, "name" : attachment.name})
            # Добавить в описание задачи
            comments.append("[{2}]({0}Task/ViewFile/{1})".format(self.servicedescpath, attachment.id, attachment.name))             
        
        if 1:
            # Первое предложение
            description = task.description.split(".")[0]
            object["description"] = "#{0}. {2} {1}.".format(task_id, description, "{0} ({1}).".format(task.creatorname, task.creatorphone) if task.creatorphone else task.creatorname)
            comments.append("###{0}".format(" ".join(task.description.split("\n"))))
            
        # Комментарии. Оставим только 3 последних комментария
        for comment in self.select("""
            select top 3 e.[Name]  as editorname
                  ,e.[Phone] as editorphone
                  ,l.[Comments] as comment
                  ,l.[Date] as date
            from [IntraService].[dbo].[TaskLifetime] l left join dbo.[User] e on l.EditorId = e.Id  
            where taskid = {0} 
              and l.comments is not null
            order by l.id desc""".format(task_id)):
            # Добавить дату и кто комментировал + телефон
            comments.append("###{0} : {1}".format(comment.date.strftime("%d.%m.%Y %H:%M:%S"), "{0} ({1})".format(comment.editorname, comment.editorphone) if comment.editorphone else comment.editorname))
            # Добавить комментарий
            comments.append(comment.comment.replace(">", ""))
        
        # Вернуть объект, attachments и комментарии    
        return {"data" : object, "attachments" : attachments, "comment" : "\n".join(comments)}    


# Объект работы с API trello        
class Trello():

    # Конструктор
    def __init__(self, db, data):
        self.db             = db
        self.auth = {}
        # Код пользователя IntraService
        self.auth["UserId"] = data["UserId"]
        # Глобальные переменные идентификации
        self.auth["AppKey"] = data["AppKey"]
        self.auth["Token"]  = data["Token"]
        debug("Trello auth info : {0}".format(self.auth), "Trello auth info")
        # Глобальные переменные для списков
        self.boards = None
        self.lists  = None
        self.labels = None
        self.fields = None
        self.cards  = None
        # url на доступ к сайту
        self.servicedescpath = data["ServiceDescPath"]
            
    # Получить полный url запроса     
    def get_url_trello(self, url):
        return "https://trello.com/1" + url + "?key={0}&token={1}".format(self.auth["AppKey"], self.auth["Token"])
        
    def test_responce(self, result, url = ""):
        if result.status_code == requests.codes.ok:
            return result
        else:
            debug('Error trello api : "{0}" for url : {1}'.format(result.text, url), "error")
            return None
    
    # Операция get
    def get_request(self, url, query = {}):
        trello_url = self.get_url_trello(url)
        debug('get : "{0}" query : "{1}"'.format(trello_url, query), "get api")
        return self.test_responce(requests.get(trello_url, query), trello_url) 
        
    # Операция post
    def post_request(self, url, query = {}):
        trello_url = self.get_url_trello(url)
        debug('post : "{0}" query : "{1}"'.format(trello_url, query), "post api")
        return self.test_responce(requests.post(trello_url, query), trello_url)
        
    # Операция put
    def put_request(self, url, query = {}):
        trello_url = self.get_url_trello(url)
        debug('put : "{0}" query : "{1}"'.format(trello_url, query), "put api")
        return self.test_responce(requests.put(trello_url, query), trello_url)
        
    # Операция delete
    def delete_request(self, url):
        trello_url = self.get_url_trello(url)
        debug('delete : "{0}" '.format(trello_url), "delete api")
        return self.test_responce(requests.delete(trello_url), trello_url)
        
    # Найти или создать доску по имени    
    def get_board(self, board_name):
        debug('get board "{0}"'.format(board_name), "get board")
        if self.boards is None:
            # Список досок не загружен
            self.boards = {}
            # Нужно загрузить все доски
            for board in self.get_request("/members/my/boards").json():
                self.boards[board["name"]] = board["id"]
        # Ищем нужную доску        
        if self.boards.get(board_name):
            # Доска найдена
            debug('finded board "{0}" id:"{1}"'.format(board_name, self.boards[board_name]), "get board")
            return self.boards[board_name]
        else:
            # Нужно создать доску с заданным именем
            query = {"name" : board_name}
            board_json = self.post_request("/boards", query).json()
            debug('created board "{0}" json:"{1}"'.format(board_name, board_json), "get board")
            self.boards[board_name] = board_json["id"]
            return board_json["id"]
            
    # Найти список по имени на доске    
    def get_list(self, list_name, board_id):
        debug('get list "{0}" on board "{1}"'.format(list_name, board_id), "get list")
        if self.lists is None:
            # Список не загружен
            self.lists = {}
            # Нужно загрузить все списки
            for list in self.get_request("/boards/{0}/lists".format(board_id)).json():
                self.lists[list["name"]] = list["id"]
        # Ищем нужный список 
        if self.lists.get(list_name):
            # Список найден
            debug('finded list "{0}" id:"{1}"'.format(list_name, self.lists[list_name]), "get list")
            return self.lists[list_name]
        else:
            # Нужно создать список с заданным именем
            debug("create list : {0}".format(list_name))
            query = {"name" : list_name, "idBoard" : board_id}
            list_json = self.post_request("/lists", query).json()
            debug('created list "{0}" json:"{1}"'.format(list_name, list_json), "get list")
            self.lists[list_name] = list_json["id"]
            return list_json["id"]
            
    # Найти метку по имени    
    def get_label(self, label_name, board_id):
        debug('get label "{0}" on board "{1}"'.format(label_name, board_id), "get label")
        if self.labels is None:
            # Список не загружен
            self.labels = {}
            # Нужно загрузить все списки
            for label in self.get_request("/boards/{0}".format(board_id), {"labels" : "all"}).json()["labels"]:
                if label["name"]:
                    self.labels[label["name"]] = label["id"]
        # Ищем нужный список 
        if self.labels.get(label_name):
            # Список найден
            debug('finded label "{0}" id:"{1}"'.format(label_name, self.labels[label_name]), "get label")
            return self.labels[label_name]
        else:
            # Нужно создать список с заданным именем
            debug("create label : {0}".format(label_name))
            query = {"name" : label_name, "idBoard" : board_id}
            label_json = self.post_request("/labels", query).json()
            debug('created label "{0}" json:"{1}"'.format(label_name, label_json), "get label")
            self.labels[label_name] = label_json["id"]
            return label_json["id"]
            
    # Найти задачу в trello
    def find_card(self, card_name, board_id):
        found_card = None
        # Получить все задачи на доске
        for card in self.get_request("/boards/{0}/cards".format(board_id)).json():
            # Номер задачи в trello и заголовке задачи равны
            if card["name"][0:7] == card_name[0:7]:
                # Вернуть идентификатор карточки в trello
                found_card = card
                break
        return found_card  

    # Удалить карточку в trello        
    def delete_card(self, card_id):
        if card_id:
            debug('delete card "{0}" in trello'.format(card_id), "delete card")
            self.delete_request("/cards/{0}".format(card_id))
    
    # Обновить задачу на доске
    def update_task(self, taskid, board_name):
    
        # Скачаем задачу из базы
        base = self.db.get_task(taskid, self.auth["UserId"])
        # Положим задачу на основную доску
        options = {"board" : board_name
                 , "list" : base["data"]["status"]
                 , "label" : base["data"]["service"]
                 , "label_comm" : "Новый комментарий" if base["data"]["newcomment"] else None
                  }

        debug('update task "{0}" "{1}" "{2}"'.format(taskid, base["data"]["status"], base["data"]["description"]), "update task")
        
        # Получим доску, список и метку
        board_id = self.get_board(options["board"])
     
        # Найдем и удалим карточку по задаче
        found_card = self.find_card(base["data"]["description"], board_id)
        if found_card:
            # Если руками перенесли задачу в TODAY, то оставим список там для заданных списков
            if (found_card["idList"] == self.get_list("TODAY", board_id)) and ((options["list"] == "В работе") or (options["list"] == "Открыта")):
                debug('Оставим задачу {0} в "TODAY".'.format(taskid), "error")
                options["list"] = "TODAY"
            self.delete_card(found_card["id"])
        
        if options["list"] == "Не показывать":
            debug('Закрытые задачи не показываем для данного пользователя', "update task")
        else:
            # Для закрытых задач, оставим только у которых дата изменения менее одного месяца
            create_card = 1
            if (options["list"] == "Закрыта/Отменена") or (options["list"] == "Выполнена"):
                for i in self.db.select("""
                    select max(changed) as changed
                    from dbo.TaskHistory th 
                    where th.TaskId = {0}
                    having max(changed) < dateadd(m, -1, getdate())""".format(taskid)):
                    debug('task "{0}" older one month'.format(taskid), "update task")
                    create_card = 0

            if create_card:    
            
                # Создадим новую карточку    
                query = {"name" : base["data"]["description"]
                       , "desc" : base["comment"]
                       , "pos" : "top"
                       , "due" : base["data"]["deadline"]}
                if options["list"]:
                    list_id  = self.get_list( options["list"] , board_id)
                    query["idList"] = list_id
                    
                query["idLabels"] = []
                
                if options["label"]:
                    label_id = self.get_label(options["label"], board_id)
                    query["idLabels"].append(label_id)
                    
                if options["label_comm"]:
                    label_id = self.get_label(options["label_comm"], board_id)
                    query["idLabels"].append(label_id)
                    
                card_json = self.post_request("/cards", query).json()
                debug('created new card for task "{0}" json : "{1}"'.format(taskid, card_json), "update task")
                
            else:
                debug('created new card for task "{0}" skipped'.format(taskid), "update task")
            
    # Подчистить список на доске для закрытых задач. Оставим только те которые изменялись не старше месяца назад
    def erase_old_cards(self, board_name, list_name):
        # Получим доску и список
        debug('delete old tasks for list "{0}"'.format(list_name), "erase old cards")
        board_id = self.get_board(board_name)
        list_id  = self.get_list( list_name, board_id)
        # Отобрать все карточки в списке
        for card in self.get_request("/lists/{0}/cards".format(list_id)).json():
            # Получить номер задачи
            taskid = card["name"][1:7]
            # Найти задачи у которых дата изменения старше одного месяца
            for i in self.db.select("""
                select 1
                from dbo.TaskHistory th 
                where th.TaskId = {0}
                having max(changed) < dateadd(m, -1, getdate())""".format(taskid)):
                debug('delete old task "{0}"'.format(taskid), "erase old cards")
                self.delete_card(card["id"])

    # Обновить список свободных задач            
    def update_free_list(self, list_task, board_name, list_name):
        debug('update free list для "{0}/{1}". Tasks count : "{2}"'.format(board_name, list_name, len(list_task)), "update free list")
        # Получим доску, список
        board_id = self.get_board(board_name)
        list_id  = self.get_list( list_name, board_id)
        # Отобрать все карточки в списке
        i = 0
        for card in self.get_request("/lists/{0}/cards".format(list_id)).json():
            # Получить номер задачи
            task_id = int(card["name"][1:7])
            if list_task.count(task_id):
                # Есть карточка в списке, удалить из списка
                list_task.remove(task_id)
                i = i + 1
                pass
            else:
                # Нет в списке, удалить из списка в trello
                self.delete_card(card["id"])
        debug("On board trello already exist {0} free task count".format(i), "update free list")        
        # list_task - содержит задачи, которые нужно добавить на доску
        i = 0
        for task_id in sorted(list_task):
            i = i + 1
            debug("{0} from {1}. Add free tasks in free list".format(i, len(list_task)), "update free list")
            self.update_task(task_id, board_name)
    
def Main():

    debug(""                   , "program")
    debug("start update trello", "program")
    
    try:    
        db = DB_reader(param["ConnectString"])
        board_name = param["board_name"]
        
        for user in db.select("""
                              SELECT UserId,
                                    AppKey,
                                    Token, 
                                    HistoryId, 
                                    (select u.Name from dbo.[User] u where u.id = ut.UserId) as username,
                                    ViewClosed 
                              FROM UserTrello ut /*where userid = 3605*/
                              ORDER BY 1
                              """):
            try:
        
                debug("**********************************************************", "program")
                debug("Update for user {0} {1}".format(user.UserId, user.username), "program")
                debug("**********************************************************", "program")
                
                # Создать объект trello    
                trello = Trello(db, {"UserId" : user.UserId, "AppKey" : user.AppKey, "Token" : user.Token, "db" : db, "ServiceDescPath" : db.get_servicedescpath(user.UserId)})
                
                
                list_task = []
                # Получить список свободных заявок, для данного пользователя
                for x in db.select("""
                    SELECT task.Id 
                    FROM [IntraService].[dbo].[Task] task
                         left join dbo.[Service] s on task.ServiceId = s.id
                    WHERE task.Executors is null
                      and s.NameXml.value('(/Language/Ru)[1]', 'varchar(100)') = 'Инциденты'
                      and task.StatusId not in (41, 42, 44) -- Выполнена, Закрыта, Отменена
                      and task.ExecutorGroupId in (
                          select ege.ExecutorGroupId 
                          from [IntraService].[dbo].[ExecutorGroupExecutor] ege 
                          where ege.UserId = {0})
                    """.format(user.UserId)):
                    list_task.append(int(x[0])) 
                debug("Update free list tasks", "program")
                trello.update_free_list(list_task, board_name, "Инциденты")

                list_task = []
                # Получить список свободных заявок, для данного пользователя
                for x in db.select("""
                    SELECT task.Id 
                    FROM [IntraService].[dbo].[Task] task
                         left join dbo.[Service] s on task.ServiceId = s.id
                    WHERE task.Executors is null
                      and s.NameXml.value('(/Language/Ru)[1]', 'varchar(100)') <> 'Инциденты'
                      and task.StatusId not in (41, 42, 44) -- Выполнена, Закрыта, Отменена
                      and task.ExecutorGroupId in (
                          select ege.ExecutorGroupId 
                          from [IntraService].[dbo].[ExecutorGroupExecutor] ege 
                          where ege.UserId = {0})
                    """.format(user.UserId)):
                    list_task.append(int(x[0])) 
                debug("Update free list tasks", "program")
                trello.update_free_list(list_task, board_name, "Свободные")
                

                #
                for x in db.select("select max(id) as max_id from [dbo].[TaskHistory]"):
                    HistoryId = x[0]
                debug("get history update : {0}".format(HistoryId), "program")
                
                tasks = db.select("""
                    select th.TaskId as taskid
                         , max(th.id) maxid
                         , max(th.Changed) as max_changed
                         , (select StatusId from dbo.[Task] t where t.id = th.TaskId) as statusid 
                         , (select Name     from dbo.[Task] t where t.id = th.TaskId) as taskname
                    from [dbo].[TaskHistory] th, dbo.[TaskExecutor] te 
                    where te.UserId = {1} and te.TaskId = th.TaskId and th.id > {0}
                    group by th.TaskId
                    having case when ((select StatusId from dbo.[Task] t where t.id = th.TaskId) in (41, 42, 44))
                           then
                                case when (max(th.Changed) > dateadd(m, -1, getdate()))
                                then 1
                                else 0
                                end
                           else 1
                           end = 1 
                    order by 2
                    """.format(user.HistoryId, user.UserId))
                
                debug("For this period need update {0} tasks".format(len(tasks)), "program")
                # Обработать задачи    
                i = 0
                for task in tasks:
                    i = i + 1
                    debug('{0} from {1}. tasks "#{3}:{2}"'.format(i, len(tasks), task.taskname, task.taskid), "program")
                    trello.update_task(task.taskid, board_name)
                    debug('update history id : {0}'.format(task.maxid), "program")
                    db.execute("update UserTrello set HistoryId = {0} where UserId = {1} ".format(task.maxid, user[0]))
                    
                # Удалить лишние задачи на доске
                for list_name in ["Выполнена"]:
                    trello.erase_old_cards(board_name, list_name)

                if user.ViewClosed == 1:        
                    for list_name in ["Закрыта/Отменена"]:
                        trello.erase_old_cards(board_name, list_name)
                    
                debug('update history id : {0}'.format(HistoryId), "program")
                db.execute("update UserTrello set HistoryId = {0} where UserId = {1} ".format(HistoryId, user[0]))
                
            except Exception as e:
                debug('Error for user {1} : "{0}"'.format(e, user[0]), "error")
                
    except Exception as e:
        debug('Error "{0}"'.format(e), "error")

    debug("stop update trello", "program")

Main()

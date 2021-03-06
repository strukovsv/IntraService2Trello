# IntraService2Trello
Пакет позволяет связать известную service desk IntraServer с web доской Trello.com. Программа на Python вызывается с заданной периодичностью, проверяет изменные статусы задач, по заданным пользователям, и обновляет доски пользователей Trello.com, используя API вызовы Trello. 
## Установка
1. Для пользователей trello, необходимо создать таблицу на сервере IntraService. В моем случае это MS SQL Server.
```
CREATE TABLE [dbo].[UserTrello](
    [UserId] [int] NOT NULL,
    [AppKey] [nvarchar](100) NOT NULL,
    [Token] [nvarchar](100) NOT NULL,
    [HistoryId] [int] NOT NULL,
    [ViewClosed] [int] NOT NULL
) ON [PRIMARY]
```
2. Таблица заполняется вручную.
- **USerId** = mидентификатор пользователя из таблицы dbo.[User]
- **AppKey** = ключ API разработчика получаем по адресу <https://trello.com/app-key>
- **Token** = токен API разработчика получаем там же
- **HistoryId** = текущий идентификатор в таблице [dbo].[TaskHistory]. При заведении пользователя, устанавливаем в ноль. 
- **ViewClosed** = 1 - Показывать список закрытых задач, 0 - Не показывать
3. Запуск программы на Windows, производится планировщиком задач, с заданной переодичностью. 
## Настройка
Для настройки необходимо прописать в начале программы на python, следующие переменные: 
- **param["servicedescpath"]** = url сервера IntraService, для создания ссылки обращения к задачам и файлам.
- **param["ConnectString"]**   = строка ODBC соединения с сервером БД IntraService
- **param["board_name"]**      = наименование доски в trello
## Поддержка 
Если у вас возникли сложности или вопросы по использованию пакета, создайте в данном репозитории или напишите на электронную почту <strukovsv@mail.ru>.
## Лицензия
Вы можете использовать данный пакет в личных и коммерческих целях. Любые изменения приветствуются.
## Что дальше?
- Создать файл конфигурации. 
- Возможно использовать потоки python, для отказа от планировщика задач.
- Возможно изменение внешнего вида задачи, для удобства работы.
## Документация
- Документацию API Trello.com можно найти по адресу <https://developers.trello.com/reference/>
- Ключ и токен API разработчика получаем по адресу <https://trello.com/app-key>

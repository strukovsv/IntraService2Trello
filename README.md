# IntraService2Trello
Пакет позволяет связать известную service desk IntraServer с web доской Trello.com. Программа на Python вызывается с заданной периодичностью, проверяет изменные статусы задач, по заданным пользователям, и обновляет доски пользователей Trello.com, используя API вызовы Trello. 
## Установка
Для пользователей trello, необходимо создать таблицу на сервере IntraService.В моем случае это MS SQL Server.
```
CREATE TABLE [dbo].[UserTrello](
    [UserId] [int] NOT NULL,
    [AppKey] [nvarchar](100) NOT NULL,
    [Token] [nvarchar](100) NOT NULL,
    [HistoryId] [int] NOT NULL,
    [ViewClosed] [int] NOT NULL
) ON [PRIMARY]
```

## Настройка


## Поддержка 

Если у вас возникли сложности или вопросы по использованию пакета, создайте 
[обсуждение][] в данном репозитории или напишите на электронную почту 
<strukovsv@mail.ru>.

## Лицензия

## Что дальше?

## Документация

Документацию API Trello.com можно найти по адресу [TRELLO REST API](https://developers.trello.com/reference/ "API web доски Trello.com")

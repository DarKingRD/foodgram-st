🧀🍔🍔🌭🌭🍙🍙🍳🍳🍐

«Фудграм» — сайт, на котором пользователи будут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.
Проект состоит из следующих страниц: главная, страница входа, страница регистрации, страница рецепта, страница пользователя, страница подписок, избранное, список покупок, создание и редактирование рецепта, страница смены пароля, статические страницы «О проекте» и «Технологии».

## Старт

1. Клонируйте репозиторий

2. Создайте файл `.env` в директории `infra`, похожий на  `.env.example`:
```bash
cp infra/.env.example infra/.env
```

3. Запустите проект:
```bash
cd infra
docker-compose up
```

4. Создайте суперпользователя:
```bash
docker-compose run backend python manage.py createsuperuser
```

## Данные

В файле `.env` параметр `LOAD_TEST_DATA=1` позволяет загрузить тестовые данные при запуске. (Сами тестовые данные находятся в backend/test_data.json)

Также вы можете зайти в админ панель и загрузить ингридиенты нажав на "Импорт" и выбрав по пути data/ingredients.csv.

## Доступ к приложению

- Веб-интерфейс: [Localhost](http://localhost/)
- API документация: [Localhost docs](http://localhost/api/docs/)
- Админ-панель: [Localhost admin](http://localhost/admin/)

«Фудграм» — сайт, на котором пользователи будут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.
Проект состоит из следующих страниц: главная, страница входа, страница регистрации, страница рецепта, страница пользователя, страница подписок, избранное, список покупок, создание и редактирование рецепта, страница смены пароля, статические страницы «О проекте» и «Технологии».

## Старт

1. Клонируйте репозиторий
```bash
git clone https://github.com/DarKingRD/foodgram-st.git
```
2. Перейдите в директорию `infra` и создайте файл `.env` на примере `.env.example`
```bash
cd foodgram-st/infra
touch .env
```
3. В директории `infra` Запустите проект:
```bash
docker-compose up
```
4. Выполните миграции:
```bash
docker-compose exec backend python manage.py migrate
```
5. Создайте суперпользователя:
```bash
docker-compose run backend python manage.py createsuperuser
```
6. Заполните базу ингредиентами (ингредиенты загружаются из `data/ingredients.json`, при помощи команды `python manage.py import_ingredients`):
```bash
docker-compose exec backend python manage.py import_ingredients
```
## Доступ к приложению

- Веб-интерфейс: [Localhost](http://localhost/)
- API документация: [Localhost docs](http://localhost/api/docs/)
- Админ-панель: [Localhost admin](http://localhost/admin/)

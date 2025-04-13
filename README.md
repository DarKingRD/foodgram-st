---

# Foodgram - «Продуктовый помощник»

**Foodgram** - это онлайн-сервис для публикации рецептов. Пользователи могут создавать аккаунты, добавлять рецепты, подписываться на других авторов, добавлять рецепты в избранное и в список покупок, а также скачивать сводный список продуктов.

## 🚀 Стек технологий

### **Backend**
- **Python** (основной язык)
- **Django** (веб-фреймворк)
- **Django REST Framework (DRF)** (API)
- **PostgreSQL** (база данных)
- **Docker** (контейнеризация)
- **Nginx** (веб-сервер)
- **Gunicorn** (WSGI-сервер)

### **Аутентификация и безопасность**
- **JWT (JSON Web Tokens)** (`djangorestframework-simplejwt`)
- **Django Auth System** (стандартная аутентификация)

### **Дополнительные библиотеки**
- **Pillow** (работа с изображениями)
- **Django Filter** (фильтрация данных)
- **Psycopg2** (PostgreSQL адаптер)
- **python-dotenv** (переменные окружения)

### **Инфраструктура**
- **Docker Compose** (оркестрация контейнеров)
- **GitHub Actions** (CI/CD)

---

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

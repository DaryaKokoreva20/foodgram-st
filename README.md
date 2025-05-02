# Foodgram – онлайн-сервис для публикации и подбора рецептов

**Foodgram** — веб-приложение, в котором пользователи могут публиковать рецепты, добавлять рецепты других в избранное, подписываться на авторов и формировать список покупок.

---

## Технологии

- Python 3.11, Django 5
- Django REST Framework, Djoser
- PostgreSQL, Gunicorn, Nginx
- Docker, Docker Compose
- GitHub Actions (CI/CD)
- React (SPA, frontend уже собран)

---

## CI/CD

Сборка и публикация backend-образа на Docker Hub происходят автоматически при пуше в `main`.

Docker Hub: [`dokysmiller/foodgram-st`](https://hub.docker.com/repository/docker/dokysmiller/foodgram-st)

---

## Установка и запуск проекта (локально через Docker)

1. Клонируйте репозиторий:

```bash
git clone https://github.com/DaryaKokoreva20/foodgram-st.git
cd foodgram-st
```

2. Создайте `.env` в корне проекта:

```dotenv
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_pass
DB_HOST=db
DB_PORT=5432
```
> Этот файл не нужно коммитить — он должен быть в `.gitignore`  
> Файл используется docker-compose для подключения к PostgreSQL

3. Соберите и запустите проект:

```bash
cd infra
docker-compose up --build
```

4. Проект будет доступен по адресу: [http://localhost](http://localhost)

---

## Админка

Создание суперпользователя:

```bash
docker-compose exec backend python manage.py createsuperuser
```

Админка: [http://localhost/admin](http://localhost/admin)

---

## Документация API

Доступна по адресу:  
[http://localhost/api/docs/](http://localhost/api/docs/)

---

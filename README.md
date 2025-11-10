# Loyo - Telegram loyalty program bot

[![CI](https://img.shields.io/github/actions/workflow/status/Echways/telegram-loyalty-program-bot/ci.yml?branch=main)](https://github.com/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)
[![Redis](https://img.shields.io/badge/cache-Redis-orange)](https://redis.io/)
[![SQLAlchemy](https://img.shields.io/badge/orm-SQLAlchemy-blueviolet)](https://www.sqlalchemy.org/)
[![Aiogram](https://img.shields.io/badge/framework-Aiogram-brightgreen)](https://docs.aiogram.dev/)

---

> **Классика и надёжность + взгляд в будущее.**  
> Этот проект — реализация Telegram-бота с профилем пользователя и программой лояльности для офлайн-магазинов. Простая архитектура, проверенные библиотеки и готовая Docker-окружение делают проект пригодным и для небольших магазинов, и для пилотов в больших системах.

---

## Возможности

- Регистрация и профиль пользователя (Telegram).
- Система рангов (ранги хранятся в `data/ranks.json`).
- Каталог категорий и товаров (`data/catalog.json`).
- Начисление и списание бонусов при покупке (поддержка выбора списания бонусов пользователем).
- История покупок (после подтверждения администратором).
- Подтверждение оплат администраторами (поддерживает inline-кнопки).
- Поддержка резервирования/временных покупок (Pending purchases).
- Поддержка Redis для кеша/состояния и PostgreSQL через SQLAlchemy.
- Миграции базы данных через Alembic.
- Docker для быстрого развёртывания.

---

## Быстрый запуск (Docker)
1. Клонируйте репозиторий:
   
   ```bash
   git clone git@github.com:Echways/telegram-loyalty-program-bot.git
   cd telegram-loyalty-program-bot
   ```
2. Создайте файл `.env` рядом с `docker-compose.yml` и заполните обязательные переменные (ниже пример):

   ```
   BOT_TOKEN=123:abc-def
   DB_DSN=postgresql+asyncpg://postgres:postgres@db:5432/bot_db
   RANKS_FILE=./data/ranks.json
   CATALOG_FILE=./data/catalog.json
   REDIS_DSN=redis://redis:6379/0
   ADMINS=123456789  # comma separated list of admin Telegram IDs e.g. "12345,67890"
   ```
3. Поднимите контейнеры:
   
   ```sh
   chmod +x scripts/migrate.sh
   make full
   ```
## Локальный запуск

1. Клонируйте репозиторий:
   
   ```bash
   git clone git@github.com:Echways/telegram-loyalty-program-bot.git
   cd telegram-loyalty-program-bot
   ```
3. Установите зависимости через Poetry:

   ```sh
   pip install poetry
   poetry install --only main
   ```
4. Создайте файл `.env` и заполните обязательные переменные (ниже пример):

   ```
   BOT_TOKEN=123:abc-def
   DB_DSN=postgresql+asyncpg://postgres:postgres@db:5432/bot_db
   RANKS_FILE=./data/ranks.json
   CATALOG_FILE=./data/catalog.json
   REDIS_DSN=redis://redis:6379/0
   ADMINS=123456789  # comma separated list of admin Telegram IDs e.g. "12345,67890"
   ```
5. Примените alembic миграции:
   
   ```sh
   export DATABASE_URL={Ваша DB_DSN}
   alembic upgrade head
   ```
6. Запустите бот:

   ```sh
   python3 app_run.py
   ```
   

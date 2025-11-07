# Baza_Zapchastey

Проект для учета базы запчастей и устройств: автоматизация, парсинг цен через Selenium, совместимость с облачным деплоем Render.

## Старт

- FastAPI backend
- SQLAlchemy (ORM)
- Selenium (для парсинга цен)

**Деплой на Render:**  
Сервис запускается командой:
```
gunicorn src.main:app --bind 0.0.0.0:10000
```
Либо:
```
uvicorn src.main:app --host 0.0.0.0 --port 10000
```

## Структура

- src/ — исходный API (FastAPI)
- requirements.txt — зависимости
- .render.yaml — конфиг для Render
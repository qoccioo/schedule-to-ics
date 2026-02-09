# ETU Schedule → ICS Calendar Exporter

Скрипт для автоматического получения расписания из личного кабинета СПбГЭТУ «ЛЭТИ» и конвертации его в формат `.ics` для импорта в Google / Apple / Outlook Calendar.

## Что делает скрипт? 

- Авторизация через браузер (Playwright)
- Получение расписания через API
- Генерация календаря на семестр

## Установка
Сначала клонируйте репозиторий
### Windows
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1  

pip install -r requirements.txt
python -m playwright install chromium
python schedule_to_ics.py
```
### macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
python -m playwright install chromium
python schedule_to_ics.py
```

## Первый запуск

- Откроется окно браузера
- Нужно войти в личный кабинет
- Сессия сохранится локально, повторный логин не потребуется, если не удалять файл etu_storage.json (cookies могут протухнуть!)
- При успешном запуске создатся файл etu_schedule.ics, смело вставляйте его в свой календарь




import json
import requests
import hashlib 

from datetime import datetime, date, timedelta
from playwright.sync_api import sync_playwright
from ics import Calendar, Event
from dateutil.tz import gettz

TZ = gettz("Europe/Moscow")
DAY_ORDER = [
    "ПОНЕДЕЛЬНИК",
    "ВТОРНИК",
    "СРЕДА",
    "ЧЕТВЕРГ",
    "ПЯТНИЦА",
    "СУББОТА",
    "ВОСКРЕСЕНЬЕ",
]

BYDAY = {"ПОНЕДЕЛЬНИК" : "MO", "ВТОРНИК" : "TU", "СРЕДА" : "WE", "ЧЕТВЕРГ" : "TH", "ПЯТНИЦА" : "FR", "СУББОТА" : "SA", "ВОСКРЕСЕНЬЕ" : "SU"}

SUBJECT_TYPE_MAP = {
    "Лек": "Лекция",
    "Пр": "Практика", 
    "Лаб": "Лабораорная",
}

s = requests.Session()

def stable_uid(*parts: str) -> str:
    s = "||".join(parts)
    h = hashlib.sha1(s.encode("utf-8")).hexdigest()
    return f"{h}@lk.etu.ru"

def day_date(base_monday: date, day_name: str) -> date:
    idx = DAY_ORDER.index(day_name)
    return base_monday + timedelta(days=idx)

def make_dt(d: date, hhmm: str) -> datetime:
    return datetime.fromisoformat(f"{d.isoformat()}T{hhmm}:00").replace(tzinfo=TZ)

def rrule_dt(day_name: str, week_type: str) -> str:
    if week_type == "3":
        return f"RRULE:FREQ=WEEKLY;BYDAY={BYDAY[day_name]}"
    return f"RRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY={BYDAY[day_name]}"

def build_ics_from_schedule(data: dict, weekA_monday: date, weeks : int = 18) -> Calendar:
    cal = Calendar()
    schedule = data.get("schedule", {})
    group = schedule.get("group", "unknown")
    cal.creator = f"ETU Schedule Exporter (group {group})"

    days = []
    for day in schedule.get("days", []):
        day_name = (day.get("name") or "").upper().strip()
        if day_name in DAY_ORDER:
            days.append((day_name, day.get("lessons", [])))
        
        for w in range(weeks):
            monday = weekA_monday + timedelta(days=7 * w)
            is_A_week = (w % 2 == 0)

            for day_name, lessons in days:
                cur_date = day_date(monday, day_name)

                for l in lessons:
                    name = (l.get("name") or "").strip()
                    start_time = l.get("start_time")
                    end_time = l.get("end_time")
                    week_type = str(l.get("week", "3")).strip()
                    subj_type_short = (l.get("subjectType") or "").strip()
                    subj_type_full = SUBJECT_TYPE_MAP.get(subj_type_short, subj_type_short)

                    if not (name and start_time and end_time):
                        continue

                    if week_type == "1" and not is_A_week:
                        continue
                    if week_type == "2" and is_A_week:
                        continue           

                    e = Event()
                    e.name = f"{name} - {subj_type_full}" if subj_type_full else name
                    e.begin = make_dt(cur_date, start_time)
                    e.end = make_dt(cur_date, end_time)
                    e.uid = stable_uid(group, cur_date.isoformat(), day_name, start_time, end_time, name, week_type, subj_type_full)
                
                    room = (l.get("room") or "").strip()
                    form = (l.get("form") or "").strip()
                    if room:
                        e.location = room
                    elif form == "distant":
                        e.location = "Online"

                    teacher = (l.get("teacher") or "").strip()
                    teacher2 = (l.get("second_teacher") or "").strip()
                    comment = (l.get("comment") or "").strip()

                    desc = []
                    if teacher: desc.append(f"Преподаватель: {teacher}")
                    if teacher2: desc.append(f"Преподаватель (2): {teacher2}")
                    if form: desc.append(f"Формат: {form}")
                    if week_type: desc.append(f"Неделя: {week_type}")
                    if comment: desc.append(f"Комментарий: {comment}")
                    if desc:
                        e.description = "\n".join(desc)
                    
                    cal.events.add(e)

    return cal

def fetch_schedule_json(storage_path: str = "etu_storage.json") -> dict:
    schedule_url = "https://lk.etu.ru/api/schedule"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state = storage_path if _file_exists(storage_path) else None)
        page = context.new_page()

        page.goto("https://lk.etu.ru", wait_until="domcontentloaded")

        resp = page.request.get(schedule_url)
        if resp.status != 200 or not resp.headers.get("content-type", "").lower().startswith("application/json"):
            print("Похоже, ты же не залогинен. Войди в ЛК, потом вернись сюда!")
            input("Нажми Enter после логина, а далее волшебство...")
            
            resp = page.request.get(schedule_url)

        if resp.status != 200:
            raise RuntimeError("Что-то не так! Неправильный статус.")

        context.storage_state(path=storage_path)
        data = resp.json()
        browser.close()
        return data    
    
def _file_exists(path: str) -> bool:
    try:
        with open(path, "rb"):
            return True
        
    except FileNotFoundError:
        return False
    
def main():
    weekA_monday = date(2026, 2, 9)
    data = fetch_schedule_json(storage_path="etu_storage.json")
    with open("schedule.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    cal = build_ics_from_schedule(data, weekA_monday=weekA_monday)
    with open("etu_schedule.ics", "w", encoding="utf-8") as f:
        f.writelines(cal.serialize_iter())

    print("Готово: etu_schedule.ics")
    print("Сессия сохранена в: etu_storage.json")

if __name__ == "__main__":
    main()

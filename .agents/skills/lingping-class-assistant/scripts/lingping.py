#!/usr/bin/env python3
"""Read Lingping schedules/bookings and emit Chinese automation messages."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

SITE = "https://lingpingclub.com"
EMAIL = ""
STATE = Path.home() / ".codex" / "lingping-class-assistant" / "state.json"
CONFIG = Path.home() / ".config" / "lingping" / "config.json"


def configured_timezone() -> ZoneInfo:
    try:
        value = json.loads(CONFIG.read_text()).get("timezone", "Asia/Bangkok")
    except (FileNotFoundError, json.JSONDecodeError):
        value = "Asia/Bangkok"
    try:
        return ZoneInfo(value)
    except (KeyError, TypeError) as exc:
        raise RuntimeError(f"无效时区：{value}") from exc


TZ = configured_timezone()
CATALOGS = {
    "community-online": "695c763e2d652e065db71030",
    "community-chiangmai": "67eab5b337cd4b56a080743f",
    "english-online": "6982e63b245037c5977a9390",
}


def curl(url: str, *, headers: dict[str, str] | None = None, data: dict | None = None,
         allow_404: bool = False) -> str:
    cmd = ["curl", "-sSL", "--retry", "1", "--max-time", "25", "-w", "\n%{http_code}", url]
    for key, value in (headers or {}).items():
        cmd += ["-H", f"{key}: {value}"]
    if data is not None:
        cmd += ["-H", "Content-Type: application/json", "--data", json.dumps(data)]
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"HTTP request failed: {url}")
    body, _, status = result.stdout.rpartition("\n")
    if status == "404" and allow_404:
        return '{"data": []}'
    if not status.startswith("2"):
        raise RuntimeError(f"网站请求失败（HTTP {status}）")
    return body


def client_config() -> tuple[str, str, str]:
    config = curl(f"{SITE}/config.js")
    auth = curl(f"{SITE}/js/auth.js")
    base = re.search(r'BASE_URL:\s*"([^"]+)"', config)
    key = re.search(r'API_KEY:\s*"([^"]+)"', config)
    password = re.search(r'password:\s*"([^"]+)"', auth)
    if not (base and key and password):
        raise RuntimeError("网站客户端配置格式已变化")
    return base.group(1), key.group(1), password.group(1)


def api_json(url: str, key: str, data: dict | None = None, *, allow_404: bool = False) -> dict:
    raw = curl(url, headers={"X-API-KEY": key}, data=data, allow_404=allow_404)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("网站返回了无法解析的数据") from exc


def settings() -> dict:
    defaults = {
        "lingping_username": EMAIL,
        "timezone": "Asia/Bangkok",
        "calendar_id": "primary",
        "notification": {
            "mode": "auto", "hermes_channel": "",
            "fallbacks": ["google_calendar", "macos_notification"],
            "avoid_duplicates": True,
        },
    }
    try:
        saved = json.loads(CONFIG.read_text())
        defaults.update({k: v for k, v in saved.items() if v})
    except FileNotFoundError:
        pass
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"配置文件格式错误：{CONFIG}") from exc
    if not defaults.get("lingping_username"):
        raise RuntimeError(f"请先在 {CONFIG} 配置 lingping_username")
    return defaults


def notification_status() -> dict:
    cfg = settings().get("notification") or {}
    requested = cfg.get("mode", "auto")
    channel = str(cfg.get("hermes_channel") or "").strip()
    hermes_path = shutil.which("hermes")
    hermes_ok = False
    hermes_detail = "未安装"
    if hermes_path:
        result = subprocess.run(
            [hermes_path, "gateway", "status"], text=True, capture_output=True, timeout=12
        )
        hermes_ok = result.returncode == 0 and channel != ""
        hermes_detail = "已连接并配置通知渠道" if hermes_ok else "入口存在，但未运行或未配置通知渠道"
    calendar_ok = bool(settings().get("calendar_id"))
    macos_ok = sys.platform == "darwin" and shutil.which("osascript") is not None
    if requested == "hermes" and hermes_ok:
        selected = "hermes"
    elif requested == "macos_notification" and macos_ok:
        selected = "macos_notification"
    elif requested == "google_calendar" and calendar_ok:
        selected = "google_calendar"
    elif requested == "auto":
        selected = "hermes" if hermes_ok else ("google_calendar" if calendar_ok else ("macos_notification" if macos_ok else "none"))
    else:
        selected = "google_calendar" if calendar_ok else ("macos_notification" if macos_ok else "none")
    return {
        "requested": requested, "selected": selected,
        "hermes": {"available": hermes_ok, "detail": hermes_detail, "channel": channel or None},
        "google_calendar": {"available": calendar_ok, "calendar_id": settings().get("calendar_id")},
        "macos_notification": {"available": macos_ok},
        "avoid_duplicates": bool(cfg.get("avoid_duplicates", True)),
    }


def login(base: str, key: str, password: str) -> str:
    username = settings()["lingping_username"]
    payload = api_json(f"{base}/auth/login", key, {"username": username, "password": password})
    user_id = payload.get("data", {}).get("userId")
    if not user_id:
        raise RuntimeError("账号登录失败")
    return user_id


def parse_time(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TZ)


def normalize(raw: dict, catalog: str = "") -> dict:
    start = parse_time(raw["startTime"])
    duration = int(raw.get("durationMins") or 60)
    level = str(raw.get("level") or "")
    location = str(raw.get("location") or "").strip()
    online = "online" in level.lower() or "online" in catalog or not location
    hosts = ", ".join(h.get("name", "") for h in raw.get("hosts", []) if h.get("name")) or "待定"
    return {
        "id": str(raw.get("_id") or raw.get("id") or ""),
        "title": str(raw.get("title") or "未命名课程"),
        "start": start,
        "end": start + timedelta(minutes=duration),
        "online": online,
        "location": "线上" if online else (location or "地点待定"),
        "location_url": raw.get("locationUrl") or "",
        "host": hosts,
        "description": str(raw.get("fullDescription") or raw.get("shortDescription") or "课程内容待网站更新"),
        "full": bool(raw.get("isFull")),
        "canceled": raw.get("maxParticipants") == -1,
        "seats": raw.get("numberOfSeatsLeft"),
    }


def is_english(session: dict) -> bool:
    title = session["title"].lower()
    return "english" in title or "英语" in title or "🇬🇧" in title


def load_data() -> tuple[list[dict], list[dict]]:
    base, key, password = client_config()
    user_id = login(base, key, password)
    now = datetime.now(TZ)
    start = now.date().isoformat()
    end = (now.date() + timedelta(days=9)).isoformat()
    sessions: dict[str, dict] = {}
    for catalog, level in CATALOGS.items():
        url = f"{base}/reading-sessions?fromDate={start}&toDate={end}&level={level}"
        for raw in api_json(url, key, allow_404=True).get("data") or []:
            item = normalize(raw, catalog)
            if is_english(item):
                sessions[item["id"]] = item
    booking_rows = api_json(
        f"{base}/bookings/future/user/{user_id}", key, allow_404=True
    ).get("data") or []
    bookings = [normalize(row.get("readingSession") or row) for row in booking_rows]
    return sorted(sessions.values(), key=lambda x: x["start"]), sorted(bookings, key=lambda x: x["start"])


def calendar_items() -> list[dict]:
    sessions, bookings = load_data()
    booked_ids = {s["id"] for s in bookings}
    items = []
    for s in bookings:
        items.append({
            "source_id": s["id"], "booked": True,
            "title": f"【已报名】{s['title']}",
            "start": s["start"].isoformat(), "end": s["end"].isoformat(),
            "location": s["location"], "reminder_minutes": 60, "transparency": "opaque",
            "description": f"课程内容：{s['description']}\n老师：{s['host']}\n状态：已报名\n来源：{SITE}\nLingping Session ID: {s['id']}",
        })
    for s in sessions:
        if s["id"] in booked_ids or s["online"]:
            continue
        items.append({
            "source_id": s["id"], "booked": False,
            "title": f"【未报名】{s['title']}",
            "start": s["start"].isoformat(), "end": s["end"].isoformat(),
            "location": s["location"], "reminder_minutes": None, "transparency": "transparent",
            "description": f"课程内容：{s['description']}\n老师：{s['host']}\n状态：未报名，仅供查阅\n余位：{s['seats'] if s['seats'] is not None else '待确认'}\n来源：{SITE}\nLingping Session ID: {s['id']}",
        })
    return sorted(items, key=lambda x: x["start"])


def status(s: dict) -> str:
    if s["canceled"]:
        return "已取消"
    if s["full"]:
        return "已满"
    if s["seats"] is not None:
        return f"可报（余 {s['seats']} 位）"
    return "可报"


def line(s: dict, booked: bool = False) -> str:
    place = "线上" if s["online"] else f"清迈线下 · {s['location']}"
    marker = " · 已预定" if booked else f" · {status(s)}"
    return f"- {s['start']:%H:%M}–{s['end']:%H:%M}｜{s['title']}｜{place}｜老师：{s['host']}{marker}"


def print_bookings(bookings: list[dict], tomorrow=None) -> None:
    if not bookings:
        print("暂无未来预定。")
        return
    for s in bookings:
        mark = "（明天）" if tomorrow and s["start"].date() == tomorrow else ""
        print(f"- {s['start']:%m月%d日 %H:%M} {mark}｜{s['title']}｜{s['location']}｜老师：{s['host']}")


def daily() -> None:
    sessions, bookings = load_data()
    tomorrow = datetime.now(TZ).date() + timedelta(days=1)
    choices = [s for s in sessions if s["start"].date() == tomorrow]
    booked_ids = {s["id"] for s in bookings}
    print(f"Lingping 明日课程更新｜{tomorrow:%Y年%m月%d日}｜清迈时间")
    print("\n一、明天全部英文课程")
    if choices:
        for s in choices:
            print(line(s, s["id"] in booked_ids))
    else:
        print("暂无")
    print("\n二、清迈线下英文课")
    local = [s for s in choices if not s["online"]]
    if local:
        for s in local:
            print(line(s, s["id"] in booked_ids))
    else:
        print("暂无")
    print("\n三、线上英文课")
    online = [s for s in choices if s["online"]]
    if online:
        for s in online:
            print(line(s, s["id"] in booked_ids))
    else:
        print("暂无")
    print("\n四、当前未来预定")
    print_bookings(bookings, tomorrow)
    print(f"\n同步时间：{datetime.now(TZ):%Y-%m-%d %H:%M}（Asia/Bangkok）")


def load_state() -> dict:
    try:
        return json.loads(STATE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {"reminded": {}}


def reminders(force: bool) -> None:
    _, bookings = load_data()
    now = datetime.now(TZ)
    state = load_state()
    reminded = state.setdefault("reminded", {})
    changed = False
    for s in bookings:
        minutes = (s["start"] - now).total_seconds() / 60
        if 55 <= minutes <= 65 and (force or s["id"] not in reminded):
            print(f"上课提醒：你预定的《{s['title']}》将在约 1 小时后开始。")
            print(f"时间：{s['start']:%Y年%m月%d日 %H:%M}（清迈时间）")
            print(f"形式：{'线上' if s['online'] else s['location']}｜老师：{s['host']}")
            if not force:
                reminded[s["id"]] = now.isoformat()
                changed = True
    cutoff = now - timedelta(days=30)
    state["reminded"] = {k: v for k, v in reminded.items() if parse_time(v) >= cutoff}
    if changed:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["daily", "bookings", "reminders", "calendar-json", "notification-status", "self-test"])
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "daily":
            daily()
        elif args.command == "bookings":
            _, bookings = load_data()
            print_bookings(bookings)
        elif args.command == "reminders":
            reminders(args.force)
        elif args.command == "calendar-json":
            print(json.dumps({"calendar_id": settings()["calendar_id"], "items": calendar_items()}, ensure_ascii=False, indent=2))
        elif args.command == "notification-status":
            print(json.dumps(notification_status(), ensure_ascii=False, indent=2))
        else:
            sessions, bookings = load_data()
            print(f"OK: {len(sessions)} English sessions, {len(bookings)} bookings")
        return 0
    except Exception as exc:
        print(f"Lingping 同步失败：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
import asyncio
import json
import logging
import os
import re
import subprocess
import shutil
import time
from mcrcon import MCRcon
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

def require_env(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_int_env(name, default=None, required=False):
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        if required:
            raise RuntimeError(f"Missing required environment variable: {name}")
        return default

    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"Invalid integer value for {name}: {raw}") from exc


def get_int_list_env(name, default=None):
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return [] if default is None else default

    ids = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.append(int(part))
        except ValueError as exc:
            raise RuntimeError(f"Invalid integer in {name}: {part}") from exc
    return ids


# CONFIG (from environment)
TG_TOKEN = require_env("TG_TOKEN")
TG_CHAT_ID = get_int_env("TG_CHAT_ID", required=True)
CHAT_TOPIC_ID = get_int_env("CHAT_TOPIC_ID", required=True)
LOG_TOPIC_ID = get_int_env("LOG_TOPIC_ID", required=True)
RCON_HOST = os.getenv("RCON_HOST", "localhost")
RCON_PORT = get_int_env("RCON_PORT", default=25575)
RCON_PASSWORD = require_env("RCON_PASSWORD")
LOG_FILE = os.getenv("LOG_FILE", "/opt/minecraft/server-2/logs/latest.log")
ADMIN_IDS = get_int_list_env("ADMIN_IDS", default=[])
MINECRAFT_SERVICE = os.getenv("MINECRAFT_SERVICE", "minecraft")
BACKUP_SCRIPT = os.getenv("BACKUP_SCRIPT", "/opt/minecraft/backup.sh")
BACKUP_DIR = os.getenv("BACKUP_DIR", "/opt/minecraft/backups")
BACKUP_REMOTE = os.getenv("BACKUP_REMOTE", "gdrive:minecraft-backups/")
BACKUP_RETENTION_DAYS = get_int_env("BACKUP_RETENTION_DAYS", default=7)
HEALTH_DISK_PATH = os.getenv("HEALTH_DISK_PATH", "/opt/minecraft")

# Optional mapping of Telegram topic IDs to short names.
# Format: "123:GUIDE,456:LOG,789:NEWS"
TOPIC_MAP_RAW = os.getenv("TOPIC_MAP", "")
TOPIC_MAP = {}
if TOPIC_MAP_RAW:
    for part in TOPIC_MAP_RAW.split(','):
        if not part.strip():
            continue
        if ':' in part:
            tid, name = part.split(':', 1)
            try:
                TOPIC_MAP[int(tid.strip())] = name.strip()
            except ValueError:
                continue

# PIN topic for coordinate-like messages from Minecraft chat.
# Priority: explicit PIN_TOPIC_ID env -> TOPIC_MAP entry named PIN -> CHAT_TOPIC_ID fallback.
PIN_TOPIC_ID = get_int_env("PIN_TOPIC_ID", default=None)
if PIN_TOPIC_ID is None:
    for tid, name in TOPIC_MAP.items():
        if (name or "").strip().lower() == "pin":
            PIN_TOPIC_ID = tid
            break
if PIN_TOPIC_ID is None:
    PIN_TOPIC_ID = CHAT_TOPIC_ID

BACKUP_JOB = None

PUBLIC_COMMANDS = [
    ("/start", "Bot haqida qisqa ma'lumot"),
    ("/help", "Komandalar ro'yxati"),
    ("/online", "O'yinchilar ro'yxati"),
    ("/tps", "Server TPS/MSPT"),
    ("/time", "O'yin vaqti"),
    ("/status", "Qisqa server holati"),
    ("/ping", "RCON aloqasini tekshirish"),
]

ADMIN_COMMANDS = [
    ("/server <start|stop|restart|status>", "Minecraft service boshqaruvi"),
    ("/backup", "Qo'lda backup ishga tushirish"),
    ("/say <matn>", "Serverga announcement yuborish"),
    ("/op <nick>", "OP berish"),
    ("/deop <nick>", "OP olish"),
    ("/wl <on|off|list|reload|add|remove> [nick]", "Whitelist boshqaruvi"),
    ("/logs [n]", "So'nggi loglar (1..100)"),
    ("/health", "Disk, TPS, service, backup holati"),
    ("/kick <nick> [sabab]", "Playerni kick qilish"),
    ("/ban <nick> [sabab]", "Playerni ban qilish"),
    ("/mc <minecraft_command>", "YANGI: RCON orqali console command ishlatish"),
]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def strip_ansi(text):
    return re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', text)


def strip_mc_format(text):
    return re.sub(r'§.', '', text)


def clean_mc_output(text, max_lines=60, max_chars=3800):
    if not text:
        return ""

    # Remove ANSI and Minecraft formatting codes
    out = strip_ansi(text)
    out = strip_mc_format(out)

    # Remove common log/console prefixes per-line
    lines = [(strip_log_prefix(l) or l).rstrip() for l in out.splitlines()]

    # Drop empty lines at start/end and collapse multiple empties
    cleaned_lines = []
    empty_run = False
    for l in lines:
        if not l.strip():
            if not empty_run:
                cleaned_lines.append("")
            empty_run = True
            continue
        empty_run = False
        cleaned_lines.append(l)

    # Truncate by lines if it's huge
    if len(cleaned_lines) > max_lines:
        head = cleaned_lines[: max_lines // 2]
        tail = cleaned_lines[-(max_lines // 2) :]
        cleaned_lines = head + ["... (output truncated) ..."] + tail

    joined = "\n".join(cleaned_lines).strip()

    # Ensure we don't exceed Telegram limits per chunk
    if len(joined) > max_chars:
        joined = joined[: max_chars - 100] + "\n... (truncated)"

    return joined


def parse_spark_tps(text):
    if not text:
        return None

    cleaned = strip_mc_format(strip_ansi(text)).replace('\r', '').strip()
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]

    tps_vals = None
    mspt_vals = None

    for line in lines:
        m_tps = re.search(r'TPS\s+from\s+last\s+[^:]*:\s*([0-9.,\s]+)', line, flags=re.IGNORECASE)
        if m_tps:
            tps_vals = [v.strip() for v in m_tps.group(1).split(',') if v.strip()]

        m_mspt = re.search(r'MSPT\s+from\s+last\s+[^:]*:\s*([0-9.,\s]+)', line, flags=re.IGNORECASE)
        if m_mspt:
            mspt_vals = [v.strip() for v in m_mspt.group(1).split(',') if v.strip()]

    if tps_vals:
        labels = ["5s", "10s", "1m", "5m", "15m"]
        tps_parts = []
        for i, value in enumerate(tps_vals[:5]):
            label = labels[i] if i < len(labels) else f"t{i + 1}"
            tps_parts.append(f"{label}: {value}")

        msg = "⚡ TPS\n" + " | ".join(tps_parts)

        if mspt_vals:
            mspt_parts = []
            for i, value in enumerate(mspt_vals[:5]):
                label = labels[i] if i < len(labels) else f"t{i + 1}"
                mspt_parts.append(f"{label}: {value}ms")
            msg += "\n🧠 MSPT\n" + " | ".join(mspt_parts)

        return msg

    number_fallback = re.findall(r'\d+(?:\.\d+)?', cleaned)
    if number_fallback:
        return "⚡ TPS: " + ", ".join(number_fallback[:5])

    return cleaned or None


def valid_mc_username(username):
    return bool(re.fullmatch(r'[A-Za-z0-9_]{3,16}', username or ""))


def run_systemctl(action, service_name):
    if action not in {"start", "stop", "restart"}:
        return False, "Noto'g'ri action"

    proc = subprocess.run(
        ["systemctl", action, service_name],
        capture_output=True,
        text=True
    )
    if proc.returncode == 0:
        return True, "OK"

    err = (proc.stderr or proc.stdout or "xatolik").strip()
    return False, err


def get_service_state(service_name):
    proc = subprocess.run(
        ["systemctl", "is-active", service_name],
        capture_output=True,
        text=True
    )
    state = (proc.stdout or proc.stderr or "unknown").strip()
    return state


def human_bytes(value):
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}"
        size /= 1024


def get_latest_backup_info():
    try:
        backups = []
        for name in os.listdir(BACKUP_DIR):
            if name.endswith(".zip"):
                path = os.path.join(BACKUP_DIR, name)
                try:
                    backups.append((os.path.getmtime(path), path, os.path.getsize(path)))
                except OSError:
                    continue
    except FileNotFoundError:
        return None
    except Exception as e:
        logging.error(f"Backup info error: {e}")
        return None

    if not backups:
        return None

    backups.sort(key=lambda item: item[0], reverse=True)
    mtime, path, size = backups[0]
    age_seconds = max(0, int(time.time() - mtime))
    return {
        "path": path,
        "size": size,
        "age_seconds": age_seconds,
    }


def format_age(seconds):
    minutes, sec = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if not parts:
        parts.append(f"{sec}s")
    return " ".join(parts)


def is_admin(update: Update):
    return bool(update.effective_user and update.effective_user.id in ADMIN_IDS)


def build_commands_text(include_admin=False):
    lines = [
        "📚 Minecraft Bridge komandalar",
        "",
        "👥 Umumiy komandalar:",
    ]
    for cmd, desc in PUBLIC_COMMANDS:
        lines.append(f"• {cmd} - {desc}")

    if include_admin:
        lines.extend(["", "🛡 Admin komandalar:"])
        for cmd, desc in ADMIN_COMMANDS:
            lines.append(f"• {cmd} - {desc}")


    return "\n".join(lines)


async def reply_chunked(message, text):
    chunks = [text[i:i + 3900] for i in range(0, len(text), 3900)] or [""]
    for chunk in chunks:
        await message.reply_text(chunk)


async def run_backup_job(bot: Bot, requested_by: str):
    global BACKUP_JOB
    try:
        proc = await asyncio.create_subprocess_exec(
            BACKUP_SCRIPT,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await proc.communicate()
        output = (stdout or b"").decode("utf-8", errors="ignore").strip()
        tail = "\n".join(output.splitlines()[-20:]) if output else ""

        if proc.returncode == 0:
            msg = f"💾 Backup tugadi\n👤 {requested_by}\n📁 {BACKUP_DIR}"
            if tail:
                msg += f"\n{tail}"
            await send(bot, msg, topic_id=LOG_TOPIC_ID)
        else:
            msg = f"❌ Backup xato (exit {proc.returncode})\n👤 {requested_by}"
            if tail:
                msg += f"\n{tail}"
            await send(bot, msg, topic_id=LOG_TOPIC_ID)
    except Exception as e:
        logging.exception("Backup job failed")
        await send(bot, f"❌ Backup job xato: {e}", topic_id=LOG_TOPIC_ID)
    finally:
        BACKUP_JOB = None

def rcon_cmd(command):
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as rcon:
            return rcon.command(command)
    except Exception as e:
        logging.error(f"RCON Connection Error: {e}")
        return None

async def send(bot, text, md=False, topic_id=None):
    try:
        target_topic = CHAT_TOPIC_ID if topic_id is None else topic_id
        chunks = [text[i:i + 3900] for i in range(0, len(text), 3900)] or [""]
        for chunk in chunks:
            # Markdown yoqilgan bo'lsa parse_mode ishlatiladi, aks holda oddiy matn yuboriladi
            if md:
                kwargs = {
                    "chat_id": TG_CHAT_ID,
                    "text": chunk,
                    "message_thread_id": target_topic,
                    "parse_mode": "Markdown"
                }
            else:
                kwargs = {
                    "chat_id": TG_CHAT_ID,
                    "text": chunk,
                    "message_thread_id": target_topic
                }

            await bot.send_message(**kwargs)
    except Exception as e:
        logging.error(f"Telegram Send Error (topic={target_topic}): {e}")

# --- KOMANDALAR ---

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != TG_CHAT_ID: return
    if not update.message: return

    # Short welcome — use /help for full command list
    await update.message.reply_text(
        "👋 Bot ishga tushdi. Qo'llanma uchun /help ni bosing."
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != TG_CHAT_ID: return
    if not update.message: return
    text = build_commands_text(include_admin=is_admin(update))
    await reply_chunked(update.message, text)


async def cmd_online(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != TG_CHAT_ID: return
    result = rcon_cmd("list")
    msg = f"👥 {result}" if result else "❌ Server o'chiq yoki RCON ulanmadi"
    await update.message.reply_text(msg)


def is_mc_parser_error(text):
    if not text:
        return False
    low = text.lower()
    return "unknown or incomplete command" in low or "[here]" in low

async def cmd_tps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != TG_CHAT_ID: return
    try:
        result = rcon_cmd("spark tps")
        if not result or is_mc_parser_error(result):
            result = rcon_cmd("mspt")
        if not result or is_mc_parser_error(result):
            result = rcon_cmd("tps")

        parsed = parse_spark_tps(result) if result else None
        if result and is_mc_parser_error(result):
            msg = "❌ TPS komanda serverda mavjud emas yoki plugin yoqilmagan"
        else:
            msg = parsed or "❌ TPS aniqlanmadi"
    except Exception as e:
        logging.error(f"TPS parse error: {e}")
        msg = "❌ TPS o'qishda xatolik"

    await update.message.reply_text(msg)


async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != TG_CHAT_ID: return
    result = rcon_cmd("list")
    if result is None:
        await update.message.reply_text("🏓 RCON javob bermadi")
        return
    await update.message.reply_text("🏓 Pong, server bilan aloqa bor")


async def cmd_mc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != TG_CHAT_ID: return
    if not update.message: return
    if not is_admin(update):
        await update.message.reply_text("⛔ Bu buyruq faqat adminlar uchun")
        return

    if not context.args:
        await update.message.reply_text("❓ Ishlatish: /mc <minecraft_command>")
        return

    command = " ".join(context.args).strip()
    if not command:
        await update.message.reply_text("❌ Command bo'sh")
        return

    # Older syntax compatibility: users often type "gamemode set survival".
    if command.lower().startswith("gamemode set "):
        command = "gamemode " + command[13:].strip()

    result = rcon_cmd(command)
    if result is None:
        await update.message.reply_text("❌ RCON xato yoki server o'chiq")
        return
    cleaned = clean_mc_output(result)

    if not cleaned.strip():
        await update.message.reply_text(f"✅ Bajarildi: {command}")
        return

    if is_mc_parser_error(result):
        pretty = (
            "❌ Minecraft command xato\n"
            f"> {command}\n\n"
            f"{cleaned}\n\n"
            "ℹ️ Eslatma: [HERE] Telegram tugmasi emas, command xato joyini ko'rsatadi."
        )
        await reply_chunked(update.message, pretty)
        return

    await reply_chunked(update.message, f"🖥 CONSOLE\n> {command}\n\n{cleaned}")


async def cmd_health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != TG_CHAT_ID: return
    if not is_admin(update):
        await update.message.reply_text("⛔ Bu buyruq faqat adminlar uchun")
        return

    service_state = get_service_state(MINECRAFT_SERVICE)
    online = rcon_cmd("list") or "Noma'lum"
    tps_raw = rcon_cmd("spark tps") or rcon_cmd("tps") or "Noma'lum"
    tps_pretty = parse_spark_tps(tps_raw) or "Noma'lum"

    try:
        disk = shutil.disk_usage(HEALTH_DISK_PATH)
        disk_msg = f"{human_bytes(disk.used)} / {human_bytes(disk.total)} ({human_bytes(disk.free)} free)"
    except Exception as e:
        logging.error(f"Disk usage error: {e}")
        disk_msg = "Noma'lum"

    backup_info = get_latest_backup_info()
    if backup_info:
        backup_msg = f"{backup_info['path'].split('/')[-1]} ({human_bytes(backup_info['size'])}, {format_age(backup_info['age_seconds'])} old)"
    else:
        backup_msg = "Backup topilmadi"

    msg = (
        "🩺 Server health\n"
        f"🖥 Service: {service_state}\n"
        f"👥 {online}\n"
        f"⚡ {tps_pretty}\n"
        f"💽 Disk: {disk_msg}\n"
        f"💾 Last backup: {backup_msg}"
    )
    await update.message.reply_text(msg)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != TG_CHAT_ID: return

    online = rcon_cmd("list") or "Noma'lum"
    tps_raw = rcon_cmd("spark tps") or rcon_cmd("tps") or "Noma'lum"
    tps_pretty = parse_spark_tps(tps_raw)
    time_raw = rcon_cmd("time query daytime")

    time_msg = "Noma'lum"
    if time_raw:
        m = re.search(r'\d+', time_raw)
        if m:
            ticks = int(m.group())
            if 0 <= ticks < 6000:
                t_str = "Tong"
            elif 6000 <= ticks < 12000:
                t_str = "Kunduz"
            elif 12000 <= ticks < 13000:
                t_str = "Kech"
            else:
                t_str = "Tun"
            time_msg = f"{t_str} ({ticks} ticks)"

    msg = (
        "📊 Server holati\n"
        f"👥 {online}\n"
        f"🕐 {time_msg}\n"
        f"{tps_pretty}"
    )
    await update.message.reply_text(msg)

async def cmd_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != TG_CHAT_ID: return
    result = rcon_cmd("time query daytime")
    if result:
        ticks = int(re.search(r'\d+', result).group())
        if 0 <= ticks < 6000: t_str = "🌅 Tong"
        elif 6000 <= ticks < 12000: t_str = "☀️ Kunduz"
        elif 12000 <= ticks < 13000: t_str = "🌇 Kech"
        else: t_str = "🌙 Tun"
        await update.message.reply_text(f"🕐 {t_str} ({ticks} ticks)")
    else:
        await update.message.reply_text("❌ Xatolik yuz berdi")

async def cmd_kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args:
        await update.message.reply_text("❓ Ishlatish: /kick <username>")
        return
    user = context.args[0]
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "Admin qarori"
    rcon_cmd(f'kick {user} {reason}')
    await update.message.reply_text(f"👢 *{user}* haydaldi. Sabab: {reason}", parse_mode="Markdown")

async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args:
        await update.message.reply_text("❓ Ishlatish: /ban <username>")
        return
    user = context.args[0]
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "Admin qarori"
    rcon_cmd(f'ban {user} {reason}')
    await update.message.reply_text(f"🔨 *{user}* banlandi. Sabab: {reason}", parse_mode="Markdown")


async def cmd_say(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != TG_CHAT_ID: return
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Bu buyruq faqat adminlar uchun")
        return
    if not context.args:
        await update.message.reply_text("❓ Ishlatish: /say <matn>")
        return

    text = " ".join(context.args)
    rcon_cmd(f"say [TG-ADMIN] {text}")
    await update.message.reply_text("✅ Xabar serverga yuborildi")


async def cmd_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != TG_CHAT_ID: return
    if not is_admin(update):
        await update.message.reply_text("⛔ Bu buyruq faqat adminlar uchun")
        return

    count = 20
    if context.args:
        try:
            count = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❓ Ishlatish: /logs [1-100]")
            return

    count = max(1, min(count, 100))

    try:
        with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()[-count:]
    except Exception as e:
        await update.message.reply_text(f"❌ Log o'qib bo'lmadi: {e}")
        return

    cleaned = []
    for line in lines:
        if not line.strip():
            continue
        c = strip_log_prefix(line) or line.strip()
        if not should_forward_log(c):
            continue
        cleaned.append(c)

    if not cleaned:
        await update.message.reply_text("ℹ️ Log bo'sh yoki filtr qilingan")
        return

    body = "\n".join(f"• {line}" for line in cleaned)
    await update.message.reply_text(f" So'nggi {len(cleaned)} ta log:\n{body}")


async def cmd_server(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != TG_CHAT_ID: return
    if not is_admin(update):
        await update.message.reply_text("⛔ Bu buyruq faqat adminlar uchun")
        return

    if not context.args:
        await update.message.reply_text("❓ Ishlatish: /server <start|stop|restart|status>")
        return

    action = context.args[0].lower()
    if action == "status":
        state = get_service_state(MINECRAFT_SERVICE)
        await update.message.reply_text(f"🖥 Server service holati: {state}")
        return

    ok, out = run_systemctl(action, MINECRAFT_SERVICE)
    if ok:
        state = get_service_state(MINECRAFT_SERVICE)
        await update.message.reply_text(f"✅ /server {action} bajarildi. Holat: {state}")
    else:
        await update.message.reply_text(f"❌ /server {action} xato: {out[:300]}")


async def cmd_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BACKUP_JOB

    if update.effective_chat.id != TG_CHAT_ID: return
    if not is_admin(update):
        await update.message.reply_text("⛔ Bu buyruq faqat adminlar uchun")
        return

    if BACKUP_JOB and not BACKUP_JOB.done():
        await update.message.reply_text("⏳ Backup allaqachon ishlayapti")
        return

    requested_by = tg_name(update.effective_user)
    await update.message.reply_text("⏳ Backup boshlandi. Tugaganda LOG topicda natija chiqadi.")
    BACKUP_JOB = asyncio.create_task(run_backup_job(context.bot, requested_by))


async def cmd_op(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != TG_CHAT_ID: return
    if not is_admin(update):
        await update.message.reply_text("⛔ Bu buyruq faqat adminlar uchun")
        return
    if not context.args:
        await update.message.reply_text("❓ Ishlatish: /op <nick>")
        return

    nick = context.args[0].strip()
    if not valid_mc_username(nick):
        await update.message.reply_text("❌ Nick noto'g'ri")
        return

    result = rcon_cmd(f"op {nick}")
    await update.message.reply_text(f"✅ OP: {nick}\n{result or ''}".strip())


async def cmd_deop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != TG_CHAT_ID: return
    if not is_admin(update):
        await update.message.reply_text("⛔ Bu buyruq faqat adminlar uchun")
        return
    if not context.args:
        await update.message.reply_text("❓ Ishlatish: /deop <nick>")
        return

    nick = context.args[0].strip()
    if not valid_mc_username(nick):
        await update.message.reply_text("❌ Nick noto'g'ri")
        return

    result = rcon_cmd(f"deop {nick}")
    await update.message.reply_text(f"✅ DEOP: {nick}\n{result or ''}".strip())


async def cmd_wl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != TG_CHAT_ID: return
    if not is_admin(update):
        await update.message.reply_text("⛔ Bu buyruq faqat adminlar uchun")
        return
    if not context.args:
        await update.message.reply_text("❓ Ishlatish: /wl <on|off|list|reload|add|remove> [nick]")
        return

    action = context.args[0].lower()
    if action in {"on", "off", "list", "reload"}:
        result = rcon_cmd(f"whitelist {action}")
        await update.message.reply_text(result or "✅ Bajarildi")
        return

    if action in {"add", "remove"}:
        if len(context.args) < 2:
            await update.message.reply_text(f"❓ Ishlatish: /wl {action} <nick>")
            return
        nick = context.args[1].strip()
        if not valid_mc_username(nick):
            await update.message.reply_text("❌ Nick noto'g'ri")
            return

        result = rcon_cmd(f"whitelist {action} {nick}")
        await update.message.reply_text(result or "✅ Bajarildi")
        return

    await update.message.reply_text("❌ Noto'g'ri action. /wl <on|off|list|reload|add|remove> [nick]")

# --- CHAT BRIDGE ---

def short_text(text, limit=70):
    if not text:
        return ""
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[:limit - 1] + "…"


def tg_name(user):
    if user is None:
        return "Unknown"
    return user.first_name or user.username or str(user.id)


def strip_log_prefix(line):
    return re.sub(r'^\[[^\]]+\]\s+\[[^\]]+\]:\s*', '', line).strip()


def should_forward_log(line):
    if not line:
        return False

    noisy_patterns = [
        r'Thread RCON Client',
        r'RCON Listener',
        r'RCON running on',
        r'Thread RCON',
        r'UUID of player .* is ',
        r'\[Not Secure\]',
        r'Starting remote control listener',
        r'Thread RCON Listener',
    ]

    for pat in noisy_patterns:
        if re.search(pat, line, flags=re.IGNORECASE):
            return False
    return True


def is_coordinate_text(text):
    if not text:
        return False

    t = text.strip()
    low = t.lower()

    # x: 123 y: 64 z: -321 or x=123, y=64, z=-321
    if re.search(r'\bx\s*[:=]\s*-?\d+(?:\.\d+)?\b.*\by\s*[:=]\s*-?\d+(?:\.\d+)?\b.*\bz\s*[:=]\s*-?\d+(?:\.\d+)?\b', low):
        return True

    # (123, 64, -321) or 123,64,-321 or 123;64;-321
    if re.search(r'\(?\s*-?\d+(?:\.\d+)?\s*[,;]\s*-?\d+(?:\.\d+)?\s*[,;]\s*-?\d+(?:\.\d+)?\s*\)?', t):
        return True

    # For plain space-separated triples, require a coordinate hint keyword
    has_hint = any(k in low for k in ["coord", "koordinat", "xyz", "pos", "location", "loc"])
    if has_hint and re.search(r'(?<!\d)-?\d+(?:\.\d+)?\s+-?\d+(?:\.\d+)?\s+-?\d+(?:\.\d+)?(?!\d)', t):
        return True

    return False

async def tg_to_mc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != TG_CHAT_ID: return
    if not update.message or not update.message.text: return

    user = tg_name(update.message.from_user)
    text = update.message.text

    reply_part = ""
    reply_to = update.message.reply_to_message
    if reply_to:
        # In forum topics Telegram may implicitly set reply_to_message to topic root.
        # Treat it as a real reply only when it's not the topic root message.
        is_topic_root_reply = False
        try:
            if update.message.message_thread_id and reply_to.message_id == update.message.message_thread_id:
                is_topic_root_reply = True
        except Exception:
            pass

        if not is_topic_root_reply:
            replied_text = reply_to.text or reply_to.caption or ""
            replied_text = short_text(replied_text, limit=40)
            if replied_text:
                reply_part = f" {replied_text} —> "
            else:
                reply_part = " "

    # Add topic prefix for topic messages so Minecraft users can see source topic.
    topic_name = None
    try:
        thread_id = update.message.message_thread_id
        if thread_id:
            topic_name = TOPIC_MAP.get(thread_id)
            if not topic_name:
                if thread_id == CHAT_TOPIC_ID:
                    topic_name = "CHAT"
                elif thread_id == LOG_TOPIC_ID:
                    topic_name = "LOG"
                else:
                    topic_name = f"TOPIC-{thread_id}"
    except Exception:
        thread_id = None

    tellraw_payload = []
    tellraw_payload.extend([
        {"text": "[TG] ", "color": "gold"},
    ])
    if topic_name:
        tellraw_payload.append({"text": f"[{topic_name}] ", "color": "dark_aqua"})
    tellraw_payload.extend([
        {"text": user, "color": "yellow"},
        {"text": ": ", "color": "white"},
        {"text": f"{reply_part}{text}", "color": "white"}
    ])
    tellraw = f"tellraw @a {json.dumps(tellraw_payload, ensure_ascii=False)}"
    rcon_cmd(tellraw)

async def mc_to_tg(bot: Bot):
    chat_pattern = re.compile(r'\[.*?INFO\].*?<([^>]+)> (.+)')
    join_pattern = re.compile(r'\[.*?INFO\].*?([a-zA-Z0-9_]+) joined the game')
    leave_pattern = re.compile(r'\[.*?INFO\].*?([a-zA-Z0-9_]+) lost connection: (.+)')

    f = None
    watched_inode = None

    try:
        while True:
            if f is None:
                try:
                    f = open(LOG_FILE, 'r', encoding='utf-8', errors='ignore')
                    st = os.fstat(f.fileno())
                    watched_inode = st.st_ino
                    f.seek(0, os.SEEK_END)
                    logging.info(f"Log tail started: {LOG_FILE} (inode={watched_inode})")
                except Exception as e:
                    logging.error(f"Log open error: {e}")
                    await asyncio.sleep(1)
                    continue

            line = f.readline()
            if not line:
                await asyncio.sleep(0.5)
                try:
                    current = os.stat(LOG_FILE)
                    if current.st_ino != watched_inode or current.st_size < f.tell():
                        logging.info("Log file rotated/truncated, reopening tail")
                        f.close()
                        f = None
                except FileNotFoundError:
                    logging.warning("Log file not found, waiting...")
                    f.close()
                    f = None
                except Exception as e:
                    logging.error(f"Log stat error: {e}")
                continue

            clean_line = strip_log_prefix(line)
            if should_forward_log(clean_line):
                await send(bot, f" {clean_line}", topic_id=LOG_TOPIC_ID)

            # Player join notification -> 6-chi topic'ga yuborish
            if m := join_pattern.search(line):
                player = m.group(1)
                msg = f"✅ {player} serverga kirdi"
                logging.info(f"Forwarding join to Telegram topic 6: {player}")
                await send(bot, msg, topic_id=CHAT_TOPIC_ID)

            # Player leave notification -> 6-chi topic'ga yuborish
            if m := leave_pattern.search(line):
                player = m.group(1)
                reason = m.group(2).strip() if m.group(2) else "Disconnected"
                msg = f"❌ {player} serverdan chiqdi ({reason})"
                logging.info(f"Forwarding leave to Telegram topic 6: {player}")
                await send(bot, msg, topic_id=CHAT_TOPIC_ID)

            if m := chat_pattern.search(line):
                player = m.group(1)
                message = m.group(2)
                target_topic = PIN_TOPIC_ID if is_coordinate_text(message) else CHAT_TOPIC_ID
                logging.info(f"Forwarding MC chat to Telegram topic {target_topic}: {player}")
                await send(bot, f" {player}: {message}", topic_id=target_topic)
    finally:
        if f is not None:
            f.close()

async def main():
    app = Application.builder().token(TG_TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("online", cmd_online))
    app.add_handler(CommandHandler("tps", cmd_tps))
    app.add_handler(CommandHandler("ping", cmd_ping))
    app.add_handler(CommandHandler("health", cmd_health))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("time", cmd_time))
    app.add_handler(CommandHandler("say", cmd_say))
    app.add_handler(CommandHandler("backup", cmd_backup))
    app.add_handler(CommandHandler("logs", cmd_logs))
    app.add_handler(CommandHandler("server", cmd_server))
    app.add_handler(CommandHandler("mc", cmd_mc))
    app.add_handler(CommandHandler("op", cmd_op))
    app.add_handler(CommandHandler("deop", cmd_deop))
    app.add_handler(CommandHandler("wl", cmd_wl))
    app.add_handler(CommandHandler("kick", cmd_kick))
    app.add_handler(CommandHandler("ban", cmd_ban))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tg_to_mc))

    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        logging.info("Bot ishga tushdi!")
        await mc_to_tg(app.bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

# bot.py - Rocket Micro Jobs - Render Ready
import json, os, random, string, asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode
import openpyxl

# ============ CONFIG - Render Env থেকে আসবে ============
BOT_TOKEN = os.getenv("9021082578:AAF75iJ1AkmbfBAlv0W6UxOfAzaklf_-sus")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7952385899"))
CHANNEL_ID = os.getenv("CHANNEL_ID", "@your_channel")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/your_channel")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@DULU_VAI")
MIN_WITHDRAW = int(os.getenv("MIN_WITHDRAW", "100"))
REF_BONUS = 00
WELCOME_BONUS = 00
DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "tasks": [], "withdraws": [], "deposits": [], "settings": {"welcome": "👋 স্বাগতম {name}!\n\n🎁 বোনাস পেয়েছো {bonus} টাকা\n\nনিচ থেকে অপশন বেছে নাও।", "min_withdraw": MIN_WITHDRAW, "spin": "1", "checkin": "1", "leaderboard": "1"}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

db = load_data()

def get_user(uid):
    uid = str(uid)
    if uid not in db["users"]:
        db["users"][uid] = {"id": uid, "name": "", "username": "", "balance": 0, "total_earn": 0, "total_withdraw": 0, "referrals": 0, "referred_by": None, "lang": "bn", "tasks_done": [], "last_checkin": "", "joined_date": str(datetime.now().date())}
        save_data(db)
    return db["users"][uid]

def is_on(key):
    return db["settings"].get(key, "1") == "1"

def main_menu(uid):
    u = get_user(uid)
    kb = [
        [InlineKeyboardButton("💰 ব্যালেন্স", callback_data="balance"), InlineKeyboardButton("🎁 টাস্ক", callback_data="tasks")],
        [InlineKeyboardButton("🎡 Spin", callback_data="spin"), InlineKeyboardButton("📅 Daily Bonus", callback_data="checkin")],
        [InlineKeyboardButton("💸 উইথড্র", callback_data="withdraw"), InlineKeyboardButton("💳 ডিপোজিট", callback_data="deposit")],
        [InlineKeyboardButton("👥 রেফার", callback_data="refer"), InlineKeyboardButton("🏆 লিডারবোর্ড", callback_data="leader")],
        [InlineKeyboardButton("🛒 প্রক্সি শপ", callback_data="proxy"), InlineKeyboardButton("🆘 সাপোর্ট", callback_data="support")],
        [InlineKeyboardButton("🌐 ভাষা / Language", callback_data="lang")],
    ]
    if int(uid) == ADMIN_ID:
        kb.append([InlineKeyboardButton("🛠 অ্যাডমিন প্যানেল", callback_data="admin")])
    return InlineKeyboardMarkup(kb)

async def check_join(update, context):
    try:
        m = await context.bot.get_chat_member(CHANNEL_ID, update.effective_user.id)
        return m.status in ["member", "administrator", "creator"]
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = get_user(user.id)
    u["name"] = user.first_name
    u["username"] = user.username or ""
    if context.args and not u["referred_by"] and context.args[0].startswith("ref"):
        try:
            ref_id = context.args[0][3:]
            if ref_id != str(user.id) and ref_id in db["users"]:
                u["referred_by"] = ref_id
                u["balance"] += WELCOME_BONUS; u["total_earn"] += WELCOME_BONUS
                db["users"][ref_id]["balance"] += REF_BONUS
                db["users"][ref_id]["total_earn"] += REF_BONUS
                db["users"][ref_id]["referrals"] += 1
                await context.bot.send_message(ref_id, f"🎉 নতুন রেফার! +{REF_BONUS} টাকা পেয়েছো!")
        except: pass
    save_data(db)
    if not await check_join(update, context):
        kb = [[InlineKeyboardButton("📢 চ্যানেলে জয়েন করো", url=CHANNEL_LINK)],
              [InlineKeyboardButton("✅ জয়েন করেছি", callback_data="check_join")]]
        await update.message.reply_text("⚠️ প্রথমে আমাদের চ্যানেলে জয়েন করতে হবে!", reply_markup=InlineKeyboardMarkup(kb))
        return
    welcome = db["settings"]["welcome"].format(name=user.first_name, bonus=WELCOME_BONUS)
    await update.message.reply_text(welcome, reply_markup=main_menu(user.id))

async def check_join_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if await check_join(update, context):
        await q.edit_message_text("✅ জয়েন কনফার্ম! এবার বট ব্যবহার করতে পারো।", reply_markup=main_menu(q.from_user.id))
    else:
        await q.answer("❌ এখনো জয়েন করোনি!", show_alert=True)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; uid = str(q.from_user.id); u = get_user(uid); data = q.data; await q.answer()
    if data == "balance":
        await q.edit_message_text(f"💰 *তোমার ব্যালেন্স*\n\n👤 নাম: {u['name']}\n💵 ব্যালেন্স: {u['balance']} টাকা\n📈 মোট আয়: {u['total_earn']} টাকা\n💸 মোট উইথড্র: {u['total_withdraw']} টাকা\n👥 রেফার: {u['referrals']} জন", parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="back")]]))
    elif data == "tasks":
        if not db["tasks"]:
            await q.edit_message_text("😔 এখন কোনো টাস্ক নেই।", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="back")]])); return
        kb = []
        for t in db["tasks"]:
            done = "✅" if t["id"] in u["tasks_done"] else "🎯"
            kb.append([InlineKeyboardButton(f"{done} {t['title']} - {t['reward']}৳", callback_data=f"task_{t['id']}")])
        kb.append([InlineKeyboardButton("🔙 ব্যাক", callback_data="back")])
        await q.edit_message_text("🎁 *টাস্ক লিস্ট:*", parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(kb))
    elif data.startswith("task_"):
        tid = data[5:]; t = next((x for x in db["tasks"] if x["id"] == tid), None)
        if not t: return
        if tid in u["tasks_done"]:
            await q.answer("এই টাস্ক আগেই করেছো!", show_alert=True); return
        u["tasks_done"].append(tid); u["balance"] += t["reward"]; u["total_earn"] += t["reward"]; save_data(db)
        await q.edit_message_text(f"✅ টাস্ক সম্পন্ন! +{t['reward']}৳\nনতুন ব্যালেন্স: {u['balance']}৳", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="back")]]))
    elif data == "spin":
        if not is_on("spin"):
            await q.answer("❌ Spin এখন বন্ধ!", show_alert=True); return
        reward = random.choices([0, 1, 2, 5, 10], weights=[50, 30, 10, 7, 3])[0]
        if reward > 0:
            u["balance"] += reward; u["total_earn"] += reward; save_data(db)
            await q.edit_message_text(f"🎡 Spin! তুমি জিতেছো {reward}৳\nব্যালেন্স: {u['balance']}৳", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="back")]]))
        else:
            await q.edit_message_text("😢 এবার কিছু পাওনি, আবার ট্রাই করো!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="back")]]))
    elif data == "checkin":
        today = str(datetime.now().date())
        if u.get("last_checkin") == today:
            await q.answer("আজকে already নিয়েছো!", show_alert=True); return
        u["last_checkin"] = today; u["balance"] += 5; u["total_earn"] += 5; save_data(db)
        await q.edit_message_text(f"✅ Daily Bonus +5৳\nব্যালেন্স: {u['balance']}৳", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="back")]]))
    elif data == "leader":
        top = sorted(db["users"].values(), key=lambda x: x["total_earn"], reverse=True)[:10]
        txt = "🏆 *লিডারবোর্ড*\n\n"
        for i, x in enumerate(top, 1):
            txt += f"{i}. {x['name']} - {x['total_earn']}৳\n"
        await q.edit_message_text(txt, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="back")]]))
    elif data == "refer":
        link = f"https://t.me/{context.bot.username}?start=ref{uid}"
        await q.edit_message_text(f"👥 *রেফার করে আয় করো!*\n\nপ্রতি রেফারে তুমি পাবে {REF_BONUS}৳\nতোমার বন্ধু পাবে {WELCOME_BONUS}৳\n\n🔗 লিংক:\n`{link}`\n\n👥 মোট রেফার: {u['referrals']} জন", parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="back")]]))
    elif data == "proxy":
        kb = [[InlineKeyboardButton("🇧🇩 BD Proxy - 50৳", callback_data="buy_proxy_bd")],[InlineKeyboardButton("🇺🇸 US Proxy - 80৳", callback_data="buy_proxy_us")],[InlineKeyboardButton("🔙 ব্যাক", callback_data="back")]]
        await q.edit_message_text("🛒 *প্রক্সি শপ*", parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(kb))
    elif data.startswith("buy_proxy"):
        price = 50 if "bd" in data else 80
        if u["balance"] < price:
            await q.answer("❌ ব্যালেন্স কম!", show_alert=True); return
        u["balance"] -= price
        proxy = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}:{random.randint(1000,9999)}"
        save_data(db)
        await q.edit_message_text(f"✅ প্রক্সি কেনা হয়েছে!\n🌐 Proxy: `{proxy}`\n💵 বাকি: {u['balance']}৳", parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="back")]]))
    elif data == "support":
        await q.edit_message_text(f"🆘 *সাপোর্ট*\n\nমেসেজ করো: {SUPPORT_USERNAME}", parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="back")]]))
    elif data == "lang":
        kb = [[InlineKeyboardButton("🇧🇩 বাংলা", callback_data="lang_bn"), InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")],[InlineKeyboardButton("🔙 ব্যাক", callback_data="back")]]
        await q.edit_message_text("🌐 ভাষা বেছে নাও:", reply_markup=InlineKeyboardMarkup(kb))
    elif data.startswith("lang_"):
        u["lang"] = data[5:]; save_data(db); await q.answer("✅ ভাষা বদলে গেছে!")
    elif data == "withdraw":
        context.user_data["await"] = "withdraw"
        await q.edit_message_text(f"💸 *উইথড্র*\nমিনিমাম: {db['settings']['min_withdraw']}৳\nব্যালেন্স: {u['balance']}৳\n\nএভাবে পাঠাও:\n`01712345678 200 bKash`", parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="back")]]))
    elif data == "deposit":
        context.user_data["await"] = "deposit"
        await q.edit_message_text("💳 *ডিপোজিট*\nএভাবে পাঠাও:\n`01712345678 500 9HX123`", parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="back")]]))
    elif data == "back":
        await q.edit_message_text("🏠 মেইন মেনু", reply_markup=main_menu(uid))
    elif data == "admin" and int(uid) == ADMIN_ID:
        await admin_panel(q)
    elif data.startswith("wd_approve_") and int(uid) == ADMIN_ID:
        wid = data[11:]; w = next((x for x in db["withdraws"] if x["id"] == wid), None)
        if w and w["status"] == "pending":
            w["status"] = "approved"; db["users"][w["user_id"]]["total_withdraw"] += w["amount"]; save_data(db)
            await context.bot.send_message(w["user_id"], f"✅ তোমার {w['amount']}৳ উইথড্র Approve হয়েছে!")
            await q.edit_message_text(f"✅ Approve Done - {w['amount']}৳")
    elif data.startswith("wd_reject_") and int(uid) == ADMIN_ID:
        wid = data[10:]; w = next((x for x in db["withdraws"] if x["id"] == wid), None)
        if w and w["status"] == "pending":
            w["status"] = "rejected"; db["users"][w["user_id"]]["balance"] += w["amount"]; save_data(db)
            await context.bot.send_message(w["user_id"], "❌ উইথড্র Reject হয়েছে, টাকা ফেরত দেওয়া হয়েছে।")
            await q.edit_message_text("❌ Rejected")
    elif data.startswith("dep_approve_") and int(uid) == ADMIN_ID:
        did = data[12:]; d = next((x for x in db["deposits"] if x["id"] == did), None)
        if d and d["status"] == "pending":
            d["status"] = "approved"; db["users"][d["user_id"]]["balance"] += d["amount"]; db["users"][d["user_id"]]["total_earn"] += d["amount"]; save_data(db)
            await context.bot.send_message(d["user_id"], f"✅ তোমার {d['amount']}৳ ডিপোজিট Approve হয়েছে!")
            await q.edit_message_text("✅ Deposit Approved")
    elif data.startswith("dep_reject_") and int(uid) == ADMIN_ID:
        did = data[11:]; d = next((x for x in db["deposits"] if x["id"] == did), None)
        if d and d["status"] == "pending":
            d["status"] = "rejected"; save_data(db)
            await context.bot.send_message(d["user_id"], "❌ ডিপোজিট Reject হয়েছে।")
            await q.edit_message_text("❌ Deposit Rejected")
    elif data.startswith("toggle_") and int(uid) == ADMIN_ID:
        key = data[7:]
        db["settings"][key] = "0" if is_on(key) else "1"; save_data(db)
        await q.answer(f"{key} {'OFF' if not is_on(key) else 'ON'}")
        await admin_panel(q)

async def admin_panel(q):
    total_users = len(db["users"])
    pend_wd = len([x for x in db["withdraws"] if x["status"] == "pending"])
    pend_dep = len([x for x in db["deposits"] if x["status"] == "pending"])
    kb = [
        [InlineKeyboardButton(f"👥 ইউজার ({total_users})", callback_data="admin_users"), InlineKeyboardButton(f"💸 উইথড্র ({pend_wd})", callback_data="admin_wd")],
        [InlineKeyboardButton(f"💳 ডিপোজিট ({pend_dep})", callback_data="admin_dep"), InlineKeyboardButton("🎁 টাস্ক যোগ", callback_data="admin_addtask")],
        [InlineKeyboardButton("📢 ব্রডকাস্ট", callback_data="admin_broadcast"), InlineKeyboardButton("📊 এক্সেল", callback_data="admin_export")],
        [InlineKeyboardButton(f"🎡 Spin: {'🟢 ON' if is_on('spin') else '🔴 OFF'}", callback_data="toggle_spin"), InlineKeyboardButton(f"📅 Daily: {'🟢 ON' if is_on('checkin') else '🔴 OFF'}", callback_data="toggle_checkin")],
        [InlineKeyboardButton("✏️ ওয়েলকাম", callback_data="admin_welcome"), InlineKeyboardButton("🔙 ব্যাক", callback_data="back")],
    ]
    await q.edit_message_text("🛠 *অ্যাডমিন প্যানেল*", parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(kb))

async def admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if int(q.from_user.id) != ADMIN_ID: return
    data = q.data; await q.answer()
    if data == "admin_users":
        txt = "👥 *সব ইউজার:*\n\n"
        for uid, u in list(db["users"].items())[:30]:
            txt += f"• {u['name']} (@{u['username']}) - {u['balance']}৳ - ID: {uid}\n"
        await q.edit_message_text(txt, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="admin")]]))
    elif data == "admin_wd":
        pend = [x for x in db["withdraws"] if x["status"] == "pending"]
        if not pend:
            await q.edit_message_text("কোনো পেন্ডিং উইথড্র নেই।", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="admin")]])); return
        for w in pend:
            kb = [[InlineKeyboardButton("✅ Approve", callback_data=f"wd_approve_{w['id']}"), InlineKeyboardButton("❌ Reject", callback_data=f"wd_reject_{w['id']}")]]
            await context.bot.send_message(ADMIN_ID, f"💸 Withdraw\n👤 {w['user_name']} ({w['user_id']})\n📱 {w['number']}\n💵 {w['amount']}৳\n🏦 {w['method']}", reply_markup=InlineKeyboardMarkup(kb))
        await q.edit_message_text("পেন্ডিং উইথড্র নিচে পাঠানো হয়েছে।", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="admin")]]))
    elif data == "admin_dep":
        pend = [x for x in db["deposits"] if x["status"] == "pending"]
        if not pend:
            await q.edit_message_text("কোনো পেন্ডিং ডিপোজিট নেই।", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="admin")]])); return
        for d in pend:
            kb = [[InlineKeyboardButton("✅ Approve", callback_data=f"dep_approve_{d['id']}"), InlineKeyboardButton("❌ Reject", callback_data=f"dep_reject_{d['id']}")]]
            await context.bot.send_message(ADMIN_ID, f"💳 Deposit\n👤 {d['user_name']} ({d['user_id']})\n📱 {d['number']}\n💵 {d['amount']}৳\n🧾 {d['trx']}", reply_markup=InlineKeyboardMarkup(kb))
        await q.edit_message_text("পেন্ডিং ডিপোজিট নিচে পাঠানো হয়েছে।", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="admin")]]))
    elif data == "admin_export":
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Users"
        ws.append(["ID", "Name", "Username", "Balance", "Total Earn", "Total Withdraw", "Referrals", "Date"])
        for uid, u in db["users"].items():
            ws.append([uid, u["name"], u["username"], u["balance"], u["total_earn"], u["total_withdraw"], u["referrals"], u["joined_date"]])
        wb.save("export.xlsx")
        await context.bot.send_document(ADMIN_ID, open("export.xlsx", "rb"), caption="📊 Export Done")
        await q.edit_message_text("✅ এক্সেল পাঠানো হয়েছে!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="admin")]]))
    elif data in ["admin_addtask", "admin_broadcast", "admin_welcome"]:
        context.user_data["await"] = data
        prompts = {"admin_addtask": "টাস্ক পাঠাও এভাবে:\n`টাইটেল | রিওয়ার্ড`\nযেমন: `চ্যানেল জয়েন করো | 20`", "admin_broadcast": "ব্রডকাস্ট মেসেজ লিখে পাঠাও, সবাই পাবে।", "admin_welcome": "নতুন ওয়েলকাম মেসেজ লিখো। {name} দিয়ে নাম আসবে।"}
        await q.edit_message_text(prompts[data], parse_mode=ParseMode.MARKDOWN)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id); u = get_user(uid); txt = update.message.text.strip(); await_state = context.user_data.get("await")
    if int(uid) == ADMIN_ID and await_state:
        if await_state == "admin_addtask":
            try:
                title, reward = txt.split("|"); tid = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
                db["tasks"].append({"id": tid, "title": title.strip(), "reward": int(reward.strip())}); save_data(db)
                await update.message.reply_text(f"✅ টাস্ক যোগ হয়েছে: {title} - {reward}৳")
            except: await update.message.reply_text("❌ ফরম্যাট ভুল! `টাইটেল | রিওয়ার্ড`")
            context.user_data["await"] = None; return
        if await_state == "admin_broadcast":
            count = 0
            for uid2 in list(db["users"].keys()):
                try: await context.bot.send_message(uid2, f"📢 *ব্রডকাস্ট*\n\n{txt}", parse_mode=ParseMode.MARKDOWN); count += 1
                except: pass
                await asyncio.sleep(0.05)
            await update.message.reply_text(f"✅ {count} জনকে পাঠানো হয়েছে."); context.user_data["await"] = None; return
        if await_state == "admin_welcome":
            db["settings"]["welcome"] = txt; save_data(db); await update.message.reply_text("✅ ওয়েলকাম মেসেজ বদলে গেছে!"); context.user_data["await"] = None; return
    if await_state == "withdraw":
        try:
            parts = txt.split(); number, amount, method = parts[0], int(parts[1]), parts[2]
            if amount < db["settings"]["min_withdraw"]:
                await update.message.reply_text(f"❌ মিনিমাম {db['settings']['min_withdraw']}৳"); return
            if amount > u["balance"]:
                await update.message.reply_text("❌ ব্যালেন্স কম!"); return
            u["balance"] -= amount; wid = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            db["withdraws"].append({"id": wid, "user_id": uid, "user_name": u["name"], "number": number, "amount": amount, "method": method, "status": "pending"}); save_data(db)
            await update.message.reply_text("✅ উইথড্র রিকোয়েস্ট পাঠানো হয়েছে!")
            kb = [[InlineKeyboardButton("✅ Approve", callback_data=f"wd_approve_{wid}"), InlineKeyboardButton("❌ Reject", callback_data=f"wd_reject_{wid}")]]
            await context.bot.send_message(ADMIN_ID, f"💸 নতুন উইথড্র!\n👤 {u['name']} ({uid})\n📱 {number}\n💵 {amount}৳\n🏦 {method}", reply_markup=InlineKeyboardMarkup(kb))
        except: await update.message.reply_text("❌ ফরম্যাট ভুল! `নাম্বার পরিমাণ মেথড`")
        context.user_data["await"] = None; return
    if await_state == "deposit":
        try:
            parts = txt.split(); number, amount, trx = parts[0], int(parts[1]), parts[2]
            did = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            db["deposits"].append({"id": did, "user_id": uid, "user_name": u["name"], "number": number, "amount": amount, "trx": trx, "status": "pending"}); save_data(db)
            await update.message.reply_text("✅ ডিপোজিট রিকোয়েস্ট পাঠানো হয়েছে!")
            kb = [[InlineKeyboardButton("✅ Approve", callback_data=f"dep_approve_{did}"), InlineKeyboardButton("❌ Reject", callback_data=f"dep_reject_{did}")]]
            await context.bot.send_message(ADMIN_ID, f"💳 নতুন ডিপোজিট!\n👤 {u['name']} ({uid})\n📱 {number}\n💵 {amount}৳\n🧾 {trx}", reply_markup=InlineKeyboardMarkup(kb))
        except: await update.message.reply_text("❌ ফরম্যাট ভুল! `নাম্বার পরিমাণ TrxID`")
        context.user_data["await"] = None; return
    if txt and not txt.startswith("/"):
        await context.bot.send_message(ADMIN_ID, f"📩 সাপোর্ট\n👤 {u['name']} (@{u['username']}) ID: {uid}\n💬 {txt}")
        await update.message.reply_text("✅ তোমার মেসেজ অ্যাডমিনের কাছে গেছে।")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(admin_callbacks, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(check_join_cb, pattern="^check_join$"))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    print("Bot Running on Render...")
    app.run_polling()

if __name__ == "__main__":
    main()

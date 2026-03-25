import asyncio, random, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, MessageHandler,
                           CallbackQueryHandler, ConversationHandler,
                           ContextTypes, filters)
from config import TELEGRAM_TOKEN, ADMIN_IDS, log
from documents import DocumentGenerator
from automation import Automation, verify_cookie, set_profile, check_approval

# ─── STATES ─────────────────────────────────────
WAIT_COOKIE, WAIT_PROXY = 1, 2

# ─── INDONESIAN DATA ────────────────────────────
UNIVERSITIES = [
    {"full":"Universitas Indonesia",               "short":"UI",    "city":"Depok",      "province":"West Java",      "domain":"ui.ac.id"},
    {"full":"Institut Teknologi Bandung",           "short":"ITB",   "city":"Bandung",    "province":"West Java",      "domain":"itb.ac.id"},
    {"full":"Universitas Gadjah Mada",             "short":"UGM",   "city":"Yogyakarta", "province":"DI Yogyakarta",  "domain":"ugm.ac.id"},
    {"full":"Institut Teknologi Sepuluh Nopember", "short":"ITS",   "city":"Surabaya",   "province":"East Java",      "domain":"its.ac.id"},
    {"full":"Universitas Airlangga",               "short":"UNAIR", "city":"Surabaya",   "province":"East Java",      "domain":"unair.ac.id"},
    {"full":"Universitas Brawijaya",               "short":"UB",    "city":"Malang",     "province":"East Java",      "domain":"ub.ac.id"},
    {"full":"Universitas Diponegoro",              "short":"UNDIP", "city":"Semarang",   "province":"Central Java",   "domain":"undip.ac.id"},
    {"full":"Universitas Padjadjaran",             "short":"UNPAD", "city":"Bandung",    "province":"West Java",      "domain":"unpad.ac.id"},
    {"full":"Universitas Bina Nusantara",          "short":"BINUS", "city":"Jakarta",    "province":"DKI Jakarta",    "domain":"binus.ac.id"},
    {"full":"Universitas Pelita Harapan",          "short":"UPH",   "city":"Tangerang",  "province":"Banten",         "domain":"uph.edu"},
]
NAMES_MALE   = ["Budi Santoso","Ahmad Hidayat","Rudi Gunawan","Hendra Wijaya",
                "Fajar Rahman","Indra Pratama","Gilang Ramadhan","Eko Prasetyo"]
NAMES_FEMALE = ["Siti Nurhaliza","Dewi Lestari","Ayu Puspita","Karina Putri",
                "Maya Salsabila","Rika Amelia","Fitri Handayani","Nanda Permata"]
STREETS      = ["Jl. Merdeka","Jl. Sudirman","Jl. Gatot Subroto",
                "Jl. Pemuda","Jl. Diponegoro","Jl. Ahmad Yani"]

def is_admin(uid): return uid in ADMIN_IDS

def gen_identity():
    name = random.choice(NAMES_MALE + NAMES_FEMALE)
    uni  = random.choice(UNIVERSITIES)
    nim  = f"{random.randint(2021,2024)}{random.randint(10000000,99999999)}"
    addr = f"{random.choice(STREETS)} No.{random.randint(1,150)}, {uni['city']}, {uni['province']}, Indonesia"
    return name, uni, nim, addr

# ─── HANDLERS ───────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Admin only!")
        return
    kb = [[InlineKeyboardButton("🚀 Apply Now", callback_data="apply"),
           InlineKeyboardButton("❓ Help",       callback_data="help")]]
    await update.message.reply_text(
        "🎓 *GITHUB EDUCATION BOT*\n\n"
        "Indonesian auto-mode enabled.\n"
        "Documents, identity, submission — all automatic.\n\n"
        "Tap Apply to start 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "apply":
        await q.message.reply_text(
            "📋 *STEP 1 — GITHUB COOKIE*\n\n"
            "Paste your full GitHub cookie below.\n"
            "_(F12 → Network → Any request → Cookie header)_",
            parse_mode="Markdown"
        )
        return WAIT_COOKIE
    elif q.data == "help":
        await q.message.reply_text(
            "📖 *HOW TO USE*\n\n"
            "1. /start → Tap Apply\n"
            "2. Paste GitHub cookie\n"
            "3. Send proxy or skip\n"
            "4. Bot does everything automatically ✅",
            parse_mode="Markdown"
        )

async def receive_cookie(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cookie = update.message.text.strip()
    if len(cookie) < 100:
        await update.message.reply_text("⚠️ Cookie too short. Copy the full Cookie header.")
        return WAIT_COOKIE

    msg = await update.message.reply_text("⏳ Verifying cookie...")
    ok, info = verify_cookie(cookie)
    if not ok:
        await msg.edit_text(f"❌ Invalid cookie: {info.get('error')}")
        return WAIT_COOKIE

    ctx.user_data["cookie"] = cookie
    ctx.user_data["gh_info"] = info
    await msg.edit_text(
        f"✅ *Account Verified!*\n\n"
        f"👤 Login: `{info['username']}`\n"
        f"📛 Name: {info['name']}\n"
        f"📧 Email: {info['email']}\n"
        f"👥 Followers: {info['followers']}\n"
        f"📁 Repos: {info['repos']}\n"
        f"📅 Age: {info['account_age']} days",
        parse_mode="Markdown"
    )
    kb = [[InlineKeyboardButton("⏭ Skip Proxy", callback_data="skip_proxy")]]
    await update.message.reply_text(
        "📋 *STEP 2 — PROXY (Optional)*\n\n"
        "Send proxy URL or skip.\n"
        "`http://ip:port` or `socks5://ip:port`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return WAIT_PROXY

async def receive_proxy(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["proxy"] = update.message.text.strip()
    await update.message.reply_text("🔗 Proxy saved. Starting automation...")
    return await run_automation(update, ctx)

async def skip_proxy(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ctx.user_data["proxy"] = None
    await q.message.reply_text("⏭ Proxy skipped. Starting automation...")
    return await run_automation(update, ctx)

async def run_automation(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg_obj = update.message or update.callback_query.message
    cookie  = ctx.user_data["cookie"]
    proxy   = ctx.user_data.get("proxy")
    start_t = time.time()

    def elapsed():
        s = int(time.time() - start_t)
        return f"{s//60}m {s%60}s"

    # Generate identity
    name, uni, nim, addr = gen_identity()
    ctx.user_data.update({"name": name, "uni": uni, "nim": nim, "addr": addr})

    await msg_obj.reply_text(
        f"✅ *Identity Generated* | _{elapsed()}_\n\n"
        f"👤 Name:       `{name}`\n"
        f"🏫 University: `{uni['full']}`\n"
        f"📍 Address:    `{addr}`\n"
        f"🪪 NIM:        `{nim}`",
        parse_mode="Markdown"
    )

    # Update GitHub profile
    set_profile(cookie, name, uni['full'], uni['city'])

    # Generate documents
    await msg_obj.reply_text("📄 Generating documents...")
    docgen = DocumentGenerator(name, uni['full'], addr, nim, uni['city'])
    docs   = docgen.generate_all()
    await msg_obj.reply_text(
        f"✅ *Documents Generated* | _{elapsed()}_\n\n"
        f"📝 Enrollment Letter ✅\n"
        f"🪪 Student ID ✅\n"
        f"📋 Transcript ✅",
        parse_mode="Markdown"
    )

    # Browser automation
    await msg_obj.reply_text("🌐 Opening GitHub Education form...")
    bot_instance = Automation(cookie, uni['full'], name, uni['full'])
    result = await bot_instance.run(docs)

    # Send screenshot
    if result.get("screenshot") and os.path.exists(result["screenshot"]):
        with open(result["screenshot"], "rb") as f:
            await msg_obj.reply_photo(f, caption=f"📸 Submitted | {elapsed()}")

    await msg_obj.reply_text(
        f"📤 *Submitted!* | _{elapsed()}_\n\n"
        f"👤 Account: `{ctx.user_data['gh_info']['username']}`\n"
        f"📛 Name: {name}\n"
        f"🏫 University: {uni['full']}\n"
        f"Status: ⏳ PENDING",
        parse_mode="Markdown"
    )

    # Approval polling
    await msg_obj.reply_text("🔄 Checking approval status every 30s...")
    for i in range(20):
        await asyncio.sleep(30)
        status = check_approval(cookie)
        if status == "APPROVED":
            await msg_obj.reply_text(
                f"🎉 *APPROVED!* | _{elapsed()}_\n\n"
                f"✅ Student Developer Pack\n"
                f"✅ GitHub Copilot\n"
                f"✅ GitHub Pro\n\n"
                f"Benefits active in 72 hours!",
                parse_mode="Markdown"
            )
            return ConversationHandler.END
        elif status == "REJECTED":
            await msg_obj.reply_text("❌ Application rejected by GitHub.")
            return ConversationHandler.END
        if (i+1) % 2 == 0:
            await msg_obj.reply_text(
                f"🔄 Check {i+1}/20 | Elapsed: {elapsed()}\n⏳ Still pending..."
            )

    await msg_obj.reply_text(
        f"⏳ *PENDING* | _{elapsed()}_\n\n"
        f"GitHub review takes 2–72 hours.\nCheck back later!",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled. Send /start to restart.")
    return ConversationHandler.END

# ─── MAIN ───────────────────────────────────────
async def main():
    import os
    log.info("GHS Bot starting...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^apply$")],
        states={
            WAIT_COOKIE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_cookie)],
            WAIT_PROXY:  [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_proxy),
                CallbackQueryHandler(skip_proxy, pattern="^skip_proxy$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(conv)

    log.info("GHS Bot ready!")
    await app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    asyncio.run(main())

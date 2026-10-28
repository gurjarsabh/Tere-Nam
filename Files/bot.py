import logging
import requests
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (ApplicationBuilder, ContextTypes, CommandHandler,
                          MessageHandler, filters, CallbackQueryHandler)

from config import (BOT_TOKEN, ADMIN_ID, MAX_FILE_SIZE_MB,
                    CHANNEL_1, CHANNEL_2, CHANNEL_1_LINK, CHANNEL_2_LINK,
                    DEVELOPER, CHANNEL, QR_CODE_PATH)
from database import (get_user, update_user, increment_download, decrement_credit,
                      get_all_users, set_premium, check_premium,
                      get_premium_expiry, save_premium_request, get_premium_request,
                      get_all_premium_requests, delete_premium_request,
                      get_total_users_count, get_premium_users_count, get_pending_count)
from api import (get_fb_video, download_insta_reel, download_snapchat,
                 get_pinterest_download_links, download_youtube)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
user_states = {}


# ============ FORCE JOIN ============
async def is_user_joined(context, user_id):
    try:
        for ch in [CHANNEL_1, CHANNEL_2]:
            m = await context.bot.get_chat_member(chat_id=f"@{ch}", user_id=user_id)
            if m.status in ['left', 'kicked']:
                return False
        return True
    except Exception as e:
        logging.error(f"Force join error: {e}")
        return False


async def send_force_join(update, context):
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel 1", url=CHANNEL_1_LINK)],
        [InlineKeyboardButton("📢 Join Channel 2", url=CHANNEL_2_LINK)],
        [InlineKeyboardButton("✅ I Have Joined", callback_data='check_join')]
    ]
    text = (
        "🚫 Access Denied!\n\n"
        "बॉट use करने के लिए दोनों channels join करें:\n\n"
        f"1️⃣ {CHANNEL_1}\n"
        f"2️⃣ {CHANNEL_2}\n\n"
        "Join करने के बाद I Have Joined दबाएं।"
    )
    rm = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(text, reply_markup=rm, disable_web_page_preview=True)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=rm, disable_web_page_preview=True)


# ============ MAIN MENU ============
def get_main_menu_keyboard(user_id):
    keyboard = [
        [InlineKeyboardButton("📘 Facebook", callback_data='fb'), InlineKeyboardButton("📸 Instagram", callback_data='insta')],
        [InlineKeyboardButton("📌 Pinterest", callback_data='pin'), InlineKeyboardButton("👻 Snapchat", callback_data='snap')],
        [InlineKeyboardButton("▶️ YouTube", callback_data='yt')],
        [InlineKeyboardButton("💎 Buy Premium", callback_data='buy_premium')],
        [InlineKeyboardButton("👤 My Account", callback_data='my_account'), InlineKeyboardButton("❌ Close", callback_data='close')]
    ]
    if user_id == ADMIN_ID:
        keyboard.insert(4, [InlineKeyboardButton("⚙️ Admin Panel", callback_data='admin_panel')])
    return InlineKeyboardMarkup(keyboard)


async def show_main_menu(update, context, edit=False):
    user = update.effective_user
    user_id = user.id
    get_user(user_id)
    update_user(user_id, name=user.full_name, username=user.username or "N/A")

    if not await is_user_joined(context, user_id):
        await send_force_join(update, context)
        return

    u = get_user(user_id)
    prem = "✅ Active" if check_premium(user_id) else "❌ Not Active"
    expiry = get_premium_expiry(user_id) if check_premium(user_id) else "N/A"

    text = (
        f"👋 स्वागत है, {user.full_name}!\n\n"
        f"🆔 Your ID: {user_id}\n"
        f"👤 Username: @{user.username or 'N/A'}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📊 Account:\n"
        f"• Downloads: {u.get('total_downloads', 0)}\n"
        f"• Credits: {u.get('credits', 0)}\n"
        f"• Premium: {prem}\n"
        f"• Expiry: {expiry}\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"Sir Lovekush(Owner): {DEVELOPER}\nChannel: {CHANNEL}"
    )
    rm = get_main_menu_keyboard(user_id)

    if edit and update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, reply_markup=rm)
        except:
            await update.callback_query.message.reply_text(text, reply_markup=rm)
    else:
        if update.message:
            await update.message.reply_text(text, reply_markup=rm)
        elif update.callback_query:
            await update.callback_query.message.reply_text(text, reply_markup=rm)


# ============ START ============
async def start(update, context):
    get_user(update.effective_user.id)
    update_user(update.effective_user.id, name=update.effective_user.full_name,
                username=update.effective_user.username or "N/A")
    await show_main_menu(update, context, edit=False)


# ============ BUTTON HANDLER ============
async def button_click(update, context):
    q = update.callback_query
    await q.answer()
    data = q.data
    user_id = q.from_user.id

    if data == 'check_join':
        if await is_user_joined(context, user_id):
            await q.answer("✅ Thanks!", show_alert=True)
            await show_main_menu(update, context, edit=False)
        else:
            await q.answer("❌ अभी भी दोनों channel join नहीं किए!", show_alert=True)
        return

    if data == 'close':
        await q.message.delete()
        return

    if data == 'my_account':
        u = get_user(user_id)
        prem = "✅ Active" if check_premium(user_id) else "❌ Not Active"
        expiry = get_premium_expiry(user_id) if check_premium(user_id) else "N/A"
        text = (f"👤 My Account\n\n🆔 ID: {user_id}\n📛 Name: {u.get('name')}\n"
                f"🔗 Username: @{u.get('username')}\n📥 Downloads: {u.get('total_downloads', 0)}\n"
                f"💳 Credits: {u.get('credits', 0)}\n💎 Premium: {prem}\n📅 Expiry: {expiry}")
        kb = [[InlineKeyboardButton("🔙 Back", callback_data='back')]]
        await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
        return

    # ============ BUY PREMIUM (UPDATED PRICES) ============
    if data == 'buy_premium':
        kb = [[InlineKeyboardButton("💎 ₹40 - 1 Month", callback_data='plan_40')],
              [InlineKeyboardButton("💎 ₹70 - 2 Months", callback_data='plan_70')],
              [InlineKeyboardButton("🔙 Back", callback_data='back')]]
        await q.message.reply_text(
            "💎 Premium Plans\n\n"
            "• ₹40 → 1 Month\n"
            "• ₹70 → 2 Months\n\n"
            "✅ Unlimited Downloads\n"
            "✅ Priority Support\n"
            "✅ No Ads",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    # ============ PLAN SELECTION (UPDATED) ============
    if data in ['plan_40', 'plan_70']:
        amount = "40" if data == 'plan_40' else "70"
        days = 30 if data == 'plan_40' else 60
        plan = "1 Month" if data == 'plan_40' else "2 Months"
        user_states[user_id] = {'plan': amount, 'days': days, 'plan_name': plan}
        kb = [[InlineKeyboardButton("✅ I Have Paid", callback_data='paid')],
              [InlineKeyboardButton("🔙 Back", callback_data='buy_premium')]]
        if os.path.exists(QR_CODE_PATH):
            with open(QR_CODE_PATH, 'rb') as qr:
                await context.bot.send_photo(chat_id=q.message.chat_id, photo=qr,
                    caption=f"💎 {plan} - ₹{amount}\n\nScan to pay ₹{amount}",
                    reply_markup=InlineKeyboardMarkup(kb))
        else:
            await q.message.reply_text(f"💎 {plan} - ₹{amount}\n\nQR not found. @KingXRomeo",
                                       reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == 'paid':
        user_states[user_id] = user_states.get(user_id, {})
        user_states[user_id]['awaiting_screenshot'] = True
        await q.message.reply_text("📸 अब Payment Screenshot भेजें।",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data='buy_premium')]]))
        return

    if data == 'back':
        if user_id in user_states: del user_states[user_id]
        await show_main_menu(update, context, edit=False)
        return

    if data == 'admin_panel':
        if user_id != ADMIN_ID:
            await q.answer("❌ Admin only!", show_alert=True); return
        kb = [[InlineKeyboardButton("👥 Total Users", callback_data='admin_users')],
              [InlineKeyboardButton("💎 Pending", callback_data='admin_pending')],
              [InlineKeyboardButton("🔙 Back", callback_data='back')]]
        await q.message.reply_text(f"⚙️ Admin Panel\n\n👥 Users: {get_total_users_count()}\n"
                                   f"💎 Premium: {get_premium_users_count()}\n📋 Pending: {get_pending_count()}",
                                   reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == 'admin_users':
        if user_id != ADMIN_ID: return
        users = get_all_users()
        text = f"👥 Total: {len(users)}\n\n"
        for i, (uid, u) in enumerate(list(users.items())[:20], 1):
            prem = "💎" if u.get('premium') else "🆓"
            text += f"{i}. {prem} {u.get('name', 'N/A')}\n   ID: {uid} | DL: {u.get('total_downloads', 0)}\n\n"
        await q.message.reply_text(text[:4000],
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='admin_panel')]]))
        return

    if data == 'admin_pending':
        if user_id != ADMIN_ID: return
        reqs = get_all_premium_requests()
        if not reqs:
            await q.message.reply_text("📋 कोई pending नहीं।",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='admin_panel')]]))
            return
        text = "💎 Pending:\n\n"
        for r in reqs[:10]:
            text += f"• User: {r.get('user_id')}\n  Plan: {r.get('plan')}\n  ₹{r.get('amount')}\n\n"
        await q.message.reply_text(text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='admin_panel')]]))
        return

    u = get_user(user_id)
    is_prem = check_premium(user_id)
    if not is_prem and u.get('credits', 0) <= 0:
        kb = [[InlineKeyboardButton("💎 Buy Premium", callback_data='buy_premium')],
              [InlineKeyboardButton("🔙 Back", callback_data='back')]]
        await q.message.reply_text("🚫 Credits खत्म!\n\n💎 Premium लें।", reply_markup=InlineKeyboardMarkup(kb))
        return

    user_states[user_id] = {'platform': data}
    pnames = {'fb': 'Facebook', 'insta': 'Instagram', 'pin': 'Pinterest', 'snap': 'Snapchat', 'yt': 'YouTube'}
    ct = "♾️ Unlimited" if is_prem else f"{u.get('credits', 0)} credits"
    kb = [[InlineKeyboardButton("🔙 Back", callback_data='back')]]
    await q.message.reply_text(f"✅ {pnames[data]} selected!\n\n💳 {ct}\n\nअब link भेजें:",
        reply_markup=InlineKeyboardMarkup(kb))


# ============ SIZE + DOWNLOAD ============
def check_file_size(url):
    try:
        r = requests.head(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15, allow_redirects=True)
        return int(r.headers.get('content-length', 0))
    except:
        return 0


def download_file(url, timeout=120):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, stream=True, timeout=timeout)
        r.raise_for_status()
        content = b''
        for chunk in r.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
                return None, len(content)
        return content, len(content)
    except:
        return None, 0


async def send_direct_link(msg, url, title, size, platform):
    kb = [[InlineKeyboardButton("🔗 Download Now", url=url)],
          [InlineKeyboardButton("🔙 Back", callback_data='back')]]
    await msg.edit_text(f"⚠️ फाइल बहुत बड़ी!\n\n🎬 {title[:100]}\n📦 {size} MB\n🚫 Limit: 50MB\n📱 {platform}\n\n💡 नीचे button से download करें 👇",
                        reply_markup=InlineKeyboardMarkup(kb))


# ============ MESSAGE HANDLER ============
async def handle_message(update, context):
    user_id = update.message.from_user.id
    url = update.message.text.strip()

    if user_id in user_states and user_states[user_id].get('awaiting_screenshot'):
        await update.message.reply_text("❌ कृपया screenshot भेजें।")
        return

    if user_id not in user_states or 'platform' not in user_states[user_id]:
        await update.message.reply_text("⚠️ पहले /start दें।")
        return

    if not await is_user_joined(context, user_id):
        await send_force_join(update, context)
        return

    platform = user_states[user_id]['platform']
    u = get_user(user_id)
    is_prem = check_premium(user_id)

    if not is_prem and u.get('credits', 0) <= 0:
        await update.message.reply_text("🚫 Credits खत्म! Premium लें।",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 Buy Premium", callback_data='buy_premium')]]))
        return

    pnames = {'fb': 'Facebook', 'insta': 'Instagram', 'pin': 'Pinterest', 'snap': 'Snapchat', 'yt': 'YouTube'}
    msg = await update.message.reply_text("⏳ Processing...")

    try:
        if platform == 'fb':
            data = get_fb_video(url)
        elif platform == 'insta':
            data = download_insta_reel(url)
        elif platform == 'pin':
            data = get_pinterest_download_links(url)
        elif platform == 'snap':
            data = download_snapchat(url)
        elif platform == 'yt':
            data = download_youtube(url)
        else:
            await msg.edit_text("❌ Invalid platform")
            if user_id in user_states: del user_states[user_id]
            return

        if isinstance(data, list):
            data = data[0] if data else {}

        if not isinstance(data, dict) or data.get('status') != 'success':
            err = data.get('message', 'Unknown') if isinstance(data, dict) else 'Failed'
            await msg.edit_text(f"❌ Error: {err}")
            if user_id in user_states: del user_states[user_id]
            return

        if platform == 'yt':
            formats = data.get('video', [])
            if not formats:
                await msg.edit_text("❌ कोई link नहीं मिला")
                if user_id in user_states: del user_states[user_id]
                return
            video_url = formats[0]['url']
            title = data.get('title', 'YouTube Video')
        elif platform == 'pin':
            video_url = data.get('video') or data.get('photo')
            title = data.get('title', 'Pinterest Media')
        else:
            video_url = data.get('video') or data.get('Download Link') or data.get('hd') or data.get('image')
            if isinstance(video_url, dict):
                video_url = video_url.get('hd') or video_url.get('sd')
            title = data.get('title') or data.get('Title') or 'Video'

        if not video_url:
            await msg.edit_text("❌ Link नहीं मिला।")
            if user_id in user_states: del user_states[user_id]
            return

        await msg.edit_text("🔍 Size check...")
        size = check_file_size(video_url)
        size_mb = round(size / (1024 * 1024), 2) if size else 0

        if size > MAX_FILE_SIZE_MB * 1024 * 1024:
            await send_direct_link(msg, video_url, title, size_mb, pnames[platform])
            increment_download(user_id)
            if not is_prem: decrement_credit(user_id)
            if user_id in user_states: del user_states[user_id]
            return

        await msg.edit_text("📥 Downloading...")
        content, dsize = download_file(video_url)

        if content is None:
            actual = round(dsize / (1024 * 1024), 2)
            await send_direct_link(msg, video_url, title, actual, pnames[platform])
            increment_download(user_id)
            if not is_prem: decrement_credit(user_id)
            if user_id in user_states: del user_states[user_id]
            return

        await msg.edit_text("📤 Uploading...")
        actual_mb = round(len(content) / (1024 * 1024), 2)
        lower = video_url.lower()

        try:
            if any(e in lower for e in ['.jpg', '.jpeg', '.png', '.webp']) and 'video' not in lower:
                await update.message.reply_photo(photo=content, caption=f"🖼️ {title[:100]}\n\n📦 {actual_mb} MB\n\nDev: {DEVELOPER}")
            else:
                await update.message.reply_video(video=content, caption=f"🎬 {title[:100]}\n\n📦 {actual_mb} MB\n\nDev: {DEVELOPER}", supports_streaming=True)
        except Exception as e:
            logging.error(f"Send error: {e}")
            await send_direct_link(msg, video_url, title, actual_mb, pnames[platform])

        increment_download(user_id)
        if not is_prem:
            decrement_credit(user_id)
            new_u = get_user(user_id)
            if new_u.get('credits', 0) <= 0:
                await update.message.reply_text("⚠️ 5 free downloads खत्म! Premium लें।",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 Buy Premium", callback_data='buy_premium')]]))

        await msg.delete()
    except Exception as e:
        logging.error(f"Error: {e}")
        try: await msg.edit_text(f"❌ Error: {str(e)}")
        except: pass

    if user_id in user_states: del user_states[user_id]


# ============ PHOTO HANDLER ============
async def handle_photo(update, context):
    user_id = update.message.from_user.id
    if user_id not in user_states or not user_states[user_id].get('awaiting_screenshot'):
        await update.message.reply_text("⚠️ पहले Buy Premium से plan select करें।")
        return
    info = user_states[user_id]
    photo = update.message.photo[-1]
    save_premium_request(user_id, {
        'name': update.message.from_user.full_name,
        'username': update.message.from_user.username or "N/A",
        'plan': info.get('plan_name'), 'amount': info.get('plan'),
        'days': info.get('days'), 'photo_id': photo.file_id
    })
    kb = [[InlineKeyboardButton("✅ Accept", callback_data=f'accept_{user_id}'),
           InlineKeyboardButton("❌ Reject", callback_data=f'reject_{user_id}')]]
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo.file_id,
        caption=f"💎 New Request\n\n👤 {update.message.from_user.full_name}\n🆔 {user_id}\n"
                f"🔗 @{update.message.from_user.username or 'N/A'}\n💎 {info.get('plan_name')}\n💰 ₹{info.get('plan')}",
        reply_markup=InlineKeyboardMarkup(kb))
    await update.message.reply_text("✅ Screenshot भेज दिया!")
    if user_id in user_states: del user_states[user_id]


# ============ ADMIN ACTION ============
async def admin_action(update, context):
    q = update.callback_query
    await q.answer()
    if q.from_user.id != ADMIN_ID:
        await q.answer("❌ Admin only!", show_alert=True); return
    data = q.data
    if data.startswith('accept_'):
        target = int(data.split('_')[1])
        req = get_premium_request(target)
        if req:
            set_premium(target, req.get('days', 30))
            delete_premium_request(target)
            await q.edit_message_caption(caption=f"✅ Accepted: {target}")
            try:
                await context.bot.send_message(chat_id=target,
                    text=f"🎉 Premium Activated!\n\n💎 {req.get('plan')}\n📅 {req.get('days')} days")
            except: pass
    elif data.startswith('reject_'):
        target = int(data.split('_')[1])
        if get_premium_request(target):
            delete_premium_request(target)
            await q.edit_message_caption(caption=f"❌ Rejected: {target}")
            try:
                await context.bot.send_message(chat_id=target, text="❌ Payment Rejected.")
            except: pass


# ============ MAIN ============
if __name__ == '__main__':
    print("🤖 Bot Running on Railway...")
    print(f"👨‍💻 Developer: {DEVELOPER}")
    print(f"📢 Channel: {CHANNEL}")
    print(f"👑 Admin ID: {ADMIN_ID}")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(admin_action, pattern='^(accept_|reject_)'))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

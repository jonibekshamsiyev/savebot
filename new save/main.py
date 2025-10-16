import os
import json
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import yt_dlp

# Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 🔑 BOT TOKENLARI - Environment variables dan olamiz
SAVE_BOT_TOKEN = os.getenv('SAVE_BOT_TOKEN', "8438868628:AAEue9HfCT87vCacS5Dk-DYtag2uUoNMX7k")
ADMIN_BOT_TOKEN = os.getenv('ADMIN_BOT_TOKEN', "8355541045:AAFeNXzJqbACwAEuQxEy-66PpsO0WVnzSW4")

# 👑 ADMIN ID
ADMIN_IDS = [6301812838]

# Botlarni yaratish
save_bot = Bot(token=SAVE_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
admin_bot = Bot(token=ADMIN_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

save_dp = Dispatcher()
admin_dp = Dispatcher()

# ================== FUNKSIYALAR ================== #

def load_users():
    try:
        return {"users": {}, "video_count": 0}
    except Exception as e:
        logger.error(f"Users load xatosi: {e}")
        return {"users": {}, "video_count": 0}

def save_users(data):
    try:
        # Render da fayl saqlash mumkin emas, shuning uchun memoryda saqlaymiz
        pass
    except Exception as e:
        logger.error(f"Users save xatosi: {e}")

def load_channels():
    try:
        return []
    except Exception as e:
        logger.error(f"Channels load xatosi: {e}")
        return []

def save_channels(channels):
    try:
        # Render da fayl saqlash mumkin emas
        pass
    except Exception as e:
        logger.error(f"Channels save xatosi: {e}")

def is_admin(user_id):
    return user_id in ADMIN_IDS

async def check_subscription(user_id, bot):
    """Kanal obunasini tekshirish"""
    try:
        channels = load_channels()
        if not channels:
            return True
            
        for channel in channels:
            try:
                if 't.me/' in channel:
                    channel_username = channel.split('t.me/')[-1]
                    if channel_username.startswith('@'):
                        channel_username = channel_username[1:]
                else:
                    channel_username = channel
                
                member = await bot.get_chat_member(chat_id=f"@{channel_username}", user_id=user_id)
                if member.status in ['left', 'kicked']:
                    return False
            except Exception as e:
                logger.error(f"Kanal tekshirish xatosi {channel}: {e}")
                continue
        return True
    except Exception as e:
        logger.error(f"Obuna tekshirish xatosi: {e}")
        return True

async def get_instagram_video_url(url):
    """Instagram video URL ni olish (yuklamasdan)"""
    try:
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Video URL va ma'lumotlarni qaytarish
            video_url = info.get('url')
            if not video_url:
                # Agar direct URL topilmasa, formatlar orasidan qidirish
                formats = info.get('formats', [])
                for fmt in formats:
                    if fmt.get('ext') == 'mp4' and fmt.get('url'):
                        video_url = fmt['url']
                        break
            
            return {
                'success': True,
                'video_url': video_url,
                'title': info.get('title', 'Instagram video'),
                'description': info.get('description', ''),
                'uploader': info.get('uploader', 'Instagram user'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'view_count': info.get('view_count', 0)
            }
            
    except Exception as e:
        logger.error(f"Instagram video URL olish xatosi: {e}")
        return {'success': False, 'error': str(e)}

# ================== SAVE BOT HANDLERS ================== #

@save_dp.message(Command("start"))
async def save_start_cmd(message: types.Message):
    user_id = str(message.from_user.id)
    
    # Kanal obunasini tekshirish
    is_subscribed = await check_subscription(message.from_user.id, save_bot)
    
    if not is_subscribed:
        channels = load_channels()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        for channel in channels:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=channel)
            ])
        
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="✅ Obuna bo'ldim", callback_data="check_subscription")
        ])
        
        await message.answer(
            "📢 **Botdan foydalanish uchun kanalimizga obuna bo'ling!**\n\n"
            "Quyidagi kanalga obuna bo'ling va 'Obuna bo'ldim' tugmasini bosing:",
            reply_markup=keyboard
        )
        return
    
    users_data = load_users()
    
    if user_id not in users_data["users"]:
        users_data["users"][user_id] = {
            "username": message.from_user.username,
            "first_name": message.from_user.first_name,
            "video_count": 0,
            "joined_date": message.date.isoformat()
        }
        save_users(users_data)

    welcome_message = (
        "👋 Assalomu alaykum! 📷 Instagram videolarini yuklab olish botiga xush kelibsiz!\n\n"
        "Instagram video linkini yuboring va men uni sizga yuklab beraman.\n\n"
        "📎 Misol: https://www.instagram.com/reel/...\n"
        "Yoki: https://www.instagram.com/p/..."
    )
    
    await message.answer(welcome_message)

@save_dp.callback_query(F.data == "check_subscription")
async def save_check_subscription_handler(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    
    is_subscribed = await check_subscription(callback.from_user.id, save_bot)
    
    if is_subscribed:
        await callback.message.delete()
        
        users_data = load_users()
        if user_id not in users_data["users"]:
            users_data["users"][user_id] = {
                "username": callback.from_user.username,
                "first_name": callback.from_user.first_name, 
                "video_count": 0,
                "joined_date": callback.message.date.isoformat()
            }
            save_users(users_data)
        
        welcome_message = (
            "👋 Assalomu alaykum! 📷 Instagram videolarini yuklab olish botiga xush kelibsiz!\n\n"
            "Instagram video linkini yuboring va men uni sizga yuklab beraman.\n\n"
            "📎 Misol: https://www.instagram.com/reel/...\n"
            "Yoki: https://www.instagram.com/p/..."
        )
        
        await callback.message.answer(welcome_message)
            
    else:
        await callback.answer("❌ Hali kanalga obuna bo'lmagansiz!", show_alert=True)

@save_dp.message(F.text)
async def save_handle_links(message: types.Message):
    user_id = str(message.from_user.id)
    url = message.text.strip()
    
    # Avval obunani tekshirish
    is_subscribed = await check_subscription(message.from_user.id, save_bot)
    if not is_subscribed:
        channels = load_channels()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        for channel in channels:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=channel)
            ])
        
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="✅ Obuna bo'ldim", callback_data="check_subscription")
        ])
        
        await message.answer(
            "❌ **Botdan foydalanish uchun avval kanalga obuna bo'ling!**\n\n"
            "Quyidagi kanalga obuna bo'ling va 'Obuna bo'ldim' tugmasini bosing:",
            reply_markup=keyboard
        )
        return
    
    if not url.startswith(('http://', 'https://')):
        await message.answer("❌ Iltimos, to'g'ri Instagram linkini yuboring.")
        return
    
    # Faqat Instagram linklarini qabul qilish
    if 'instagram.com' not in url:
        await message.answer(
            "❌ Faqat Instagram linklarini qo'llab-quvvatlayman.\n\n"
            "📎 Iltimos, Instagram video linkini yuboring:\n"
            "Misol: https://www.instagram.com/reel/...\n"
            "Yoki: https://www.instagram.com/p/..."
        )
        return
    
    loading_msg = await message.answer("📥 Instagram videosi yuklanmoqda...")
    
    try:
        # VIDEO URL NI OLISH (yuklamasdan)
        result = await get_instagram_video_url(url)
        
        if not result['success'] or not result['video_url']:
            await loading_msg.edit_text(
                f"❌ **Yuklash muvaffaqiyatsiz**\n\n"
                f"📹 Platforma: Instagram\n"
                f"🔧 Xato: {result.get('error', 'Video URL topilmadi')}\n\n"
                f"💡 Iltimos, boshqa Instagram linkini yuboring"
            )
            return
        
        # Statistikani yangilash
        users_data = load_users()
        if user_id in users_data["users"]:
            users_data["users"][user_id]["video_count"] += 1
        users_data["video_count"] += 1
        save_users(users_data)
        
        # Video tafsilotlari
        description = result['description']
        uploader = result['uploader']
        duration = result['duration']
        
        # Video caption tayyorlash - format xatosini to'g'irlash
        caption = f"📷 **Instagram Video**\n\n👤 **Muallif:** {uploader}\n"
        
        if duration and duration > 0:
            try:
                minutes = int(duration) // 60
                seconds = int(duration) % 60
                caption += f"⏱ **Davomiylik:** {minutes:02d}:{seconds:02d}\n"
            except (ValueError, TypeError):
                pass  # Duration bilan muammo bo'lsa, o'tkazib yuborish
        
        if description and description.strip():
            # Tavsifni cheklab qo'yish (1024 belgidan oshmasligi uchun)
            if len(description) > 800:
                description = description[:800] + "..."
            caption += f"\n📝 **Tavsif:** {description}\n"
        
        caption += f"\n📥 @savergoo_bot boti orqali yuklab olindi"
        
        # Inline tugma - Faqat "Do'stlarga yuborish" tugmasi
        share_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📤 Do'stlarga yuborish", url=f"tg://share?url={result['video_url']}")]
        ])
        
        await loading_msg.edit_text("✅ Instagram videosi topildi! Yuklanmoqda...")
        
        # Video URL orqali to'g'ridan-to'g'ri yuborish
        try:
            await message.answer_video(
                video=result['video_url'],
                caption=caption,
                reply_markup=share_keyboard
            )
            await loading_msg.delete()
                
        except Exception as e:
            logger.error(f"Video yuborishda xato: {e}")
            await loading_msg.edit_text(f"❌ Video yuborishda xato: {str(e)}")
            
    except Exception as e:
        logger.error(f"Umumiy xato: {e}")
        await loading_msg.edit_text("❌ Kutilmagan xato. Qayta urinib ko'ring.")

# ================== ADMIN BOT HANDLERS ================== #

@admin_dp.message(Command("start"))
async def admin_start_cmd(message: types.Message):
    """Admin bot start"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        return
    
    await admin_panel(message)

@admin_dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    """Admin panel"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Reklama yuborish", callback_data="admin_advert")],
        [InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="admin_add_channel")],
        [InlineKeyboardButton(text="➖ Kanal o'chirish", callback_data="admin_remove_channel")],
        [InlineKeyboardButton(text="📋 Kanallar ro'yxati", callback_data="admin_list_channels")]
    ])
    
    await message.answer(
        "🛠️ **Admin Panel**\n\n"
        "Quyidagi funksiyalardan birini tanlang:",
        reply_markup=keyboard
    )

@admin_dp.callback_query(F.data == "admin_stats")
async def admin_stats_handler(callback: types.CallbackQuery):
    """Statistika"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!")
        return
    
    users_data = load_users()
    channels = load_channels()
    
    total_users = len(users_data["users"])
    total_videos = users_data["video_count"]
    
    active_users = 0
    for user_data in users_data["users"].values():
        if user_data.get("video_count", 0) > 0:
            active_users += 1
    
    # Format xatosini to'g'irlash
    avg_videos = total_videos / max(total_users, 1)
    stats_text = (
        f"📊 **Bot Statistikasi**\n\n"
        f"👥 **Jami foydalanuvchilar:** {total_users} ta\n"
        f"🎥 **Yuklangan videolar:** {total_videos} ta\n"
        f"📢 **Majburiy kanallar:** {len(channels)} ta\n"
        f"🔥 **Faol foydalanuvchilar:** {active_users} ta\n\n"
        f"📈 **O'rtacha video/foydalanuvchi:** {avg_videos:.1f}"
    )
    
    await callback.message.edit_text(stats_text, reply_markup=callback.message.reply_markup)

@admin_dp.callback_query(F.data == "admin_advert")
async def admin_advert_handler(callback: types.CallbackQuery):
    """Reklama yuborish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!")
        return
    
    await callback.message.edit_text(
        "📢 **Reklama yuborish**\n\n"
        "Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")
        ]])
    )

@admin_dp.message(F.text)
async def admin_handle_text(message: types.Message):
    """Admin bot text handler"""
    if not is_admin(message.from_user.id):
        return
    
    # Reklama xabarini yuborish
    users_data = load_users()
    total_users = len(users_data["users"])
    
    sent_count = 0
    error_count = 0
    
    progress_msg = await message.answer(f"📤 Xabar yuborilmoqda... 0/{total_users}")
    
    for user_id in users_data["users"].keys():
        try:
            await save_bot.send_message(int(user_id), message.text)
            sent_count += 1
            if sent_count % 10 == 0:
                await progress_msg.edit_text(f"📤 Xabar yuborilmoqda... {sent_count}/{total_users}")
            await asyncio.sleep(0.1)
        except Exception as e:
            error_count += 1
            logger.error(f"Xabar yuborish xatosi {user_id}: {e}")
    
    await progress_msg.edit_text(
        f"✅ **Reklama yuborildi!**\n\n"
        f"📤 Yuborildi: {sent_count} ta\n"
        f"❌ Xatolar: {error_count} ta\n"
        f"👥 Jami: {total_users} ta"
    )

@admin_dp.callback_query(F.data == "admin_add_channel")
async def admin_add_channel_handler(callback: types.CallbackQuery):
    """Kanal qo'shish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!")
        return
    
    await callback.message.edit_text(
        "➕ **Kanal qo'shish**\n\n"
        "Qo'shmoqchi bo'lgan kanal linkini yuboring:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")
        ]])
    )

@admin_dp.callback_query(F.data == "admin_remove_channel")
async def admin_remove_channel_handler(callback: types.CallbackQuery):
    """Kanal o'chirish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!")
        return
    
    channels = load_channels()
    
    if not channels:
        await callback.message.edit_text(
            "❌ Hozircha kanallar mavjud emas.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")
            ]])
        )
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for channel in channels:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=f"❌ {channel}", callback_data=f"remove_{channel}")
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")
    ])
    
    await callback.message.edit_text(
        "➖ **Kanal o'chirish**\n\n"
        "O'chirmoqchi bo'lgan kanalni tanlang:",
        reply_markup=keyboard
    )

@admin_dp.callback_query(F.data.startswith("remove_"))
async def process_remove_channel(callback: types.CallbackQuery):
    """Kanalni o'chirish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!")
        return
    
    channel_url = callback.data.replace("remove_", "")
    channels = load_channels()
    
    if channel_url in channels:
        channels.remove(channel_url)
        save_channels(channels)
        await callback.message.edit_text(f"✅ Kanal o'chirildi: {channel_url}")
    else:
        await callback.answer("❌ Kanal topilmadi!")

@admin_dp.callback_query(F.data == "admin_list_channels")
async def admin_list_channels_handler(callback: types.CallbackQuery):
    """Kanallar ro'yxati"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!")
        return
    
    channels = load_channels()
    
    if not channels:
        channels_text = "❌ Hozircha kanallar mavjud emas."
    else:
        channels_text = "📢 **Majburiy kanallar ro'yxati:**\n\n"
        for i, channel in enumerate(channels, 1):
            channels_text += f"{i}. {channel}\n"
    
    await callback.message.edit_text(
        channels_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")
        ]])
    )

@admin_dp.callback_query(F.data == "admin_back")
async def admin_back_handler(callback: types.CallbackQuery):
    """Admin panelga qaytish"""
    await admin_panel(callback.message)

# ================== ASOSIY FUNKSIYALAR ================== #

async def run_save_bot():
    """Save botni ishga tushiradi"""
    logger.info("🟢 Save Bot ishga tushmoqda...")
    await save_dp.start_polling(save_bot)

async def run_admin_bot():
    """Admin botni ishga tushiradi"""
    logger.info("🔵 Admin Bot ishga tushmoqda...")
    await admin_dp.start_polling(admin_bot)

async def main():
    """Ikkala botni bir vaqtda ishga tushiradi"""
    logger.info("🚀 Botlar ishga tushmoqda...")
    
    # Ikkala botni parallel ishga tushirish
    await asyncio.gather(
        run_save_bot(),
        run_admin_bot()
    )

if __name__ == "__main__":
    asyncio.run(main())
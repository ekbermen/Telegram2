import os
import re
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from downloader import Downloader

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = ("8782987027:AAHW-fc_ljVioDLwjZJQfIkx-2g2oSsae_g")
DOWNLOAD_DIR = "./downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

downloader = Downloader(DOWNLOAD_DIR)

# ─── URL detection ───────────────────────────────────────────────────────────
URL_PATTERN = re.compile(
    r"(https?://(?:www\.)?"
    r"(?:youtube\.com|youtu\.be|"
    r"instagram\.com|"
    r"pinterest\.com|pin\.it|"
    r"facebook\.com|fb\.watch|fb\.com|"
    r"twitter\.com|x\.com|"
    r"tiktok\.com|"
    r"vimeo\.com|"
    r"soundcloud\.com|"
    r"reddit\.com|"
    r"dailymotion\.com|"
    r"twitch\.tv|"
    r"[^\s]+)"
    r"[^\s]*)",
    re.IGNORECASE,
)

def detect_platform(url: str) -> str:
    url_lower = url.lower()
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "YouTube"
    if "instagram.com" in url_lower:
        return "Instagram"
    if "pinterest.com" in url_lower or "pin.it" in url_lower:
        return "Pinterest"
    if "facebook.com" in url_lower or "fb.watch" in url_lower or "fb.com" in url_lower:
        return "Facebook"
    if "twitter.com" in url_lower or "x.com" in url_lower:
        return "Twitter/X"
    if "tiktok.com" in url_lower:
        return "TikTok"
    if "vimeo.com" in url_lower:
        return "Vimeo"
    if "soundcloud.com" in url_lower:
        return "SoundCloud"
    if "reddit.com" in url_lower:
        return "Reddit"
    if "dailymotion.com" in url_lower:
        return "Dailymotion"
    if "twitch.tv" in url_lower:
        return "Twitch"
    return "Web"

# ─── Handlers ────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Hoş Geldiniz!*\n\n"
        "🔗 Herhangi bir link gönderin, ne indirmek istediğinizi seçin:\n\n"
        "📹 *Video* — 360p, 480p, 720p, 1080p, 1440p, 2K\n"
        "🎵 *Müzik* — MP3 (En yüksek kalite)\n"
        "🖼 *Fotoğraf* — 1080p / Orijinal\n\n"
        "✅ *Desteklenen Siteler:*\n"
        "YouTube • Instagram • Pinterest • Facebook\n"
        "Twitter/X • TikTok • Vimeo • SoundCloud\n"
        "Reddit • Dailymotion • Twitch • Ve daha fazlası!\n\n"
        "📌 Linki doğrudan gönderin, gerisini bot halleder.",
        parse_mode="Markdown",
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Kullanım Kılavuzu*\n\n"
        "1. Herhangi bir video/müzik/fotoğraf linkini gönderin\n"
        "2. Format seçin (Video / Müzik / Fotoğraf)\n"
        "3. Video için kalite seçin\n"
        "4. İndirme başlar ✅\n\n"
        "*Komutlar:*\n"
        "/start — Başlangıç mesajı\n"
        "/help — Bu yardım mesajı\n"
        "/about — Bot hakkında",
        parse_mode="Markdown",
    )

async def about_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Universal Downloader Bot*\n\n"
        "yt-dlp tabanlı güçlü indirici.\n"
        "Desteklenen 1000+ site için çalışır.\n\n"
        "📦 *Kütüphaneler:* yt-dlp, python-telegram-bot\n"
        "👨‍💻 Kendi sunucunuzda çalıştırın.",
        parse_mode="Markdown",
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    match = URL_PATTERN.search(text)

    if not match:
        await update.message.reply_text(
            "❌ Geçerli bir link bulamadım.\n"
            "Lütfen tam URL gönderin. (https://...)"
        )
        return

    url = match.group(0)
    platform = detect_platform(url)
    context.user_data["url"] = url

    keyboard = [
        [
            InlineKeyboardButton("📹 Video İndir", callback_data="type_video"),
            InlineKeyboardButton("🎵 Müzik (MP3)", callback_data="type_audio"),
        ],
        [InlineKeyboardButton("🖼 Fotoğraf İndir", callback_data="type_photo")],
    ]
    await update.message.reply_text(
        f"🔗 *{platform}* linki algılandı!\n\n`{url[:60]}{'...' if len(url)>60 else ''}`\n\n"
        "Ne indirmek istersiniz?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    url = context.user_data.get("url")

    if not url:
        await query.edit_message_text("❌ URL bulunamadı. Lütfen tekrar link gönderin.")
        return

    # ── Format selection ──────────────────────────────────────────────────
    if data == "type_video":
        keyboard = [
            [
                InlineKeyboardButton("360p", callback_data="vid_360"),
                InlineKeyboardButton("480p", callback_data="vid_480"),
                InlineKeyboardButton("720p", callback_data="vid_720"),
            ],
            [
                InlineKeyboardButton("1080p", callback_data="vid_1080"),
                InlineKeyboardButton("1440p", callback_data="vid_1440"),
                InlineKeyboardButton("2K (2048p)", callback_data="vid_2048"),
            ],
            [InlineKeyboardButton("🔙 Geri", callback_data="back")],
        ]
        await query.edit_message_text(
            "📹 *Video kalitesi seçin:*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    if data == "type_audio":
        await _start_download(query, context, url, "audio", None)
        return

    if data == "type_photo":
        await _start_download(query, context, url, "photo", None)
        return

    if data == "back":
        platform = detect_platform(url)
        keyboard = [
            [
                InlineKeyboardButton("📹 Video İndir", callback_data="type_video"),
                InlineKeyboardButton("🎵 Müzik (MP3)", callback_data="type_audio"),
            ],
            [InlineKeyboardButton("🖼 Fotoğraf İndir", callback_data="type_photo")],
        ]
        await query.edit_message_text(
            f"🔗 *{platform}* — Ne indirmek istersiniz?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    # ── Quality selection ─────────────────────────────────────────────────
    quality_map = {
        "vid_360": 360, "vid_480": 480, "vid_720": 720,
        "vid_1080": 1080, "vid_1440": 1440, "vid_2048": 2048,
    }
    if data in quality_map:
        await _start_download(query, context, url, "video", quality_map[data])

async def _start_download(query, context, url: str, media_type: str, quality):
    type_labels = {"video": "📹 Video", "audio": "🎵 Müzik (MP3)", "photo": "🖼 Fotoğraf"}
    qual_label = f" — {quality}p" if quality else ""
    await query.edit_message_text(
        f"⏳ *{type_labels[media_type]}{qual_label}* indiriliyor...\n\n"
        "Bu işlem biraz sürebilir, lütfen bekleyin.",
        parse_mode="Markdown",
    )

    chat_id = query.message.chat_id
    bot = context.bot

    try:
        loop = asyncio.get_event_loop()
        file_path, title = await loop.run_in_executor(
            None,
            lambda: downloader.download(url, media_type, quality),
        )

        if media_type == "video":
            await bot.send_video(
                chat_id=chat_id,
                video=open(file_path, "rb"),
                caption=f"📹 {title}\n\n✅ İndirildi | {quality}p",
                supports_streaming=True,
            )
        elif media_type == "audio":
            await bot.send_audio(
                chat_id=chat_id,
                audio=open(file_path, "rb"),
                caption=f"🎵 {title}\n\n✅ MP3 İndirildi",
            )
        elif media_type == "photo":
            await bot.send_document(
                chat_id=chat_id,
                document=open(file_path, "rb"),
                caption=f"🖼 {title}\n\n✅ Fotoğraf İndirildi",
            )

        await query.edit_message_text(f"✅ *{title}*\n\nBaşarıyla gönderildi!", parse_mode="Markdown")

        # Clean up
        try:
            os.remove(file_path)
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Download error: {e}")
        await query.edit_message_text(
            f"❌ *İndirme hatası!*\n\n`{str(e)[:200]}`\n\n"
            "• Link özel/gizli olabilir\n"
            "• Site desteklenmiyor olabilir\n"
            "• Seçilen kalite mevcut olmayabilir",
            parse_mode="Markdown",
        )

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("about", about_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))

    logger.info("🤖 Bot başlatılıyor...")
    asyncio.run(app.start_polling())

if __name__ == "__main__":
    main()

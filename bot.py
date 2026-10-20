import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from deep_translator import GoogleTranslator

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# User language storage (in-memory)
user_languages = {}

# Branding text for SB24
WELCOME_TEXT = (
    "សូមស្វាគមន៍មកកាន់វេបសាយ SB24 📩🌟\n"
    "ដែលជាវេបសាយធំបំផុតនៅក្នុងស្រុក និង📲មានទំនុកចិត្តបំផុត🎁\n\n"
    "Please select your default target translation language:"
)

def get_language_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🇰🇭 ភាសាខ្មែរ (Khmer)", callback_data="lang_km"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        ],
        [
            InlineKeyboardButton("🇨🇳 中文 (Chinese)", callback_data="lang_zh-cn"),
            InlineKeyboardButton("🇹🇭 ไทย (Thai)", callback_data="lang_th"),
        ],
        [
            InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="lang_vi"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def post_init(application: Application) -> None:
    """Set bot command menu on startup."""
    commands = [
        BotCommand("start", "Start the bot & choose language"),
        BotCommand("language", "Change target translation language"),
        BotCommand("help", "How to use this bot"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands menu set successfully!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message and language selector keyboard on /start."""
    chat_id = update.effective_chat.id
    if chat_id not in user_languages:
        user_languages[chat_id] = "km"  # Default language: Khmer

    await update.message.reply_text(
        text=WELCOME_TEXT,
        reply_markup=get_language_keyboard()
    )

async def set_language_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Trigger language selection via command /language."""
    await update.message.reply_text(
        text="🌐 Choose your preferred language for translation:",
        reply_markup=get_language_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message on /help."""
    help_text = (
        "<b>SB24 Translation Help 📩🌟</b>\n\n"
        "1. Use /language to choose your target language.\n"
        "2. Simply send any text message to the bot.\n"
        "3. The bot will automatically translate it for you!"
    )
    await update.message.reply_html(help_text)

async def language_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language selection from inline keyboard."""
    query = update.callback_query
    await query.answer()

    lang_code = query.data.replace("lang_", "")
    user_languages[query.message.chat_id] = lang_code

    lang_names = {
        "km": "🇰🇭 ភាសាខ្មែរ (Khmer)",
        "en": "🇬🇧 English",
        "zh-cn": "🇨🇳 中文 (Chinese)",
        "th": "🇹🇭 ไทย (Thai)",
        "vi": "🇻🇳 Tiếng Việt"
    }

    selected_lang = lang_names.get(lang_code, lang_code)
    await query.edit_message_text(
        text=f"{WELCOME_TEXT}\n\n✅ **Selected Language:** {selected_lang}\n\n"
             f"Send any text message now, and I will translate it for you!"
    )

async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Translate user input to the selected language."""
    chat_id = update.effective_chat.id
    target_lang = user_languages.get(chat_id, "km")
    user_text = update.message.text

    try:
        # Use deep-translator to translate text automatically
        translated_text = GoogleTranslator(source='auto', target=target_lang).translate(user_text)
        
        response_text = (
            f"<b>SB24 Translation 📩🌟</b>\n\n"
            f"<b>Original:</b> {user_text}\n"
            f"<b>Translated ({target_lang}):</b> {translated_text}"
        )
        await update.message.reply_html(response_text)
    except Exception as e:
        logger.error(f"Translation Error: {e}")
        await update.message.reply_text("❌ Failed to translate text. Please try again.")

def main() -> None:
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN environment variable is missing!")

    application = Application.builder().token(token).post_init(post_init).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("language", set_language_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(language_button_callback, pattern="^lang_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_text))

    logger.info("Bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

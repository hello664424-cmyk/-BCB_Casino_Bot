import os
import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Environment variables
TOKEN = os.getenv("BOT_TOKEN")
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "@YourChannelUsername")  # Must start with @

# In-memory storage for user data (Replace with database like SQLite/PostgreSQL for production)
user_balances = {}
user_claims = {}

def get_balance(user_id: int) -> int:
    return user_balances.get(user_id, 100)  # Starting balance 100 credits

def set_balance(user_id: int, amount: int):
    user_balances[user_id] = amount

async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Verifies if the user is subscribed to the boost target channel."""
    if not REQUIRED_CHANNEL or REQUIRED_CHANNEL == "@YourChannelUsername":
        return True
    try:
        member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        if member.status in ["creator", "administrator", "member"]:
            return True
        return False
    except Exception as e:
        logging.error(f"Channel membership check failed: {e}")
        return False

def get_main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🎰 Slots", callback_data="game_slots"),
            InlineKeyboardButton("🎲 Dice", callback_data="game_dice"),
        ],
        [
            InlineKeyboardButton("🎯 Roulette", callback_data="game_roulette"),
            InlineKeyboardButton("🎁 Daily Bonus", callback_data="claim_bonus"),
        ],
        [
            InlineKeyboardButton("💰 My Balance", callback_data="check_balance"),
            InlineKeyboardButton("🚀 Boost Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Check Channel Subscription (Boost system)
    is_subscribed = await check_subscription(user_id, context)
    
    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel to Play", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("✅ Verify Joining", callback_data="verify_subscription")]
        ]
        await update.message.reply_text(
            f"⚠️ **Access Restricted!**\n\nTo play games and earn rewards, please subscribe to our official channel first: {REQUIRED_CHANNEL}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    balance = get_balance(user_id)
    await update.message.reply_text(
        f"🎉 **Welcome to Telegram Casino & Boost Bot!**\n\nYour Current Balance: `{balance}` Credits\nChoose a game or option below to get started!",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # Mandatory Channel Boost Guard
    if not await check_subscription(user_id, context):
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel to Play", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("✅ Verify Joining", callback_data="verify_subscription")]
        ]
        await query.edit_message_text(
            f"❌ You must join {REQUIRED_CHANNEL} before playing!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    data = query.data
    balance = get_balance(user_id)

    if data == "verify_subscription":
        await query.edit_message_text(
            f"✅ **Verification successful!** Welcome!\n\nBalance: `{balance}` Credits",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )

    elif data == "check_balance":
        await query.edit_message_text(
            f"💳 **Account Details**\n\nUser ID: `{user_id}`\nAvailable Balance: `{balance}` Credits",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )

    elif data == "claim_bonus":
        bonus = 50
        set_balance(user_id, balance + bonus)
        await query.edit_message_text(
            f"🎁 **Daily Reward Claimed!**\n\nYou received +`{bonus}` Credits.\nNew Balance: `{balance + bonus}` Credits",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )

    # GAME: SLOTS
    elif data == "game_slots":
        bet = 10
        if balance < bet:
            await query.edit_message_text("❌ Insufficient balance! (Requires 10 Credits)", reply_markup=get_main_menu_keyboard())
            return
        
        symbols = ["🍒", "🍋", "🔔", "7️⃣"]
        reel = [random.choice(symbols) for _ in range(3)]
        
        if reel[0] == reel[1] == reel[2]:
            win = 100
            set_balance(user_id, balance - bet + win)
            res = f"🎰 **JACKPOT!** [{' '.join(reel)}]\nYou won `{win}` Credits!"
        elif reel[0] == reel[1] or reel[1] == reel[2] or reel[0] == reel[2]:
            win = 25
            set_balance(user_id, balance - bet + win)
            res = f"🎰 **MATCH 2!** [{' '.join(reel)}]\nYou won `{win}` Credits!"
        else:
            set_balance(user_id, balance - bet)
            res = f"🎰 **NO MATCH!** [{' '.join(reel)}]\nYou lost `{bet}` Credits."

        await query.edit_message_text(
            f"{res}\n\nNew Balance: `{get_balance(user_id)}` Credits",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )

    # GAME: DICE
    elif data == "game_dice":
        bet = 10
        if balance < bet:
            await query.edit_message_text("❌ Insufficient balance! (Requires 10 Credits)", reply_markup=get_main_menu_keyboard())
            return

        user_roll = random.randint(1, 6)
        bot_roll = random.randint(1, 6)

        if user_roll > bot_roll:
            win = 20
            set_balance(user_id, balance - bet + win)
            msg = f"🎲 You rolled `{user_roll}` vs Bot `{bot_roll}`.\n**YOU WON `{win}` Credits!**"
        elif user_roll < bot_roll:
            set_balance(user_id, balance - bet)
            msg = f"🎲 You rolled `{user_roll}` vs Bot `{bot_roll}`.\n**YOU LOST `{bet}` Credits.**"
        else:
            msg = f"🎲 Both rolled `{user_roll}`.\n**DRAW!** Bet returned."

        await query.edit_message_text(
            f"{msg}\n\nNew Balance: `{get_balance(user_id)}` Credits",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )

    # GAME: ROULETTE
    elif data == "game_roulette":
        bet = 15
        if balance < bet:
            await query.edit_message_text("❌ Insufficient balance! (Requires 15 Credits)", reply_markup=get_main_menu_keyboard())
            return

        outcomes = ["Red 🔴", "Black 🔴", "Green 🟢 (Jackpot)"]
        weights = [0.45, 0.45, 0.10]
        result = random.choices(outcomes, weights=weights)[0]

        if "Green" in result:
            win = 150
            set_balance(user_id, balance - bet + win)
            res = f"🎯 Result: **{result}**\n🔥 **SUPER WIN!** +`{win}` Credits!"
        elif "Red" in result:
            win = 30
            set_balance(user_id, balance - bet + win)
            res = f"🎯 Result: **{result}**\n✨ **WIN!** +`{win}` Credits!"
        else:
            set_balance(user_id, balance - bet)
            res = f"🎯 Result: **{result}**\n💀 **LOST!** -`{bet}` Credits."

        await query.edit_message_text(
            f"{res}\n\nNew Balance: `{get_balance(user_id)}` Credits",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )

def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN environment variable is missing!")
        
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

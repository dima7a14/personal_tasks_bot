from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext, ConversationHandler

from common import logger, conversations
import db
from utils import auth, split_list
from tasks import format_tasks


@auth
def show_lists(update: Update, context: CallbackContext):
    lists = db.get_lists()
    buttons = [[InlineKeyboardButton(l["name"], callback_data=f"list_name={l['name']}")] for l in lists]

    reply_markup = InlineKeyboardMarkup(buttons)
    update.message.reply_text("Your lists:", reply_markup=reply_markup)


def choose_list(list_name: str, update: Update, context: CallbackContext):
    list = db.get_list(list_name)
    tasks = db.get_tasks(list["id"])
    text = format_tasks(tasks)

    context.user_data["current_list"] = list

    return context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text=text,
        parse_mode=ParseMode.HTML,
    )


@auth
def add_list(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        update.message.reply_text("Please write list name:")
        return conversations["add_list"]["name"]
    list_name = " ".join(context.args)
    return save_list(update, context, list_name)


def save_list(update: Update, context: CallbackContext, name: str):
    user = update.message.from_user
    logger.info("User %s created a new list: %s", user.first_name, name)
    created_list = db.add_list(name)
    context.user_data["current_list"] = created_list
    update.message.reply_text("New list was created.")

    return ConversationHandler.END


def handle_list_name(update: Update, context: CallbackContext):
    return save_list(update, context, update.message.text)


@auth
def remove_list(update: Update, context: CallbackContext):
    lists = db.get_lists()
    buttons = [l.get("name") for l in lists]
    reply_markup = ReplyKeyboardMarkup(split_list(buttons, 3))
    update.message.reply_text("Choose list:", reply_markup=reply_markup)

    return conversations["remove_list"]["choose_list"]


def handle_removing_list(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("User %s removed list \"%s\"", user.first_name, update.message.text)
    db.remove_list(update.message.text)
    update.message.reply_text("Deleted.", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END

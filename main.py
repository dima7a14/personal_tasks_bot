import os
from dotenv import load_dotenv
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, ConversationHandler
from telegram.utils.request import Request
from telegram.utils.helpers import escape_markdown

from db import init_db, get_lists, add_list, remove_list, add_task, get_tasks, edit_task
import lists
import tasks
from common import logger, conversations
from utils import auth, split_list


@auth
def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    update.message.reply_text("Hi. Please create or choose task list from existing.")



def handle_error(update: Update, context: CallbackContext):
    logger.warning("Update \"%s\" caused error \"%s\"", update, context.error)


commands = {
    "start": "start",
    "lists": "lists",
    "add_list": "addlist",
    "remove_list": "removelist",
    "tasks": "tasks",
    "add_tasks": "addtasks",
    "done_task": "done",
    "undone_task": "undone",
    "cancel": "cancel",
}


def parse_callback_data(data: str):
    field, value = data.split("=")
    return {"field": field, "value": value}


def callback_handler(update: Update, context: CallbackContext):
    callback_data = update.callback_query.data
    data = parse_callback_data(callback_data)

    if data.get("field") == "list_name":
        return lists.choose_list(data.get("value"), update, context)


def cancel(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("User %s canceled conversation", user.first_name)
    update.message.reply_text("Canceled.")
    return ConversationHandler.END


def main():
    logger.info("Start tasks bot")
    bot_token = os.getenv("bot_token")
    req = Request(connect_timeout=0.5, read_timeout=1, con_pool_size=8)
    bot = Bot(token=bot_token, request=req, )
    updater = Updater(bot=bot, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler(commands["start"], start))
    dp.add_handler(CommandHandler(commands["lists"], lists.show_lists))
    dp.add_handler(CallbackQueryHandler(callback_handler))

    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler(commands["add_list"], lists.add_list)],
        states={
            conversations["add_list"]["name"]: [MessageHandler(Filters.text, lists.handle_list_name)],
        },
        fallbacks=[CommandHandler(commands["cancel"], cancel)],
    ))

    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler(commands["remove_list"], lists.remove_list)],
        states={
            conversations["remove_list"]["choose_list"]: [MessageHandler(Filters.text, lists.handle_removing_list)],
        },
        fallbacks=[CommandHandler(commands["cancel"], cancel)],
    ))

    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler(commands["add_tasks"], tasks.add_tasks)],
        states={
            conversations["add_tasks"]["choose_list"]: [MessageHandler(Filters.text, tasks.choose_list_to_add)],
            conversations["add_tasks"]["handle_tasks"]: [MessageHandler(Filters.text, tasks.handle_adding_task)],
        },
        fallbacks=[CommandHandler(commands["cancel"], cancel)],
    ))

    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler(commands["tasks"], tasks.show_tasks)],
        states={
            conversations["tasks"]["choose_list"]: [MessageHandler(Filters.text, tasks.choose_list_to_show)],
        },
        fallbacks=[CommandHandler(commands["cancel"], cancel)],
    ))

    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler(commands["done_task"], tasks.done_task)],
        states={
            conversations["done_task"]["choose_list"]: [MessageHandler(Filters.text, tasks.choose_list_to_done)],
            conversations["done_task"]["handle_task"]: [MessageHandler(Filters.text, tasks.handle_done_task)],
        },
        fallbacks=[CommandHandler(commands["cancel"], cancel)],
    ))

    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler(commands["undone_task"], tasks.undone_task)],
        states={
            conversations["undone_task"]["choose_list"]: [MessageHandler(Filters.text, tasks.choose_list_to_undone)],
            conversations["undone_task"]["handle_task"]: [MessageHandler(Filters.text, tasks.handle_undone_task)],
        },
        fallbacks=[CommandHandler(commands["cancel"], cancel)],
    ))

    dp.add_error_handler(handle_error)

    updater.start_polling()

    updater.idle()
    logger.info("Stop tasks bot")


if __name__ == "__main__":
    main()

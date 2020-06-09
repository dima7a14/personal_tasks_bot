from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, ParseMode
from telegram.ext import CallbackContext, ConversationHandler

from common import logger, conversations
import db
from utils import auth, split_list


def format_tasks(tasks):
    text = ""

    for i, t in enumerate(tasks):
        start_tag = "<del>" if t.get("done") else ""
        end_tag = "</del>" if t.get("done") else ""
        title = f"{i + 1}. {t.get('title')}"
        text += f"{start_tag}{title}{end_tag}\n"

    if not text:
        text = "You don't have tasks in this list."

    return text


def show_lists(update: Update, msg: str):
    lists = db.get_lists()
    buttons = [l.get("name") for l in lists]
    reply_markup = ReplyKeyboardMarkup(split_list(buttons, 3))
    update.message.reply_text(msg, reply_markup=reply_markup)


@auth
def add_tasks(update: Update, context: CallbackContext):
    if not context.user_data.get("current_list", None):
        show_lists(update, "Please choose list to add tasks")

        return conversations["add_tasks"]["choose_list"]

    buttons = [["Done"]]
    update.message.reply_text("Please add tasks:", reply_markup=ReplyKeyboardMarkup(buttons))

    return conversations["add_tasks"]["handle_tasks"]


def print_tasks(list_id: int):
    tasks = db.get_tasks(list_id)
    return format_tasks(tasks)



def set_current_list(update: Update, context: CallbackContext):
    list_name = update.message.text
    current_list = db.get_list(list_name)
    context.user_data["current_list"] = current_list
    return current_list


def choose_list_to_add(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("User %s started adding tasks for list \"%s\"", user.first_name, update.message.text)
    current_list = set_current_list(update, context)
    existing_tasks = print_tasks(current_list["id"])
    answer = f"Current tasks: \n{existing_tasks}\n\nAdd new tasks:"
    buttons = [["Done"]]

    update.message.reply_text(
        answer,
        reply_markup=ReplyKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML,
    )

    return conversations["add_tasks"]["handle_tasks"]


def handle_adding_task(update: Update, context: CallbackContext):
    user = update.message.from_user
    task = update.message.text
    current_list = context.user_data["current_list"]

    if task == "Done":
        logger.info("User %s finished adding tasks to the list \"%s\"", user.first_name, current_list["name"])
        tasks = db.get_tasks(current_list["id"])
        update.message.reply_text(format_tasks(tasks), reply_markup=ReplyKeyboardRemove())

        return ConversationHandler.END

    logger.info(
        "User %s added task \"%s\" to the list \"%s\"",
        user.first_name,
        task,
        current_list["name"],
    )
    db.add_task(task, False, current_list["id"])

    update.message.reply_text("Task added.")

    return conversations["add_tasks"]["handle_tasks"]


@auth
def show_tasks(update: Update, context: CallbackContext):
    if not context.user_data.get("current_list"):
        show_lists(update, "Please choose list:")
        return conversations["tasks"]["choose_list"]

    current_list = context.user_data["current_list"]
    tasks = print_tasks(current_list["id"])
    update.message.reply_text(tasks, reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.HTML)
    return ConversationHandler.END


def choose_list_to_show(update: Update, context: CallbackContext):
    set_current_list(update, context)
    return show_tasks(update, context)


@auth
def done_task(update: Update, context: CallbackContext):
    if not context.user_data.get("current_list", None):
        show_lists(update, "Please choose list:")
        return conversations["done_task"]["choose_list"]

    if len(context.args) == 0:
        update.message.reply_text("Please write task number")
        return conversations["done_task"]["handle_task"]

    task_number = int(context.args[0])
    return save_task(update, context, task_number, True)


def choose_list_to_edit(update: Update, context: CallbackContext):
    current_list = set_current_list(update, context)
    existing_tasks = print_tasks(current_list["id"])
    answer = f"Current tasks: \n{existing_tasks}\n\nWrite task number:"
    update.message.reply_text(answer, reply_markup=ReplyKeyboardRemove())


def choose_list_to_done(update: Update, context: CallbackContext):
    choose_list_to_edit(update, context)
    return conversations["done_task"]["handle_task"]


def handle_done_task(update: Update, context: CallbackContext):
    task_number = int(update.message.text)
    return save_task(update, context, task_number, True)


def save_task(update: Update, context: CallbackContext, task_number: int, done: bool):
    current_list = context.user_data["current_list"]
    tasks = db.get_tasks(current_list["id"])

    try:
        task = tasks[task_number - 1]
    except IndexError:
        update.message(f"Your task number is invalid - \"{task_number}\".")
        return ConversationHandler.END

    db.edit_task(id=task["id"], title=task["title"], done=done)

    user = update.message.from_user
    value = "done" if done else "undone"
    logger.info("User %s marked task \"%s\" as \"%s\".", user.first_name, task["title"], value)

    update.message.reply_text(f"Task \"{task_number}\" marked as {value}.")

    return ConversationHandler.END


def undone_task(update: Update, context: CallbackContext):
    if not context.user_data.get("current_list"):
        show_lists(update, "Please choose list:")
        return conversations["undone_task"]["choose_list"]

    if len(context.args) == 0:
        update.message.reply_text("Please write task number")
        return conversations["undone_task"]["handle_task"]

    task_number = int(context.args[0])
    return save_task(update, context, task_number, False)


def choose_list_to_undone(update: Update, context: CallbackContext):
    choose_list_to_edit(update, context)
    return conversations["undone_task"]["handle_task"]


def handle_undone_task(update: Update, context: CallbackContext):
    task_number = int(update.message.text)
    return save_task(update, context, task_number, False)

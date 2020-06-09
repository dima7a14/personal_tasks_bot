import os
from dotenv import load_dotenv


allowed_ids = []


def auth(func):
    if len(allowed_ids) == 0:
        load_dotenv()

    allowed_ids.extend([int(id) for id in os.getenv("allowed_ids", "").split(" ")])

    def wrapper(update, *args, **kwargs):
        user = update.message.from_user
        if user["id"] not in allowed_ids:
            return update.message.reply_text("Access Denied")
        return func(update, *args, **kwargs)
    return wrapper


def split_list(l, n: int):
    for i in range(0, len(l), n):
        yield l[i:i+n]

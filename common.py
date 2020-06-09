import logging

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

logger = logging.getLogger("Personal tasks")

conversations = {
    "add_list": {
        "name": "00",
    },
    "remove_list": {
        "choose_list": "10",
    },
    "add_tasks": {
        "choose_list": "20",
        "handle_tasks": "21",
    },
    "tasks": {
        "choose_list": "30",
    },
    "done_task": {
        "choose_list": "40",
        "handle_task": "41",
    },
    "undone_task": {
        "choose_list": "50",
        "handle_task": "51",
    },
}

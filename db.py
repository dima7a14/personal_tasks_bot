import sqlite3


def ensure_connection(func):
    def wrapper(*args, **kwargs):
        with sqlite3.connect("tasks.db") as conn:
            res = func(*args, connection=conn, **kwargs)
        return res
    return wrapper


@ensure_connection
def init_db(connection):
    c = connection.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS lists (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0,
            list_id INTEGER NOT NULL,
            FOREIGN KEY(list_id) REFERENCES lists(id)
        )
    """)

    connection.commit()


@ensure_connection
def add_list(name: str, connection):
    c = connection.cursor()
    c.execute("INSERT INTO lists (name) VALUES (?)", (name,))
    connection.commit()

    return get_list(name)


@ensure_connection
def add_task(title: str, done: bool, list_id: int, connection):
    c = connection.cursor()
    c.execute("INSERT INTO tasks (title, done, list_id) VALUES (?, ?, ?)", (title, done, list_id))
    connection.commit()


def parse_list(list_from_db):
    (id, name) = list_from_db

    return {"id": id, "name": name}


@ensure_connection
def get_lists(connection):
    c = connection.cursor()
    c.execute("SELECT * FROM lists ORDER BY id DESC")
    res = c.fetchall()

    return [parse_list(l) for l in res]


@ensure_connection
def get_list(list_name: str, connection):
    c = connection.cursor()
    c.execute("SELECT * FROM lists WHERE name=?", (list_name,))
    res = c.fetchone()

    return parse_list(res)


def parse_task(task_from_db):
    (id, title, done) = task_from_db
    return {
        "id": id,
        "title": title,
        "done": bool(done),
    }


@ensure_connection
def get_tasks(list_id: int, connection):
    c = connection.cursor()
    c.execute("SELECT id, title, done FROM tasks WHERE list_id=?", (list_id,))
    res = c.fetchall()

    return [parse_task(t) for t in res]


@ensure_connection
def remove_list(name: str, connection):
    c = connection.cursor()
    c.execute("SELECT id FROM lists WHERE name=?", (name,))
    (id,) = c.fetchone()
    c.execute("DELETE FROM lists WHERE id=?", (id,))
    c.execute("DELETE FROM tasks WHERE list_id=?", (id,))
    connection.commit()


@ensure_connection
def edit_task(id: int, title: str, done: bool, connection):
    c = connection.cursor()
    c.execute("UPDATE tasks SET title=?, done=? WHERE id=?", (title, done, id))
    connection.commit()


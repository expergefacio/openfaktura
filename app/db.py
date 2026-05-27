import os
import sqlite3
from flask import g

DATABASE = os.environ.get("DATABASE", "/data/faktura.sqlite")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    with app.app_context():
        db = get_db()

        with app.open_resource("schema.sql") as f:
            db.executescript(f.read().decode("utf-8"))

        db.commit()

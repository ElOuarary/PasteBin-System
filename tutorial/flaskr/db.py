from datetime import datetime
import sqlite3

import click
from flask import current_app, g

def get_db():
    # g is a special object that is unique for each request
    # It is used to store data that might be accessed by multiple functions during the request
    
    # current_app is another special object that points to the Flask application handling the request
    # get_db will be called when the application has been created and is handling a request
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:  db.close()
    
def init_db():
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf-8"))
        
@click.command("init-db")
def init_db_command():
    """Clears the existing data and create a new tables"""
    init_db()
    click.echo("Initializing the database")
    
sqlite3.register_converter(
    "timestamp", lambda v: datetime.fromisoformat(v.decode())
)

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
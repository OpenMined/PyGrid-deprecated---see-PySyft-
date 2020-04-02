from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def get_db_instance():
    global db
    return db

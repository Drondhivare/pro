"""
Run once (or whenever schema.sql changes) to create the database, tables,
and seed data:

    python init_db.py
"""
from database import init_db

if __name__ == "__main__":
    print("Initializing database from schema.sql ...")
    init_db()
    print("Done. Tables and seed data are ready.")

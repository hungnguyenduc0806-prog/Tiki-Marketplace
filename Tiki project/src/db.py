"""
Ket noi PostgreSQL.

Thong tin dang nhap doc tu bien moi truong (file .env), KHONG BAO GIO
viet thang trong code - file .py se bi commit len GitHub, .env thi khong.
"""

import os

import psycopg2
from dotenv import load_dotenv

import config

load_dotenv(config.BASE_DIR / ".env")


def get_conn():
    """Tra ve mot ket noi Postgres moi. Dung trong 'with' de tu dong dong."""
    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "tiki"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", ""),
    )


def run_sql_file(path) -> None:
    """Chay mot file .sql - dung de tao schema."""
    sql = open(path, encoding="utf-8").read()
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql)
    print(f"Da chay {path}")


if __name__ == "__main__":
    # python -m src.db  -> tao bang
    run_sql_file(config.BASE_DIR / "sql" / "01_schema.sql")

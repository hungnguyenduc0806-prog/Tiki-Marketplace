import os
import psycopg2
from dotenv import load_dotenv
import config

load_dotenv(config.BASE_DIR / ".env")


def get_conn():
    return psycopg2.connect(
        host=os.environ["PGHOST"],
        port=os.environ["PGPORT"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
    )


def run_sql_file(path) -> None:
    sql = open(path, encoding="utf-8").read()
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql)
    print(f"Da chay {path}")


if __name__ == "__main__":
    run_sql_file(config.BASE_DIR / "sql" / "01_schema.sql")

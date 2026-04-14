from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
import pyodbc
import os
from dotenv import load_dotenv


load_dotenv()

app = FastAPI()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")


if not all([DB_USER, DB_PASSWORD, DB_SERVER, DB_NAME]):
    raise Exception("Missing database environment variables")


CONN_STR = (
    f"Driver={{ODBC Driver 18 for SQL Server}};"
    f"Server=tcp:{DB_SERVER},1433;"
    f"Database={DB_NAME};"
    f"Uid={DB_USER};"
    f"Pwd={DB_PASSWORD};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=yes;"
)

SCHEMA = "MaksimDarvin_portfolio"

def get_conn():
    return pyodbc.connect(CONN_STR)




class Portfolio(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    author_id: int




@app.post("/init")
def init():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(f"""
    IF NOT EXISTS (
        SELECT * FROM sys.schemas WHERE name = '{SCHEMA}'
    )
    EXEC('CREATE SCHEMA {SCHEMA}')
    """)

    cursor.execute(f"""
    IF NOT EXISTS (
        SELECT * FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = '{SCHEMA}' AND TABLE_NAME = 'portfolios'
    )
    CREATE TABLE {SCHEMA}.portfolios (
        id INT IDENTITY PRIMARY KEY,
        title NVARCHAR(255),
        description NVARCHAR(MAX),
        author_id INT
    )
    """)

    conn.commit()
    conn.close()

    return {"status": "ready"}




@app.get("/portfolios", response_model=List[Portfolio])
def get_all():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(f"SELECT id, title, description, author_id FROM {SCHEMA}.portfolios")
    rows = cursor.fetchall()
    conn.close()

    return [Portfolio(id=r[0], title=r[1], description=r[2], author_id=r[3]) for r in rows]




@app.post("/portfolios")
def create(p: Portfolio):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(f"""
        INSERT INTO {SCHEMA}.portfolios (title, description, author_id)
        VALUES (?, ?, ?)
    """, p.title, p.description, p.author_id)

    conn.commit()
    conn.close()

    return {"status": "created"}
import sqlite3
from pathlib import Path
import pandas as pd
from .config import DB_PATH, DATA_PATH

REQUIRED_COLUMNS=['ticket_id','created_at','category','priority','status','response_time_hrs','resolution_time_hrs','agent_id','customer_rating','issue_summary']

def get_connection():
    DB_PATH.parent.mkdir(parents=True,exist_ok=True); conn=sqlite3.connect(DB_PATH,check_same_thread=False); conn.row_factory=sqlite3.Row; return conn

def _ensure_csv(path):
    if path.exists(): return
    try:
        from . import dataset_payload
        path.parent.mkdir(parents=True,exist_ok=True); dataset_payload.write_csv(path)
    except Exception as exc: raise FileNotFoundError(f'Dataset not found: {path}') from exc

def ingest_csv(csv_path=DATA_PATH):
    _ensure_csv(csv_path); df=pd.read_csv(csv_path); missing=[c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing: raise ValueError(f'Dataset missing required columns: {missing}')
    df=df[REQUIRED_COLUMNS].copy(); df['created_at']=pd.to_datetime(df['created_at'],errors='raise').dt.strftime('%Y-%m-%d %H:%M:%S')
    for col in ['response_time_hrs','resolution_time_hrs','customer_rating']: df[col]=pd.to_numeric(df[col],errors='coerce')
    conn=get_connection()
    try:
        df.to_sql('tickets',conn,if_exists='replace',index=False)
        for col in ['status','priority','category','agent_id','created_at']: conn.execute(f'CREATE INDEX IF NOT EXISTS idx_tickets_{col} ON tickets({col})')
        conn.commit()
    finally: conn.close()
    return len(df)

def initialize_database():
    conn=get_connection()
    try: exists=conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tickets'").fetchone()
    finally: conn.close()
    return ingest_csv() if not exists else table_count()

def table_count():
    conn=get_connection()
    try: return int(conn.execute('SELECT COUNT(*) FROM tickets').fetchone()[0])
    finally: conn.close()

def query_rows(sql,params=()):
    conn=get_connection()
    try: return [dict(r) for r in conn.execute(sql,params).fetchall()]
    finally: conn.close()

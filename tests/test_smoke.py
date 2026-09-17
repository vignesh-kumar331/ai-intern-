from pathlib import Path
import pandas as pd
from app import dataset_payload

ROOT=Path(__file__).parents[1]
DATA=ROOT/'data'/'support_tickets.csv'

def get_df():
    if not DATA.exists(): dataset_payload.write_csv(DATA)
    return pd.read_csv(DATA)

def test_dataset_has_500_rows(): assert len(get_df())==500

def test_required_columns():
    required=['ticket_id','created_at','category','priority','status','response_time_hrs','resolution_time_hrs','agent_id','customer_rating','issue_summary']
    assert list(get_df().columns)==required

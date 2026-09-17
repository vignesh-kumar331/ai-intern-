from pathlib import Path
import pandas as pd

def test_dataset_has_500_rows():
    path = Path(__file__).parents[1] / 'data' / 'support_tickets.csv'
    assert len(pd.read_csv(path)) == 500

def test_required_columns():
    df = pd.read_csv(Path(__file__).parents[1] / 'data' / 'support_tickets.csv')
    required = ['ticket_id','created_at','category','priority','status','response_time_hrs','resolution_time_hrs','agent_id','customer_rating','issue_summary']
    assert list(df.columns) == required

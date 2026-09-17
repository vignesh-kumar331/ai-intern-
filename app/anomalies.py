from .database import query_rows


def detect_anomalies():
    latest = query_rows('SELECT MAX(created_at) AS latest FROM tickets')[0]['latest']
    values = [float(r['resolution_time_hrs']) for r in query_rows('SELECT resolution_time_hrs FROM tickets WHERE resolution_time_hrs IS NOT NULL ORDER BY resolution_time_hrs')]
    if values:
        q1 = values[(len(values)-1)*25//100]; q3 = values[(len(values)-1)*75//100]
        threshold = q3 + 1.5*(q3-q1)
    else: threshold = 0
    long_resolution = query_rows('''SELECT ticket_id,created_at,category,priority,status,resolution_time_hrs,agent_id,issue_summary FROM tickets WHERE resolution_time_hrs > ? ORDER BY resolution_time_hrs DESC''',(threshold,))
    stale = query_rows('''SELECT ticket_id,created_at,category,priority,status,response_time_hrs,agent_id,issue_summary FROM tickets WHERE priority IN ('High','Critical') AND status IN ('Open','Escalated') AND (julianday(?) - julianday(created_at))*24 > 24 ORDER BY created_at ASC''',(latest,))
    return {'reference_timestamp':latest,'rules':{'long_resolution':f'resolution_time_hrs > {threshold:.2f} (Q3 + 1.5 × IQR)','stale_high_priority':'High/Critical + Open/Escalated + older than 24 hours relative to latest dataset timestamp'},'summary':{'long_resolution_count':len(long_resolution),'stale_high_priority_count':len(stale),'total_anomalies':len(long_resolution)+len(stale)},'long_resolution':long_resolution,'stale_high_priority':stale}

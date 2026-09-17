from datetime import datetime, timedelta
from .database import query_rows
from .schemas import QueryPlan

ALLOWED_GROUPS = {'agent_id':'agent_id','category':'category','priority':'priority','status':'status'}
METRICS = {'count':'COUNT(*)','avg_customer_rating':'AVG(customer_rating)','avg_resolution_time_hrs':'AVG(resolution_time_hrs)','avg_response_time_hrs':'AVG(response_time_hrs)','max_resolution_time_hrs':'MAX(resolution_time_hrs)','min_customer_rating':'MIN(customer_rating)'}


def _date_bounds(time_range):
    if not time_range: return None, None
    row = query_rows('SELECT MIN(created_at) AS lo, MAX(created_at) AS hi FROM tickets')[0]
    latest = datetime.fromisoformat(row['hi'])
    if time_range == 'this_week':
        start = (latest - timedelta(days=latest.weekday())).replace(hour=0, minute=0, second=0)
        return start.strftime('%Y-%m-%d %H:%M:%S'), (start + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    if time_range == 'this_month':
        start = latest.replace(day=1, hour=0, minute=0, second=0)
        end = start.replace(year=start.year + (start.month == 12), month=1 if start.month == 12 else start.month + 1)
        return start.strftime('%Y-%m-%d %H:%M:%S'), end.strftime('%Y-%m-%d %H:%M:%S')
    start = latest - timedelta(days=7 if time_range == 'last_7_days' else 30)
    return start.strftime('%Y-%m-%d %H:%M:%S'), latest.strftime('%Y-%m-%d %H:%M:%S')


def execute_plan(plan: QueryPlan) -> list[dict]:
    where, params = [], []
    for field in ('category','priority','status','agent_id'):
        value = getattr(plan, field)
        if value: where.append(f'{field} = ?'); params.append(value)
    if not plan.status and plan.unresolved_only: where.append("status IN ('Open','Escalated')")
    start, end = _date_bounds(plan.time_range)
    if start: where.append('created_at >= ?'); params.append(start)
    if end: where.append('created_at < ?'); params.append(end)
    if plan.resolution_gt is not None: where.append('(resolution_time_hrs > ? OR resolution_time_hrs IS NULL)'); params.append(plan.resolution_gt)
    if plan.resolution_lte is not None: where.append('resolution_time_hrs <= ?'); params.append(plan.resolution_lte)
    clause = (' WHERE ' + ' AND '.join(where)) if where else ''
    if plan.intent == 'list':
        params.append(plan.limit)
        return query_rows(f'''SELECT ticket_id,created_at,category,priority,status,response_time_hrs,resolution_time_hrs,agent_id,customer_rating,issue_summary FROM tickets{clause} ORDER BY created_at DESC LIMIT ?''', tuple(params))
    metric = METRICS[plan.metric or 'count']
    if plan.group_by:
        group = ALLOWED_GROUPS[plan.group_by]; direction = 'DESC' if plan.sort_desc else 'ASC'; params.append(plan.limit)
        return query_rows(f'SELECT {group} AS group_value,{metric} AS value,COUNT(*) AS ticket_count FROM tickets{clause} GROUP BY {group} ORDER BY value {direction},ticket_count {direction} LIMIT ?', tuple(params))
    if plan.metric == 'count': return query_rows(f'SELECT COUNT(*) AS value FROM tickets{clause}', tuple(params))
    return query_rows(f'SELECT {metric} AS value,COUNT(*) AS ticket_count FROM tickets{clause}', tuple(params))


def format_answer(plan, rows):
    if not rows: return 'No matching tickets were found.'
    if plan.intent == 'count': return f"There are {int(rows[0]['value'])} matching tickets."
    if plan.intent == 'list': return f"Found {len(rows)} matching ticket(s)."
    if plan.group_by:
        top = rows[0]; value = top['value']
        if value is None: text = 'N/A'
        elif 'rating' in (plan.metric or ''): text = f'{float(value):.2f}'
        elif 'hrs' in (plan.metric or ''): text = f'{float(value):.2f} hrs'
        else: text = str(int(value))
        return f"{top['group_value']} has the {'highest' if plan.sort_desc else 'lowest'} {plan.metric.replace('_',' ')} at {text}."
    value = rows[0]['value']
    if value is None: return 'The requested metric has no non-null values for the selected records.'
    return f"The {plan.metric.replace('_',' ')} is {float(value):.2f}." if plan.metric != 'count' else f'There are {int(value)} matching tickets.'

import json,re,httpx
from .config import OLLAMA_BASE_URL,OLLAMA_MODEL,LLM_TIMEOUT_SECONDS
from .schemas import QueryPlan

SYSTEM_PROMPT='''You are a support analytics query planner. Never write SQL. Return only JSON matching the QueryPlan schema. Use only these fields: ticket_id, created_at, category (Billing|Technical|General), priority (Low|Medium|High|Critical), status (Open|Resolved|Escalated), response_time_hrs, resolution_time_hrs, agent_id, customer_rating, issue_summary. Intents: count, aggregate, list. Metrics: count, avg_customer_rating, avg_resolution_time_hrs, avg_response_time_hrs, max_resolution_time_hrs, min_customer_rating. group_by: agent_id/category/priority/status/null. time_range: this_week/this_month/last_7_days/last_30_days/null. unresolved means Open or Escalated. For not resolved within N hours use resolution_gt=N and include unresolved rows. Return JSON only.'''


def _json(text):
    m=re.search(r'\{.*\}',text.strip().replace('```json','').replace('```',''),re.S)
    if not m: raise ValueError('LLM did not return JSON')
    return json.loads(m.group(0))


def plan_with_ollama(question):
    payload={'model':OLLAMA_MODEL,'messages':[{'role':'system','content':SYSTEM_PROMPT},{'role':'user','content':question}],'stream':False,'format':'json','options':{'temperature':0}}
    with httpx.Client(timeout=LLM_TIMEOUT_SECONDS) as c:
        r=c.post(f'{OLLAMA_BASE_URL}/api/chat',json=payload); r.raise_for_status()
        return QueryPlan.model_validate(_json(r.json()['message']['content']))


def heuristic_plan(question):
    q=question.lower(); category=next((x for x in ['Billing','Technical','General'] if x.lower() in q),None); priority=next((x for x in ['Critical','High','Medium','Low'] if x.lower() in q),None); status=next((x for x in ['Open','Resolved','Escalated'] if x.lower() in q),None)
    unresolved=('unresolved' in q or 'not resolved' in q); group=None
    if 'which agent' in q or 'by agent' in q or 'per agent' in q: group='agent_id'
    elif 'by category' in q or 'per category' in q: group='category'
    elif 'by priority' in q or 'per priority' in q: group='priority'
    elif 'by status' in q or 'per status' in q: group='status'
    metric='count'
    if any(x in q for x in ['average','avg','mean']): metric='avg_customer_rating' if 'rating' in q else ('avg_resolution_time_hrs' if 'resolution' in q else 'avg_response_time_hrs')
    elif any(x in q for x in ['maximum','highest','max ']): metric='max_resolution_time_hrs' if 'resolution' in q else 'count'
    elif any(x in q for x in ['minimum','lowest','min ']): metric='min_customer_rating' if 'rating' in q else 'count'
    if 'which agent resolved the most' in q: group='agent_id'; metric='count'; status='Resolved'; unresolved=False
    sort_desc=not any(x in q for x in ['lowest','least','fewest','minimum'])
    if 'lowest average customer rating' in q: group='agent_id'; metric='avg_customer_rating'; status='Resolved'; sort_desc=False
    tr='this_week' if 'this week' in q else ('this_month' if 'this month' in q else ('last_7_days' if 'last 7 days' in q or 'past 7 days' in q else ('last_30_days' if 'last 30 days' in q or 'past 30 days' in q else None)))
    gt=None; lte=None
    m=re.search(r'(?:within|under|less than)\s+(\d+(?:\.\d+)?)\s*hours?',q)
    if m and 'resolv' in q: lte=float(m.group(1))
    m=re.search(r'(?:more than|over|above|greater than)\s+(\d+(?:\.\d+)?)\s*hours?',q)
    if m and 'resolv' in q: gt=float(m.group(1))
    if 'critical' in q and 'not resolved' in q:
        priority='Critical'; status=None; unresolved=False; lte=None; intent='list'; m=re.search(r'(?:within|under|less than)\s+(\d+(?:\.\d+)?)\s*hours?',q); gt=float(m.group(1)) if m else None
    elif 'anomal' in q:
        intent='list'; tr=tr or 'this_week'
    else: intent='aggregate' if group or metric!='count' else ('list' if any(x in q for x in ['show me','list','which tickets','tickets are']) and not any(x in q for x in ['how many','count']) else 'count')
    return QueryPlan(intent=intent,metric=metric,group_by=group,category=category,priority=priority,status=status,unresolved_only=unresolved,time_range=tr,resolution_gt=gt,resolution_lte=lte,limit=100 if intent=='list' else 10,sort_desc=sort_desc)


def get_query_plan(question):
    try:return plan_with_ollama(question),True
    except Exception:return heuristic_plan(question),False

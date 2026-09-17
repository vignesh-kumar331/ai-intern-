from pathlib import Path
import httpx
from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .config import OLLAMA_BASE_URL,OLLAMA_MODEL
from .database import initialize_database,table_count,query_rows
from .schemas import QueryRequest,QueryResponse,HealthResponse
from .llm import get_query_plan
from .query_engine import execute_plan,format_answer
from .anomalies import detect_anomalies

app=FastAPI(title='AI Support Ticket Analytics',version='1.0.0')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])

@app.on_event('startup')
def startup(): initialize_database()

@app.get('/',include_in_schema=False)
def root(): return FileResponse(Path(__file__).parent/'static'/'index.html')

@app.get('/api/health',response_model=HealthResponse)
def health():
    rows=table_count(); available=False
    try:
        with httpx.Client(timeout=2) as c: available=c.get(f'{OLLAMA_BASE_URL}/api/tags').is_success
    except Exception: pass
    return HealthResponse(status='ok' if rows else 'degraded',rows=rows,llm_provider='Ollama',llm_model=OLLAMA_MODEL,llm_available=available)

@app.post('/api/query',response_model=QueryResponse)
def query(request:QueryRequest):
    try:
        plan,llm_used=get_query_plan(request.question); rows=execute_plan(plan)
        return QueryResponse(question=request.question,answer=format_answer(plan,rows),plan=plan.model_dump(),rows=rows,llm_used=llm_used)
    except Exception as exc: raise HTTPException(400,str(exc)) from exc

@app.get('/api/anomalies')
def anomalies(): return detect_anomalies()

@app.get('/api/stats')
def stats():
    return {'total_tickets':table_count(),'by_status':query_rows('SELECT status,COUNT(*) AS count FROM tickets GROUP BY status ORDER BY count DESC'),'by_priority':query_rows('SELECT priority,COUNT(*) AS count FROM tickets GROUP BY priority ORDER BY count DESC'),'by_category':query_rows('SELECT category,COUNT(*) AS count FROM tickets GROUP BY category ORDER BY count DESC')}

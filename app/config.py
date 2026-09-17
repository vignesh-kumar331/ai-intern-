from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = Path(os.getenv('DATA_PATH', BASE_DIR / 'data' / 'support_tickets.csv'))
DB_PATH = Path(os.getenv('DB_PATH', BASE_DIR / 'data' / 'support_tickets.db'))
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen2.5:3b')
LLM_TIMEOUT_SECONDS = float(os.getenv('LLM_TIMEOUT_SECONDS', '45'))

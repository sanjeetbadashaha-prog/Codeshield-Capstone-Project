# CodeShield — Project Context

## What this is
A security code review agent that scans code for vulnerabilities,
simulates how an attacker would exploit them, and generates fixes.

## Stack
- Language: Python 3.11
- LLM: Llama 3.3 70b-versatile via Groq
- UI: Streamlit
- Database: SQLite via Python's built-in sqlite3 module
  - DB file stored at: ./codeshield.db
- Env vars loaded via python-dotenv from .env file

## Rules for every file you create
- All Groq calls must have try/except returning a safe fallback
- All Firestore calls must have try/except — never crash the app
- Return types are always plain Python dicts or lists, no classes
- Groq must always be prompted to return ONLY valid JSON

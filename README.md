# 🛡️ CodeShield — AI Security Code Review Agent

## 🚀 Live Demo
https://codeshield-capstone-project-kv4kre7oln6fdzyqdi6u6u.streamlit.app/

## What It Does
- Scans code for security vulnerabilities using AI
- Simulates how an attacker would exploit each vulnerability
- Generates context-aware fixes with before/after code diff
- Scans entire GitHub repositories file by file
- Downloads a fully corrected version of your code

## Agent Architecture
```text
                  +---------------+
                  |  Source Code  |
                  +-------+-------+
                          |
                          v
               +----------------------+
               |    Scanner Agent     | (Detects security flaws using LLaMA 3.3)
               +----------+-----------+
                          |
                          v
               +----------------------+
               |   Risk Prioritizer   | (Assigns risk scores & prioritizes)
               +----------+-----------+
                          |
                          v
               +----------------------+
               |  Attacker Simulator  | (Generates exploit narratives & payloads)
               +----------+-----------+
                          |
                          v
               +----------------------+
               |    Fix Generator     | (Produces context-aware patches)
               +----------+-----------+
                          |
                          v
                +-------------------+
                | Secure Code/Fixes |
                +-------------------+
```

## How It Was Vibe Coded
This project was entirely vibe coded using Google Antigravity, an agent-first development environment. Natural language prompts were used to iteratively design, build, and debug all agent communications, backend modules, database structures, Streamlit UI components, and API integration paths without writing boilerplates manually.

## Tech Stack
- **LLM:** LLaMA 3.3 70B via Groq
- **Framework:** Python 3.11
- **UI:** Streamlit
- **Memory:** SQLite
- **Vibe Coding:** Google Antigravity
- **Deployment:** Streamlit Community Cloud

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Start the Streamlit application
streamlit run ui/app.py
```

## Future Improvements
- GitHub webhook for automatic scanning on every push
- VS Code extension for inline security alerts
- Support for JavaScript and PHP parsing
- Slack alerts for critical vulnerabilities
- Security score trend visualization over time

## Built For
Google x Kaggle AI Agents Intensive Vibe Coding Capstone 2026

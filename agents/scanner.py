import json
import traceback
from groq import Groq
from config import GROQ_API_KEY

SYSTEM_INSTRUCTION = (
    "You are an aggressive security vulnerability scanner.\n"
    "The code may be Python, JavaScript, PHP, Java, or TypeScript.\n"
    "Identify the language first then apply language-specific security rules.\n"
    "You MUST find security issues in code. Look for ANY of these:\n"
    "SQL injection, hardcoded passwords or API keys, command injection,\n"
    "path traversal, missing input validation, insecure functions,\n"
    "unparameterized queries, sensitive data in code.\n"
    "Even minor issues count. Be thorough.\n"
    "Return ONLY a valid JSON array of vulnerabilities.\n"
    "Each item must have: vuln_type, line_number, severity,\n"
    "description, vulnerable_snippet.\n"
    "If no vulnerabilities found return empty array []"
)


def validate_input(code: str) -> str:
    if not code or len(code.strip()) < 10:
        return "no_code"
    
    programming_keywords = [
        "def", "function", "class", "import", "var", 
        "const", "let", "public", "private", "SELECT", 
        "<?", "if", "for", "while", "return"
    ]
    
    code_lower = code.lower()
    has_keywords = any(kw.lower() in code_lower 
                      for kw in programming_keywords)
    
    if not has_keywords:
        return "not_code"
    
    return "valid"

def detect_language(code: str) -> str:
    """Detects the programming language based on keywords in the source code."""
    if "import" in code and "def" in code:
        return "Python"
    elif "function" in code or "const" in code or "var" in code:
        return "JavaScript"
    elif "<?php" in code:
        return "PHP"
    elif "public class" in code:
        return "Java"
    elif "interface" in code or ": string" in code:
        return "TypeScript"
    else:
        return "Python"

def scan_code(code: str) -> tuple:
    """Scans code for vulnerabilities and detects language.
    
    Args:
        code (str): The code content to scan.
        
    Returns:
        tuple: (detected_language, vulnerabilities_list)
    """
    detected_lang = detect_language(code)
    
    # Instantiate the Groq client
    client = Groq(api_key=GROQ_API_KEY)
    
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": code}
                ]
            )
            
            raw_content = response.choices[0].message.content
            print("\n--- RAW GROQ RESPONSE TEXT ---")
            print(raw_content)
            print("------------------------------\n")
            
            content = raw_content.strip()
            
            # Clean up markdown code block wrapping if present
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            if not content:
                return (detected_lang, [])
                
            data = json.loads(content)
            if isinstance(data, list):
                return (detected_lang, data)
            return (detected_lang, [])
        except Exception as e:
            print(f"Scanner error: {e}")
            traceback.print_exc()
            if attempt < 2:
                import time
                time.sleep(2)
                continue
            else:
                return (detected_lang, [])

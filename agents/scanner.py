import json
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
    "Return ONLY a valid JSON array, no markdown.\n"
    "Each item must have: vuln_type, line_number, severity,\n"
    "description, vulnerable_snippet.\n"
    "Never return an empty array if there is any suspicious code."
)

# Instantiate the Groq client
client = Groq(api_key=GROQ_API_KEY)

def scan_code(code: str) -> list:
    """Scans code for vulnerabilities using the Groq Llama 3.3 model.
    
    Args:
        code (str): The code content to scan.
        
    Returns:
        list: A list of dicts representing the vulnerabilities found, 
              or an empty list if none are found or if an error occurs.
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": code}
            ]
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up markdown code block wrapping if present
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        if not content:
            return []
            
        data = json.loads(content)
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        print(f"Scanner error: {e}")
        return []

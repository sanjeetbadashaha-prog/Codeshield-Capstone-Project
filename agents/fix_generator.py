import json
from groq import Groq
from config import GROQ_API_KEY

def generate_fix(code: str, vuln: dict) -> dict:
    """Generates a security fix for a given vulnerability in the original code.
    
    Args:
        code (str): The complete original code.
        vuln (dict): The vulnerability description dict containing vuln_type, 
                     line_number, and vulnerable_snippet.
                     
    Returns:
        dict: A dict containing before, after, and explanation, or a dict with
              an 'error' key on failure.
    """
    try:
        vuln_type = vuln.get("vuln_type", "Unknown")
        line_number = vuln.get("line_number", "Unknown")
        vulnerable_snippet = vuln.get("vulnerable_snippet", "")
        
        system_instruction = "You are a security engineer. Return ONLY valid JSON. No markdown."
        
        # Instantiate the Groq client
        client = Groq(api_key=GROQ_API_KEY)
        
        user_message = (
            f"Original code:\n{code}\n\n"
            f"Vulnerability: {vuln_type} at line {line_number}\n"
            f"Vulnerable code: {vulnerable_snippet}\n\n"
            "Return JSON with exactly these keys:\n"
            "before: the vulnerable line as-is\n"
            "after: the fixed replacement code\n"
            "explanation: why this fix works in one sentence"
        )
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_message}
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
            return {"error": "Empty response from Groq API"}
            
        data = json.loads(content)
        if isinstance(data, dict):
            # Ensure the required keys are present
            required_keys = ["before", "after", "explanation"]
            for key in required_keys:
                if key not in data:
                    data[key] = "N/A"
            return data
            
        return {"error": "Invalid response format returned from model"}
        
    except Exception as e:
        return {"error": f"An error occurred during fix generation: {str(e)}"}


def apply_all_fixes(code: str, vulns: list) -> str:
    """Sends all vulnerabilities to Groq to generate a complete corrected version of the code.
    
    Args:
        code (str): The complete original vulnerable code.
        vulns (list): List of vulnerability dicts found.
        
    Returns:
        str: The complete fixed version of the code, or the original code if anything fails.
    """
    try:
        system_instruction = (
            "You are a security engineer. Return ONLY the complete "
            "fixed version of the code. No explanation. No markdown. "
            "Just the corrected code."
        )
        
        user_message = (
            f"Here is the vulnerable code:\n"
            f"{code}\n\n"
            f"Fix ALL of these vulnerabilities:\n"
            f"{json.dumps(vulns, indent=2)}\n\n"
            f"Return the complete fixed code."
        )
        
        client = Groq(api_key=GROQ_API_KEY)
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_message}
            ]
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up markdown code block wrapping if present
        if content.startswith("```python"):
            content = content[9:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        return content
    except Exception:
        return code

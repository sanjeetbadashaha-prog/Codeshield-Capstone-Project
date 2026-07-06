import json
from groq import Groq
from config import GROQ_API_KEY

def simulate_attack(vuln: dict) -> dict:
    """Simulates an attack narrative and payload based on a vulnerability description.
    
    Args:
        vuln (dict): Vulnerability information containing vuln_type, line_number, 
                     and vulnerable_snippet.
                     
    Returns:
        dict: A dictionary containing attack_narrative, example_payload, 
              real_world_example, and damage_potential, or a dict with an 
              'error' key on failure.
    """
    vuln_type = vuln.get("vuln_type", "Unknown")
    line_number = vuln.get("line_number", "Unknown")
    vulnerable_snippet = vuln.get("vulnerable_snippet", "")
    
    system_instruction = (
        "You are a security researcher explaining attack techniques "
        "for educational purposes. Return ONLY valid JSON. No markdown."
    )
    
    # Instantiate the Groq client
    client = Groq(api_key=GROQ_API_KEY)
    
    user_message = (
        f"Vulnerability: {vuln_type} at line {line_number}\n"
        f"Code: {vulnerable_snippet}\n\n"
        "Return JSON with exactly these keys:\n"
        "attack_narrative: how attacker exploits this in 2 sentences\n"
        "example_payload: what the attacker would input\n"
        "real_world_example: a famous breach that used this method\n"
        "damage_potential: what they would gain access to"
    )
    
    for attempt in range(3):
        try:
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
                raise ValueError("Empty response from Groq API")
                
            data = json.loads(content)
            if isinstance(data, dict):
                # Ensure the required keys are present
                required_keys = ["attack_narrative", "example_payload", "real_world_example", "damage_potential"]
                for key in required_keys:
                    if key not in data:
                        data[key] = "N/A"
                return data
                
            raise ValueError("Invalid response format returned from model")
            
        except Exception as e:
            if attempt < 2:
                import time
                time.sleep(2)
            else:
                return {"error": str(e)}

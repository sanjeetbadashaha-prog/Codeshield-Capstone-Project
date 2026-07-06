import re
import time
import requests

def fetch_github_files(repo_url: str) -> tuple:
    """Parses a GitHub repo URL, fetches all supported files (.py, .js, .php, .java, .ts), and returns their raw content.
    
    Args:
        repo_url (str): The GitHub repository URL (e.g. https://github.com/owner/repo)
        
    Returns:
        tuple: (files_list, error_message)
               files_list is a list of dicts with keys 'filename' and 'content', 
               error_message is a string describing any failure.
    """
    try:
        # Parse owner and repo name from the GitHub URL
        # Handles protocols, subdomains, .git suffixes, and trailing slashes
        match = re.search(r"github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/|$)", repo_url)
        if not match:
            return ([], "Invalid GitHub URL format")
        
        owner, repo = match.groups()
        
        # Call the GitHub Git Trees API recursively
        api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
        headers = {"User-Agent": "CodeShield-Agent"}
        
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code == 404:
            return ([], "Repository not found — it may be private or the URL is incorrect")
        elif response.status_code != 200:
            return ([], "Could not fetch repository — please try again")
            
        tree_data = response.json()
        tree = tree_data.get("tree", [])
        
        files_list = []
        supported_extensions = (".py", ".js", ".php", ".java", ".ts")
        
        # Iterate and fetch raw content of supported files
        # Limit to first 25 supported files to avoid API rate limit or execution timeout
        supported_entries = [e for e in tree if e.get("type") == "blob" and e.get("path", "").endswith(supported_extensions)]
        
        for entry in supported_entries[:25]:
            path = entry.get("path", "")
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{path}"
            raw_res = requests.get(raw_url, headers=headers, timeout=10)
            
            if raw_res.status_code == 200:
                files_list.append({
                    "filename": path,
                    "content": raw_res.text
                })
            
            # Add 0.5 second delay between file fetches to avoid rate limiting
            time.sleep(0.5)
                
        return (files_list, "")
        
    except Exception:
        # Safe fallback: return empty list on any failure
        return ([], "Could not fetch repository — please try again")

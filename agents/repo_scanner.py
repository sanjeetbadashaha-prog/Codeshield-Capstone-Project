import re
import time
import requests

def fetch_github_files(repo_url: str) -> list:
    """Parses a GitHub repo URL, fetches all supported files (.py, .js, .php, .java, .ts), and returns their raw content.
    
    Args:
        repo_url (str): The GitHub repository URL (e.g. https://github.com/owner/repo)
        
    Returns:
        list: A list of dicts with keys 'filename' and 'content', 
              or an empty list if any failure occurs.
    """
    try:
        # Parse owner and repo name from the GitHub URL
        # Handles protocols, subdomains, .git suffixes, and trailing slashes
        match = re.search(r"github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/|$)", repo_url)
        if not match:
            return []
        
        owner, repo = match.groups()
        
        # Call the GitHub Git Trees API recursively
        api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
        headers = {"User-Agent": "CodeShield-Agent"}
        
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
            
        tree_data = response.json()
        tree = tree_data.get("tree", [])
        
        files_list = []
        supported_extensions = (".py", ".js", ".php", ".java", ".ts")
        
        # Iterate and fetch raw content of supported files
        for entry in tree:
            path = entry.get("path", "")
            entry_type = entry.get("type", "")
            
            # Filter supported files and ignore folders (blobs only)
            if entry_type == "blob" and path.endswith(supported_extensions):
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{path}"
                raw_res = requests.get(raw_url, headers=headers, timeout=10)
                
                if raw_res.status_code == 200:
                    files_list.append({
                        "filename": path,
                        "content": raw_res.text
                    })
                
                # Add 0.5 second delay between file fetches to avoid rate limiting
                time.sleep(0.5)
                
        return files_list
        
    except Exception:
        # Safe fallback: return empty list on any failure
        return []

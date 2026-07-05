def prioritize(vulns: list) -> list:
    """Calculates risk scores and prioritizes vulnerabilities.
    
    Args:
        vulns (list): A list of vulnerability dicts containing a 'severity' key.
        
    Returns:
        list: Sorted list of vulnerability dicts descending by risk_score.
    """
    severity_scores = {
        "Critical": 10,
        "High": 7,
        "Medium": 4,
        "Low": 1
    }
    
    processed_vulns = []
    for vuln in vulns:
        # Create a copy to prevent side effects
        vuln_copy = dict(vuln)
        severity = vuln_copy.get("severity", "Low")
        # Match case but fallback to Low (score 1) if not found
        score = severity_scores.get(severity, 1)
        vuln_copy["risk_score"] = score
        processed_vulns.append(vuln_copy)
        
    # Sort descending by risk_score
    processed_vulns.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
    return processed_vulns

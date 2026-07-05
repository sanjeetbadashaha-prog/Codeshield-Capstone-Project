import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from datetime import datetime
import streamlit as st
from agents.scanner import scan_code
from agents.risk_prioritizer import prioritize
from agents.attacker import simulate_attack
from agents.fix_generator import generate_fix, apply_all_fixes
from agents.repo_scanner import fetch_github_files
from memory.db_store import save_scan, get_recent_scans



# Page configuration for premium styling
st.set_page_config(
    page_title="CodeShield — Security Code Review Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom header styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #6B7280;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🛡️ CodeShield</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Security Code Review, Simulation & Remediation</div>', unsafe_allow_html=True)

def display_vulnerabilities(vulns, code=None, key_prefix=""):
    """Displays vulnerability details, attack simulations, and fixes in st.expanders.
    
    Args:
        vulns (list): A list of vulnerability dicts.
        code (str, optional): Original source code, used for generating fixes.
        key_prefix (str): Prefix to ensure unique Streamlit widget IDs.
    """
    if not vulns:
        return
        
    # Calculate security score (Start at 100, min 0)
    score = 100
    for v in vulns:
        severity = v.get("severity", "Low")
        if severity == "Critical":
            score -= 25
        elif severity == "High":
            score -= 15
        elif severity == "Medium":
            score -= 10
        elif severity == "Low":
            score -= 5
            
    score = max(0, score)
    
    if score >= 80:
        color_hex = "#10B981" # Green
        status = "Secure"
    elif score >= 50:
        color_hex = "#F59E0B" # Orange
        status = "Needs Attention"
    else:
        color_hex = "#EF4444" # Red
        status = "Critical Risk"
        
    # Display the colored gauge card
    st.markdown(f"""
    <div style="background-color: #F9FAFB; padding: 1.2rem; border-radius: 0.5rem; text-align: center; border-left: 5px solid {color_hex}; margin-bottom: 1.5rem; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);">
        <span style="font-size: 2.8rem; font-weight: 800; color: {color_hex}; line-height: 1;">{score}</span><br>
        <span style="font-size: 1.1rem; font-weight: 600; color: #4B5563;">{status}</span>
    </div>
    """, unsafe_allow_html=True)
        
    st.write("### Vulnerability Details")
    for idx, vuln in enumerate(vulns):
        severity = vuln.get("severity", "Low")
        vuln_type = vuln.get("vuln_type", "Unknown")
        line_number = vuln.get("line_number", "Unknown")
        vulnerable_snippet = vuln.get("vulnerable_snippet", "")
        description = vuln.get("description", "")
        source_file = vuln.get("source_file")
        
        sim_key = f"{key_prefix}_sim_{idx}"
        fix_key = f"{key_prefix}_fix_{idx}"
        
        # Build expander title
        title_prefix = f"[{source_file}] " if source_file else ""
        expander_title = f"{title_prefix}{severity} — {vuln_type} at line {line_number}"
        
        with st.expander(expander_title):
            # source_file badge if it exists in the vuln dict
            if source_file:
                st.caption(f"📁 **Source File:** `{source_file}`")
                
            # Code block with vulnerable_snippet
            st.code(vulnerable_snippet, language="python")
            # Description
            st.write(description)
            
            # Subheader for Attacker section
            st.subheader("⚔️ How an attacker exploits this")
            
            # Reveal Attack button
            if st.button("Reveal Attack", key=f"btn_{sim_key}"):
                with st.spinner("Simulating attack..."):
                    sim_res = simulate_attack(vuln)
                    st.session_state[sim_key] = sim_res
            
            # Show results fields one by one if they exist in session state
            if sim_key in st.session_state:
                res = st.session_state[sim_key]
                if "error" in res:
                    st.error(res["error"])
                else:
                    st.write(f"**Attack Narrative:** {res.get('attack_narrative', 'N/A')}")
                    st.write(f"**Example Payload:** `{res.get('example_payload', 'N/A')}`")
                    st.write(f"**Real-World Example:** {res.get('real_world_example', 'N/A')}")
                    st.write(f"**Damage Potential:** {res.get('damage_potential', 'N/A')}")

            # Subheader for Fix section
            st.subheader("✅ The Fix")
            
            # Resolve code from repo_files if needed
            resolved_code = code
            if resolved_code is None and source_file and st.session_state.get("repo_files"):
                for file_info in st.session_state["repo_files"]:
                    if file_info["filename"] == source_file:
                        resolved_code = file_info["content"]
                        break
            
            if resolved_code is None:
                st.warning("No source code available for fix")
            else:
                # Generate Fix button
                if st.button("Generate Fix", key=f"btn_{fix_key}"):
                    with st.spinner("Generating fix..."):
                        fix_res = generate_fix(resolved_code, vuln)
                        st.session_state[fix_key] = fix_res
                
                # Show results if they exist in session state
                if fix_key in st.session_state:
                    res = st.session_state[fix_key]
                    if "error" in res:
                        st.error(res["error"])
                    else:
                        st.write("**Before:**")
                        st.code(res.get("before", ""), language="python")
                        st.write("**After:**")
                        st.code(res.get("after", ""), language="python")
                        st.info(res.get("explanation", ""))

# Initialize session state variables
if "vulns" not in st.session_state:
    st.session_state["vulns"] = None
if "code" not in st.session_state:
    st.session_state["code"] = ""
if "repo_files" not in st.session_state:
    st.session_state["repo_files"] = None
if "repo_vulns" not in st.session_state:
    st.session_state["repo_vulns"] = None
if "fixed_code" not in st.session_state:
    st.session_state["fixed_code"] = None
if "repo_fixed_code" not in st.session_state:
    st.session_state["repo_fixed_code"] = None

# Sidebar context
with st.sidebar:
    st.header("About CodeShield")
    st.write(
        "CodeShield is an advanced security agent that scans code for vulnerabilities, "
        "simulates attacker exploitation techniques, and generates secure fixes."
    )
    st.divider()
    
    # Recent Scans Section
    st.subheader("Recent Scans")
    recent = get_recent_scans(limit=5)
    if recent:
        for scan in recent:
            st.caption(f"ID: `{scan['scan_id']}` | {scan['language']} ({scan['vuln_count']} vulns)")
    else:
        st.caption("No recent scans found.")
        
    st.divider()
    st.caption("Stack: Python 3.11 • Gemini 2.5 Flash • SQLite")

# Tabs layout
tab1, tab2 = st.tabs(["Scan Code", "Scan GitHub Repo"])

with tab1:
    # Language Selectbox
    language = st.selectbox(
        "Select Code Language",
        ["Python", "JavaScript", "Go", "Java", "C++", "HTML/CSS", "TypeScript", "Other"],
        index=0,
        key="tab1_language"
    )

    # Code Input text area
    code_input = st.text_area(
        "Enter Source Code",
        value=st.session_state.get("code", ""),
        placeholder="Paste your source code here to analyze...",
        height=250,
        key="tab1_code_input"
    )

    # Scan Button trigger
    if st.button("Scan Code", type="primary", key="tab1_scan_btn"):
        if not code_input.strip():
            st.warning("Please paste some code before scanning.")
        else:
            # Clear old simulations and fixes from session state
            for key in list(st.session_state.keys()):
                if key.startswith("sim_") or key.startswith("fix_"):
                    del st.session_state[key]
            st.session_state["fixed_code"] = None

            with st.spinner("Scanning for vulnerabilities..."):
                # 2. Call scan_code() with the code from the text area
                raw_vulns = scan_code(code_input)
                
                # 3. Call prioritize() on the results
                prioritized_vulns = prioritize(raw_vulns)
                
                # 4. Store the results in st.session_state["vulns"]
                st.session_state["vulns"] = prioritized_vulns
                
                # 5. Store the original code in st.session_state["code"]
                st.session_state["code"] = code_input

                # Save the scan history in SQLite
                scan_id = uuid.uuid4().hex[:8]
                vuln_count = len(prioritized_vulns)
                critical_count = sum(1 for v in prioritized_vulns if v.get("severity") == "Critical")
                timestamp = datetime.now().isoformat()
                
                save_scan(
                    scan_id=scan_id,
                    language=language,
                    vuln_count=vuln_count,
                    critical_count=critical_count,
                    timestamp=timestamp
                )
                
            # 6. If no vulnerabilities found show st.success "No vulnerabilities found"
            if not prioritized_vulns:
                st.success("No vulnerabilities found")
            else:
                st.success(f"Scan complete. Found {len(prioritized_vulns)} vulnerabilities.")

    # Show metrics & details inside tab1 if they exist in session state
    if st.session_state.get("vulns"):
        st.divider()
        m_col1, m_col2, m_col3 = st.columns(3)
        
        vulns_list = st.session_state["vulns"]
        total_vulns = len(vulns_list)
        critical_count = sum(1 for v in vulns_list if v.get("severity") == "Critical")
        highest_score = max((v.get("risk_score", 0) for v in vulns_list), default=0)
        
        m_col1.metric("Total Vulnerabilities", total_vulns)
        m_col2.metric("Critical Severities", critical_count)
        m_col3.metric("Highest Risk Score", highest_score)
        
        display_vulnerabilities(vulns_list, code=st.session_state["code"], key_prefix="tab1")

        # Download Fixed File section
        st.divider()
        st.write("### Download Fixed File")
        
        if st.button("Generate Fixed Version", key="generate_fixed_version_btn"):
            with st.spinner("Applying all security fixes..."):
                fixed_code = apply_all_fixes(st.session_state["code"], vulns_list)
                st.session_state["fixed_code"] = fixed_code
                st.success("Fixed code version successfully generated!")

        if st.session_state.get("fixed_code"):
            st.download_button(
                label="Download Fixed app.py",
                data=st.session_state["fixed_code"],
                file_name="fixed_app.py",
                mime="text/x-python"
            )

with tab2:
    # Text input for GitHub repo URL
    repo_url = st.text_input(
        "GitHub Repository URL",
        placeholder="https://github.com/username/repo",
        key="tab2_repo_url"
    )
    
    # Button "Fetch & Scan Repo"
    if st.button("Fetch & Scan Repo", type="primary", key="tab2_fetch_btn"):
        if not repo_url.strip():
            st.warning("Please enter a GitHub repository URL.")
        else:
            # Clear old repo scans and fixes
            st.session_state["repo_vulns"] = None
            st.session_state["repo_fixed_code"] = None
            with st.spinner("Fetching files from GitHub..."):
                files = fetch_github_files(repo_url)
            if files:
                st.session_state["repo_files"] = files
                st.success(f"Successfully fetched {len(files)} Python files.")
                # Initialize checkboxes to False (unchecked by default)
                for file_info in files:
                    st.session_state[f"cb_{file_info['filename']}"] = False
            else:
                st.error("No Python files found or failed to fetch repository content. Make sure the repository is public and the URL is correct.")
                
    # Show the file list if files exist in session state
    if st.session_state.get("repo_files") is not None:
        files = st.session_state["repo_files"]
        st.info(f"Repository contains {len(files)} Python files. Select which files to scan:")
        
        # Select All / Deselect All buttons
        col_sel1, col_sel2 = st.columns(2)
        if col_sel1.button("Select All", key="select_all_btn"):
            for file_info in files:
                st.session_state[f"cb_{file_info['filename']}"] = True
            st.rerun()
        if col_sel2.button("Deselect All", key="deselect_all_btn"):
            for file_info in files:
                st.session_state[f"cb_{file_info['filename']}"] = False
            st.rerun()
        
        st.write("") # Add visual spacing
        selected_files = []
        for file_info in files:
            cb_key = f"cb_{file_info['filename']}"
            if cb_key not in st.session_state:
                st.session_state[cb_key] = False
                
            if st.checkbox(file_info['filename'], key=cb_key):
                selected_files.append(file_info)
                
        # Scan Selected Files button
        if st.button("Scan Selected Files", type="primary", key="tab2_scan_btn"):
            if not selected_files:
                st.warning("Please select at least one file to scan.")
            else:
                st.session_state["repo_fixed_code"] = None
                combined_vulns = []
                scan_progress = st.progress(0)
                
                # Loop through selected files
                for i, file_info in enumerate(selected_files):
                    content_str = file_info.get("content", "")
                    char_count = len(content_str)
                    preview = content_str[:200]
                    
                    # Print verification details to the console
                    print(f"\n--- VERIFYING FILE CONTENT: {file_info['filename']} ---")
                    print(f"Character Count: {char_count}")
                    print(f"Preview (first 200 chars):\n{preview}")
                    print("--------------------------------------------------\n")
                    
                    with st.spinner(f"Scanning {file_info['filename']}..."):
                        # Call scan_code with the content string
                        raw_vulns = scan_code(content_str)
                        # Add source_file field
                        for vuln in raw_vulns:
                            vuln["source_file"] = file_info["filename"]
                        combined_vulns.extend(raw_vulns)
                    
                    # Update progress bar
                    scan_progress.progress((i + 1) / len(selected_files))
                
                # Store in session state
                st.session_state["repo_vulns"] = combined_vulns
                
        # Show total vulnerabilities found across all files if scan completed
        if st.session_state.get("repo_vulns") is not None:
            combined_vulns = st.session_state["repo_vulns"]
            if combined_vulns:
                st.success(f"Scan complete. Found a total of {len(combined_vulns)} vulnerabilities across selected files.")
                # Show details inside tab2
                display_vulnerabilities(combined_vulns, code=None, key_prefix="tab2")
                
                # Download Fixed Version section
                st.divider()
                st.write("### Download Fixed Version")
                
                if st.button("Generate Fixed Version", key="generate_repo_fixed_btn"):
                    with st.spinner("Applying all security fixes across files..."):
                        # Join content of all selected files
                        combined_content = "\n\n".join(file_info.get("content", "") for file_info in selected_files)
                        repo_fixed_code = apply_all_fixes(combined_content, combined_vulns)
                        st.session_state["repo_fixed_code"] = repo_fixed_code
                        st.success("Fixed code version successfully generated!")
                
                if st.session_state.get("repo_fixed_code"):
                    st.download_button(
                        label="Download Fixed Code",
                        data=st.session_state["repo_fixed_code"],
                        file_name="fixed_repo_code.py",
                        mime="text/x-python"
                    )
            else:
                st.success("Scan complete. No vulnerabilities found in the selected files.")






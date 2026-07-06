import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from datetime import datetime
import streamlit as st
from agents.scanner import scan_code, validate_input
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

# Custom premium header styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Apply Inter font to everything */
    html, body, [class*="css"], [data-testid="stAppViewContainer"], .stApp, * {
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Main background */
    [data-testid="stAppViewContainer"], .stApp {
        background-color: #0f0a1a !important;
    }
    
    /* Sidebar background */
    [data-testid="stSidebar"] {
        background-color: #0d0a17 !important;
    }
    
    /* Header decorations removal */
    [data-testid="stHeader"] {
        background-color: rgba(0, 0, 0, 0) !important;
    }
    [class*="stDecoration"] {
        display: none !important;
    }
    
    /* Reduced default padding on main block */
    [data-testid="stAppViewContainer"] [class*="block-container"] {
        padding-top: 1.5rem !important;
        padding-bottom: 1.5rem !important;
    }
    
    /* Typography Hierarchy */
    h1, .main-header {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        margin-bottom: 0.3rem !important;
    }
    
    h2, .section-header {
        font-size: 1.4rem !important;
        font-weight: 600 !important;
        color: #e6edf3 !important;
        margin-top: 1rem !important;
        margin-bottom: 0.8rem !important;
    }
    
    h3 {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #c9d1d9 !important;
        margin-top: 0.8rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    body, p, span, label, [data-testid="stMarkdownContainer"] p {
        font-size: 0.95rem !important;
        color: #8b949e !important;
    }
    
    .sub-header {
        font-size: 1.0rem !important;
        color: #8b949e !important;
        margin-bottom: 1.5rem !important;
    }
    
    /* Hero Title Shadow and Typing Animations */
    .hero-container {
        background: linear-gradient(135deg, #0f0a1a 0%, #13111c 100%);
        border: 1px solid #2d2640;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    .hero-title {
        font-size: 2.8rem !important;
        font-weight: 800 !important;
        color: #ffffff !important;
        text-shadow: 0 0 15px rgba(139, 92, 246, 0.35) !important;
        margin-bottom: 0.5rem !important;
        line-height: 1.2 !important;
    }
    
    @keyframes typing {
      from { width: 0 }
      to { width: 100% }
    }
    @keyframes blink-caret {
      from, to { border-color: transparent }
      50% { border-color: #8b5cf6 }
    }
    .typing-container {
      overflow: hidden;
      border-right: .15em solid #8b5cf6;
      white-space: nowrap;
      margin: 0 auto;
      letter-spacing: .15em;
      animation: 
        typing 3.5s steps(20, end) infinite alternate,
        blink-caret .75s step-end infinite;
      max-width: fit-content;
      font-size: 1.1rem;
      font-weight: 500;
      color: #8b949e;
      margin-bottom: 0.5rem;
    }

    /* Tab Styling (Pill buttons) */
    div[data-baseweb="tab-list"] {
        background-color: #1a1625 !important;
        border-radius: 8px !important;
        padding: 4px !important;
        gap: 0px !important;
        border-bottom: none !important;
    }
    
    button[data-baseweb="tab"] {
        color: #8b949e !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        background-color: transparent !important;
        border-bottom: none !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 8px 16px !important;
        transition: background-color 0.2s ease, color 0.2s ease !important;
        flex-grow: 1 !important;
        text-align: center !important;
    }
    
    button[data-baseweb="tab"][aria-selected="true"],
    button[data-baseweb="tab"][aria-selected="true"] p,
    button[data-baseweb="tab"][aria-selected="true"] span,
    button[data-baseweb="tab"][aria-selected="true"] div {
        color: #ffffff !important;
        background-color: #8b5cf6 !important;
        font-weight: 700 !important;
        border-bottom: none !important;
    }
    
    /* Language selector buttons custom styling */
    div[data-testid="column"] div.stButton > button {
        background-color: #1a1625 !important;
        border: 1px solid #2d2640 !important;
        border-radius: 6px !important;
        padding: 6px 14px !important;
        color: #8b949e !important;
        font-weight: 500 !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="column"] div.stButton > button[kind="primary"] {
        border-color: #8b5cf6 !important;
        color: #8b5cf6 !important;
    }
    div[data-testid="column"] div.stButton > button[kind="secondary"]:hover {
        border-color: #8b949e !important;
        color: #ffffff !important;
    }
    
    /* Code input area styling */
    div[data-testid="stTextArea"] textarea {
        border: 1px solid #2d2640 !important;
        border-radius: 8px !important;
        background-color: #13111c !important;
        color: #c9d1d9 !important;
        font-family: monospace !important;
    }
    div[data-testid="stTextArea"] textarea:focus {
        border-color: #8b5cf6 !important;
        box-shadow: 0 0 5px rgba(139, 92, 246, 0.2) !important;
    }
    
    div.stButton > button,
    div.stButton > button:hover,
    div.stButton > button:focus,
    div.stButton > button p,
    div.stButton > button span {
        background: linear-gradient(135deg, #8b5cf6, #6d28d9) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 24px !important;
        box-shadow: 0 4px 15px #8b5cf640 !important;
    }
    
    div.stButton > button:hover {
        filter: brightness(1.1) !important;
        box-shadow: 0 6px 20px #8b5cf660 !important;
    }
    
    /* Styled container card rules */
    div[data-testid="stVerticalBlock"]:has(div.vuln-card-marker) {
        background-color: #1a1625 !important;
        border-top: 1px solid #2d2640 !important;
        border-right: 1px solid #2d2640 !important;
        border-bottom: 1px solid #2d2640 !important;
        border-radius: 8px !important;
        padding: 16px !important;
        margin-bottom: 12px !important;
        gap: 12px !important;
    }
    div[data-testid="stVerticalBlock"]:has(div.vuln-card-marker-critical) {
        border-left: 3px solid #ff4444 !important;
    }
    div[data-testid="stVerticalBlock"]:has(div.vuln-card-marker-high) {
        border-left: 3px solid #ff8c00 !important;
    }
    div[data-testid="stVerticalBlock"]:has(div.vuln-card-marker-medium) {
        border-left: 3px solid #ffd700 !important;
    }
    div[data-testid="stVerticalBlock"]:has(div.vuln-card-marker-low) {
        border-left: 3px solid #4488ff !important;
    }
    
    /* Attack section styling */
    div[data-testid="stVerticalBlock"]:has(div.attack-section-marker) {
        background-color: #1a0a0a !important;
        border-left: 3px solid #8b5cf6 !important;
        border-top: 1px solid #8b5cf620 !important;
        border-right: 1px solid #8b5cf620 !important;
        border-bottom: 1px solid #8b5cf620 !important;
        border-radius: 6px !important;
        padding: 12px !important;
        margin-top: 8px !important;
        gap: 8px !important;
    }
    
    /* Fix section styling */
    div[data-testid="stVerticalBlock"]:has(div.fix-section-marker) {
        background-color: #0a1a0a !important;
        border-left: 3px solid #8b5cf6 !important;
        border-top: 1px solid #8b5cf620 !important;
        border-right: 1px solid #8b5cf620 !important;
        border-bottom: 1px solid #8b5cf620 !important;
        border-radius: 6px !important;
        padding: 12px !important;
        margin-top: 12px !important;
        gap: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# Hero section with gradient background
st.markdown("""
<div class="hero-container">
    <div class="hero-title">🛡️ CodeShield</div>
    <div class="typing-container">Scan &rarr; Simulate &rarr; Fix</div>
</div>
""", unsafe_allow_html=True)

# Three feature badges in a row using columns
col_b1, col_b2, col_b3 = st.columns(3)
col_b1.markdown('<div style="background-color: #1a1625; border: 1px solid #2d2640; border-radius: 8px; padding: 8px 16px; text-align: center; color: #e6edf3; font-weight: 500; font-size: 0.95rem;">🔍 Smart Scanning</div>', unsafe_allow_html=True)
col_b2.markdown('<div style="background-color: #1a1625; border: 1px solid #2d2640; border-radius: 8px; padding: 8px 16px; text-align: center; color: #e6edf3; font-weight: 500; font-size: 0.95rem;">⚔️ Attack Simulation</div>', unsafe_allow_html=True)
col_b3.markdown('<div style="background-color: #1a1625; border: 1px solid #2d2640; border-radius: 8px; padding: 8px 16px; text-align: center; color: #e6edf3; font-weight: 500; font-size: 0.95rem;">✅ Auto Fix</div>', unsafe_allow_html=True)

# Thin red divider line
st.markdown('<hr style="border: 0; height: 1px; background: #8b5cf630; margin: 1.5rem 0;">', unsafe_allow_html=True)

def set_attack_loading(key):
    st.session_state[key] = True

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
        
    # Display the colored circular gauge card
    st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 2rem; padding: 1.5rem; background-color: #1a1625; border: 1px solid #2d2640; border-radius: 12px; max-width: 260px; margin: 0 auto 2rem auto; box-shadow: 0 4px 15px rgba(0,0,0,0.25);">
        <div style="width: 120px; height: 120px; border-radius: 50%; border: 8px solid {color_hex}; display: flex; align-items: center; justify-content: center; margin-bottom: 0.8rem; box-shadow: 0 0 15px {color_hex}30; background-color: #13111c;">
            <span style="font-size: 2.2rem; font-weight: 800; color: #ffffff;">{score}</span>
        </div>
        <div style="font-size: 1.0rem; font-weight: 700; color: #ffffff; text-align: center; margin-bottom: 2px;">Security Score</div>
        <div style="font-size: 0.85rem; color: {color_hex}; font-weight: 600; text-align: center; text-transform: uppercase; letter-spacing: 0.5px;">{status}</div>
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
        
        # Color coding for severity pill badges
        sev_colors = {
            "Critical": "#ff4444",
            "High": "#ff8c00",
            "Medium": "#ffd700",
            "Low": "#4488ff"
        }
        sev_color = sev_colors.get(severity, "#8b949e")
        
        with st.container():
            # Inject CSS card marker
            st.markdown(f'<div class="vuln-card-marker vuln-card-marker-{severity.lower()}"></div>', unsafe_allow_html=True)
            
            # Card header: severity pill badge, title, line number gray badge
            st.markdown(f"""
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; flex-wrap: wrap; gap: 8px;">
                <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                    <span style="background-color: {sev_color}20; color: {sev_color}; border: 1px solid {sev_color}40; border-radius: 20px; padding: 3px 12px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">{severity}</span>
                    <span style="font-weight: 700; color: #ffffff; font-size: 1.1rem;">{vuln_type}</span>
                </div>
                <span style="background-color: #21262d; border: 1px solid #2d2640; border-radius: 4px; padding: 2px 8px; font-size: 11px; color: #8b949e; font-weight: 500;">Line {line_number}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # source_file badge if it exists
            if source_file:
                st.caption(f"📁 **Source File:** `{source_file}`")
                
            # Code block with vulnerable_snippet
            st.code(vulnerable_snippet, language="python")
            # Description
            st.write(description)
            
            # Inner Container for Attacker section
            with st.container():
                st.markdown('<div class="attack-section-marker"></div>', unsafe_allow_html=True)
                st.markdown('<div style="font-weight: 600; color: #a78bfa; font-size: 1rem; margin-bottom: 6px;">💀 How attacker exploits this</div>', unsafe_allow_html=True)
                
                # Reveal Attack button
                loading_key = f"loading_{sim_key}"
                if loading_key not in st.session_state:
                    st.session_state[loading_key] = False
                
                is_disabled = st.session_state[loading_key]
                if st.button(
                    "Reveal Attack", 
                    key=f"btn_{sim_key}", 
                    disabled=is_disabled,
                    on_click=set_attack_loading,
                    args=(loading_key,)
                ):
                    with st.spinner("Simulating attack..."):
                        sim_res = simulate_attack(vuln)
                        st.session_state[sim_key] = sim_res
                    st.session_state[loading_key] = False
                    st.rerun()
                
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

            # Inner Container for Fix section
            with st.container():
                st.markdown('<div class="fix-section-marker"></div>', unsafe_allow_html=True)
                st.markdown('<div style="font-weight: 600; color: #00ff88; font-size: 1rem; margin-bottom: 10px;">✅ The Fix</div>', unsafe_allow_html=True)
                
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
                            col_before, col_after = st.columns(2)
                            with col_before:
                                st.write("**Before:**")
                                st.code(res.get("before", ""), language="python")
                            with col_after:
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
if "vulns_today" not in st.session_state:
    st.session_state["vulns_today"] = 0
if "files_scanned" not in st.session_state:
    st.session_state["files_scanned"] = 0
if "detected_language" not in st.session_state:
    st.session_state["detected_language"] = None

# Sidebar context
with st.sidebar:
    # Styled Logo Section
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem;">
        <div style="width: 40px; height: 40px; background-color: #8b5cf620; border: 1px solid #8b5cf640; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.2rem;">🛡️</div>
        <div>
            <div style="font-size: 1.3rem; font-weight: 700; color: #ffffff; line-height: 1.2;">CodeShield</div>
            <div style="font-size: 0.8rem; color: #8b949e;">AI Security Agent</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Styled Stats Cards
    st.markdown(f"""
    <div style="background-color: #1a1625; border: 1px solid #2d2640; border-radius: 6px; padding: 12px; margin-bottom: 10px;">
        <div style="font-size: 0.8rem; color: #8b949e; margin-bottom: 4px;">Vulnerabilities Detected Today</div>
        <div style="font-size: 1.6rem; font-weight: 700; color: #a78bfa; line-height: 1;">{st.session_state["vulns_today"]}</div>
    </div>
    <div style="background-color: #1a1625; border: 1px solid #2d2640; border-radius: 6px; padding: 12px; margin-bottom: 1.5rem;">
        <div style="font-size: 0.8rem; color: #8b949e; margin-bottom: 4px;">Files Scanned</div>
        <div style="font-size: 1.6rem; font-weight: 700; color: #58a6ff; line-height: 1;">{st.session_state["files_scanned"]}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Recent Scans Section
    st.markdown('<div style="font-size: 1.0rem; font-weight: 600; color: #e6edf3; margin-bottom: 10px;">Recent Scans</div>', unsafe_allow_html=True)
    recent = get_recent_scans(limit=5)
    if recent:
        for scan in recent:
            ts = scan['timestamp']
            if "T" in ts:
                date_part, time_part = ts.split("T")
                time_str = time_part[:5] # show HH:MM
                display_ts = f"{date_part} {time_str}"
            else:
                display_ts = ts[:16]
                
            st.markdown(f"""
            <div style="border-left: 3px solid #8b5cf6; background-color: #1a1625; border-top: 1px solid #2d2640; border-right: 1px solid #2d2640; border-bottom: 1px solid #2d2640; border-radius: 0 4px 4px 0; padding: 8px 12px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; font-size: 11px; color: #8b949e; margin-bottom: 2px;">
                    <strong>ID: {scan['scan_id']}</strong>
                    <span>{display_ts}</span>
                </div>
                <div style="font-size: 12px; color: #c9d1d9;">
                    {scan['language']} — <span style="color: #a78bfa; font-weight: 600;">{scan['vuln_count']} vulns</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("No recent scans found.")
        
    st.divider()
    
    # Stack badges info at bottom
    st.markdown("""
    <div style="font-size: 0.8rem; color: #8b949e; margin-bottom: 6px;">Tech Stack</div>
    <div style="display: flex; flex-wrap: wrap; gap: 6px;">
        <span style="background-color: #1a1625; border: 1px solid #2d2640; border-radius: 20px; padding: 3px 10px; font-size: 11px; color: #c9d1d9;">Python 3.11</span>
        <span style="background-color: #1a1625; border: 1px solid #2d2640; border-radius: 20px; padding: 3px 10px; font-size: 11px; color: #c9d1d9;">LLaMA 3.3</span>
        <span style="background-color: #1a1625; border: 1px solid #2d2640; border-radius: 20px; padding: 3px 10px; font-size: 11px; color: #c9d1d9;">Groq</span>
        <span style="background-color: #1a1625; border: 1px solid #2d2640; border-radius: 20px; padding: 3px 10px; font-size: 11px; color: #c9d1d9;">Streamlit</span>
        <span style="background-color: #1a1625; border: 1px solid #2d2640; border-radius: 20px; padding: 3px 10px; font-size: 11px; color: #c9d1d9;">SQLite</span>
    </div>
    """, unsafe_allow_html=True)

# Tabs layout
tab1, tab2 = st.tabs(["Scan Code", "Scan GitHub Repo"])

with tab1:
    # Code Input text area
    st.markdown('<div style="font-weight: 600; color: #e6edf3; font-size: 1.1rem; margin-bottom: 2px;">Source Code</div>', unsafe_allow_html=True)
    st.markdown('<div style="color: #8b949e; font-size: 0.85rem; margin-bottom: 10px;">paste your code below</div>', unsafe_allow_html=True)
    
    code_input = st.text_area(
        "Source Code",
        value=st.session_state.get("code", ""),
        placeholder="Paste your source code here to analyze...",
        height=250,
        key="tab1_code_input",
        label_visibility="collapsed"
    )
    
    # Display the detected language badge if it exists
    if st.session_state.get("detected_language"):
        st.markdown(f'<div style="color: #a78bfa; font-weight: 600; margin-top: -6px; margin-bottom: 12px; font-size: 0.9rem;">Detected Language: {st.session_state["detected_language"]}</div>', unsafe_allow_html=True)

    # Scan Button trigger
    if st.button("Scan Code", type="primary", key="tab1_scan_btn"):
        validation = validate_input(code_input)
        if validation == "no_code":
            st.warning("⚠️ Please paste some code to scan. The input is too short.")
        elif validation == "not_code":
            st.info("🤔 This doesn't look like code. CodeShield scans source code for security vulnerabilities. Please paste Python, JavaScript, PHP, Java or TypeScript code.")
        else:
            # Clear old simulations and fixes from session state
            for key in list(st.session_state.keys()):
                if key.startswith("sim_") or key.startswith("fix_"):
                    del st.session_state[key]
            st.session_state["fixed_code"] = None

            with st.spinner("Scanning for vulnerabilities..."):
                # 2. Call scan_code() with the code from the text area
                detected_lang, raw_vulns = scan_code(code_input)
                
                # 3. Call prioritize() on the results
                prioritized_vulns = prioritize(raw_vulns)
                
                # 4. Store the results & detected language in st.session_state
                st.session_state["vulns"] = prioritized_vulns
                st.session_state["detected_language"] = detected_lang
                
                # Update sidebar counts
                st.session_state["vulns_today"] += len(prioritized_vulns)
                st.session_state["files_scanned"] += 1
                
                # 5. Store the original code in st.session_state["code"]
                st.session_state["code"] = code_input

                # Save the scan history in SQLite
                scan_id = uuid.uuid4().hex[:8]
                vuln_count = len(prioritized_vulns)
                critical_count = sum(1 for v in prioritized_vulns if v.get("severity") == "Critical")
                timestamp = datetime.now().isoformat()
                
                save_scan(
                    scan_id=scan_id,
                    language=st.session_state.get("detected_language", "Unknown"),
                    vuln_count=vuln_count,
                    critical_count=critical_count,
                    timestamp=timestamp
                )
                
            # 6. If no vulnerabilities found show st.success
            if not prioritized_vulns:
                st.success("✅ Great news! No security vulnerabilities detected in your code.")
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
            st.warning("Please enter a GitHub repository URL")
            st.stop()
        if "github.com" not in repo_url:
            st.error("Please enter a valid GitHub URL e.g. https://github.com/username/repo")
            st.stop()
            
        # Clear old repo scans and fixes
        st.session_state["repo_vulns"] = None
        st.session_state["repo_fixed_code"] = None
        with st.spinner("Fetching files from GitHub..."):
            files, err_msg = fetch_github_files(repo_url)
        if files:
            st.session_state["repo_files"] = files
            st.success(f"Successfully fetched {len(files)} files.")
            # Initialize checkboxes to False (unchecked by default)
            for file_info in files:
                st.session_state[f"cb_{file_info['filename']}"] = False
        else:
            if err_msg:
                st.error(err_msg)
            else:
                st.info("No scannable files found in this repository. CodeShield supports: .py .js .php .java .ts files")
                
    # Show the file list if files exist in session state
    if st.session_state.get("repo_files") is not None:
        files = st.session_state["repo_files"]
        st.info(f"Repository contains {len(files)} files. Select which files to scan:")
        
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
                        file_lang, raw_vulns = scan_code(content_str)
                        # Add source_file field
                        for vuln in raw_vulns:
                            vuln["source_file"] = file_info["filename"]
                        combined_vulns.extend(raw_vulns)
                    
                    # Update progress bar
                    scan_progress.progress((i + 1) / len(selected_files))
                
                # Store in session state
                st.session_state["repo_vulns"] = combined_vulns
                
                # Update sidebar counts
                st.session_state["vulns_today"] += len(combined_vulns)
                st.session_state["files_scanned"] += len(selected_files)
                
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






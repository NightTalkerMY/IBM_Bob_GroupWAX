import os
import re
import shutil
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from gemini_client import ResilientClient
import difflib
import html
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# Load environment variables for local development
load_dotenv()

def get_api_key(key_name: str) -> str | None:
    """
    Get API key from Streamlit secrets (production) or environment variables (local).
    
    Args:
        key_name: Name of the API key to retrieve
        
    Returns:
        API key value or None if not found
    """
    # Try Streamlit secrets first (Production/Cloud deployment)
    try:
        if key_name in st.secrets:
            return st.secrets[key_name]
    except (FileNotFoundError, KeyError):
        pass
    
    # Fall back to environment variables (Local development with .env)
    return os.getenv(key_name)

# Load API keys with fallback support
GEMINI_API_KEY_1 = get_api_key("GEMINI_API_KEY_1")
GEMINI_API_KEY_2 = get_api_key("GEMINI_API_KEY_2")
GEMINI_API_KEY_3 = get_api_key("GEMINI_API_KEY_3")
GEMINI_API_KEY_4 = get_api_key("GEMINI_API_KEY_4")
GEMINI_API_KEY_5 = get_api_key("GEMINI_API_KEY_5")

# Configuration
TEMP_DIR = "temp"
WORKING_FILE = os.path.join(TEMP_DIR, "working_netlist.txt")

# File path mapping for example test cases
EXAMPLE_CASES = {
    "Example Case 1": "mistake/m_netlist_case1.txt",
    "Example Case 2": "mistake/m_netlist_case2.txt",
    "Example Case 3": "mistake/m_netlist_case3.txt"
}

# Directory for user-uploaded netlists
USER_NETLISTS_DIR = os.path.join(TEMP_DIR, "user_netlists")

# System prompt template
SYSTEM_PROMPT_TEMPLATE = """You are CircuitSense, an expert analog electronics engineer and strict LTspice compiler.

CRITICAL INSTRUCTIONS - Perform a systematic review:
1. Node Check: Nodes tied to voltage sources (e.g., 'V+') are VALID. Do not flag them as floating.
2. Syntax Check: Assume LTspice syntax. YOU MUST IGNORE 'µ', 'level2', or 'SINE'. Do NOT mention them in your explanation. They are 100% correct LTspice formatting.
3. Physics Check:
   - Recognize that feedback from the output to the inverting input is NEGATIVE feedback and is inherently STABLE. Do not call it unstable.
   - Calculate op-amp voltage gain. Compare expected peak output against the DC power rails.
   - Flag Saturation/Clipping if expected output > rails.
   - THE FIX: To resolve clipping, you MUST adjust the resistor values to lower the gain. DO NOT change the input signal voltage (e.g., leave the SINE amplitude exactly as it is).
4. ESCAPE HATCH: If the circuit is mathematically and topologically perfect (e.g., gain fits within rails, no floating grounds), do NOT invent errors.

USER QUESTION: {user_question}

NETLIST TO ANALYZE:
{netlist_content}

RESPONSE FORMATTING:
IF THE CIRCUIT HAS ERRORS, respond strictly using ONLY these three headers:
### 🚨 The Error
### 🧠 The Explanation
### ✅ The Corrected Netlist
(Under the third header, output ONLY the corrected netlist wrapped in a single ```spice code block. Stop generating text immediately after.)

IF THE CIRCUIT IS PERFECT (NO ERRORS), respond strictly using ONLY this header:
### 🌟 Circuit Verified
The circuit is mathematically and topologically sound. No corrections needed."""


# ============================================================================
# WORKSPACE MANAGEMENT FUNCTIONS
# ============================================================================

def initialize_workspace():
    """Create temp directory and user netlists directory if they don't exist."""
    try:
        os.makedirs(TEMP_DIR, exist_ok=True)
        os.makedirs(USER_NETLISTS_DIR, exist_ok=True)
    except Exception as e:
        st.error(f"❌ Failed to create workspace directory: {str(e)}")


def copy_to_workspace(source_file: str) -> bool:
    """
    Copy selected netlist file to temp workspace.
    
    Args:
        source_file: Path to original file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        shutil.copy2(source_file, WORKING_FILE)
        return True
    except Exception as e:
        st.error(f"❌ Failed to copy file to workspace: {str(e)}")
        return False


def read_working_file() -> str:
    """
    Read content from working file with encoding fallback.
    
    Returns:
        File content as string
    """
    try:
        # Try UTF-8 first
        try:
            with open(WORKING_FILE, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Fall back to latin-1 for special characters
            with open(WORKING_FILE, 'r', encoding='latin-1') as f:
                return f.read()
    except FileNotFoundError:
        return ""
    except Exception as e:
        st.error(f"❌ Error reading working file: {str(e)}")
        return ""


def write_working_file(content: str) -> bool:
    """
    Write content to working file.
    
    Args:
        content: New file content
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(WORKING_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        st.error(f"❌ Error writing to working file: {str(e)}")
        return False


# ============================================================================
# API FUNCTIONS
# ============================================================================

def analyze_netlist(user_question: str, netlist_content: str) -> str:
    """
    Send custom query and netlist to Gemini API for analysis.
    
    Args:
        user_question: User's custom question
        netlist_content: SPICE netlist content
        
    Returns:
        AI-generated analysis text
        
    Raises:
        Exception: If API call fails
    """
    try:
        # Initialize Gemini client with all 5 API keys
        client = ResilientClient([
            GEMINI_API_KEY_1,
            GEMINI_API_KEY_2,
            GEMINI_API_KEY_3,
            GEMINI_API_KEY_4,
            GEMINI_API_KEY_5
        ])
        
        # Format the input
        formatted_input = f"USER QUESTION: {user_question}\n\nNETLIST TO ANALYZE:\n{netlist_content}"
        
        # Call the client
        response = client.chat(
            user_input=formatted_input,
            system_instruction=SYSTEM_PROMPT_TEMPLATE
        )
        
        # Ensure we return a string
        if response is None:
            raise Exception("Gemini API returned no response")
        
        return response
    
    except Exception as e:
        raise Exception(f"Gemini API error: {str(e)}")


# ============================================================================
# RESPONSE PARSING
# ============================================================================

def extract_corrected_netlist(ai_response: str) -> str | None:
    """
    Extract corrected netlist from AI response.
    
    Args:
        ai_response: Full AI response text
        
    Returns:
        Extracted netlist code or None if not found
    """
    # Pattern 1: Look for code block after the corrected netlist header
    pattern1 = r'### ✅ The Corrected Netlist\s*```(?:text|spice)?\s*(.*?)```'
    match1 = re.search(pattern1, ai_response, re.DOTALL | re.IGNORECASE)
    
    if match1:
        return match1.group(1).strip()
    
    # Pattern 2: Look for content after header until next header or end
    pattern2 = r'### ✅ The Corrected Netlist\s*```(?:text|spice)?\s*(.*?)(?=###|$)'
    match2 = re.search(pattern2, ai_response, re.DOTALL | re.IGNORECASE)
    
    if match2:
        content = match2.group(1).strip()
        # Remove trailing ``` if present
        content = re.sub(r'```\s*$', '', content).strip()
        return content
    
    # Pattern 3: Fallback - get everything after the header
    pattern3 = r'### ✅ The Corrected Netlist\s*(.*?)(?=###|$)'
    match3 = re.search(pattern3, ai_response, re.DOTALL | re.IGNORECASE)
    
    if match3:
        content = match3.group(1).strip()
        # Remove code block markers if present
        content = re.sub(r'^```(?:text|spice)?\s*', '', content)
        content = re.sub(r'```\s*$', '', content).strip()
        return content
    
    return None


# ============================================================================
# DIFF HIGHLIGHTING
# ============================================================================

def generate_highlighted_diff(old_text: str, new_text: str):
    """
    Generate HTML-highlighted diff showing changes between two texts.
    Returns tuple of (old_html, new_html) with color-coded changes.
    """
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    
    # Use difflib to compute differences
    diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=''))
    
    # Create highlighted versions
    old_html_lines = []
    new_html_lines = []
    
    # Use ndiff for character-level differences
    for old_line, new_line in zip(old_lines, new_lines):
        if old_line == new_line:
            # No change
            old_html_lines.append(html.escape(old_line))
            new_html_lines.append(html.escape(new_line))
        else:
            # Line changed - highlight the entire line
            old_html_lines.append(f'<span style="background-color: #ff4444; color: white; padding: 2px 4px;">{html.escape(old_line)}</span>')
            new_html_lines.append(f'<span style="background-color: #44ff44; color: black; padding: 2px 4px;">{html.escape(new_line)}</span>')
    
    # Handle added lines (new has more lines than old)
    if len(new_lines) > len(old_lines):
        for i in range(len(old_lines), len(new_lines)):
            new_html_lines.append(f'<span style="background-color: #44ff44; color: black; padding: 2px 4px;">{html.escape(new_lines[i])}</span>')
    
    # Handle deleted lines (old has more lines than new)
    if len(old_lines) > len(new_lines):
        for i in range(len(new_lines), len(old_lines)):
            old_html_lines.append(f'<span style="background-color: #ff4444; color: white; padding: 2px 4px;">{html.escape(old_lines[i])}</span>')
    
    old_html = '<br>'.join(old_html_lines)
    new_html = '<br>'.join(new_html_lines)
    
    return old_html, new_html


# ============================================================================
# PDF EXPORT FUNCTIONS
# ============================================================================

def generate_session_history_pdf(chat_history: list) -> BytesIO:
    """
    Generate a PDF document containing the session chat history.
    
    Args:
        chat_history: List of chat messages with 'question', 'response', 'timestamp', 'accepted'
        
    Returns:
        BytesIO buffer containing the PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Container for PDF elements
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title
    story.append(Paragraph("CircuitSense - Session History", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"<i>Generated: {timestamp}</i>", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Chat messages
    for i, msg in enumerate(chat_history, 1):
        msg_timestamp = msg['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        question = msg['question']
        response = msg['response']
        accepted = msg.get('accepted', False)
        
        # User Query
        story.append(Paragraph(f"<b>Query #{i}</b> • {msg_timestamp}", heading_style))
        story.append(Paragraph(f"<b>User Question:</b>", styles['Normal']))
        
        # Split question by lines
        for line in question.split('\n'):
            if line.strip():
                safe_line = line.replace('&', '&').replace('<', '<').replace('>', '>')
                story.append(Paragraph(safe_line, styles['Normal']))
        
        story.append(Spacer(1, 0.1*inch))
        
        # AI Response
        story.append(Paragraph(f"<b>AI Response:</b>", styles['Normal']))
        
        # Split response by lines
        for line in response.split('\n'):
            if line.strip():
                safe_line = line.replace('&', '&').replace('<', '<').replace('>', '>')
                story.append(Paragraph(safe_line, styles['Normal']))
        
        # Acceptance status
        if accepted:
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph("<i>✓ Changes accepted and applied</i>", styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_version_control_pdf(version_history: list) -> BytesIO:
    """
    Generate a PDF document containing the version control history.
    
    Args:
        version_history: List of version entries with timestamp, from_content, to_content, question, ai_explanation
        
    Returns:
        BytesIO buffer containing the PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Container for PDF elements
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=12
    )
    
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        fontSize=9,
        leftIndent=20,
        fontName='Courier'
    )
    
    # Title
    story.append(Paragraph("CircuitSense - Version Control History", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"<i>Generated: {timestamp}</i>", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Version entries
    for i, version in enumerate(version_history, 1):
        version_timestamp = version['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        story.append(Paragraph(f"<b>Change #{i}</b>", heading_style))
        story.append(Paragraph(f"<i>Timestamp: {version_timestamp}</i>", styles['Normal']))
        story.append(Paragraph(f"<b>Question:</b> {version.get('question', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        
        # Previous version
        story.append(Paragraph("<b>Previous Version:</b>", styles['Normal']))
        old_lines = version['from_content'].split('\n')
        for line in old_lines[:30]:  # Limit lines to prevent huge PDFs
            safe_line = line.replace('&', '&').replace('<', '<').replace('>', '>')
            story.append(Paragraph(f"<font name='Courier' size='8'>{safe_line}</font>", styles['Normal']))
        
        if len(old_lines) > 30:
            story.append(Paragraph("<i>... (truncated)</i>", styles['Normal']))
        
        story.append(Spacer(1, 0.15*inch))
        
        # Updated version
        story.append(Paragraph("<b>Updated Version:</b>", styles['Normal']))
        new_lines = version['to_content'].split('\n')
        for line in new_lines[:30]:  # Limit lines to prevent huge PDFs
            safe_line = line.replace('&', '&').replace('<', '<').replace('>', '>')
            story.append(Paragraph(f"<font name='Courier' size='8'>{safe_line}</font>", styles['Normal']))
        
        if len(new_lines) > 30:
            story.append(Paragraph("<i>... (truncated)</i>", styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def initialize_session_state():
    """Initialize all session state variables."""
    if 'selected_case' not in st.session_state:
        st.session_state.selected_case = None
    
    if 'working_content' not in st.session_state:
        st.session_state.working_content = ""
    
    if 'ai_response' not in st.session_state:
        st.session_state.ai_response = None
    
    if 'corrected_netlist' not in st.session_state:
        st.session_state.corrected_netlist = None
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'version_history' not in st.session_state:
        st.session_state.version_history = []
    
    if 'workspace_initialized' not in st.session_state:
        st.session_state.workspace_initialized = False
    
    if 'user_cases' not in st.session_state:
        st.session_state.user_cases = {}
    
    if 'case_type' not in st.session_state:
        st.session_state.case_type = 'example'  # 'example' or 'user'


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main Streamlit application."""
    
    # Page configuration
    st.set_page_config(
        page_title="CircuitSense",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for professional styling (theme-adaptive)
    st.markdown("""
        <style>
        /* Header styling */
        h1 {
            font-weight: 600;
            letter-spacing: -0.5px;
            margin-bottom: 0.5rem;
        }
        
        h2, h3 {
            font-weight: 500;
        }
        
        /* Tab styling - cleaner look */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            background-color: transparent;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            border-radius: 4px;
            font-weight: 500;
            padding: 8px 16px;
            border-bottom: 2px solid transparent;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: transparent;
            border-bottom: 2px solid #4CAF50;
        }
        
        /* Button styling - professional */
        .stButton button {
            border-radius: 4px;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        
        .stButton button:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
        
        /* Code block - better contrast */
        .stCodeBlock {
            border-radius: 4px;
        }
        
        /* Remove excessive padding */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Pulsing status indicator animation */
        @keyframes pulse {
            0%, 100% {
                opacity: 1;
                transform: scale(1);
            }
            50% {
                opacity: 0.7;
                transform: scale(1.1);
            }
        }
        
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: #4CAF50;
            margin-right: 8px;
            animation: pulse 2s ease-in-out infinite;
        }
        
        .status-text {
            display: inline-flex;
            align-items: center;
            font-size: 14px;
            font-weight: 500;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Initialize workspace on first run
    if not st.session_state.workspace_initialized:
        initialize_workspace()
        st.session_state.workspace_initialized = True
    
    # Check for credentials
    api_keys = [GEMINI_API_KEY_1, GEMINI_API_KEY_2, GEMINI_API_KEY_3, GEMINI_API_KEY_4, GEMINI_API_KEY_5]
    if not any(api_keys):
        st.error("⚠️ Missing credentials! Please ensure at least one GEMINI_API_KEY is set in your .env file.")
        st.stop()
    
    # ========================================================================
    # PROFESSIONAL HEADER
    # ========================================================================
    st.title("CircuitSense")
    st.caption("AI-Powered Circuit Analysis & Debugging Platform")
    
    # Compact control bar with glass pane design
    header_col1, header_col2, header_col3, header_col4 = st.columns([2, 2, 1.5, 1.5])
    
    with header_col1:
        case_type = st.radio(
            "Case Type",
            options=["Example Cases", "Custom Netlist"],
            horizontal=True,
            help="Choose between example cases or upload your own netlist",
            key="case_type_radio"
        )
    
    # Check if case type changed - clear workspace if switching to Custom Netlist without files
    previous_case_type = st.session_state.get('case_type', 'example')
    current_case_type = 'example' if case_type == "Example Cases" else 'user'
    
    if current_case_type != previous_case_type:
        if current_case_type == 'user' and not st.session_state.user_cases:
            # Switching to Custom Netlist mode with no uploaded files - clear workspace
            st.session_state.selected_case = None
            st.session_state.working_content = ""
            st.session_state.ai_response = None
            st.session_state.corrected_netlist = None
        st.session_state.case_type = current_case_type
        st.rerun()
    
    with header_col2:
        if case_type == "Example Cases":
            # Show example case dropdown
            all_cases = list(EXAMPLE_CASES.keys())
            selected_case = st.selectbox(
                "Select Example",
                options=all_cases,
                index=0,
                help="Choose a pre-loaded example SPICE netlist"
            )
        else:
            # Show user cases dropdown or upload
            if st.session_state.user_cases:
                user_case_names = list(st.session_state.user_cases.keys())
                selected_case = st.selectbox(
                    "Select Custom",
                    options=user_case_names,
                    help="Choose from your uploaded netlists"
                )
            else:
                st.info("Upload a netlist file below")
                selected_case = None
    
    with header_col3:
        st.markdown("**AI Engine**")
        st.caption("Gemini-3.1-Flash-Lite")
    
    with header_col4:
        active_keys = sum(1 for key in api_keys if key)
        st.markdown("**API Status**")
        st.caption(f"Active: {active_keys} key{'s' if active_keys > 1 else ''}")
    
    # File upload section for custom netlists
    if case_type == "Custom Netlist":
        uploaded_file = st.file_uploader(
            "Upload your SPICE netlist file",
            type=['txt', 'sp', 'cir', 'net', 'asc'],
            help="Upload a SPICE netlist file (.txt, .sp, .cir, .net, or .asc)",
            accept_multiple_files=False
        )
        
        # Automatically load file when uploaded
        if uploaded_file is not None:
            # Check if this is a new file (not already loaded)
            if uploaded_file.name not in st.session_state.user_cases or st.session_state.selected_case != uploaded_file.name:
                try:
                    # Read uploaded file content
                    file_content = uploaded_file.read().decode('utf-8')
                    
                    # Save to user netlists directory
                    user_file_path = os.path.join(USER_NETLISTS_DIR, uploaded_file.name)
                    with open(user_file_path, 'w', encoding='utf-8') as f:
                        f.write(file_content)
                    
                    # Add to user cases
                    st.session_state.user_cases[uploaded_file.name] = user_file_path
                    
                    # Copy to workspace
                    if copy_to_workspace(user_file_path):
                        st.session_state.selected_case = uploaded_file.name
                        st.session_state.case_type = 'user'
                        st.session_state.working_content = read_working_file()
                        st.session_state.ai_response = None
                        st.session_state.corrected_netlist = None
                        st.success(f"✅ Loaded {uploaded_file.name} into workspace")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to load file: {str(e)}")
    
    # Handle case selection change
    if selected_case and (selected_case != st.session_state.selected_case or current_case_type != st.session_state.case_type):
        if case_type == "Example Cases":
            source_file = EXAMPLE_CASES[selected_case]
        else:
            source_file = st.session_state.user_cases[selected_case]
        
        if copy_to_workspace(source_file):
            st.session_state.selected_case = selected_case
            st.session_state.case_type = current_case_type
            st.session_state.working_content = read_working_file()
            st.session_state.ai_response = None
            st.session_state.corrected_netlist = None
        else:
            st.stop()
    
    # Load working content if not already loaded (but not in Custom Netlist mode without files)
    if not st.session_state.working_content and os.path.exists(WORKING_FILE):
        # Only auto-load if we're in Example Cases mode or have user cases
        if current_case_type == 'example' or st.session_state.user_cases:
            st.session_state.working_content = read_working_file()
    
    # ========================================================================
    # TABBED INTERFACE
    # ========================================================================
    tab1, tab2, tab3 = st.tabs(["Workspace & Analysis", "Version Control", "Session History"])
    
    # ========================================================================
    # TAB 1: Workspace & Chat
    # ========================================================================
    with tab1:
        col_left, col_right = st.columns([1, 1])
        
        # LEFT COLUMN: Current Working Netlist
        with col_left:
            st.subheader("Current Working Netlist")
            
            if st.session_state.working_content:
                # Use container with fixed height
                with st.container(height=600):
                    line_count = len(st.session_state.working_content.split('\n'))
                    st.caption(f"{line_count} lines • {os.path.basename(WORKING_FILE)}")
                    
                    st.code(
                        st.session_state.working_content,
                        language="text",
                        line_numbers=True
                    )
            else:
                st.info("Select a test case from the header to begin analysis")
        
        # RIGHT COLUMN: AI Assistant Chat Interface + Proposed Changes
        with col_right:
            st.subheader("AI Analysis Interface")
            
            # Use container with fixed height to match left column
            with st.container(height=600):
                # Custom query input
                user_question = st.text_area(
                    "Ask a question about this circuit:",
                    placeholder="e.g., Why is my op-amp clipping? What's wrong with this circuit? Can you fix the voltage divider?",
                    height=100,
                    help="Enter your custom question. The AI will analyze the netlist and provide a detailed answer."
                )
                
                # Ask AI button
                col_btn1, col_btn2 = st.columns([1, 1])
                
                with col_btn1:
                    ask_button = st.button("Analyze Circuit", type="primary", use_container_width=True)
                
                with col_btn2:
                    if st.button("Clear Response", use_container_width=True):
                        st.session_state.ai_response = None
                        st.session_state.corrected_netlist = None
                        st.rerun()
                
                # Process query
                if ask_button:
                    if not user_question.strip():
                        st.warning("Please enter a question first.")
                    elif not st.session_state.working_content:
                        st.warning("Please select a test case first.")
                    else:
                        try:
                            with st.spinner("Analyzing circuit with Gemini AI..."):
                                ai_response = analyze_netlist(
                                    user_question,
                                    st.session_state.working_content
                                )
                            
                            # Store response
                            st.session_state.ai_response = ai_response
                            
                            # Extract corrected netlist
                            corrected = extract_corrected_netlist(ai_response)
                            st.session_state.corrected_netlist = corrected
                            
                            # Add to chat history
                            st.session_state.chat_history.append({
                                'timestamp': datetime.now(),
                                'question': user_question,
                                'response': ai_response,
                                'accepted': False
                            })
                            
                            st.success("Analysis complete!")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                
                # Display AI response with enhanced styling
                if st.session_state.ai_response:
                    st.markdown("---")
                    
                    # Check if circuit is verified (no errors)
                    if "🌟 Circuit Verified" in st.session_state.ai_response:
                        st.success("### Analysis Complete")
                        st.info(st.session_state.ai_response)
                    else:
                        st.success("### Analysis Complete")
                        st.markdown(st.session_state.ai_response)
                    
                    if not st.session_state.corrected_netlist:
                        if "🌟 Circuit Verified" not in st.session_state.ai_response:
                            st.warning("Could not extract corrected netlist from response. The AI may not have provided a fix.")
                    
                    # PROPOSED CHANGES - Shown in expander within right column
                    if st.session_state.corrected_netlist:
                        st.markdown("---")
                        with st.expander("📋 **Proposed Changes** (Click to expand)", expanded=True):
                            st.caption("🔴 Red = Removed/Changed  |  🟢 Green = Added/Changed")
                            
                            # Generate highlighted diff
                            old_html, new_html = generate_highlighted_diff(
                                st.session_state.working_content,
                                st.session_state.corrected_netlist
                            )
                            
                            # Show diffs side by side in smaller format
                            diff_col1, diff_col2 = st.columns(2)
                            
                            with diff_col1:
                                st.markdown("**Current**")
                                st.markdown(
                                    f'<div style="padding: 0.5rem; border-radius: 4px; border: 1px solid rgba(128,128,128,0.3); max-height: 250px; overflow-y: auto; font-family: monospace; font-size: 11px; line-height: 1.4;">{old_html}</div>',
                                    unsafe_allow_html=True
                                )
                            
                            with diff_col2:
                                st.markdown("**Suggested**")
                                st.markdown(
                                    f'<div style="padding: 0.5rem; border-radius: 4px; border: 1px solid rgba(128,128,128,0.3); max-height: 250px; overflow-y: auto; font-family: monospace; font-size: 11px; line-height: 1.4;">{new_html}</div>',
                                    unsafe_allow_html=True
                                )
                            
                            # Accept changes button
                            st.markdown("")
                            if st.button("✅ Accept Changes", type="primary", use_container_width=True, help="Apply the AI's suggested fix to your working file"):
                                if write_working_file(st.session_state.corrected_netlist):
                                    # Record the change in version history
                                    st.session_state.version_history.append({
                                        'timestamp': datetime.now(),
                                        'from_content': st.session_state.working_content,
                                        'to_content': st.session_state.corrected_netlist,
                                        'question': st.session_state.chat_history[-1]['question'] if st.session_state.chat_history else "N/A",
                                        'ai_explanation': st.session_state.ai_response
                                    })
                                    
                                    st.session_state.working_content = st.session_state.corrected_netlist
                                    
                                    # Mark as accepted in chat history
                                    if st.session_state.chat_history:
                                        st.session_state.chat_history[-1]['accepted'] = True
                                    
                                    # Clear diff viewer
                                    st.session_state.ai_response = None
                                    st.session_state.corrected_netlist = None
                                    
                                    st.success("Changes accepted! Working file updated.")
                                    st.rerun()
    
    # ========================================================================
    # TAB 2: Version Control History
    # ========================================================================
    with tab2:
        if st.session_state.version_history:
            # Header with export button
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"Version Control Log ({len(st.session_state.version_history)} changes)")
                st.caption("Track all accepted changes throughout this session")
            with col2:
                if st.button("📄 Export to PDF", key="export_version_control", use_container_width=True):
                    try:
                        pdf_buffer = generate_version_control_pdf(st.session_state.version_history)
                        st.download_button(
                            label="⬇️ Download PDF",
                            data=pdf_buffer,
                            file_name=f"version_control_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Failed to generate PDF: {str(e)}")
            
            st.markdown("---")
            
            # Display version history in reverse chronological order
            for i, change in enumerate(reversed(st.session_state.version_history)):
                change_num = len(st.session_state.version_history) - i
                timestamp = change['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                
                with st.expander(f"Change #{change_num} • {timestamp}", expanded=False):
                    st.markdown(f"**Question:** {change['question']}")
                    st.caption("🔴 Red = Removed/Changed  |  🟢 Green = Added/Changed")
                    st.markdown("---")
                    
                    # Generate highlighted diff for this change
                    old_html, new_html = generate_highlighted_diff(
                        change['from_content'],
                        change['to_content']
                    )
                    
                    # Show what changed with highlighting
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Before:**")
                        st.markdown(
                            f'<div style="padding: 1rem; border-radius: 4px; border: 1px solid rgba(128,128,128,0.3); max-height: 400px; overflow-y: auto; font-family: monospace; font-size: 14px; line-height: 1.6;">{old_html}</div>',
                            unsafe_allow_html=True
                        )
                    
                    with col2:
                        st.markdown("**After:**")
                        st.markdown(
                            f'<div style="padding: 1rem; border-radius: 4px; border: 1px solid rgba(128,128,128,0.3); max-height: 400px; overflow-y: auto; font-family: monospace; font-size: 14px; line-height: 1.6;">{new_html}</div>',
                            unsafe_allow_html=True
                        )
                    
                    st.markdown("---")
                    st.markdown("**AI Explanation:**")
                    st.info(change['ai_explanation'])
        else:
            st.info("No changes accepted yet. Accept changes in the **Workspace & Analysis** tab to see them tracked here.")
    
    # ========================================================================
    # TAB 3: Session History
    # ========================================================================
    with tab3:
        if st.session_state.chat_history:
            # Header with export button
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"Session History ({len(st.session_state.chat_history)} queries)")
                st.caption("Complete conversation log with the AI assistant")
            with col2:
                if st.button("📄 Export to PDF", key="export_session_history", use_container_width=True):
                    try:
                        pdf_buffer = generate_session_history_pdf(st.session_state.chat_history)
                        st.download_button(
                            label="⬇️ Download PDF",
                            data=pdf_buffer,
                            file_name=f"session_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Failed to generate PDF: {str(e)}")
            
            st.markdown("---")
            
            # Display chat history in modern chat format
            for i, chat in enumerate(reversed(st.session_state.chat_history)):
                query_num = len(st.session_state.chat_history) - i
                timestamp = chat['timestamp'].strftime('%H:%M:%S')
                
                # User message
                with st.chat_message("user"):
                    st.markdown(f"**Query #{query_num}** • {timestamp}")
                    st.markdown(chat['question'])
                
                # Assistant message
                with st.chat_message("assistant"):
                    st.markdown(chat['response'])
                    if chat['accepted']:
                        st.success("Changes accepted and applied to workspace")
                
                st.markdown("---")
        else:
            st.info("No queries yet. Start a conversation with the AI in the **Workspace & Analysis** tab.")
    
    # Footer
    st.markdown("---")
    st.caption("CircuitSense | AI-Powered Circuit Analysis Platform | Built with Streamlit, Google Gemini & IBM Bob IDE")


if __name__ == "__main__":
    main()

# Made with Bob

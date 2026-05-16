import os
import re
import shutil
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from gemini_client import ResilientClient
import difflib
import html

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

# File path mapping for test cases
CASE_FILES = {
    "Case 1": "mistake/m_netlist_case1.txt",
    "Case 2": "mistake/m_netlist_case2.txt",
    "Case 3": "mistake/m_netlist_case3.txt",
    "Case 4": "mistake/m_netlist_case4.txt"
}

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
    """Create temp directory if it doesn't exist."""
    try:
        os.makedirs(TEMP_DIR, exist_ok=True)
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


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main Streamlit application."""
    
    # Page configuration
    st.set_page_config(
        page_title="CircuitSense v2.0",
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
    st.title("CircuitSense v2.0")
    st.caption("AI-Powered Circuit Analysis & Debugging Platform")
    
    # Compact control bar with glass pane design
    header_col1, header_col2, header_col3, header_col4 = st.columns([3, 2, 2, 1])
    
    with header_col1:
        selected_case = st.selectbox(
            "Test Case Selection",
            options=list(CASE_FILES.keys()),
            index=0,
            help="Choose a SPICE netlist to analyze"
        )
    
    with header_col2:
        st.markdown("**AI Engine**")
        st.caption("Gemini-3.1-Flash-Lite")
    
    with header_col3:
        active_keys = sum(1 for key in api_keys if key)
        st.markdown("**API Status**")
        st.caption(f"Active: {active_keys} key{'s' if active_keys > 1 else ''}")
    
    with header_col4:
        st.markdown("**Actions**")
        if st.button("Reset", help="Clear workspace and start fresh", use_container_width=True):
            if os.path.exists(WORKING_FILE):
                os.remove(WORKING_FILE)
            st.session_state.working_content = ""
            st.session_state.ai_response = None
            st.session_state.corrected_netlist = None
            st.session_state.selected_case = None
            st.success("Workspace reset successfully")
            st.rerun()
    
    st.markdown("---")
    
    # Handle case selection change
    if selected_case != st.session_state.selected_case:
        source_file = CASE_FILES[selected_case]
        if copy_to_workspace(source_file):
            st.session_state.selected_case = selected_case
            st.session_state.working_content = read_working_file()
            st.session_state.ai_response = None
            st.session_state.corrected_netlist = None
            st.success(f"✅ Loaded {selected_case} into workspace")
        else:
            st.stop()
    
    # Load working content if not already loaded
    if not st.session_state.working_content and os.path.exists(WORKING_FILE):
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
        
        # RIGHT COLUMN: AI Assistant Chat Interface
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
        
        # Show diff preview and accept button BELOW the two columns (full width)
        if st.session_state.corrected_netlist:
            st.markdown("---")
            st.subheader("Proposed Changes")
            st.caption("🔴 Red = Removed/Changed  |  🟢 Green = Added/Changed")
            st.markdown("")
            
            # Generate highlighted diff
            old_html, new_html = generate_highlighted_diff(
                st.session_state.working_content,
                st.session_state.corrected_netlist
            )
            
            diff_col1, diff_col2 = st.columns(2)
            
            with diff_col1:
                st.markdown("**Current Version**")
                st.markdown(
                    f'<div style="padding: 1rem; border-radius: 4px; border: 1px solid rgba(128,128,128,0.3); max-height: 400px; overflow-y: auto; font-family: monospace; font-size: 14px; line-height: 1.6;">{old_html}</div>',
                    unsafe_allow_html=True
                )
            
            with diff_col2:
                st.markdown("**Suggested Fix**")
                st.markdown(
                    f'<div style="padding: 1rem; border-radius: 4px; border: 1px solid rgba(128,128,128,0.3); max-height: 400px; overflow-y: auto; font-family: monospace; font-size: 14px; line-height: 1.6;">{new_html}</div>',
                    unsafe_allow_html=True
                )
            
            # Accept changes button
            st.markdown("")
            col_accept1, col_accept2, col_accept3 = st.columns([1, 1, 1])
            
            with col_accept2:
                if st.button("Accept Changes", type="primary", use_container_width=True, help="Apply the AI's suggested fix to your working file"):
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
            st.subheader(f"Version Control Log ({len(st.session_state.version_history)} changes)")
            st.caption("Track all accepted changes throughout this session")
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
            st.subheader(f"Session History ({len(st.session_state.chat_history)} queries)")
            st.caption("Complete conversation log with the AI assistant")
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
    st.caption("CircuitSense v2.0 | AI-Powered Circuit Analysis Platform | Built with Streamlit & Google Gemini")


if __name__ == "__main__":
    main()

# Made with Bob

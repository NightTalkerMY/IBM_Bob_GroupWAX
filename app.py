import os
import re
import shutil
import requests
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("IBM_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")

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
SYSTEM_PROMPT_TEMPLATE = """You are CircuitSense, an expert analog electronics engineer and Electronic Design Automation (EDA) assistant.

CRITICAL INSTRUCTIONS - Perform a systematic review using this Chain of Thought:

Step 1. Node & Ground Check
Step 2. Syntax & Value Check
Step 3. Passive Topology Check
Step 4. Active Component Physics Check (Calculate expected voltage gain and compare against DC power supply rails to check for clipping/saturation)

USER QUESTION: {user_question}

NETLIST TO ANALYZE:
{netlist_content}

Respond strictly using ONLY these three markdown headers:
### 🚨 The Error
### 🧠 The Explanation
### ✅ The Corrected Netlist

Place the corrected netlist code inside a code block after the third header."""


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

def get_access_token(api_key: str) -> str:
    """
    Authenticate with IBM Cloud and retrieve access token.
    
    Args:
        api_key: IBM Cloud API key
        
    Returns:
        Access token string
        
    Raises:
        Exception: If authentication fails
    """
    try:
        token_response = requests.post(
            "https://iam.cloud.ibm.com/identity/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": api_key
            },
            timeout=30
        )
        
        if token_response.status_code != 200:
            raise Exception(f"Authentication failed: {token_response.text}")
            
        return token_response.json().get("access_token")
    
    except requests.exceptions.Timeout:
        raise Exception("Authentication request timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error during authentication: {str(e)}")


def analyze_netlist(user_question: str, netlist_content: str, access_token: str, project_id: str) -> str:
    """
    Send custom query and netlist to IBM watsonx.ai for analysis.
    
    Args:
        user_question: User's custom question
        netlist_content: SPICE netlist content
        access_token: IBM Cloud access token
        project_id: Watsonx project ID
        
    Returns:
        AI-generated analysis text
        
    Raises:
        Exception: If API call fails
    """
    try:
        # Build the complete prompt
        prompt = SYSTEM_PROMPT_TEMPLATE.format(
            user_question=user_question,
            netlist_content=netlist_content
        )
        
        # API endpoint
        url = "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"
        
        # Request headers
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        # Request body
        body = {
            "input": prompt,
            "parameters": {
                "decoding_method": "greedy",
                "max_new_tokens": 800,
                "repetition_penalty": 1.2
            },
            "model_id": "meta-llama/llama-3-3-70b-instruct",
            "project_id": project_id
        }
        
        # Make API call
        response = requests.post(url, headers=headers, json=body, timeout=60)
        
        if response.status_code == 200:
            result = response.json()['results'][0]['generated_text'].strip()
            return result
        else:
            raise Exception(f"API call failed with status {response.status_code}: {response.text}")
    
    except requests.exceptions.Timeout:
        raise Exception("Analysis request timed out. The netlist might be too complex.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error during analysis: {str(e)}")
    except KeyError:
        raise Exception("Unexpected API response format. Please try again.")


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
    
    # Initialize session state
    initialize_session_state()
    
    # Initialize workspace on first run
    if not st.session_state.workspace_initialized:
        initialize_workspace()
        st.session_state.workspace_initialized = True
    
    # Header
    st.title("⚡ CircuitSense v2.0")
    st.markdown("**Interactive AI-Powered EDA Debugging Workspace** | Powered by IBM watsonx.ai (Llama-3.3-70B-Instruct)")
    st.markdown("---")
    
    # Check for credentials
    if not API_KEY or not PROJECT_ID:
        st.error("⚠️ Missing credentials! Please ensure IBM_API_KEY and PROJECT_ID are set in your .env file.")
        st.stop()
    
    # Case selection
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        selected_case = st.selectbox(
            "📁 Select Test Case:",
            options=list(CASE_FILES.keys()),
            index=0,
            help="Choose a SPICE netlist to analyze"
        )
    
    with col2:
        st.markdown("### 🎯 Model Info")
        st.caption("Llama-3.3-70B-Instruct")
    
    with col3:
        if st.button("🔄 Reset Workspace", help="Clear temp directory and start fresh"):
            if os.path.exists(WORKING_FILE):
                os.remove(WORKING_FILE)
            st.session_state.working_content = ""
            st.session_state.ai_response = None
            st.session_state.corrected_netlist = None
            st.session_state.selected_case = None
            st.success("✅ Workspace reset!")
            st.rerun()
    
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
    
    st.markdown("---")
    
    # Main two-column layout
    col_left, col_right = st.columns([1, 1])
    
    # ========================================================================
    # LEFT COLUMN: Current Working Netlist
    # ========================================================================
    with col_left:
        st.subheader("📄 Current Working Netlist")
        
        if st.session_state.working_content:
            line_count = len(st.session_state.working_content.split('\n'))
            st.caption(f"📊 {line_count} lines | 📁 {WORKING_FILE}")
            
            st.code(
                st.session_state.working_content,
                language="text",
                line_numbers=True
            )
        else:
            st.info("👈 Select a test case to begin")
    
    # ========================================================================
    # RIGHT COLUMN: AI Assistant Chat Interface
    # ========================================================================
    with col_right:
        st.subheader("💬 AI Assistant")
        
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
            ask_button = st.button("🔍 Ask AI", type="primary", use_container_width=True)
        
        with col_btn2:
            if st.button("🗑️ Clear Response", use_container_width=True):
                st.session_state.ai_response = None
                st.session_state.corrected_netlist = None
                st.rerun()
        
        # Process query
        if ask_button:
            if not user_question.strip():
                st.warning("⚠️ Please enter a question first.")
            elif not st.session_state.working_content:
                st.warning("⚠️ Please select a test case first.")
            else:
                try:
                    with st.spinner("🔐 Authenticating with IBM Cloud..."):
                        access_token = get_access_token(API_KEY)
                    
                    with st.spinner("🧠 Analyzing circuit... This may take a moment..."):
                        ai_response = analyze_netlist(
                            user_question,
                            st.session_state.working_content,
                            access_token,
                            PROJECT_ID
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
                    
                    st.success("✅ Analysis complete!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        # Display AI response
        if st.session_state.ai_response:
            st.markdown("---")
            st.markdown("### 📊 AI Analysis")
            st.markdown(st.session_state.ai_response)
            
            if not st.session_state.corrected_netlist:
                st.warning("⚠️ Could not extract corrected netlist from response. The AI may not have provided a fix.")
    
    # ========================================================================
    # DIFF VIEWER: Before & After Comparison
    # ========================================================================
    if st.session_state.corrected_netlist:
        st.markdown("---")
        st.markdown("## 📊 Before & After Comparison")
        
        diff_col1, diff_col2 = st.columns(2)
        
        with diff_col1:
            st.markdown("#### 🔴 Current Version")
            st.code(
                st.session_state.working_content,
                language="text",
                line_numbers=True
            )
        
        with diff_col2:
            st.markdown("#### 🟢 AI Suggested Fix")
            st.code(
                st.session_state.corrected_netlist,
                language="text",
                line_numbers=True
            )
        
        # Accept changes button
        st.markdown("---")
        col_accept1, col_accept2, col_accept3 = st.columns([1, 1, 1])
        
        with col_accept2:
            if st.button("✅ Accept Changes", type="primary", use_container_width=True, help="Apply the AI's suggested fix to your working file"):
                if write_working_file(st.session_state.corrected_netlist):
                    st.session_state.working_content = st.session_state.corrected_netlist
                    
                    # Mark as accepted in chat history
                    if st.session_state.chat_history:
                        st.session_state.chat_history[-1]['accepted'] = True
                    
                    # Clear diff viewer
                    st.session_state.ai_response = None
                    st.session_state.corrected_netlist = None
                    
                    st.success("✅ Changes accepted! Working file updated.")
                    st.rerun()
    
    # ========================================================================
    # CHAT HISTORY (Optional - in sidebar or expander)
    # ========================================================================
    if st.session_state.chat_history:
        st.markdown("---")
        with st.expander(f"📜 Chat History ({len(st.session_state.chat_history)} queries)", expanded=False):
            for i, chat in enumerate(reversed(st.session_state.chat_history)):
                st.markdown(f"**Query {len(st.session_state.chat_history) - i}** - {chat['timestamp'].strftime('%H:%M:%S')}")
                st.markdown(f"❓ *{chat['question']}*")
                if chat['accepted']:
                    st.success("✅ Changes accepted")
                st.markdown("---")
    
    # Footer
    st.markdown("---")
    st.caption("CircuitSense v2.0 | Interactive AI Debugging Workspace | Built with Streamlit & IBM watsonx.ai")


if __name__ == "__main__":
    main()

# Made with Bob

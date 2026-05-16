import os
import requests
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("IBM_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")

# File path mapping for test cases
CASE_FILES = {
    "Case 1": "mistake/m_netlist_case1.txt",
    "Case 2": "mistake/m_netlist_case2.txt",
    "Case 3": "mistake/m_netlist_case3.txt",
    "Case 4": "mistake/m_netlist_case4.txt"
}

# System prompt template
SYSTEM_PROMPT = """You are CircuitSense, an expert analog electronics engineer and Electronic Design Automation (EDA) assistant. Analyze the following SPICE netlist.

CRITICAL INSTRUCTIONS - Perform a systematic review using this Chain of Thought:

Step 1. Node & Ground Check
Step 2. Syntax & Value Check
Step 3. Passive Topology Check
Step 4. Active Component Physics Check (Calculate expected voltage gain and compare against DC power supply rails to check for clipping/saturation)

Respond strictly using ONLY these three markdown headers:
### 🚨 The Error
### 🧠 The Explanation
### ✅ The Corrected Netlist

Netlist to analyze:

{netlist_text}"""


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


def analyze_netlist(netlist_text: str, access_token: str, project_id: str) -> str:
    """
    Send netlist to IBM watsonx.ai for analysis.
    
    Args:
        netlist_text: SPICE netlist content
        access_token: IBM Cloud access token
        project_id: Watsonx project ID
        
    Returns:
        AI-generated analysis text
        
    Raises:
        Exception: If API call fails
    """
    try:
        # Build the complete prompt
        prompt = SYSTEM_PROMPT.format(netlist_text=netlist_text)
        
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


def read_netlist_file(filepath: str) -> str:
    """
    Read netlist file content with multiple encoding attempts.
    
    Args:
        filepath: Path to the .asc file
        
    Returns:
        File content as string
        
    Raises:
        Exception: If file cannot be read
    """
    try:
        # Try UTF-8 first
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Fall back to latin-1 which can handle special characters like µ
            with open(filepath, 'r', encoding='latin-1') as f:
                return f.read()
    except FileNotFoundError:
        raise Exception(f"File not found: {filepath}")
    except Exception as e:
        raise Exception(f"Error reading file: {str(e)}")


def main():
    """Main Streamlit application."""
    
    # Page configuration
    st.set_page_config(
        page_title="CircuitSense",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Header
    st.title("⚡ CircuitSense")
    st.markdown("**AI-Powered EDA Debugging Tool** | Powered by IBM watsonx.ai (Llama-3.3-70B-Instruct)")
    st.markdown("---")
    
    # Check for credentials
    if not API_KEY or not PROJECT_ID:
        st.error("⚠️ Missing credentials! Please ensure IBM_API_KEY and PROJECT_ID are set in your .env file.")
        st.stop()
    
    # Case selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_case = st.selectbox(
            "📁 Select Test Case:",
            options=list(CASE_FILES.keys()),
            index=0,
            help="Choose a SPICE netlist to analyze"
        )
    
    with col2:
        st.markdown("### 🎯 Model Info")
        st.caption("Model: Llama-3.3-70B-Instruct")
        st.caption("Max Tokens: 800")
    
    # Load selected file
    try:
        filepath = CASE_FILES[selected_case]
        netlist_content = read_netlist_file(filepath)
        
        # Display file info
        line_count = len(netlist_content.split('\n'))
        st.info(f"📄 Loaded: `{filepath}` ({line_count} lines)")
        
    except Exception as e:
        st.error(f"❌ Error loading file: {str(e)}")
        st.stop()
    
    # Netlist display and editing
    st.markdown("### 📝 SPICE Netlist")
    edited_netlist = st.text_area(
        "You can edit the netlist before debugging:",
        value=netlist_content,
        height=400,
        help="Modify the netlist if needed, then click Debug Circuit"
    )
    
    # Debug button
    st.markdown("---")
    if st.button("🔍 Debug Circuit", type="primary", use_container_width=True):
        
        # Validate netlist is not empty
        if not edited_netlist.strip():
            st.error("❌ Netlist is empty. Please provide a valid SPICE netlist.")
            st.stop()
        
        # Analysis process
        try:
            with st.spinner("🔐 Authenticating with IBM Cloud..."):
                access_token = get_access_token(API_KEY)
            
            st.success("✅ Authentication successful!")
            
            with st.spinner("🧠 Analyzing circuit with AI... This may take a moment..."):
                analysis_result = analyze_netlist(edited_netlist, access_token, PROJECT_ID)
            
            # Display results
            st.markdown("---")
            st.markdown("## 📊 Analysis Results")
            st.markdown(analysis_result)
            
            # Success message
            st.success("✅ Analysis complete!")
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("💡 Tip: Check your internet connection and verify your credentials in the .env file.")
    
    # Footer
    st.markdown("---")
    st.caption("CircuitSense v1.0 | Built with Streamlit & IBM watsonx.ai")


if __name__ == "__main__":
    main()

# Made with Bob

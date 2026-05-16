# Advanced Mode Rules

## Custom Utilities (Non-Obvious)

### ResilientClient (gemini_client.py)
- **MUST use ResilientClient**, never direct `genai.Client`
- Implements custom 5-key rotation on 429 errors
- Pass all 5 API keys as list: `[GEMINI_API_KEY_1, ..., GEMINI_API_KEY_5]`
- Handles retries automatically - don't add your own retry logic

### Dual Environment Config Pattern
- `get_api_key()` checks Streamlit secrets FIRST, then .env
- When adding new config: follow this pattern (st.secrets → os.getenv)
- Don't use direct `os.getenv()` for API keys

### Netlist Extraction (app.py lines 215-253)
- Uses 3 fallback regex patterns - this is intentional
- AI responses are inconsistent - don't simplify to single pattern
- Pattern order matters: code block → header content → fallback

## LTspice Syntax (CRITICAL)
- `µ`, `level2`, `SINE` are VALID - never flag as errors
- System prompt explicitly ignores these - don't modify this behavior
- When editing SYSTEM_PROMPT_TEMPLATE, preserve LTspice syntax rules

## File Operations
- All edits in `temp/` directory - never modify `mistake/` or `ground truth/`
- Use `read_working_file()` for encoding handling (UTF-8/latin-1 fallback)
- Use `write_working_file()` for safe writes with error handling

## Session State Management
- Streamlit session state stores: working_content, ai_response, chat_history, version_history
- Initialize with `initialize_session_state()` before accessing
- Don't use global variables - use st.session_state

## Access to MCP and Browser Tools Available
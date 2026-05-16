# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Critical Non-Obvious Patterns

### API System Architecture
- **test.py uses IBM Watson API** (outdated) - expects `IBM_API_KEY` and `PROJECT_ID` in .env
- **app.py uses Google Gemini API** - expects `GEMINI_API_KEY_1` through `GEMINI_API_KEY_5`
- test.py will NOT work with current production setup - it's legacy code from IBM Watson migration

### Custom Resilient Client (gemini_client.py)
- **NOT standard Google Gemini SDK usage** - implements custom 5-key rotation system
- Automatically rotates through API keys on 429/RESOURCE_EXHAUSTED errors
- Retries on 503 errors with 1-second delay
- Always use `ResilientClient` class, never direct `genai.Client`

### Dual Environment Configuration
- `get_api_key()` in app.py checks **Streamlit secrets FIRST**, then falls back to .env
- This is non-standard - supports both local dev (.env) and cloud deployment (st.secrets)
- When deploying to Streamlit Cloud, use secrets.toml, not .env

### LTspice Syntax Handling (CRITICAL)
- System prompt explicitly tells AI to **IGNORE** these valid LTspice formats:
  - `µ` (micro symbol)
  - `level2` (MOSFET model parameter)
  - `SINE` (waveform function)
- These are NOT errors - they're correct LTspice syntax
- Standard SPICE parsers would incorrectly flag them as syntax errors

### Netlist Extraction Pattern
- `extract_corrected_netlist()` uses **3 fallback regex patterns** (lines 215-253 in app.py)
- AI responses are inconsistent - robust parsing required
- Pattern 1: Code block after "✅ The Corrected Netlist" header
- Pattern 2: Content until next header or end
- Pattern 3: Everything after header with markdown cleanup

### Non-Destructive Workspace
- All edits happen in `temp/` directory - original files NEVER modified
- `mistake/` contains test cases with intentional errors
- `ground truth/` contains correct reference netlists
- This is intentional architecture, not temporary storage

## Commands

```bash
# Run application
streamlit run app.py

# Test API connection (NOTE: test.py is outdated and uses IBM Watson, not Gemini)
python test.py  # Will fail unless you have IBM Watson credentials

# Install dependencies
pip install -r requirements.txt
```

## Environment Setup

Required .env variables for production:
```
GEMINI_API_KEY_1=your_key_here
GEMINI_API_KEY_2=your_key_here  # Optional but recommended for failover
GEMINI_API_KEY_3=your_key_here  # Optional
GEMINI_API_KEY_4=your_key_here  # Optional
GEMINI_API_KEY_5=your_key_here  # Optional
```

Legacy variables (not used in current app.py):
```
IBM_API_KEY=...      # Only for test.py
PROJECT_ID=...       # Only for test.py
```

## File Encoding
- App handles both UTF-8 and latin-1 encoding automatically (see `read_working_file()`)
- Special characters (µ, Ω) are supported in netlists
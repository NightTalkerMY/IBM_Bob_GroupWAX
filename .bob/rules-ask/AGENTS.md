# Ask Mode Rules

## Project Context (Non-Obvious)

### Dual API System Architecture
- **test.py is OUTDATED** - uses IBM Watson API (not Gemini)
- Production app (app.py) uses Google Gemini with custom failover
- Don't reference test.py for current API patterns

### Directory Structure (Counterintuitive)
- `mistake/` contains test cases with **intentional errors** (not actual mistakes)
- `ground truth/` contains correct reference netlists
- `temp/` is the working directory - all edits happen here
- Original files are NEVER modified - this is by design

### LTspice Syntax Context
- `µ`, `level2`, `SINE` appear in netlists - these are VALID
- System is designed to work with LTspice-specific syntax
- Don't suggest "fixing" these - they're correct

### Deployment Context
- App supports both local (.env) and cloud (st.secrets) deployment
- `get_api_key()` function handles dual environment automatically
- When discussing deployment, mention both options

### Session State Architecture
- Version control is in-memory (Streamlit session state), not git
- PDF export provides persistence
- Chat history and version history are separate concerns
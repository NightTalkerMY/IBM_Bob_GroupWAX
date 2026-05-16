# Plan Mode Rules

## Architecture Constraints (Non-Obvious)

### API System Evolution
- Project migrated from IBM Watson to Google Gemini
- test.py is legacy code - don't base new features on it
- Custom ResilientClient implements 5-key failover (not standard SDK)
- When planning API changes, account for multi-key rotation system

### Non-Destructive Design Pattern
- `temp/` directory is the workspace - all modifications happen here
- `mistake/` and `ground truth/` are reference data - never modified
- This is intentional architecture for safe experimentation
- New features must preserve this pattern

### Dual Environment Support
- Must support both local (.env) and cloud (st.secrets) deployment
- `get_api_key()` pattern should be followed for all config
- Don't hardcode environment-specific logic

### LTspice Integration Constraints
- System must handle LTspice-specific syntax (µ, level2, SINE)
- AI prompt engineering explicitly ignores these patterns
- Any netlist parsing must account for LTspice quirks
- Standard SPICE parsers won't work - custom parsing required

### Session State Architecture
- Streamlit session state is the source of truth
- No external database or git integration
- Version control and chat history are in-memory
- PDF export is the only persistence mechanism

### Response Parsing Complexity
- AI responses are inconsistent - requires 3 fallback patterns
- Don't assume structured output - robust parsing essential
- Pattern order matters for extraction reliability
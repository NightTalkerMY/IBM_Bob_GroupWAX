# ⚡ CircuitSense

**AI-Powered Circuit Analysis & Debugging Platform**

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-4285F4?style=flat&logo=google&logoColor=white)](https://ai.google.dev/)

## 🎯 Overview

CircuitSense is an advanced web application that leverages Google Gemini AI to provide interactive, intelligent debugging of SPICE netlists. Built with Streamlit, it offers a professional workspace for analyzing analog circuits, identifying errors, and applying AI-suggested fixes with full version control.

### Key Capabilities

- 🔍 **Intelligent Circuit Analysis** - AI-powered error detection and explanation
- 💬 **Natural Language Interface** - Ask questions in plain English
- 📊 **Visual Diff Comparison** - Side-by-side before/after highlighting
- ✅ **Version Control** - Track all changes with full history
- 📄 **PDF Export** - Generate professional reports
- 🔄 **Multi-API Resilience** - Automatic failover across 5 API keys

## ✨ Features

### 🤖 AI-Powered Analysis
- **Smart Error Detection**: Identifies floating nodes, syntax errors, and physics violations
- **Context-Aware Explanations**: Understands op-amp clipping, feedback stability, and more
- **Automatic Fixes**: Generates corrected netlists with proper formatting
- **Custom Queries**: Ask specific questions about your circuit

### 🎨 Professional Interface
- **Three-Tab Layout**: Workspace, Version Control, and Session History
- **Syntax-Highlighted Code**: Line-numbered SPICE netlist display
- **Color-Coded Diffs**: Red for removed, green for added changes
- **Responsive Design**: Clean, modern UI that adapts to your screen

### 📚 Version Control System
- **Change Tracking**: Every accepted modification is logged
- **Timestamp Records**: Know exactly when changes were made
- **Rollback Capability**: Review previous versions
- **Export History**: Generate PDF reports of all changes

### 🔒 Non-Destructive Workflow
- **Isolated Workspace**: Original files remain untouched
- **Temporary Directory**: All edits in `temp/` folder
- **Safe Experimentation**: Test fixes without risk
- **Easy Reset**: Start fresh anytime

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key(s)
- Modern web browser

### Installation

1. **Clone the repository:**
```bash
git clone <your-repo-url>
cd ibm_hackathon
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure API keys:**

Create a `.env` file in the project root:
```env
GEMINI_API_KEY_1=your_first_api_key_here
GEMINI_API_KEY_2=your_second_api_key_here
GEMINI_API_KEY_3=your_third_api_key_here
GEMINI_API_KEY_4=your_fourth_api_key_here
GEMINI_API_KEY_5=your_fifth_api_key_here
```

**Note:** You need at least one API key. Additional keys provide automatic failover for quota management.

### Running the Application

```bash
streamlit run app.py
```

The application will open automatically at `http://localhost:8501`

## 📖 Usage Guide

### 1️⃣ Select a Test Case
- Choose from **Case 1-4** in the header dropdown
- File automatically loads into workspace
- View the netlist in the left panel

### 2️⃣ Ask Your Question
- Enter a natural language query in the right panel
- Examples:
  - *"What's wrong with this circuit?"*
  - *"Why is my op-amp clipping?"*
  - *"Can you fix the voltage divider?"*
  - *"Explain the feedback configuration"*

### 3️⃣ Get AI Analysis
- Click **"Analyze Circuit"** button
- AI processes your netlist with context
- Receive structured response:
  - 🚨 **The Error** - What's wrong
  - 🧠 **The Explanation** - Why it's wrong
  - ✅ **The Corrected Netlist** - How to fix it

### 4️⃣ Review Changes
- **Proposed Changes** section appears below
- Side-by-side comparison with color highlighting
- 🔴 Red = Current version (removed/changed)
- 🟢 Green = Suggested fix (added/changed)

### 5️⃣ Accept or Reject
- Click **"Accept Changes"** to apply the fix
- Workspace updates automatically
- Change logged in version control
- Or click **"Clear Response"** to reject

### 6️⃣ Track Your Progress
- **Version Control Tab**: See all accepted changes
- **Session History Tab**: Review all conversations
- **Export to PDF**: Generate professional reports

## 🏗️ Project Structure

```
ibm_hackathon/
├── app.py                      # Main Streamlit application
├── gemini_client.py            # Resilient API client with failover
├── config.py                   # Model configuration
├── requirements.txt            # Python dependencies
├── .env                        # API keys (not in git)
├── .gitignore                  # Git ignore rules
├── README.md                   # This file
├── test.py                     # API connection test
├── temp/                       # Workspace directory (auto-created)
│   └── working_netlist.txt     # Current working file
├── mistake/                    # Test cases with intentional errors
│   ├── 65nm_bulk.lib           # Technology library
│   ├── 180nm_bulk.lib          # Technology library
│   ├── m_netlist_case1.txt     # Test case 1 netlist
│   ├── m_netlist_case2.txt     # Test case 2 netlist
│   ├── m_netlist_case3.txt     # Test case 3 netlist
│   ├── m_netlist_case4.txt     # Test case 4 netlist
│   ├── m_case1.asc             # LTspice schematic
│   ├── m_case2.asc             # LTspice schematic
│   ├── m_case3.asc             # LTspice schematic
│   └── m_case4.asc             # LTspice schematic
└── ground truth/               # Reference netlists (correct versions)
    ├── 65nm_bulk.lib
    ├── 180nm_bulk.lib
    ├── t_netlist_case1.txt
    ├── t_netlist_case2.txt
    ├── t_netlist_case3.txt
    ├── t_netlist_case4.txt
    ├── t_case1.asc
    ├── t_case2.asc
    ├── t_case3.asc
    └── t_case4.asc
```

## 🔧 Technical Architecture

### AI Engine

**Model**: Google Gemini 3.1 Flash Lite
- Fast response times
- Cost-effective for iterative debugging
- Excellent circuit analysis capabilities

**Resilient Client System**:
```python
class ResilientClient:
    - Manages 5 API keys
    - Automatic failover on quota exhaustion
    - Graceful error handling
    - Verbose logging for debugging
```

### System Prompt Engineering

The AI is instructed to:
1. **Node Check**: Validate voltage source connections
2. **Syntax Check**: Ignore LTspice-specific formatting (µ, level2, SINE)
3. **Physics Check**: Calculate gain, detect clipping, verify stability
4. **Escape Hatch**: Don't invent errors in perfect circuits

### Response Parsing

Multi-pattern extraction system:
1. Primary: Code block after "✅ The Corrected Netlist"
2. Fallback: Text extraction with markdown cleanup
3. Validation: Ensures clean SPICE format

### Session State Management

Tracked variables:
- `selected_case` - Current test case
- `working_content` - Active netlist
- `ai_response` - Latest analysis
- `corrected_netlist` - Extracted fix
- `chat_history` - All Q&A pairs
- `version_history` - Accepted changes

### PDF Generation

Uses ReportLab to create professional documents:
- **Session History PDF**: Complete conversation log
- **Version Control PDF**: All changes with diffs
- Custom styling and formatting
- Timestamp and metadata

## 🧪 Test Cases

### Case 1: Complex Digital Logic
- **Type**: MOSFET-based logic circuit
- **Complexity**: ~30 lines
- **Common Issues**: Node connections, ground references

### Case 2: NAND Gate
- **Type**: CMOS logic gate
- **Complexity**: ~15 lines
- **Common Issues**: Transistor sizing, power supply connections

### Case 3: RC Filter
- **Type**: Passive filter network
- **Complexity**: ~10 lines
- **Common Issues**: Component values, topology errors

### Case 4: Op-Amp Circuit
- **Type**: Operational amplifier configuration
- **Complexity**: ~13 lines
- **Common Issues**: Feedback, biasing, saturation/clipping

## 🛠️ Troubleshooting

### API Key Issues

**Problem**: "Missing credentials" error
**Solution**:
- Verify `.env` file exists in project root
- Check at least one `GEMINI_API_KEY_X` is set
- Ensure no typos in variable names
- Test with `test.py` if available

### Workspace Errors

**Problem**: "Failed to create workspace" error
**Solution**:
- Check write permissions in project directory
- Manually create `temp/` folder
- Verify sufficient disk space
- Run as administrator if needed (Windows)

### Extraction Failures

**Problem**: "Could not extract corrected netlist" warning
**Solution**:
- AI may not have provided a fix (circuit might be correct)
- Try rephrasing your question more specifically
- Review full AI response for insights
- Check if the error is actually fixable

### Encoding Issues

**Problem**: Special characters display incorrectly
**Solution**:
- App handles UTF-8 and latin-1 automatically
- Special characters (µ, Ω) are supported
- If issues persist, check source file encoding
- Try re-saving files with UTF-8 encoding

### Startup Problems

**Problem**: Application won't start
**Solution**:
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Check Python version
python --version  # Should be 3.8+

# Verify Streamlit
streamlit --version

# Test API connection
python test.py  # If available
```

## 💡 Best Practices

### Asking Effective Questions

✅ **Good Questions**:
- "What's causing the voltage clipping in this op-amp?"
- "Why isn't this MOSFET turning on properly?"
- "Can you fix the ground connection issues?"
- "Explain the feedback configuration and stability"

❌ **Less Effective**:
- "Fix it" (too vague)
- "Is this good?" (yes/no questions)
- Very long, multi-part questions
- Questions about unrelated topics

### Iterative Debugging Workflow

1. **Start Broad**: Ask general questions first
2. **Review Carefully**: Understand the AI's explanation
3. **Accept Wisely**: Only apply changes you comprehend
4. **Follow Up**: Ask specific questions on updated code
5. **Track Progress**: Use version control to see evolution

### Version Control Tips

- ✅ Accept changes when you understand the reasoning
- ✅ Use "Clear Response" to reject unclear fixes
- ✅ Export PDFs before major changes
- ✅ Compare with ground truth files for validation
- ✅ Reset workspace if you get lost

## 🔒 Security & Privacy

### API Key Protection
- Never commit `.env` file to version control
- Keep Gemini API keys confidential
- `.gitignore` configured to exclude sensitive files
- Use environment variables for deployment

### Data Handling
- All processing happens locally
- Netlists sent to Google Gemini API for analysis
- No data stored on external servers
- Temp directory excluded from git

### Deployment Considerations
- For production: Use Streamlit secrets management
- Supports both `.env` (local) and `st.secrets` (cloud)
- Automatic fallback between environments
- See `get_api_key()` function in `app.py`

## 📚 Dependencies

```txt
streamlit>=1.28.0      # Web application framework
python-dotenv>=1.0.0   # Environment variable management
google-genai>=1.0.0    # Google Gemini API client
reportlab>=4.0.0       # PDF generation library
```

### Installation Notes
- All dependencies are pure Python
- No system-level packages required
- Compatible with Windows, macOS, and Linux
- Virtual environment recommended

## 🚀 Advanced Features

### Multi-API Resilience

The `ResilientClient` class provides:
- **Automatic Failover**: Switches keys on quota exhaustion
- **Retry Logic**: Handles transient 503 errors
- **Verbose Logging**: Tracks which key is active
- **Graceful Degradation**: Clear error messages

### Diff Highlighting Algorithm

```python
def generate_highlighted_diff(old_text, new_text):
    # Character-level comparison
    # Line-by-line highlighting
    # HTML generation with color coding
    # Handles additions and deletions
```

### PDF Export System

Two types of reports:
1. **Session History**: All questions and answers
2. **Version Control**: All changes with diffs

Features:
- Professional formatting
- Timestamp metadata
- Truncation for large files
- Custom styling

## 🎓 Learning Resources

### Understanding SPICE Netlists
- [LTspice Documentation](https://www.analog.com/en/design-center/design-tools-and-calculators/ltspice-simulator.html)
- SPICE syntax and component models
- Circuit simulation basics

### AI-Assisted Debugging
- How to formulate effective queries
- Interpreting AI explanations
- Validating suggested fixes

### Circuit Analysis
- Op-amp configurations
- MOSFET logic gates
- Passive filter design
- Feedback and stability

## 🤝 Contributing

This project welcomes improvements! To contribute:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature-name`
3. **Make your changes**: Follow existing code style
4. **Test thoroughly**: Verify all test cases work
5. **Update documentation**: Keep README current
6. **Submit a pull request**: Describe your changes

### Code Style
- Follow PEP 8 for Python code
- Use type hints where appropriate
- Add docstrings to functions
- Comment complex logic

## 📄 License

This project was created for educational purposes. Feel free to use and modify for your own projects.

## 🙏 Acknowledgments

- **Google Gemini AI** - For the powerful language model
- **Streamlit** - For the excellent web framework
- **ReportLab** - For PDF generation capabilities
- **LTspice** - For SPICE netlist format standards

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the troubleshooting section
- Review the usage guide

---

**CircuitSense** | AI-Powered Circuit Analysis Platform | Built with ❤️ and Streamlit

*Last Updated: 2026-05-16*
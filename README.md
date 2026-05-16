# ⚡ CircuitSense v2.0

**Interactive AI-Powered Electronic Design Automation (EDA) Debugging Workspace**

## 🎯 Overview

CircuitSense v2.0 is an advanced Streamlit web application that uses IBM watsonx.ai (Llama-3.3-70B-Instruct) to provide interactive, non-destructive debugging of SPICE netlists. It features a workspace management system, custom query interface, and version control for circuit modifications.

## ✨ New Features in v2.0

### 🔒 **Non-Destructive Workspace**
- Automatic `temp/` directory creation
- Original files in `mistake/` remain untouched
- All edits happen in isolated workspace
- Safe experimentation without data loss

### 💬 **Interactive Chat Interface**
- Ask custom questions about your circuit
- Natural language queries (e.g., "Why is my op-amp clipping?")
- AI analyzes netlist in context of your question
- Chat history tracking

### 📊 **Before & After Diff Viewer**
- Side-by-side comparison of current vs. suggested fixes
- Color-coded visualization (🔴 Current | 🟢 Suggested)
- Line-numbered code display
- Clear visual feedback

### ✅ **Version Control System**
- "Accept Changes" workflow
- Apply AI suggestions with one click
- Automatic workspace update
- Track accepted changes in history

### 🔄 **Reset Workspace**
- Clear temp directory and start fresh
- Quick reset button in UI
- Preserves original dataset

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- IBM Cloud account with watsonx.ai access
- IBM API Key and Project ID

### Installation

1. **Navigate to project directory:**
```bash
cd d:/ibm_hackathon
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**

Create a `.env` file in the project root:
```env
IBM_API_KEY=your_api_key_here
PROJECT_ID=your_project_id_here
```

### Running the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## 📖 Usage Guide

### Step 1: Select a Test Case
- Choose from Case 1-4 in the dropdown menu
- File automatically copies to `temp/working_netlist.txt`
- Left panel displays current working netlist

### Step 2: Ask a Question
- Enter your question in the right panel text area
- Examples:
  - "What's wrong with this circuit?"
  - "Why is my op-amp clipping?"
  - "Can you fix the voltage divider?"
  - "Explain the error in this netlist"

### Step 3: Get AI Analysis
- Click "🔍 Ask AI" button
- Wait for authentication and analysis
- View detailed response with three sections:
  - 🚨 **The Error**: What's wrong
  - 🧠 **The Explanation**: Why it's wrong
  - ✅ **The Corrected Netlist**: How to fix it

### Step 4: Review Changes
- Before & After comparison appears below
- Left column: Your current code
- Right column: AI's suggested fix
- Compare line-by-line with line numbers

### Step 5: Accept or Reject
- Click "✅ Accept Changes" to apply the fix
- Working file updates automatically
- Left panel refreshes with new code
- Or click "🗑️ Clear Response" to reject

### Step 6: Iterate
- Ask follow-up questions on the updated code
- Build on previous fixes
- Track all changes in chat history

## 🏗️ Project Structure

```
d:/ibm_hackathon/
├── app.py                      # Main application (v2.0)
├── test.py                     # API connection test
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not in git)
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
├── temp/                      # Workspace directory (auto-created)
│   └── working_netlist.txt   # Current working file
├── mistake/                   # Test cases with errors
│   ├── m_netlist_case1.txt
│   ├── m_netlist_case2.txt
│   ├── m_netlist_case3.txt
│   ├── m_netlist_case4.txt
│   ├── m_case1.asc           # LTspice schematics
│   ├── m_case2.asc
│   ├── m_case3.asc
│   └── m_case4.asc
└── ground truth/              # Reference netlists (correct)
    ├── t_netlist_case1.txt
    ├── t_netlist_case2.txt
    ├── t_netlist_case3.txt
    ├── t_netlist_case4.txt
    ├── t_case1.asc
    ├── t_case2.asc
    ├── t_case3.asc
    └── t_case4.asc
```

## 🔧 Technical Details

### Workspace Management

**Initialization:**
- Creates `temp/` directory on startup
- Checks for existing workspace files

**File Operations:**
- Copy: `mistake/*.txt` → `temp/working_netlist.txt`
- Read: UTF-8 with latin-1 fallback for special characters
- Write: UTF-8 encoding for corrected netlists

**Safety:**
- Original files never modified
- All operations isolated to temp directory
- Reset button clears workspace

### AI Query System

**Prompt Structure:**
```
[System Instructions]
  ↓
[Chain of Thought Steps]
  ↓
[User's Custom Question]
  ↓
[Current Netlist Content]
  ↓
[Response Format Instructions]
```

**API Configuration:**
- Model: `meta-llama/llama-3-3-70b-instruct`
- Max Tokens: 800
- Repetition Penalty: 1.2
- Decoding: Greedy

### Response Parsing

**Extraction Logic:**
1. Search for `### ✅ The Corrected Netlist` header
2. Extract code block content
3. Remove markdown formatting
4. Return clean netlist code

**Fallback Patterns:**
- Try code block extraction first
- Fall back to text extraction
- Handle various markdown formats

### Session State Management

**Tracked Variables:**
- `selected_case`: Current test case
- `working_content`: Current netlist in workspace
- `ai_response`: Latest AI analysis
- `corrected_netlist`: Extracted fix from AI
- `chat_history`: All queries and responses
- `workspace_initialized`: Setup status

**State Flow:**
```
Select Case → Copy File → Load Content
     ↓
Ask Question → Get Response → Parse Fix
     ↓
Review Diff → Accept/Reject → Update State
     ↓
Iterate or Reset
```

## 🧪 Test Cases

### Case 1: Complex Digital Logic
- **File**: `m_netlist_case1.txt`
- **Size**: ~30 lines
- **Type**: MOSFET-based logic circuit
- **Common Issues**: Node connections, ground references

### Case 2: NAND Gate
- **File**: `m_netlist_case2.txt`
- **Size**: ~15 lines
- **Type**: Simple CMOS logic
- **Common Issues**: Transistor sizing, power supply

### Case 3: RC Filter
- **File**: `m_netlist_case3.txt`
- **Size**: ~10 lines
- **Type**: Passive filter
- **Common Issues**: Component values, topology

### Case 4: Op-Amp Circuit
- **File**: `m_netlist_case4.txt`
- **Size**: ~13 lines
- **Type**: Operational amplifier
- **Common Issues**: Feedback, biasing, clipping

## 🛠️ Troubleshooting

### "Missing credentials" error
- Ensure `.env` file exists in project root
- Verify `IBM_API_KEY` and `PROJECT_ID` are set
- Check for typos in variable names

### "Failed to create workspace" error
- Check write permissions in project directory
- Manually create `temp/` folder
- Verify disk space available

### "Could not extract corrected netlist" warning
- AI may not have provided a fix
- Try rephrasing your question
- Check if error is fixable
- Review full AI response for insights

### Encoding errors
- App handles UTF-8 and latin-1 automatically
- Special characters (µ, Ω) supported
- If issues persist, check file encoding

### Application won't start
- Install dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (3.8+)
- Verify Streamlit installation: `streamlit --version`

## 💡 Tips for Best Results

### Asking Questions

**Good Questions:**
- "What's causing the voltage clipping in this op-amp?"
- "Why isn't this MOSFET turning on properly?"
- "Can you fix the ground connection issues?"
- "Explain why this circuit won't oscillate"

**Less Effective:**
- "Fix it" (too vague)
- "Is this good?" (yes/no questions)
- Very long, multi-part questions

### Iterative Debugging

1. Start with broad questions
2. Accept fixes that make sense
3. Ask follow-up questions on updated code
4. Build understanding incrementally
5. Use chat history to track progress

### Version Control

- Accept changes only when you understand them
- Use "Clear Response" to reject unclear fixes
- Reset workspace to start over if needed
- Compare with ground truth files for validation

## 🔒 Security Notes

- Never commit `.env` file to version control
- Keep IBM API key confidential
- `.gitignore` configured to exclude sensitive files
- Temp directory excluded from git

## 📚 Dependencies

```
streamlit >= 1.28.0    # Web framework
requests >= 2.31.0     # HTTP library
python-dotenv >= 1.0.0 # Environment variables
```

## 🆚 Version Comparison

### v1.0 Features
- ✅ Basic case selection
- ✅ Static netlist display
- ✅ One-shot AI analysis
- ✅ Markdown output

### v2.0 Additions
- ✅ Non-destructive workspace
- ✅ Interactive chat interface
- ✅ Custom query support
- ✅ Before/After diff viewer
- ✅ Accept/Reject workflow
- ✅ Chat history tracking
- ✅ Reset workspace button
- ✅ Session state management

## 🚀 Future Enhancements

Potential features for v3.0:
- 📥 Export chat history as JSON/PDF
- 🎨 Syntax highlighting for SPICE
- 📊 Circuit visualization
- 🔍 Multi-file project support
- 💾 Auto-save and recovery
- 📈 Analysis statistics dashboard
- 🌐 Multi-language support

## 🤝 Contributing

This is a hackathon project. For improvements:
1. Test thoroughly before deployment
2. Maintain backward compatibility
3. Update documentation
4. Follow existing code style

## 📄 License

Created for IBM Hackathon.

## 🙏 Acknowledgments

- **IBM watsonx.ai** for the Llama-3.3-70B-Instruct model
- **Streamlit** for the web framework
- **LTspice** for SPICE netlist format standards

---

**CircuitSense v2.0** | Built with ❤️ for IBM Hackathon | Interactive AI Debugging Workspace
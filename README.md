# ⚡ CircuitSense

AI-Powered Electronic Design Automation (EDA) Debugging Tool

## 🎯 Overview

CircuitSense is a Streamlit web application that uses IBM watsonx.ai (Llama-3.3-70B-Instruct) to analyze SPICE netlists and detect design and topology errors in analog circuits.

## ✨ Features

- 📁 **Case Selection**: Choose from 4 pre-loaded test cases
- 📝 **Editable Netlists**: View and modify SPICE netlists before analysis
- 🧠 **AI-Powered Analysis**: Systematic circuit debugging using Chain of Thought reasoning
- 🎨 **Clean UI**: Intuitive Streamlit interface with real-time feedback
- 🔐 **Secure**: Credentials managed via environment variables

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- IBM Cloud account with watsonx.ai access
- IBM API Key and Project ID

### Installation

1. **Clone or navigate to the project directory:**
```bash
cd d:/ibm_hackathon
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**

Create a `.env` file in the project root with your IBM credentials:
```env
IBM_API_KEY=your_api_key_here
PROJECT_ID=your_project_id_here
```

### Running the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

## 📖 Usage

1. **Select a Test Case**: Choose from Case 1-4 in the dropdown menu
2. **Review the Netlist**: The SPICE netlist will be displayed in an editable text area
3. **Edit (Optional)**: Modify the netlist if needed
4. **Debug**: Click the "🔍 Debug Circuit" button
5. **View Results**: The AI analysis will appear with three sections:
   - 🚨 **The Error**: Identified issues
   - 🧠 **The Explanation**: Detailed reasoning
   - ✅ **The Corrected Netlist**: Fixed version

## 🏗️ Project Structure

```
d:/ibm_hackathon/
├── app.py                  # Main Streamlit application
├── test.py                 # API connection test script
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in git)
├── .gitignore             # Git ignore rules
├── README.md              # This file
├── mistake/               # Test case netlists with errors
│   ├── m_case1.asc
│   ├── m_case2.asc
│   ├── m_case3.asc
│   └── m_case4.asc
└── ground truth/          # Reference netlists (correct versions)
    ├── t_case1.asc
    ├── t_case2.asc
    ├── t_case3.asc
    └── t_case4.asc
```

## 🔧 Technical Details

### AI Analysis Process

The application uses a structured Chain of Thought approach:

1. **Node & Ground Check**: Validates circuit connectivity
2. **Syntax & Value Check**: Verifies SPICE syntax and component values
3. **Passive Topology Check**: Analyzes resistor, capacitor, and inductor configurations
4. **Active Component Physics Check**: Calculates voltage gain and checks for clipping/saturation

### API Configuration

- **Model**: `meta-llama/llama-3-3-70b-instruct`
- **Max Tokens**: 800
- **Repetition Penalty**: 1.2
- **Decoding Method**: Greedy

### Error Handling

The application includes comprehensive error handling for:
- Missing credentials
- File reading errors
- Authentication failures
- API timeouts
- Network issues
- Invalid responses

## 🧪 Testing the API Connection

Before running the full application, you can test your IBM watsonx.ai connection:

```bash
python test.py
```

This will verify your credentials and API access.

## 📝 Test Cases

- **Case 1**: Complex digital logic circuit (350 lines)
- **Case 2**: Simple NAND gate implementation (69 lines)
- **Case 3**: RC filter circuit (22 lines)
- **Case 4**: Op-amp based circuit (74 lines)

## 🛠️ Troubleshooting

### "Missing credentials" error
- Ensure `.env` file exists in the project root
- Verify `IBM_API_KEY` and `PROJECT_ID` are set correctly

### "Authentication failed" error
- Check your IBM API key is valid
- Ensure you have access to watsonx.ai

### "File not found" error
- Verify the `mistake/` directory contains all test case files
- Check file paths are correct

### Application won't start
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.8+)

## 🔒 Security Notes

- Never commit your `.env` file to version control
- Keep your IBM API key confidential
- The `.gitignore` file is configured to exclude sensitive files

## 📚 Dependencies

- **streamlit**: Web application framework
- **requests**: HTTP library for API calls
- **python-dotenv**: Environment variable management

## 🤝 Contributing

This is a hackathon project. For improvements or bug fixes, please test thoroughly before deployment.

## 📄 License

This project is created for the IBM Hackathon.

## 🙏 Acknowledgments

- IBM watsonx.ai for the AI model
- Streamlit for the web framework
- LTspice for SPICE netlist format

---

**Built with ❤️ for IBM Hackathon**
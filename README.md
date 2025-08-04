# Setup Instructions for CV Chatbot with CrewAI

## 1. Install Ollama
# Download and install Ollama from https://ollama.ai
# Pull the required model:
ollama pull llama3.1:8b

## 2. Install Python Dependencies
pip install -r requirements.txt

## 3. Run the Application
streamlit run main.py

## 4. Project Structure
cv-chatbot/
├── main.py              # Streamlit app
├── crew_system.py       # CrewAI agents and tasks
├── utils.py             # Utility functions
├── requirements.txt     # Python dependencies
└── README.md           # This file

## 5. Features
- ✅ Multi-format CV parsing (PDF, Word)
- ✅ Multi-language support (French, English)
- ✅ Job matching with similarity scores
- ✅ Dynamic quiz generation
- ✅ Interactive Streamlit interface
- ✅ Three specialized AI agents using CrewAI

## 6. Usage
1. Upload your CV (PDF or Word format)
2. Get top 3 job matches with similarity scores
3. Select a job position
4. Take a personalized quiz
5. Get instant results and feedback

## 7. Customization
- Modify job_descriptions in utils.py for your job database
- Adjust agent prompts in crew_system.py
- Customize UI in main.py
- Add more question types in quiz generation

## 8. Troubleshooting
- Make sure Ollama is running: ollama serve
- Check if model is pulled: ollama list
- Verify all dependencies are installed
- Check file permissions for temp file operations

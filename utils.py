import tempfile
import os
import json
from pathlib import Path
import PyPDF2
from docx import Document
from langdetect import detect
import streamlit as st

def save_uploaded_file(uploaded_file):
    """Save uploaded file to temporary location"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return None

def extract_text_from_file(file_path):
    """Extract text from PDF or Word documents"""
    try:
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.pdf':
            return extract_text_from_pdf(file_path)
        elif file_extension in ['.docx', '.doc']:
            return extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")
    
    return text.strip()

def extract_text_from_docx(file_path):
    """Extract text from Word document"""
    try:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Error reading Word document: {str(e)}")

def detect_language(text):
    """Detect language of the text"""
    try:
        if len(text.strip()) < 10:
            return "unknown"
        lang = detect(text)
        return "french" if lang == "fr" else "english" if lang == "en" else lang
    except:
        return "unknown"

def load_job_descriptions():
    """Load sample job descriptions - you can modify this to load from database"""
    return [
        {
            "job_id": "1",
            "job_title": "Full Stack Developer",
            "company": "TechCorp Tunisia",
            "job_type": "Stage d'été",
            "description": "Develop and maintain web applications using modern technologies",
            "requirements": "JavaScript, React, Node.js, Python, SQL, Git",
            "experience_level": "Junior",
            "location": "Tunis, Tunisia"
        },
        {
            "job_id": "2",
            "job_title": "Data Scientist",
            "company": "DataTech Solutions",
            "job_type": "PFE",
            "description": "Analyze large datasets and build predictive models",
            "requirements": "Python, Machine Learning, SQL, Statistics, Pandas, Scikit-learn",
            "experience_level": "Entry Level",
            "location": "Tunis, Tunisia"
        },
        {
            "job_id": "3",
            "job_title": "DevOps Engineer",
            "company": "CloudTech",
            "job_type": "Stage d'été",
            "description": "Manage infrastructure and deployment pipelines",
            "requirements": "Docker, Kubernetes, AWS, Linux, CI/CD, Python, Bash",
            "experience_level": "Junior",
            "location": "Sfax, Tunisia"
        },
        {
            "job_id": "4",
            "job_title": "Mobile App Developer",
            "company": "MobileTech",
            "job_type": "PFE",
            "description": "Develop native and cross-platform mobile applications",
            "requirements": "React Native, Flutter, iOS, Android, JavaScript, Dart",
            "experience_level": "Entry Level",
            "location": "Tunis, Tunisia"
        },
        {
            "job_id": "5",
            "job_title": "Cybersecurity Analyst",
            "company": "SecureTech",
            "job_type": "Stage d'été",
            "description": "Monitor and protect systems against security threats",
            "requirements": "Network Security, Penetration Testing, Python, Linux, SIEM",
            "experience_level": "Junior",
            "location": "Tunis, Tunisia"
        }
    ]
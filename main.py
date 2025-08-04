import streamlit as st
import json
import tempfile
import os
from pathlib import Path
from crew_system import CVProcessingCrew
from utils import save_uploaded_file, load_job_descriptions

def main():
    st.set_page_config(
        page_title="CV Chatbot - Multi-Agent System",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 CV Processing Chatbot")
    st.markdown("Upload your CV and get matched with jobs plus take a custom quiz!")
    
    # Initialize session state
    if 'crew' not in st.session_state:
        st.session_state.crew = CVProcessingCrew()
    if 'parsed_cv' not in st.session_state:
        st.session_state.parsed_cv = None
    if 'job_matches' not in st.session_state:
        st.session_state.job_matches = None
    if 'selected_job' not in st.session_state:
        st.session_state.selected_job = None
    if 'quiz' not in st.session_state:
        st.session_state.quiz = None
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    step = st.sidebar.radio(
        "Current Step:",
        ["1. Upload CV", "2. Job Matching", "3. Take Quiz"],
        index=0
    )

    if step == "1. Upload CV":
        handle_cv_upload()
    elif step == "2. Job Matching":
        if st.session_state.get("parsed_cv") is None:
           st.warning("Veuillez d'abord téléverser un CV.")
        else:
           handle_job_matching()
    elif step == "3. Take Quiz":
        if st.session_state.get("selected_job") is None:
           st.warning("Veuillez d'abord sélectionner un emploi dans l'étape précédente.")
        else:
           handle_quiz()


def handle_cv_upload():
    st.header("📄 Step 1: Upload Your CV")
    
    uploaded_file = st.file_uploader(
        "Choose your CV file",
        type=['pdf', 'docx', 'doc'],
        help="Supported formats: PDF, Word (.docx, .doc). Languages: French, English"
    )
    
    if uploaded_file:
        st.info(f"File uploaded: {uploaded_file.name}")
        
        if st.button("Parse CV", type="primary"):
            with st.spinner("Parsing your CV... This may take a moment."):
                try:
                    # Save uploaded file temporarily
                    file_path = save_uploaded_file(uploaded_file)
                    
                    # Parse CV using CrewAI
                    result = st.session_state.crew.parse_cv(file_path)
                    st.session_state.parsed_cv = result
                    
                    # Clean up temp file
                    os.unlink(file_path)
                    
                    st.success("✅ CV parsed successfully!")
                    st.json(result)
                    
                except Exception as e:
                    st.error(f"Error parsing CV: {str(e)}")
    
    # Show parsed CV if available
    if st.session_state.parsed_cv:
        st.subheader("📋 Parsed CV Information")
        st.json(st.session_state.parsed_cv)

def handle_job_matching():
    if not st.session_state.parsed_cv:
        st.warning("Please upload and parse your CV first.")
        return
    
    st.header("🎯 Step 2: Job Matching")
    
    if st.button("Find Job Matches", type="primary"):
        with st.spinner("Finding the best job matches for you..."):
            try:
                result = st.session_state.crew.match_jobs(st.session_state.parsed_cv)
                st.session_state.job_matches = result
                st.success("✅ Job matches found!")
                st.write("Debug: job_matches content")
                st.json(st.session_state.job_matches)
            except Exception as e:
                st.error(f"Error matching jobs: {str(e)}")
    
    if st.session_state.job_matches:
        st.subheader("🏆 Top Job Matches")
        
        matches = st.session_state.job_matches.get('matches', [])
        for i, match in enumerate(matches):
            with st.expander(f"Match {i+1}: {match.get('job_title', 'Unknown')} - Score: {match.get('similarity_score', 0):.2f}"):
                st.write(f"**Company:** {match.get('company', 'N/A')}")
                st.write(f"**Type:** {match.get('job_type', 'N/A')}")
                st.write(f"**Description:** {match.get('description', 'N/A')}")
                st.write(f"**Requirements:** {match.get('requirements', 'N/A')}")
                
                if st.button(f"Select this job", key=f"select_{i}"):
                    st.session_state.selected_job = match
                    st.success(f"Selected: {match.get('job_title')}")
                    st.rerun()

def handle_quiz():
    if not st.session_state.selected_job:
        st.warning("Please select a job first.")
        return
    
    st.header("📝 Step 3: Take Your Quiz")
    st.info(f"Quiz for: {st.session_state.selected_job.get('job_title', 'Selected Job')}")
    
    if not st.session_state.quiz:
        if st.button("Generate Quiz", type="primary"):
            with st.spinner("Generating your personalized quiz..."):
                try:
                    result = st.session_state.crew.generate_quiz(
                        st.session_state.parsed_cv,
                        st.session_state.selected_job
                    )
                    st.session_state.quiz = result
                    st.success("✅ Quiz generated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error generating quiz: {str(e)}")
    
    if st.session_state.quiz:
        display_quiz()

def display_quiz():
    quiz_data = st.session_state.quiz
    questions = quiz_data.get('questions', [])
    
    if not questions:
        st.error("No questions found in quiz.")
        return
    
    st.subheader(f"📋 {quiz_data.get('title', 'Quiz')}")
    
    with st.form("quiz_form"):
        answers = {}
        
        for i, question in enumerate(questions):
            st.write(f"**Question {i+1}:** {question.get('question', '')}")
            
            if question.get('type') == 'multiple_choice':
                options = question.get('options', [])
                answers[i] = st.radio(
                    f"Select your answer for question {i+1}:",
                    options,
                    key=f"q_{i}"
                )
            elif question.get('type') == 'true_false':
                answers[i] = st.radio(
                    f"Select your answer for question {i+1}:",
                    ['True', 'False'],
                    key=f"q_{i}"
                )
            else:
                answers[i] = st.text_area(
                    f"Your answer for question {i+1}:",
                    key=f"q_{i}"
                )
            
            st.divider()
        
        submitted = st.form_submit_button("Submit Quiz", type="primary")
        
        if submitted:
            score = calculate_score(answers, questions)
            st.success(f"🎉 Quiz completed! Your score: {score:.1f}%")
            
            # Show correct answers
            st.subheader("📊 Quiz Results")
            for i, question in enumerate(questions):
                user_answer = answers.get(i, '')
                correct_answer = question.get('correct_answer', '')
                
                is_correct = str(user_answer).lower().strip() == str(correct_answer).lower().strip()
                
                st.write(f"**Question {i+1}:** {question.get('question', '')}")
                st.write(f"Your answer: {user_answer}")
                st.write(f"Correct answer: {correct_answer}")
                
                if is_correct:
                    st.success("✅ Correct!")
                else:
                    st.error("❌ Incorrect")
                
                st.divider()

def calculate_score(answers, questions):
    if not questions:
        return 0
    
    correct = 0
    total = len(questions)
    
    for i, question in enumerate(questions):
        user_answer = str(answers.get(i, '')).lower().strip()
        correct_answer = str(question.get('correct_answer', '')).lower().strip()
        
        if user_answer == correct_answer:
            correct += 1
    
    return (correct / total) * 100 if total > 0 else 0

if __name__ == "__main__":
    main()
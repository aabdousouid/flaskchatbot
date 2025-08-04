from crewai import Agent, Task, Crew, Process
from crewai_tools import FileReadTool
from langchain_community.llms import Ollama
import json
from utils import extract_text_from_file, load_job_descriptions, detect_language

class CVProcessingCrew:
    def __init__(self):
        self.llm = Ollama(model="ollama/llama3.1:8b", base_url="http://localhost:11434")
        self.setup_agents()
    
    def setup_agents(self):
        # CV Parsing Agent
        self.cv_parser = Agent(
            role='CV Parser Specialist',
            goal='Extract and structure information from CVs in multiple formats and languages',
            backstory='''You are an expert in parsing CVs and resumes. You can handle PDFs, Word documents, 
            and text in both French and English. You extract key information like personal details, 
            education, experience, skills, and certifications, then structure it into clean JSON format.''',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Job Matching Agent
        self.job_matcher = Agent(
            role='Job Matching Expert',
            goal='Match candidate profiles with suitable job opportunities based on skills and experience',
            backstory='''You are a recruitment expert who specializes in matching candidates to jobs. 
            You analyze CVs and job descriptions to find the best matches based on skills, experience, 
            education, and requirements. You provide similarity scores and detailed explanations.''',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Quiz Generation Agent
        self.quiz_generator = Agent(
            role='Technical Quiz Creator',
            goal='Generate relevant technical and behavioral quizzes based on job requirements',
            backstory='''You are an expert in creating assessments and quizzes. You design questions 
            that test both technical skills and cultural fit based on job descriptions and candidate profiles. 
            You create multiple choice, true/false with proper scoring.''',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def parse_cv(self, file_path):
        """Parse CV and return structured JSON"""
        
        # Extract text from file
        cv_text = extract_text_from_file(file_path)
        language = detect_language(cv_text)
        
        task = Task(
            description=f'''
            Parse the following CV text and extract structured information:
            
            CV Text:
            {cv_text}
            
            Language detected: {language}
            
            Extract and return a JSON with the following structure:
            {{
                "personal_info": {{
                    "name": "",
                    "email": "",
                    "phone": "",
                    "address": "",
                    "linkedin": "",
                    "github": ""
                }},
                "summary": "",
                "education": [
                    {{
                        "degree": "",
                        "institution": "",
                        "year": "",
                        "gpa": ""
                    }}
                ],
                "experience": [
                    {{
                        "title": "",
                        "company": "",
                        "duration": "",
                        "description": "",
                        "technologies": []
                    }}
                ],
                "skills": {{
                    "technical": [],
                    "soft": [],
                    "languages": []
                }},
                "certifications": [],
                "projects": [
                    {{
                        "name": "",
                        "description": "",
                        "technologies": [],
                        "url": ""
                    }}
                ],
                "detected_language": "{language}"
            }}
            
            Return only valid JSON without any additional text or markdown formatting.
            ''',
            agent=self.cv_parser,
            expected_output="Valid JSON structure with parsed CV information"
        )
        
        crew = Crew(
            agents=[self.cv_parser],
            tasks=[task],
            verbose=True,
            process=Process.sequential
        )
        
        result = crew.kickoff()
        
        try:
            return json.loads(str(result))
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {"error": "Failed to parse CV", "raw_output": str(result)}
    
    def match_jobs(self, parsed_cv, job_descriptions):
        """Match parsed CV with jobs from input, not from utils.py"""
        import json
        from crewai import Task, Crew, Process

        task = Task(
            description=f'''
            Match the following candidate profile with available job positions:

            Candidate Profile:
            {json.dumps(parsed_cv, indent=2)}

            Available Jobs:
            {json.dumps(job_descriptions, indent=2)}

            Analyze the candidate's skills, experience, and education against each job's requirements.
            Calculate similarity scores (0-100) based on:
            - Technical skills match
            - Experience relevance
            - Education requirements
            - Soft skills alignment

            Return the top 3 matches in JSON format:
            {{
                "matches": [
                    {{
                        "job_id": "",
                        "job_title": "",
                        "company": "",
                        "job_type": "",
                        "description": "",
                        "requirements": "",
                        "similarity_score": 0.0,
                        "matching_skills": [],
                        "missing_skills": [],
                        "match_explanation": ""
                    }}
                ]
            }}

            Return only valid JSON without any additional text.
            ''',
            agent=self.job_matcher,
            expected_output="JSON with top 3 job matches and similarity scores"
        )

        crew = Crew(
            agents=[self.job_matcher],
            tasks=[task],
            verbose=True,
            process=Process.sequential
        )

        result = crew.kickoff()
        try:
            return json.loads(str(result))
        except json.JSONDecodeError:
            return {"matches": [], "error": "Failed to match jobs", "raw_output": str(result)}
    
    def generate_quiz(self, parsed_cv, selected_job):
        """Generate quiz based on job requirements and candidate profile"""

        task = Task(
            description=f'''
            Create a technical and behavioral quiz for the following job and candidate:
            
            Candidate Profile:
            {json.dumps(parsed_cv, indent=2)}
            
            Selected Job:
            {json.dumps(selected_job, indent=2)}
            
            Generate 8-10 questions that test:
            - Technical skills required for the job
            - Problem-solving abilities
            - Cultural fit and soft skills
            - Specific technologies mentioned in job requirements

            Each question **MUST** be either:
            - multiple_choice (with exactly 4 options, indexed 0-3)
            - true_false (with exactly 2 options: ["True", "False"], indexed 0 or 1)

            For each question, return:
            - "type": "multiple_choice" or "true_false"
            - "options": the list of options (4 for multiple_choice, 2 for true_false)
            - "correct_answer": the index (int) of the correct option, NOT a string, NOT "A"/"B", just 0, 1, 2 or 3
            - All other fields as before

            **Never return short_answer questions.**

            Return JSON format:
            {{
                "title": "Quiz for [Job Title]",
                "description": "Assessment for [Job Title] position",
                "questions": [
                    {{
                        "id": 1,
                        "question": "",
                        "type": "multiple_choice|true_false",
                        "options": ["", "", "", ""],  # or 2 options for true_false
                        "correct_answer": 0,
                        "explanation": "",
                        "difficulty": "easy|medium|hard",
                        "category": "technical|behavioral|general"
                    }}
                ],
                "total_questions": 0,
                "estimated_time": "15 minutes"
            }}

            Return only valid JSON without any additional text.
            ''',
            agent=self.quiz_generator,
            expected_output="JSON with quiz questions and answers"
        )

        crew = Crew(
            agents=[self.quiz_generator],
            tasks=[task],
            verbose=True,
            process=Process.sequential
        )

        result = crew.kickoff()

        try:
            return json.loads(str(result))
        except json.JSONDecodeError:
            return {"error": "Failed to generate quiz", "raw_output": str(result)}

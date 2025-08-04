from flask import Flask, request, jsonify
from crew_system import CVProcessingCrew
import tempfile
import os

app = Flask(__name__)
crew = CVProcessingCrew()


def ensure_skills_is_array(job):
    skills = job.get("skills", [])
    if isinstance(skills, str):
        # Convert "Python, React, Node.js" → ["Python", "React", "Node.js"]
        job["skills"] = [s.strip() for s in skills.split(",") if s.strip()]
    return job

@app.route('/parse-cv', methods=['POST'])
def parse_cv():
    file = request.files['file']
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename.split('.')[-1]) as tmp:
        tmp.write(file.read())
        tmp_path = tmp.name
    result = crew.parse_cv(tmp_path)
    return jsonify(result)

@app.route('/match-jobs', methods=['POST'])
def match_jobs():
    data = request.get_json()
    parsed_cv = data.get("parsed_cv")
    jobs = data.get("jobs")
    jobs = [ensure_skills_is_array(job) for job in jobs if isinstance(job, dict)]

    matches_result = crew.match_jobs(parsed_cv, jobs)

    # Get only the array of matches!
    matches = []
    if isinstance(matches_result, dict):
        matches = matches_result.get("matches")
    elif isinstance(matches_result, list):
        matches = matches_result
    matches = [ensure_skills_is_array(job) for job in matches if isinstance(job, dict)]

    # Only return the array, not a dict
    return jsonify(matches)



@app.route('/generate-quiz', methods=['POST'])
def generate_quiz():
    data = request.get_json()
    parsed_cv = data.get('parsed_cv')
    job = data.get('job')
    candidate_name = data.get('candidate_name', 'Candidate')
    if not parsed_cv or not job:
        return jsonify({"error": "Missing parsed_cv or job", "questions": []}), 400

    result = crew.generate_quiz(parsed_cv, job)
    filtered = []
    if result and "questions" in result:
        filtered = patch_and_filter_questions(result["questions"])
        result["questions"] = filtered
        app.config["LAST_QUIZ"] = {
            "candidate_name": candidate_name,
            "job": job,
            "questions": filtered
        }
    return jsonify({
        "questions": filtered,
        "title": result.get("title", ""),
        "description": result.get("description", ""),
        "total_questions": len(filtered),
        "estimated_time": result.get("estimated_time", "")
    })





@app.route("/submit-quiz", methods=["POST"])
def submit_quiz():
    data = request.get_json()
    answers = data.get("answers")
    candidate_name = data.get("candidate_name", "Candidate")

    quiz_data = app.config.get("LAST_QUIZ")
    if not quiz_data:
        return jsonify({"error": "Quiz session expired or not started"}), 400

    questions_raw = quiz_data["questions"]
    job = quiz_data["job"]

    score = 0
    total = len(questions_raw)
    correct_answers = 0

    for i, q in enumerate(questions_raw):
        user_answer = answers[i] if i < len(answers) else None
        correct = q.get("correct_answer")
        if user_answer == correct:
            correct_answers += 1

    if total > 0:
        score = correct_answers / total * 100

    status = "PASS" if score >= 50 else "RETRY"

    return jsonify({
        "score": score,
        "status": status,
        "correct_answers": correct_answers,
        "total_questions": total,
        "category_scores": {},
        "next_action": "retry" if status == "RETRY" else "apply"
    })




def patch_and_filter_questions(questions):
    abcd = ["A", "B", "C", "D"]
    filtered = []
    for q in questions:
        qtype = q.get("type")
        opts = q.get("options", [])
        correct = q.get("correct_answer")
        # Only allow MCQ and TF
        if qtype == "multiple_choice" and len(opts) == 4:
            # If correct_answer is a letter, map to index
            if isinstance(correct, str):
                if correct.upper() in abcd:
                    q["correct_answer"] = abcd.index(correct.upper())
                elif correct.isdigit() and int(correct) in range(4):
                    q["correct_answer"] = int(correct)
                else:
                    # Try direct option match
                    for idx, opt in enumerate(opts):
                        if correct.strip().lower() == opt.strip().lower():
                            q["correct_answer"] = idx
            # Otherwise, keep as is (should be index)
            filtered.append(q)
        elif qtype == "true_false" and opts == ["True", "False"]:
            # Map string "True"/"False" to 0/1 index
            if correct == "True":
                q["correct_answer"] = 0
            elif correct == "False":
                q["correct_answer"] = 1
            elif isinstance(correct, int) and correct in [0, 1]:
                pass  # already correct
            filtered.append(q)
    return filtered



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, threaded=True)
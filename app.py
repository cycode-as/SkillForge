from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import google.generativeai as genai
from pypdf import PdfReader
import os
import json
import random
from dotenv import load_dotenv

# 1. Load API Key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# Emergency Fallback: If .env fails, paste your key here
if not api_key:
    api_key = "PASTE_YOUR_REAL_KEY_HERE"

genai.configure(api_key=api_key)

app = Flask(__name__)
app.secret_key = 'hackathon_super_secret_key'  # Needed for login sessions

# --- MOCK DATABASE (In-Memory) ---
otp_storage = {}

# --- HELPER FUNCTIONS ---
def extract_text_from_pdf(file_stream):
    try:
        reader = PdfReader(file_stream)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        return None

# --- ROUTES ---

@app.route('/')
def login_page():
    # This serves the Login Page first
    return render_template('login.html')

@app.route('/send_otp', methods=['POST'])
def send_otp():
    email = request.form.get('email')
    name = request.form.get('name')
    
    # Save user info temporarily
    session['temp_user'] = {
        'name': name,
        'email': email,
        'age': request.form.get('age'),
        'gender': request.form.get('gender'),
        'contact': request.form.get('contact')
    }
    
    # Generate and Print OTP
    otp = str(random.randint(1000, 9999))
    otp_storage[email] = otp
    
    print(f"\n\n=====================================")
    print(f"🔐 HACKATHON OTP for {email}: {otp}")
    print(f"=====================================\n\n")
    
    return redirect(url_for('verify_page'))

@app.route('/verify')
def verify_page():
    return render_template('verify.html')

@app.route('/check_otp', methods=['POST'])
def check_otp():
    user_otp = request.form.get('otp')
    email = session.get('temp_user', {}).get('email')
    
    if otp_storage.get(email) == user_otp:
        session['logged_in'] = True
        return redirect(url_for('landing_page'))
    else:
        return "❌ Invalid OTP! Look at your VS Code Terminal.", 401

@app.route('/home')
def landing_page():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    return render_template('landing.html', user=session['temp_user'])

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    # This is your main tool (formerly index.html)
    return render_template('dashboard.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    # Security Check
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized access"}), 401

    if 'resume' not in request.files:
        return jsonify({"error": "No resume file uploaded"}), 400
    
    file = request.files['resume']
    jd_text = request.form.get('jd_text')

    resume_text = extract_text_from_pdf(file)
    if not resume_text:
        return jsonify({"error": "Could not read PDF"}), 500

    # Using Gemini 1.5 Flash
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # UPDATED PROMPT: Now asks for Interview Questions & High Fit Roles
    prompt = f"""
    Act as an expert Technical Recruiter. Compare the RESUME against the JOB DESCRIPTION (JD).
    
    RESUME: {resume_text[:4000]}
    JD: {jd_text[:2000]}
    
    Output a JSON object with these keys:
    - "match_score": (integer 0-100)
    - "summary": (string, max 2 sentences)
    - "missing_skills": (list of strings)
    - "recommended_projects": (list of strings, 2 unique ideas)
    - "resume_tips": (list of strings)
    - "high_match_roles": (list of strings, 3 roles >80% fit)
    - "interview_questions": (list of strings, 3 hard technical questions based on gaps)
    """
    
    try:
        response = model.generate_content(
            prompt, 
            generation_config={"response_mime_type": "application/json"}
        )
        data = json.loads(response.text)
        return jsonify(data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

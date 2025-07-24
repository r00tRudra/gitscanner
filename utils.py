import pdfplumber
import re

def extract_resume_skills(resume_file):
    """Extract skills from a PDF resume using pdfplumber."""
    skills = []
    try:
        with pdfplumber.open(resume_file) as pdf:
            text = ''
            for page in pdf.pages:
                text += page.extract_text() or ''
        
        # Simple regex to find common skills (customize based on needs)
        skill_keywords = [
            r'\bPython\b', r'\bJavaScript\b', r'\bJava\b', r'\bC\+\+\b', r'\bSQL\b',
            r'\bReact\b', r'\bNode\.js\b', r'\bDjango\b', r'\bFlask\b', r'\bAWS\b'
        ]
        for pattern in skill_keywords:
            if re.search(pattern, text, re.IGNORECASE):
                skills.append(pattern.replace(r'\b', '').replace(r'\.', '.'))
        
        return skills if skills else ['No skills extracted']
    except Exception as e:
        return [f'Error extracting skills: {e}']
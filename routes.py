from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from agno.agent import Agent
from agno.models.nebius import Nebius
from agno.tools.github import GithubTools
from agno.tools.exa import ExaTools
from agno.tools.thinking import ThinkingTools
from agno.tools.reasoning import ReasoningTools
import yaml
import pdfplumber
from utils import extract_resume_skills
from models import Candidate
from app import db
import os
import json
import re

bp = Blueprint('main', __name__)

# Load YAML prompts
def load_yaml(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        flash('YAML prompt file not found.', 'danger')
        return {}
    except yaml.YAMLError as e:
        flash(f'YAML parsing error: {e}', 'danger')
        return {}

data = load_yaml(os.path.join(os.path.dirname(__file__), 'config/hiring_prompts.yaml'))
description_multi = data.get('description_for_multi_candidates', '')
instructions_multi = data.get('instructions_for_multi_candidates', '')
description_single = data.get('description_for_single_candidate', '')
instructions_single = data.get('instructions_for_single_candidate', '')

@bp.route('/')
def index():
    return render_template('landing.html')

@bp.route('/candidates')
def candidates_list():
    # Get all candidates from the database
    candidates = Candidate.query.order_by(Candidate.created_at.desc()).all()
    return render_template('candidates.html', candidates=candidates)

@bp.route('/multi-candidate', methods=['GET', 'POST'])
def multi_candidate():
    if request.method == 'POST':
        github_usernames = request.form.get('github_usernames')
        job_role = request.form.get('job_role')
        resume = request.files.get('resume')

        if not github_usernames or not job_role:
            flash('Please enter both usernames and job role.', 'danger')
            return render_template('multi_candidate.html')

        api_keys = {
            'Nebius_api_key': os.getenv('NEBIUS_API_KEY'),
            'github_api_key': os.getenv('GITHUB_API_KEY'),
            'exa_api_key': os.getenv('EXA_API_KEY'),
            'model_id': os.getenv('MODEL_ID')
        }
        if not all(api_keys.values()):
            flash('Please set all API keys in environment variables.', 'danger')
            return render_template('multi_candidate.html')

        usernames = [u.strip() for u in github_usernames.split('\n') if u.strip()]
        if not usernames:
            flash('Enter at least one valid GitHub username.', 'danger')
            return render_template('multi_candidate.html')

        # Process resume if uploaded
        skills = []
        if resume:
            skills = extract_resume_skills(resume)

        # Store skills in database
        candidate = Candidate(github_usernames=','.join(usernames), job_role=job_role, skills=','.join(skills))
        db.session.add(candidate)
        db.session.commit()

        # Initialize AI agent
        agent = Agent(
            description=description_multi,
            instructions=instructions_multi,
            model=Nebius(id=api_keys['model_id'], api_key=api_keys['Nebius_api_key']),
            name='StrictCandidateEvaluator',
            tools=[
                ThinkingTools(think=True, instructions='Strict GitHub candidate evaluation'),
                GithubTools(access_token=api_keys['github_api_key']),
                ExaTools(api_key=api_keys['exa_api_key'], include_domains=['github.com'], type='keyword'),
                ReasoningTools(add_instructions=True)
            ],
            markdown=True,
            show_tool_calls=True
        )

        query = f"Evaluate GitHub candidates for role '{job_role}': {', '.join(usernames)}. Skills from resume: {', '.join(skills) if skills else 'None'}"
        try:
            results = ''
            for chunk in agent.run(query, stream=True):
                if hasattr(chunk, 'content') and isinstance(chunk.content, str):
                    results += chunk.content
            
            # Store analysis results in the database
            candidate.analysis_results = results
            db.session.commit()
            
            # Redirect to visualization page
            flash('Analysis complete! View the visualization dashboard.', 'success')
            return redirect(url_for('main.visualization', candidate_id=candidate.id))
        except Exception as e:
            flash(f'Error during analysis: {e}', 'danger')
            return render_template('multi_candidate.html')

    return render_template('multi_candidate.html')

@bp.route('/multi-candidate.html')
def multi_candidate_html():
    return render_template('multi_candidate.html')

@bp.route('/visualization/<int:candidate_id>')
def visualization(candidate_id):
    # Get candidate from database
    candidate = Candidate.query.get_or_404(candidate_id)
    
    # Parse skills from comma-separated string
    skills = candidate.skills.split(',') if candidate.skills else []
    
    # Prepare candidate data for the template
    candidate_data = {
        'github': candidate.github_usernames,
        'job_role': candidate.job_role,
        'skills': skills
    }
    
    # Process the analysis results to extract structured data for visualization
    # This would typically come from the stored analysis results
    # For now, we'll create sample data
    analysis_results = process_analysis_results(candidate)
    
    return render_template('visualization.html', 
                           candidate_data=candidate_data, 
                           analysis_results=analysis_results)

def process_analysis_results(candidate):
    """Process raw analysis results into structured data for visualization."""
    # Get the raw analysis results
    raw_results = candidate.analysis_results or ''
    
    # If no analysis results yet, create default data
    if not raw_results:
        return create_default_visualization_data(candidate)
    
    # Extract skills data for pie chart
    skills_data = []
    candidate_skills = candidate.skills.split(',') if candidate.skills else []
    
    # Try to extract skill proficiency from the analysis results
    skill_pattern = r'(?:proficiency|expertise|skill)\s+in\s+([A-Za-z0-9\+\#\.]+)\s*(?::|is|rated|scored|level|at)\s*([0-9]+(?:\.[0-9]+)?|high|medium|low)'
    skill_matches = re.finditer(skill_pattern, raw_results, re.IGNORECASE)
    
    # Create a dictionary to store skill scores
    skill_scores = {}
    
    # Process skill matches
    for match in skill_matches:
        skill_name = match.group(1).strip()
        skill_level = match.group(2).strip().lower()
        
        # Convert text levels to numeric scores
        if skill_level == 'high':
            score = 9
        elif skill_level == 'medium':
            score = 6
        elif skill_level == 'low':
            score = 3
        else:
            try:
                score = float(skill_level)
                # Normalize score to 1-10 scale if needed
                if score > 10:
                    score = min(10, score / 10)
            except ValueError:
                score = 5  # Default score
        
        skill_scores[skill_name] = score
    
    # Add skills from candidate profile if not already in results
    for skill in candidate_skills:
        if skill and skill not in skill_scores:
            # Generate a score based on how frequently the skill appears in the analysis
            mentions = len(re.findall(r'\b' + re.escape(skill) + r'\b', raw_results, re.IGNORECASE))
            score = min(10, max(1, mentions + 5))
            skill_scores[skill] = score
    
    # Convert skill scores dictionary to list format for chart
    for skill, score in skill_scores.items():
        if skill:
            skills_data.append({
                'name': skill,
                'score': score
            })
    
    # Limit to top 8 skills by score
    skills_data = sorted(skills_data, key=lambda x: x['score'], reverse=True)[:8]
    
    # Extract performance metrics for radar chart
    # Define categories to look for
    categories = [
        'Code Quality', 'Documentation', 'Problem Solving', 'Collaboration', 
        'Technical Skills', 'Communication', 'Project Management', 'Testing'
    ]
    
    performance_metrics = []
    for category in categories:
        # Look for patterns like "Code Quality: 8/10" or "Code Quality is rated at 8"
        pattern = r'{}\s*(?::|is|rated|scored|level|at)\s*([0-9]+(?:\.[0-9]+)?|high|medium|low)(?:/10)?'.format(re.escape(category))
        match = re.search(pattern, raw_results, re.IGNORECASE)
        
        if match:
            level = match.group(1).lower()
            # Convert text levels to numeric scores
            if level == 'high':
                score = 9
            elif level == 'medium':
                score = 6
            elif level == 'low':
                score = 3
            else:
                try:
                    score = float(level)
                    # Normalize score to 1-10 scale if needed
                    if score > 10:
                        score = min(10, score / 10)
                except ValueError:
                    score = 5  # Default score
        else:
            # If no explicit rating, estimate based on keyword frequency and context
            keywords = {
                'Code Quality': ['clean code', 'well-structured', 'maintainable', 'readable', 'best practices'],
                'Documentation': ['documented', 'comments', 'readme', 'documentation'],
                'Problem Solving': ['algorithm', 'solution', 'approach', 'problem solving', 'challenges'],
                'Collaboration': ['team', 'collaborate', 'contribution', 'pull request', 'issue'],
                'Technical Skills': ['technical', 'expertise', 'proficiency', 'skilled', 'competent'],
                'Communication': ['communicate', 'articulate', 'express', 'clarity', 'presentation'],
                'Project Management': ['organize', 'planning', 'timeline', 'milestone', 'management'],
                'Testing': ['test', 'unit test', 'integration test', 'QA', 'quality assurance']
            }
            
            # Count occurrences of keywords for this category
            count = 0
            for keyword in keywords.get(category, []):
                count += len(re.findall(r'\b' + re.escape(keyword) + r'\b', raw_results, re.IGNORECASE))
            
            # Convert count to score (1-10)
            score = min(10, max(1, count + 5))
        
        performance_metrics.append({
            'category': category,
            'score': score
        })
    
    # Limit to 5-8 metrics for better radar chart visualization
    performance_metrics = sorted(performance_metrics, key=lambda x: x['score'], reverse=True)[:6]
    
    # Extract summary text - look for sections that might contain summary information
    summary_pattern = r'(?:summary|conclusion|overall assessment|final thoughts)\s*(?::|\n)\s*([\s\S]+?)(?:\n\n|\n#|$)'
    summary_match = re.search(summary_pattern, raw_results, re.IGNORECASE)
    
    if summary_match:
        summary = summary_match.group(1).strip()
    else:
        # If no explicit summary section, use the first few paragraphs
        paragraphs = re.split(r'\n\s*\n', raw_results)
        summary = '\n\n'.join(paragraphs[:3]) if paragraphs else raw_results[:500]
    
    # Format the summary with HTML
    summary = f"""<h4>Analysis Summary</h4>
    <div class="analysis-summary">
        {summary}
    </div>
    <h4>Key Strengths</h4>
    <ul>
        <li>Strong technical skills in {', '.join([s['name'] for s in skills_data[:3]]) if skills_data else 'various areas'}</li>
        <li>{performance_metrics[0]['category'] if performance_metrics else 'Technical Skills'} score: {performance_metrics[0]['score'] if performance_metrics else 'N/A'}/10</li>
        <li>{performance_metrics[1]['category'] if len(performance_metrics) > 1 else 'Problem Solving'} score: {performance_metrics[1]['score'] if len(performance_metrics) > 1 else 'N/A'}/10</li>
    </ul>"""
    
    return {
        'skills_data': skills_data,
        'performance_metrics': performance_metrics,
        'summary': summary
    }

def create_default_visualization_data(candidate):
    """Create default visualization data when no analysis results are available."""
    # Create default skills data
    skills_data = []
    candidate_skills = candidate.skills.split(',') if candidate.skills else []
    
    # Add skills from candidate profile with default scores
    for i, skill in enumerate(candidate_skills):
        if skill:
            skills_data.append({
                'name': skill,
                'score': 7 - (i % 3)  # Generate scores between 5-7 for variety
            })
    
    # If no skills provided, add some default ones
    if not skills_data:
        default_skills = ['Python', 'JavaScript', 'SQL', 'React', 'Node.js']
        for i, skill in enumerate(default_skills):
            skills_data.append({
                'name': skill,
                'score': 7 - (i % 3)  # Generate scores between 5-7 for variety
            })
    
    # Create default performance metrics
    performance_metrics = [
        {'category': 'Code Quality', 'score': 7},
        {'category': 'Documentation', 'score': 6},
        {'category': 'Problem Solving', 'score': 8},
        {'category': 'Collaboration', 'score': 7},
        {'category': 'Technical Skills', 'score': 8},
        {'category': 'Communication', 'score': 6}
    ]
    
    # Create default summary
    summary = f"""<h4>Analysis Summary</h4>
    <div class="analysis-summary">
        <p>No detailed analysis has been performed yet for this candidate. This is a preview of how the visualization dashboard will look once analysis is complete.</p>
        <p>The candidate {candidate.github_usernames} is being evaluated for the role of {candidate.job_role}.</p>
    </div>
    <h4>Key Skills</h4>
    <ul>
        <li>Skills listed from resume: {', '.join(candidate_skills) if candidate_skills else 'None provided'}</li>
    </ul>
    <div class="alert alert-info">
        <p>To generate a complete analysis, please run the evaluation process for this candidate.</p>
    </div>"""
    
    return {
        'skills_data': skills_data,
        'performance_metrics': performance_metrics,
        'summary': summary
    }

@bp.route('/single-candidate', methods=['GET', 'POST'])
def single_candidate():
    if request.method == 'POST':
        github_username = request.form.get('github_username')
        linkedin_url = request.form.get('linkedin_url')
        job_role = request.form.get('job_role')
        resume = request.files.get('resume')

        if not github_username or not job_role:
            flash('GitHub username and job role are required.', 'danger')
            return render_template('single_candidate.html')

        api_keys = {
            'Nebius_api_key': os.getenv('NEBIUS_API_KEY'),
            'github_api_key': os.getenv('GITHUB_API_KEY'),
            'exa_api_key': os.getenv('EXA_API_KEY'),
            'model_id': os.getenv('MODEL_ID')
        }
        if not all(api_keys.values()):
            flash('Please set all API keys in environment variables.', 'danger')
            return render_template('single_candidate.html')

        # Process resume if uploaded
        skills = []
        if resume:
            skills = extract_resume_skills(resume)

        # Store skills in database
        candidate = Candidate(github_usernames=github_username, job_role=job_role, skills=','.join(skills))
        db.session.add(candidate)
        db.session.commit()

        # Initialize AI agent
        agent = Agent(
            model=Nebius(id=api_keys['model_id'], api_key=api_keys['Nebius_api_key']),
            name='Candilyzer',
            tools=[
                ThinkingTools(add_instructions=True),
                GithubTools(access_token=api_keys['github_api_key']),
                ExaTools(
                    api_key=api_keys['exa_api_key'],
                    include_domains=['linkedin.com', 'github.com'],
                    type='keyword',
                    text_length_limit=2000,
                    show_results=True
                ),
                ReasoningTools(add_instructions=True)
            ],
            description=description_single,
            instructions=instructions_single,
            markdown=True,
            show_tool_calls=True,
            add_datetime_to_instructions=True
        )

        input_text = f"GitHub: {github_username}, Role: {job_role}, Skills: {', '.join(skills) if skills else 'None'}"
        if linkedin_url:
            input_text += f", LinkedIn: {linkedin_url}"

        try:
            results = ''
            for chunk in agent.run(f"Analyze candidate for {job_role}. {input_text}. Provide score and detailed report.", stream=True):
                if hasattr(chunk, 'content') and isinstance(chunk.content, str):
                    results += chunk.content
            
            # Store analysis results in the database
            candidate.analysis_results = results
            db.session.commit()
            
            # Redirect to visualization page
            flash('Analysis complete! View the visualization dashboard.', 'success')
            return redirect(url_for('main.visualization', candidate_id=candidate.id))
        except Exception as e:
            flash(f'Error during analysis: {e}', 'danger')
            return render_template('single_candidate.html')

    return render_template('single_candidate.html')
from flask import Blueprint, render_template, request, flash
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
            return render_template('multi_candidate.html', results=results)
        except Exception as e:
            flash(f'Error during analysis: {e}', 'danger')
            return render_template('multi_candidate.html')

    return render_template('multi_candidate.html')

@bp.route('/multi-candidate.html')
def multi_candidate_html():
    return render_template('multi_candidate.html')

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
            return render_template('single_candidate.html', results=results)
        except Exception as e:
            flash(f'Error during analysis: {e}', 'danger')
            return render_template('single_candidate.html')

    return render_template('single_candidate.html')
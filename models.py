from app import db

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    github_usernames = db.Column(db.String(500), nullable=False)
    job_role = db.Column(db.String(100), nullable=False)
    skills = db.Column(db.String(500), nullable=True)
    analysis_results = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
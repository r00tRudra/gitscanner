# GitScanner

An AI-powered recruitment tool that analyzes GitHub profiles to assess technical skills, coding strengths, and role fit. GitScanner helps recruiters, founders, and hiring managers gain deep insights into candidates' coding styles, activities, and expertise using public GitHub profile data.

##  Features

- **GitHub Profile Analysis**: Extract and analyze public GitHub data including repositories, commit history, and contribution patterns
- **AI-Powered Insights**: Leverage AI to generate comprehensive technical assessments and skill evaluations
- **Single & Batch Processing**: Analyze one candidate or multiple candidates simultaneously
- **Rich Visualizations**: Interactive charts and dashboards to visualize coding patterns and skills
- **Role-Based Evaluation**: Assess candidate fit for specific roles using customizable hiring prompts
- **Responsive Web Interface**: User-friendly UI for easy navigation and result viewing
- **Docker Support**: Easy deployment with containerized setup

##  Prerequisites

- Python 3.8+
- GitHub API Token (for accessing public GitHub data)
- API keys for AI services (if using external AI providers)
- Docker (optional, for containerized deployment)

##  Installation

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/r00tRudra/gitscanner.git
   cd gitscanner
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings
   ```

5. **Run the application**
   ```bash
   python app.py
   ```
   The application will be available at `http://localhost:5000`

### Docker Setup

1. **Build the Docker image**
   ```bash
   docker build -t gitscanner:latest .
   ```

2. **Run the container**
   ```bash
   docker run -p 5000:5000 --env-file .env gitscanner:latest
   ```

##  Configuration

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
FLASK_ENV=production
FLASK_DEBUG=False
GITHUB_TOKEN=your_github_api_token
AI_API_KEY=your_ai_service_api_key
DATABASE_URL=your_database_url
SECRET_KEY=your_secret_key
```

### Hiring Prompts

Customize the AI analysis behavior by editing `config/hiring_prompts.yaml`:

```yaml
prompts:
  skills_assessment: |
    Analyze the GitHub profile and assess...
  role_fit: |
    Evaluate the candidate's fit for...
```

##  Usage

### Web Interface

1. **Landing Page**: Start by visiting the home page
2. **Single Candidate Analysis**: Enter a GitHub username to analyze one candidate
3. **Multiple Candidates**: Upload or input multiple GitHub usernames for batch analysis
4. **View Results**: See detailed analysis, visualizations, and recommendations
5. **Export Reports**: Download candidate assessments and reports

### API Endpoints

The application provides REST API endpoints for programmatic access:

```bash
# Analyze single candidate
POST /api/analyze/single
Content-Type: application/json
{
  "github_username": "username"
}

# Analyze multiple candidates
POST /api/analyze/batch
Content-Type: application/json
{
  "usernames": ["user1", "user2", "user3"]
}

# Get candidate report
GET /api/report/<candidate_id>
```

##  Project Structure

```
gitscanner/
├── app.py                 # Flask application entry point
├── main.py               # Application initialization
├── models.py             # Database models
├── routes.py             # API and web routes
├── utils.py              # Utility functions
├── config/
│   └── hiring_prompts.yaml    # AI prompt configurations
├── instance/             # Instance-specific files (db, logs, etc.)
├── static/
│   ├── css/
│   │   └── styles.css    # Application styles
│   └── js/
│       └── main.js       # Frontend JavaScript
├── templates/
│   ├── base.html         # Base template
│   ├── landing.html      # Landing page
│   ├── single_candidate.html   # Single analysis page
│   ├── multi_candidate.html    # Batch analysis page
│   ├── candidates.html   # Candidates list
│   └── visualization.html      # Results visualization
├── requirements.txt      # Python dependencies
├── Dockerfile           # Container configuration
└── README.md            # This file
```

##  Development

### Setting up Development Environment

1. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov flake8
   ```

2. Set up pre-commit hooks (optional):
   ```bash
   pre-commit install
   ```

### Running Tests

```bash
pytest tests/
pytest --cov=. tests/  # With coverage
```

### Code Quality

```bash
flake8 .
black . --check
```

## 🐳 Docker Deployment

### Build and Push to Registry

```bash
docker build -t yourusername/gitscanner:latest .
docker push yourusername/gitscanner:latest
```

### Docker Compose (Optional)

Create a `docker-compose.yml` for multi-service deployment:

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    volumes:
      - ./instance:/app/instance
```

Run with: `docker-compose up`

##  Security Considerations

- **API Token Security**: Never commit `.env` files or expose API tokens
- **GitHub Rate Limits**: Be aware of GitHub API rate limits when processing multiple candidates
- **Data Privacy**: Ensure compliance with privacy regulations when storing candidate data
- **Input Validation**: Validate all user inputs to prevent injection attacks

##  Features in Detail

### Profile Analysis
- Extracts repositories, languages, commit history
- Analyzes contribution patterns and activity levels
- Identifies areas of expertise and specialization

### AI Assessment
- Generates role-fit recommendations
- Provides skill gap analysis
- Suggests learning areas and growth opportunities

### Visualizations
- Language proficiency charts
- Contribution timeline graphs
- Repository statistics
- Collaboration metrics

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure your code follows the project's style guide and includes appropriate tests.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the documentation and examples

## 🙏 Acknowledgments

- GitHub API for providing access to public profile data
- Flask framework for web application development
- AI services for intelligent analysis capabilities

---

**Made with ❤️ by the GitScanner Team**

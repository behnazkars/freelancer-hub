# Freelancer Business Hub

A full-stack SaaS application for freelancers to manage their business operations.

## Features

- JWT authentication (register/login)
- Client management
- Project tracking
- Time entry logging
- Invoice generation
- Analytics dashboard

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy
- **Database:** SQLite (development), PostgreSQL (production)
- **Frontend:** Jinja2 templates, HTML/CSS
- **Auth:** JWT tokens, bcrypt password hashing

## Getting Started

### Prerequisites
- Python 3.10+
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/freelancer-hub.git
cd freelancer-hub

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Create your .env file
cp .env.example .env
# Edit .env and add your SECRET_KEY

# Run the app
uvicorn app.main:app --reload
```

Visit `http://127.0.0.1:8000/docs` for the interactive API documentation.

## Project Structure

freelancer-hub/
├── app/
│   ├── main.py          # FastAPI app entry point
│   ├── config.py        # Settings and environment variables
│   ├── database.py      # SQLAlchemy engine and session
│   ├── routers/         # API endpoints (one file per feature)
│   ├── models/          # Database table definitions
│   ├── schemas/         # Pydantic validation schemas
│   ├── services/        # Business logic layer
│   └── auth/            # Authentication utilities
├── templates/           # Jinja2 HTML templates
├── static/              # CSS, JavaScript, images
├── requirements.txt
└── README.md

## Status

🚧 In active development — MVP in progress
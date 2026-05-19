# Student Faculty Event Registration Management System

A Flask-based web application for managing student and faculty event registrations. The system supports user authentication, event creation, event browsing, and registration workflows through a simple and responsive interface.

## Live Demo

Deployed version: [https://flask-eventhub-1.onrender.com](https://flask-eventhub-1.onrender.com)

## Features

* Student and faculty login/signup
* Event listing and registration
* Event creation and management
* Profile and dashboard pages
* Session-based authentication
* SQLite support for local development
* PostgreSQL support for production deployment
* Responsive UI with HTML, CSS, and Flask templates

## Tech Stack

* **Frontend:** HTML, CSS, Jinja2 Templates
* **Backend:** Python, Flask
* **Database:** SQLite / PostgreSQL
* **Deployment:** Render

## Project Structure

```text
flask_eventhub/
├── app.py
├── requirements.txt
├── Procfile
├── static/
│   └── style.css
├── templates/
│   ├── home.html
│   ├── login.html
│   ├── signup.html
│   ├── profile.html
│   └── ...
└── eventhub.db
```

## Prerequisites

Before running the project, make sure you have:

* Python 3.10+
* pip
* Git

## Installation

1. Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

2. Create a virtual environment:

```bash
python -m venv venv
```

3. Activate the virtual environment:

**Windows**

```bash
venv\Scripts\activate
```

**macOS/Linux**

```bash
source venv/bin/activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run Locally

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Environment Variables

For production deployment, set the following environment variables if required by your app:

* `SECRET_KEY`
* `DATABASE_URL`
* `PORT`

## Deployment on Render

1. Push the project to GitHub.
2. Create a new **Web Service** on Render.
3. Connect the GitHub repository.
4. Set the build command:

```bash
pip install -r requirements.txt
```

5. Set the start command:

```bash
gunicorn app:app
```

6. Add the required environment variables.
7. Deploy the service.

## Notes

* SQLite is suitable for local development.
* For persistent production data, use PostgreSQL.
* Make sure `gunicorn` is included in `requirements.txt` for Render deployment.

## Author

Created by **YogaSSN**

## License

This project is for educational and portfolio use.

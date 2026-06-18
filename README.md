![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-teal?style=flat&logo=fastapi)
![React](https://img.shields.io/badge/React-18+-blue?style=flat&logo=react)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue?style=flat&logo=docker)

# Site Availability Checker
---
https://solvit.space/projects/uptime_monitor
---
**Service for monitoring website availability.**

---

### 🛠 Tech Stack

- **Backend**: Python 3.12 + FastAPI
- **Frontend**: React
- **Authentication**: Google OAuth 2.0
- **Database**: PostgreSQL + Alembic
- **Queue & Tasks**: RabbitMQ + Taskiq
- **Deployment**: Docker + Docker Compose

---

### 🚀 Quick Start

---
```bash
docker compose up --build
```

### 🧪 Testing

```bash
docker compose run --rm backend_api uv run pytest -v
```

### 📸 User Interface Showcase

| Login Page | Signup Page | Main Dashboard |
|------------|-------------|----------------|
| ![Login Page](screenshots/loginpage.png) | ![Signup Page](screenshots/signuppage.png) | ![Main Dashboard](screenshots/mainpage.png) |

| Password Reset Request | Password Reset Confirm | Account Deletion (OTP) | Account Deletion (Success) |
|------------------------|------------------------|------------------------|----------------------------|
| ![Password Reset Request](screenshots/resetpasswordpage1.png) | ![Password Reset Confirm](screenshots/resetpasswordpage2.png) | ![Account Deletion (OTP)](screenshots/deleteaccountpage1.png) | ![Account Deletion (Success)](screenshots/deleteaccountpage2.png) |

| API Keys Page | API Docs Page |
|---------------|---------------|
| ![API Keys Page](screenshots/apikeyspage.png) | ![API Docs Page](screenshots/apidocspage.png) |

| Main Swagger | Public API Swagger |
|--------------|--------------------|
| ![Main Swagger](screenshots/mainswagger.png) | ![Public API Swagger](screenshots/publicapiswagger.png) |

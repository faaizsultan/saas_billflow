# SupportLens - Setup Guide

SupportLens is a minimal, AI-augmented observability tool designed for B2B SaaS operators. It provides a real-time chatbot interface that integrates with Google's Gemini LLM.

## Setup Instructions 🚀

This application is fully Dockerized. You can run the entire frontend and backend stack with a single command.

### 1. Environment Variables 🔑

**Backend Environments (`backend/.env` file):**
Create a `.env` file inside the `backend/` directory with the following variables:
```bash
GOOGLE_API_KEY=your_actual_api_key_here
SECRET_KEY=dev-secret-123
DEBUG=True
```

**Frontend Environments:**
The frontend uses `VITE_API_URL` to connect to the backend API. This is automatically handled and mapped for you in the shared `docker-compose.yml` file (`VITE_API_URL=http://localhost:8000/api`), so no manual frontend `.env` file is required to run this project!

### 2. Single Command to Run the Application 🐳

Once your backend variables are set, run this explicit single command from the root directory of the project (where this `README.md` is located) to build and start both containers:
```bash
docker-compose up --build -d
```

### 3. Access the Application 🌍

Once the containers are running and the database migrations have finished naturally, you can access:

- **Frontend Application:** [http://localhost:5173](http://localhost:5173)
- **Backend API Layer (Traces):** [http://localhost:8000/api/traces/](http://localhost:8000/api/traces/)
- **Backend API Layer (Analytics):** [http://localhost:8000/api/analytics/](http://localhost:8000/api/analytics/)

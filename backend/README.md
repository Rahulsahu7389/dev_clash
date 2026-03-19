# AI-Powered EdTech Backend (Phase 1)

This is the foundational backend for the JEE/NEET/UPSC AI EdTech platform.

## Tech Stack
- **FastAPI**: Modern, fast web framework.
- **Motor**: Async MongoDB driver.
- **Pydantic v2**: Data validation and settings management.
- **PyJWT**: JSON Web Token implementation.
- **Passlib (bcrypt)**: Secure password hashing.

## Getting Started

### 1. Prerequisites
- Python 3.9+
- MongoDB instance (Local or Atlas)

### 2. Installation
```powershell
pip install -r requirements.txt
```

### 3. Environment Variables
Configure your `.env` file:
- `MONGO_URI`: Your MongoDB connection string.
- `JWT_SECRET_KEY`: A strong secret key for token generation.
- `ALGORITHM`: Token signature algorithm (default: HS256).

### 4. Running the Server
```powershell
uvicorn app.main:app --reload
```

## API Endpoints
- `GET /`: Health check.
- `POST /auth/register`: Register a new user.
- `POST /auth/login`: Login with email and password to receive a JWT.

## Folder Structure
- `app/main.py`: App entry point and configuration.
- `app/config.py`: Environment variable loading.
- `app/database.py`: MongoDB connection lifecycle.
- `app/models.py`: Pydantic schemas for request/response validation.
- `app/routes/auth.py`: Authentication logic.

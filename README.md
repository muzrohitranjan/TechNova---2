# Tech Nova App

AI-powered Cultural Recipe Documentation & Guided Cooking Platform

## Tech Stack

- Frontend: React
- Backend: FastAPI
- Database & Auth: Supabase (PostgreSQL)
- Security: Row Level Security (RLS)


## Local Setup Guide

### 1️. Clone Repository

git clone https://github.com/muzrohitranjan/Tech-Nova-App.git

cd Tech-Nova-App

### 2️. Frontend Setup

cd frontend

npm install

npm start

Node version :node-v22.17.1-x64.msi https://drive.google.com/file/d/1ce40Ke0JGcASKJ0yWPLuknFHW3fg146D/view?usp=sharing

Runs on:
http://localhost:3000

### 3️. Backend Setup

cd backend

python -m venv venv

venv\Scripts\activate on Windows

pip install -r requirements.txt

uvicorn main:app --reload

Runs on:

http://127.0.0.1:8000

## Database Design
The system uses PostgreSQL via Supabase.

### Core Tables:

->profiles – Stores user metadata and role (user/admin)

->recipes – Stores recipe records linked to users

### Role-Based Access:

User → Can view only their own profile

Admin → Can view all profiles

### Row-Level Security (RLS):

RLS is enabled on all tables.

### Policies enforce:

->Users can only access their own data.

->Admins have elevated access via is_admin() function.

->Security is enforced at database level, not just frontend.

### Demo Checklist:

->Signup and Login functional

->Profile auto-created via trigger

->Normal user sees only their data

->Admin sees all profiles

->RLS prevents unauthorized access
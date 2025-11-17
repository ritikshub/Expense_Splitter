# Expense Splitter API

A backend API for an Expense Tracker / Splitter application built using FastAPI, PostgreSQL, SQLAlchemy, Docker, and uv.

---

## 🔧 Tech Stack
- **Python 3.13**
- **FastAPI** (async APIs, Pydantic validation)
- **uv** (Rust-based package manager, faster than pip)
- **PostgreSQL** (open-source, widely used in production)
- **Docker** (running PostgreSQL container instead of local installation)
- **SQLAlchemy** (ORM)
- **Uvicorn** (ASGI server)

---

## 📁 Project Structure

- **main.py** — Entry file; creates FastAPI `app` and runs using Uvicorn  
- **database.py** — PostgreSQL connection setup using SQLAlchemy  
- **models.py** — Database tables, relationships, and schema  
- **schemas.py** — Pydantic models defining request & response formats  
- **cruds.py** — Core logic layer; all DB queries & business logic  
- **routes.py** — API endpoints and route definitions  
- **\_\_init\_\_.py** — Marks folder as Python package  

---

## ▶️ How to Run

### 1. Start PostgreSQL (Docker)
Use Docker Compose to pull and run PostgreSQL:

```bash
docker-compose up -d


- Entry file that creates the FastAPI `app` instance.
- The server is run using:

  ```bash
  uvicorn main:app --reload
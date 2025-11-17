# Expense Splitter API

A backend API for an Expense Tracker / Splitter application built using FastAPI, PostgreSQL, SQLAlchemy, Docker, and uv.

---

## 🔧 Tech Stack

- **Python 3.13**  
  Latest version with improved performance and typing features

- **uv**  
  A blazing-fast Python package manager written in Rust. Used instead of pip for speed and built-in tooling.

- **FastAPI**  
  Modern, async-ready Python framework for building APIs. Uses Pydantic for data validation and auto-generates Swagger docs.

- **PostgreSQL**  
  Open-source relational database. Chosen for its speed, reliability, and wide adoption in production systems.

- **Docker**  
  Used to run PostgreSQL as a container instead of installing it locall

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

```bash
1. git clone https://github.com/ritikshub/expense-splitter-api.git
2. cd expense-splitter-api
3. If you don't have uv, kindly install it. I have mentioned the link below:
   https://docs.astral.sh/uv/getting-started/installation/#__tabbed_1_1
4. uv venv .venv --> this creates virtual environment for this project, so we can avoid conflicts and keep ourproject clean & organized.
5. source .venv/bin/activate --> command for activate the virtual environment
6. Install the dependency, just type, uv sync
7. Keep the database up and runnig: docker-compose up -d (do changes in your docker-compose, like username, passwd, db name)
8. finally, run the command: uvicorn main:app --reload

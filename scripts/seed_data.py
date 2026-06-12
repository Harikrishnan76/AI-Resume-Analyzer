#!/usr/bin/env python3
"""
AI Resume Analyzer — Database Seeder

Creates sample users, candidates, jobs, and synthetic resume data
for immediate testing without file uploads.

Usage:
    python scripts/seed_data.py
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import settings
from backend.database import init_db, async_session
from backend.models import (
    User, UserRole, Candidate, Resume, Job, ParseStatus
)
from backend.auth import hash_password


# ── Sample resume texts (synthetic) ──

RESUME_ALICE = """
ALICE CHEN
Email: alice.chen@email.com | Phone: +1-555-0101
LinkedIn: linkedin.com/in/alicechen | GitHub: github.com/alicechen

PROFESSIONAL SUMMARY
Senior Python developer with 7+ years of experience building scalable backend systems,
REST APIs, and microservices. Strong expertise in FastAPI, Django, and cloud deployments.

SKILLS
Python, FastAPI, Django, Flask, SQL, PostgreSQL, Redis, Docker, Kubernetes,
AWS, Git, CI/CD, REST API, GraphQL, Celery, RabbitMQ, Linux, Agile, Scrum

EXPERIENCE
Senior Backend Engineer — TechCorp Inc.
Jan 2021 - Present
- Architected and deployed microservices handling 5M+ daily requests using FastAPI
- Led migration from monolithic Django app to event-driven microservices
- Reduced API latency by 40% through Redis caching and query optimization
- Mentored 4 junior developers and conducted code reviews

Python Developer — DataFlow Solutions
Mar 2018 - Dec 2020
- Built ETL pipelines processing 2TB+ daily using Apache Airflow
- Developed REST APIs serving 50+ internal tools and dashboards
- Implemented CI/CD pipelines with GitHub Actions and Docker

Junior Developer — StartupXYZ
Jun 2016 - Feb 2018
- Full-stack development with Django and React
- Database design and optimization with PostgreSQL
- Automated deployment scripts using Ansible

EDUCATION
Master of Science in Computer Science — Stanford University, 2016
Bachelor of Science in Computer Engineering — UC Berkeley, 2014
"""

RESUME_BOB = """
BOB MARTINEZ
Email: bob.martinez@email.com | Phone: +1-555-0202

PROFESSIONAL SUMMARY
Data scientist with 4 years of experience in machine learning, NLP, and statistical analysis.
Passionate about building ML models that drive business impact.

SKILLS
Python, Machine Learning, Deep Learning, TensorFlow, PyTorch, Scikit-learn,
Pandas, NumPy, SQL, NLP, Computer Vision, Docker, Spark, Jupyter, R,
Statistics, A/B Testing, MLflow

EXPERIENCE
Data Scientist — AI Innovations Lab
Jul 2021 - Present
- Built recommendation system improving CTR by 25% using collaborative filtering
- Developed NLP pipeline for sentiment analysis of 100K+ daily reviews
- Created automated ML training pipeline with MLflow and Docker
- Conducted A/B tests and presented data-driven insights to leadership

ML Engineer Intern — BigData Corp
Jan 2020 - Jun 2021
- Implemented image classification models with 95% accuracy using PyTorch
- Built data preprocessing pipelines for 500GB+ datasets with PySpark
- Assisted in deploying models to production with Kubernetes

EDUCATION
Master of Science in Data Science — MIT, 2020
Bachelor of Science in Mathematics — Georgia Tech, 2018

CERTIFICATIONS
- AWS Machine Learning Specialty
- Google Professional Data Engineer
"""

RESUME_CAROL = """
CAROL JOHNSON
Email: carol.j@email.com | Phone: +1-555-0303

PROFESSIONAL SUMMARY
Junior web developer with 1 year of experience. Eager to learn and grow.
Familiar with Python and basic web development.

SKILLS
Python, HTML, CSS, JavaScript, Git, SQL, Flask

EXPERIENCE
Web Developer Intern — Small Agency LLC
Jun 2023 - Present
- Built static websites using HTML/CSS and JavaScript
- Assisted with Python Flask backend development
- Managed content updates and basic database queries

EDUCATION
Bachelor of Science in Information Technology — State University, 2023

PROJECTS
- Personal blog built with Flask and SQLite
- Weather dashboard using React and OpenWeatherMap API
"""


async def seed():
    """Seed the database with sample data."""
    print("🌱 Seeding database...")

    # Auto-delete existing SQLite database file to avoid IntegrityError on duplicates
    if settings.database_url.startswith("sqlite"):
        db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
        db_file = Path(db_path)
        if db_file.exists():
            print(f"🗑️ Removing existing database file: {db_file}")
            try:
                db_file.unlink()
            except Exception as e:
                print(f"⚠️ Could not delete database file: {e}")

    await init_db()


    async with async_session() as db:
        try:
            # ── Create Users ──
            print("👤 Creating users...")

            admin_user = User(
                username="admin",
                email="admin@resumeanalyzer.local",
                password_hash=hash_password("admin123"),
                role=UserRole.admin,
            )
            db.add(admin_user)

            alice_user = User(
                username="alice",
                email="alice.chen@email.com",
                password_hash=hash_password("alice123"),
                role=UserRole.candidate,
            )
            db.add(alice_user)

            bob_user = User(
                username="bob",
                email="bob.martinez@email.com",
                password_hash=hash_password("bob123"),
                role=UserRole.candidate,
            )
            db.add(bob_user)

            carol_user = User(
                username="carol",
                email="carol.j@email.com",
                password_hash=hash_password("carol123"),
                role=UserRole.candidate,
            )
            db.add(carol_user)

            await db.flush()

            # ── Create Candidates with synthetic resume data ──
            print("📋 Creating candidate profiles...")

            from backend.services.parser import extract_structured

            alice_data = extract_structured(RESUME_ALICE)
            alice = Candidate(
                user_id=alice_user.id,
                full_name="Alice Chen",
                email="alice.chen@email.com",
                phone="+1-555-0101",
                extracted_text=RESUME_ALICE,
                extracted_skills=alice_data["skills"],
                extracted_experience=alice_data["experience"],
                extracted_education=alice_data["education"],
            )
            db.add(alice)

            bob_data = extract_structured(RESUME_BOB)
            bob = Candidate(
                user_id=bob_user.id,
                full_name="Bob Martinez",
                email="bob.martinez@email.com",
                phone="+1-555-0202",
                extracted_text=RESUME_BOB,
                extracted_skills=bob_data["skills"],
                extracted_experience=bob_data["experience"],
                extracted_education=bob_data["education"],
            )
            db.add(bob)

            carol_data = extract_structured(RESUME_CAROL)
            carol = Candidate(
                user_id=carol_user.id,
                full_name="Carol Johnson",
                email="carol.j@email.com",
                phone="+1-555-0303",
                extracted_text=RESUME_CAROL,
                extracted_skills=carol_data["skills"],
                extracted_experience=carol_data["experience"],
                extracted_education=carol_data["education"],
            )
            db.add(carol)

            await db.flush()

            # ── Create Jobs ──
            print("💼 Creating job descriptions...")

            jobs_dir = PROJECT_ROOT / "data" / "sample_jobs"
            for job_file in jobs_dir.glob("*.json"):
                with open(job_file) as f:
                    job_data = json.load(f)

                job = Job(
                    created_by=admin_user.id,
                    title=job_data["title"],
                    description=job_data["description"],
                    required_skills=job_data.get("required_skills", []),
                    preferred_skills=job_data.get("preferred_skills", []),
                    experience_level=job_data.get("experience_level"),
                )
                db.add(job)
                print(f"   📄 {job_data['title']}")

            await db.commit()

            print()
            print("═" * 50)
            print("✅ Database seeded successfully!")
            print("═" * 50)
            print()
            print("📦 Created:")
            print("   • 1 admin user (admin / admin123)")
            print("   • 3 candidate users:")
            print("     - alice / alice123 (Senior Python Dev, 7 years)")
            print("     - bob / bob123 (Data Scientist, 4 years)")
            print("     - carol / carol123 (Junior Web Dev, 1 year)")
            print("   • 2 job descriptions (from data/sample_jobs/)")
            print()
            print("🚀 Start the app with: bash scripts/run_all.sh")

        except Exception as e:
            await db.rollback()
            print(f"❌ Seeding failed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed())

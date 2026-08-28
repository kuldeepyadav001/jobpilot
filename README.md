# 🚀 JobPilot — Automated Job Hunting System

Stop manually scrolling job portals. JobPilot scrapes, scores, applies, and tracks — automatically.

## The Problem

- Hours wasted daily scrolling Internshala & Naukri
- Sending wrong resumes to wrong roles
- No cover letters or generic ones
- Losing track of who responded
- Zero visibility into interview conversion rate

## The Solution

A self-hosted app that runs a full job hunting loop every 6 hours:

1. **Scrapes** Internshala + Naukri (Playwright)
2. **Scores** jobs against your resume (TF-IDF)
3. **Generates** tailored cover letters (Ollama LLM)
4. **Applies** via portal or email automatically
5. **Tracks** recruiter replies via Gmail IMAP
6. **Updates** Kanban board status automatically

You only open the dashboard to see results.

## Tech Stack

| Layer | Tool |
|-------|------|
| Backend | Python 3.11, FastAPI, SQLAlchemy |
| Database | PostgreSQL 15.5 |
| Scraping | Playwright (Chromium) |
| AI | Ollama + qwen2.5:1.5b (local, free) |
| Matching | scikit-learn TF-IDF |
| Frontend | React 18, Vite, TailwindCSS |
| DevOps | Docker Compose, Nginx |

**100% free. Zero paid APIs. Zero cloud costs.**

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/jobpilot.git
cd jobpilot
cp .env.example .env        # Add your Gmail + cookies
docker compose up -d         # Starts DB, backend, Ollama, Nginx
docker exec -it jobpilot_ollama ollama pull qwen2.5:1.5b
cd frontend && npm install && npm run dev

# JobPilot — Automated Job Hunting System

Scrapes jobs, matches your resume, applies automatically, tracks responses.

## Quick Start

1. Clone the repo
   git clone https://github.com/yourusername/jobpilot.git
   cd jobpilot

2. Setup environment
   cp .env.example .env
   # Edit .env with your credentials

3. Start services
   docker compose up --build

4. Verify
   Visit http://localhost/health

## Architecture
- Backend: FastAPI (port 8000)
- Database: PostgreSQL 15.5
- Proxy: Nginx (port 80)

## Stages
- [x] Stage 1: Foundation
- [ ] Stage 2: Database models
- [ ] Stage 3: Scrapers
- [ ] Stage 4: Resume engine
- [ ] Stage 5: Apply engine
- [ ] Stage 6: AI layer
- [ ] Stage 7: Response tracker
- [ ] Stage 8: Scheduler
- [ ] Stage 9: REST API
- [ ] Stage 10: React dashboard
# CLAUDE.md - Assignment Evaluator Project Rules

> Project-specific rules for Claude Code. This file is read automatically.

---

## Project Overview

**Project Name:** Assignment Evaluator (RoastAssignment)
**Description:** Students submit a GitHub repo link via Google Form; the app syncs the response, auto-evaluates the repo with an AI roast + static analysis, emails the result, and lets Examiners/Coaches review everything in a dashboard.
**Tech Stack:**
- Backend: FastAPI + Python 3.11+
- Frontend: React + TypeScript + Vite
- Database: PostgreSQL + SQLAlchemy
- Auth: JWT + Google OAuth (roles: student, examiner, coach)
- UI: Chakra UI

---

## Project Structure

```
roastassignment/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── user.py            # includes role: student | examiner | coach
│   │   │   ├── submission.py
│   │   │   └── evaluation.py
│   │   ├── schemas/
│   │   ├── routers/
│   │   ├── services/
│   │   │   ├── google_forms_sync.py
│   │   │   ├── github_fetcher.py
│   │   │   ├── ai_roast.py
│   │   │   ├── static_analysis.py
│   │   │   └── email.py
│   │   └── auth/
│   ├── alembic/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── context/
│   │   └── types/
│   └── package.json
├── .claude/
│   └── commands/
├── skills/
├── agents/
└── PRPs/
```

---

## Code Standards

### Python (Backend)
```python
# ALWAYS use type hints
def get_submission(db: Session, submission_id: int) -> Submission:
    pass

# ALWAYS add docstrings for public functions
def create_submission(db: Session, data: SubmissionCreate) -> Submission:
    """
    Create a new submission from a synced Google Form response.

    Args:
        db: Database session
        data: Submission creation data

    Returns:
        Created Submission object
    """
    pass
```

### TypeScript (Frontend)
```typescript
// ALWAYS define interfaces for props and data
interface SubmissionProps {
  id: number;
  studentName: string;
  assignmentName: string;
  githubRepoUrl: string;
}

// NO any types allowed
const fetchSubmission = async (id: number): Promise<Submission> => {
  // ...
};
```

---

## Forbidden Patterns

### Backend
- ❌ Never use `print()` - use `logging` module
- ❌ Never store passwords in plain text
- ❌ Never hardcode secrets - use environment variables
- ❌ Never use `SELECT *` - specify columns
- ❌ Never skip input validation
- ❌ Never fetch a GitHub repo without file count/size/timeout caps
- ❌ Never run email sending or evaluation synchronously inside a request handler - use background tasks

### Frontend
- ❌ Never use `any` type
- ❌ Never leave console.log in production
- ❌ Never skip error handling in async operations
- ❌ Never use inline styles - use Chakra UI

---

## Module-Specific Rules

### Submissions Module
- Every `Submission` must be matched to an existing `User` (role=student) by email; if no match exists, mark `sync_status=error` instead of creating an orphaned record
- Sync must be idempotent on `google_form_response_id` - never create duplicate submissions for the same Form response
- Students may only list/view their own submissions; examiners/coaches may view all

### Evaluation Module
- Evaluation must always run asynchronously (background task), triggered automatically right after a submission syncs successfully
- GitHub repo fetches must enforce a max file count, max total size, and a timeout - fail gracefully (status=failed) on invalid URLs, private repos, or limits exceeded
- `overall_score` must be a clearly defined weighted combination of `ai_score` and `static_analysis_score` (document the weights in code)
- Evaluation status must transition strictly: `pending -> running -> completed` or `pending -> running -> failed`

### Notifications Module
- Email sending must never block or fail the submission sync or evaluation pipeline - log and continue on email errors

---

## API Conventions

- All endpoints prefixed with `/api/v1/`
- Use plural nouns for resources: `/submissions`, `/evaluations`
- Return appropriate HTTP status codes:
  - 200: Success
  - 201: Created
  - 400: Bad Request
  - 401: Unauthorized
  - 404: Not Found
  - 409: Conflict

---

## Authentication

### JWT Configuration
- Access token expires: 30 minutes
- Refresh token expires: 7 days
- Algorithm: HS256

### Roles
- `student`: can only access their own submissions/evaluations
- `examiner` / `coach`: can access all submissions/evaluations, trigger manual sync/retry, and add comments/overrides

### OAuth Providers
- Google OAuth 2.0 enabled
- Always verify state parameter for CSRF protection

---

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/roastassignment

# Auth
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret

# Google Forms/Sheets sync (service account)
GOOGLE_SERVICE_ACCOUNT_JSON=path/to/service-account.json
GOOGLE_FORMS_SHEET_ID=your-form-response-sheet-id

# GitHub API
GITHUB_TOKEN=ghp_xxx

# LLM provider (AI roast generation)
OPENAI_API_KEY=sk-xxx

# Email notifications
SENDGRID_API_KEY=SG.xxx
# (or SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASSWORD)

# Frontend
VITE_API_URL=http://localhost:8000
```

---

## Development Commands

```bash
# Backend
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Docker
docker-compose up -d

# Tests
pytest backend/tests -v
cd frontend && npm test

# Linting
ruff check backend/
cd frontend && npm run lint
```

---

## Commit Message Format

```
feat([module]): add [feature]
fix([module]): fix [bug]
refactor([module]): refactor [component]
test([module]): add tests for [feature]
docs: update [documentation]
```

---

## Skills Reference

| Task | Skill to Read |
|------|---------------|
| Database models | skills/DATABASE.md |
| API + Auth | skills/BACKEND.md |
| React + UI | skills/FRONTEND.md |
| Testing | skills/TESTING.md |
| Deployment | skills/DEPLOYMENT.md |

---

## Agent Coordination

For complex tasks, the ORCHESTRATOR coordinates:
- DATABASE-AGENT → Backend models (User w/ role, Submission, Evaluation)
- BACKEND-AGENT → API development (auth, submissions sync, evaluation pipeline, notifications)
- FRONTEND-AGENT → UI components (auth pages, submissions list/detail, dashboard)
- TEST-AGENT → Testing
- REVIEW-AGENT → Code review
- DEVOPS-AGENT → Deployment (incl. scheduled Google Form sync job)

Read agent definitions in `/agents/` folder.

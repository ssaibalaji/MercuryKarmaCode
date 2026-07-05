# CLAUDE.md - Abhyas Project Rules

> Project-specific rules for Claude Code. This file is read automatically.

---

## Project Overview

**Project Name:** Abhyas
**Description:** Student portal for teachers/institutes to manage student records, attendance, and fee collection/reminders. Parents get read-only access. Future: Google Classroom integration for materials, assignments, tests.
**Tech Stack:**
- Backend: FastAPI + Python 3.11+
- Frontend: React + TypeScript + Vite
- Database: PostgreSQL + SQLAlchemy
- Auth: JWT + Google OAuth (teachers), Email/Password (parents, read-only role)
- UI: Chakra UI
- Payments: Razorpay

---

## Project Structure

```
abhyas-saas/
├── backend/
│   ├── app/
│   │   ├── main.py, config.py, database.py
│   │   ├── models/
│   │   │   ├── user.py           # User, RefreshToken (role: teacher | parent | admin)
│   │   │   ├── student.py        # Student
│   │   │   ├── attendance.py     # AttendanceRecord
│   │   │   └── fee.py            # FeeStructure, Payment, FeeReminder
│   │   ├── schemas/
│   │   ├── routers/
│   │   │   ├── auth.py, students.py, attendance.py, fees.py, payments.py, admin.py
│   │   ├── services/
│   │   │   ├── razorpay_service.py
│   │   │   └── email_service.py
│   │   └── auth/
│   ├── alembic/
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/, pages/, hooks/, services/, context/, types/
├── skills/
├── agents/
└── .claude/commands/
```

---

## Code Standards

### Python (Backend)
```python
# ALWAYS use type hints
def get_student(db: Session, student_id: int) -> Student:
    pass

# Async endpoints
@router.get("/students/{id}")
async def get_student(id: int, db: Session = Depends(get_db)):
    pass
```

### TypeScript (Frontend)
```typescript
// Interfaces required - NO any types
interface Student { id: number; full_name: string; class_grade: string; }

const fetchStudent = async (id: number): Promise<Student> => { ... };
```

---

## Forbidden

- `print()` → use `logging`
- Plain passwords → use bcrypt
- Hardcoded secrets → use env vars
- `any` type in TypeScript
- `console.log` in production
- Inline styles → use Chakra UI

---

## Role-Based Access Rules

- Every `Student` row belongs to exactly one `teacher_id` (the creating teacher/institute).
- `Student.parent_user_id` links a parent account once they accept an invite — nullable until then.
- Parents (`role == "parent"`) may only read data (students, attendance, fees) for students where `parent_user_id == current_user.id`. Never allow parent writes to Student/Attendance/FeeStructure.
- Teachers (`role == "teacher"`) may only access students where `teacher_id == current_user.id`.
- Admins (`role == "admin"`) may access all data via `/admin/*` routes only.
- Enforce role checks in a shared FastAPI dependency (e.g. `require_role(...)`), not ad hoc per-endpoint checks.

---

## Module-Specific Rules

### Attendance
- One `AttendanceRecord` per (student_id, date) — enforce via unique constraint, upsert on re-mark.
- Valid `status` values: `present`, `absent`, `late`.

### Fees & Payments
- Razorpay webhook endpoint MUST verify the webhook signature before recording a payment — never trust unsigned payloads.
- `Payment.status` transitions: `pending` → `completed` | `failed`. Never allow a client to directly set `completed`; only the verified webhook handler may do so.
- Outstanding balance = `FeeStructure.amount` minus sum of `completed` payments for that fee.
- Fee reminder emails are only sent for fees past `due_date` with an outstanding balance > 0.

---

## API Conventions

- All endpoints prefixed with `/api/v1/`
- Use plural nouns for resources: `/students`, `/fees`, `/payments`
- Return appropriate HTTP status codes:
  - 200: Success
  - 201: Created
  - 400: Bad Request
  - 401: Unauthorized
  - 403: Forbidden (role mismatch)
  - 404: Not Found
  - 409: Conflict

---

## Authentication

### JWT Configuration
- Access token expires: 30 minutes
- Refresh token expires: 7 days
- Algorithm: HS256

### OAuth Providers
- Google OAuth 2.0 enabled for teachers
- Always verify state parameter for CSRF protection

### Parent Onboarding
- Parent accounts are created via an invite flow (`POST /api/students/{id}/invite-parent`), not open self-registration — this keeps the parent-student link secure.

---

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/abhyas

# Auth
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret

# Razorpay
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...

# Email
EMAIL_SERVICE_API_KEY=...
EMAIL_FROM_ADDRESS=noreply@abhyas.app

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
- DATABASE-AGENT → Backend models
- BACKEND-AGENT → API development
- FRONTEND-AGENT → UI components
- TEST-AGENT → Testing
- REVIEW-AGENT → Code review
- DEVOPS-AGENT → Deployment

Read agent definitions in `/agents/` folder.

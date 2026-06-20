# PRP: Assignment Evaluator (RoastAssignment)

> Implementation blueprint for parallel agent execution

---

## METADATA

| Field | Value |
|-------|-------|
| **Product** | Assignment Evaluator (RoastAssignment) |
| **Type** | SaaS |
| **Version** | 1.0 |
| **Created** | 2026-06-20 |
| **Complexity** | High |

---

## PRODUCT OVERVIEW

**Description:** Students submit an assignment's GitHub repo link via a Google Form. The backend syncs new Form responses, matches them to the student's account by email, then automatically fetches the repo and runs a combined AI-generated "roast" review plus rule-based static analysis to produce a score and feedback. The student is emailed when evaluation completes. Examiners and Coaches use a dashboard to review all submissions and results.

**Value Proposition:** Replaces slow, manual GitHub-link grading with an automated, consistent, and entertaining ("roast") code review pipeline — examiners get instant first-pass feedback + scores instead of reading every repo by hand.

**MVP Scope:**
- [ ] User registration/login (email/password + Google OAuth) with role: student/examiner/coach
- [ ] Google Form -> Sheets sync creates Submission records (idempotent on google_form_response_id)
- [ ] Automatic evaluation: GitHub fetch + AI roast + static analysis -> overall score
- [ ] Email notification to student when evaluation completes
- [ ] Examiner/Coach dashboard listing submissions + evaluation detail view
- [ ] Student view of their own submission and result

---

## TECH STACK

| Layer | Technology | Skill Reference |
|-------|------------|-----------------|
| Backend | FastAPI + Python 3.11+ | skills/BACKEND.md |
| Frontend | React + TypeScript + Vite | skills/FRONTEND.md |
| Database | PostgreSQL + SQLAlchemy | skills/DATABASE.md |
| Auth | JWT + bcrypt + Google OAuth | skills/BACKEND.md |
| UI | Chakra UI | skills/FRONTEND.md |
| Testing | pytest + RTL | skills/TESTING.md |
| Deployment | Docker + GitHub Actions | skills/DEPLOYMENT.md |

---

## DATABASE MODELS

### User Model
- id, email, hashed_password, full_name, role (student | examiner | coach), is_active, is_verified, oauth_provider, created_at

### RefreshToken Model
- id, user_id (FK -> User), token, expires_at, revoked

### Submission Model
- id, user_id (FK -> User, the student), student_name, student_email, assignment_name, github_repo_url, google_form_response_id (unique), sync_status (pending | synced | error), submitted_at, created_at, updated_at

### Evaluation Model
- id, submission_id (FK -> Submission, one-to-one), ai_roast_text, ai_score, static_analysis_report (JSON), static_analysis_score, overall_score, status (pending | running | completed | failed), evaluated_at, created_at, updated_at

---

## MODULES

### Module 1: Authentication
**Agents:** DATABASE-AGENT + BACKEND-AGENT + FRONTEND-AGENT

**Backend Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/register | Create account (with role) |
| POST | /auth/login | Get tokens |
| POST | /auth/refresh | Refresh token |
| POST | /auth/logout | Revoke refresh token |
| GET | /auth/google | Start Google OAuth flow |
| GET | /auth/google/callback | Google OAuth callback |
| GET | /auth/me | Current user |
| PUT | /auth/me | Update profile |

**Frontend Pages:**
| Route | Page | Components |
|-------|------|------------|
| /login | LoginPage | LoginForm, GoogleOAuthButton |
| /register | RegisterPage | RegisterForm, RoleSelect |
| /forgot-password | ForgotPasswordPage | ForgotPasswordForm |
| /profile | ProfilePage | ProfileForm |

---

### Module 2: Submissions
**Agents:** BACKEND-AGENT + FRONTEND-AGENT

**Backend Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/submissions | List submissions (role-scoped: students see own, examiners/coaches see all) |
| GET | /api/submissions/{id} | Get one submission + its evaluation |
| POST | /api/submissions/sync | Manually trigger Google Form sync (examiner/coach only) |

**Backend Services:**
- `services/google_forms_sync.py` — polls the Google Sheet behind the Form via Google Sheets API, matches rows to existing students by email, upserts `Submission` rows idempotently on `google_form_response_id`, then enqueues evaluation for newly synced submissions.

**Frontend Pages:**
| Route | Page | Components |
|-------|------|------------|
| /submissions | SubmissionsListPage | SubmissionTable, RoleScopedFilter |
| /submissions/{id} | SubmissionDetailPage | SubmissionInfo, EvaluationPanel |

---

### Module 3: Evaluation
**Agents:** BACKEND-AGENT + FRONTEND-AGENT

**Backend Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/evaluations/{submission_id} | Get evaluation result for a submission |
| POST | /api/evaluations/{submission_id}/retry | Re-run evaluation (examiner/coach only) |
| PUT | /api/evaluations/{submission_id} | Add manual comment / override score (examiner/coach only) |

**Backend Services:**
- `services/github_fetcher.py` — fetches repo file tree/contents via GitHub API; enforces max file count, max total size, and a timeout; raises a clear error on invalid URL, private repo, or limits exceeded.
- `services/ai_roast.py` — sends fetched code to the LLM provider (Anthropic) and returns `ai_roast_text` + `ai_score`.
- `services/static_analysis.py` — runs language-aware static checks (e.g. `ruff` for Python, generic file-count/LOC metrics for other languages) and returns `static_analysis_report` + `static_analysis_score`.
- Evaluation orchestration combines `ai_score` and `static_analysis_score` into `overall_score` via a documented weighting, and runs entirely as a background task with strict status transitions: `pending -> running -> completed|failed`.

**Frontend Pages:**
| Route | Page | Components |
|-------|------|------------|
| (embedded in /submissions/{id}) | EvaluationPanel | RoastText, ScoreBadge, StaticAnalysisReport, ExaminerCommentBox |

---

### Module 4: Notifications
**Agents:** BACKEND-AGENT

**Backend Services:**
- `services/email.py` — sends the student a result email when an `Evaluation` transitions to `completed`. Always runs as a background task; logs and continues on failure without affecting submission/evaluation state.

---

### Module 5: Dashboard
**Agents:** FRONTEND-AGENT (+ BACKEND-AGENT for stats endpoints)

**Frontend Pages:**
| Route | Page | Components |
|-------|------|------------|
| /dashboard | DashboardPage | RoleScopedStats, RecentSubmissions |
| /settings | SettingsPage | UserPreferencesForm |
| /admin *(post-MVP)* | AdminPage | UserList, RoleManager |
| /admin/users *(post-MVP)* | AdminUsersPage | UserTable |
| /analytics *(post-MVP)* | AnalyticsPage | ScoreDistributionChart, SubmissionsOverTimeChart |

---

## PHASE EXECUTION PLAN

**Phase 1: Foundation (4 agents in parallel)**
- DATABASE-AGENT: User (with role), RefreshToken, Submission, Evaluation models + migrations, database.py
- BACKEND-AGENT: main.py, config.py, project structure, env var loading for Google/GitHub/LLM/email credentials
- FRONTEND-AGENT: Vite setup, folder structure, base components, Chakra theme
- DEVOPS-AGENT: Docker, CI/CD, env files, scheduled job runner for Google Form sync

**Validation Gate 1:** `pip install`, `alembic upgrade head`, `npm install`, `docker-compose config`

**Phase 2: Modules (backend + frontend parallel per module)**
- Auth Module: JWT + Google OAuth endpoints + Login/Register/Profile pages
- Submissions Module: Google Forms sync service + endpoints + Submissions list/detail pages
- Evaluation Module: GitHub fetcher + AI roast + static analysis services + endpoints + EvaluationPanel
- Notifications Module: email service wired to evaluation completion
- Dashboard Module: stats endpoints + Dashboard/Settings pages

**Validation Gate 2:** `ruff check backend/`, `mypy backend/`, `npm run lint`, `npm run type-check`

**Phase 3: Quality (3 agents in parallel)**
- TEST-AGENT: pytest (incl. mocked GitHub/LLM/email/Google Sheets calls) + RTL tests, 80%+ coverage
- REVIEW-AGENT: security audit (GitHub URL validation, fetch caps, secret handling, role-based access), performance review
- RESEARCH-AGENT: best-practices validation for Google Sheets API polling and LLM prompt design for the roast review

**Final Validation:** Full test suite, docker build, health checks

---

## VALIDATION GATES

| Gate | Commands |
|------|----------|
| 1 | `alembic upgrade head`, `npm install`, `docker-compose config` |
| 2 | `ruff check backend/`, `npm run type-check` |
| 3 | `pytest --cov --cov-fail-under=80`, `npm test` |
| Final | `docker-compose up -d`, `curl localhost:8000/health` |

---

## ENVIRONMENT VARIABLES

```env
DATABASE_URL=postgresql://user:password@localhost:5432/roastassignment
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-secret
GOOGLE_SERVICE_ACCOUNT_JSON=path/to/service-account.json
GOOGLE_FORMS_SHEET_ID=your-form-response-sheet-id
GITHUB_TOKEN=ghp_xxx
ANTHROPIC_API_KEY=sk-ant-xxx
SENDGRID_API_KEY=SG.xxx
VITE_API_URL=http://localhost:8000
```

---

## NEXT STEP

Execute with parallel agents:
/execute-prp PRPs/assignment-evaluator-prp.md

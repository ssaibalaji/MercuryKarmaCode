# INITIAL.md - Assignment Evaluator Product Definition

> AI-powered assignment evaluation: students submit a GitHub repo link via Google Form, the system auto-fetches and "roasts" the code with combined AI review + static analysis, and emails the result.

---

## PRODUCT

### Name
Assignment Evaluator (RoastAssignment)

### Description
A platform where students submit their assignment's GitHub repository link through a Google Form. The backend syncs new Form responses, matches them to the student's account by email, then automatically fetches the repo and runs a combined AI-generated "roast" review plus rule-based static analysis to produce a score and feedback. The student receives an email once evaluation completes. Examiners and Coaches log into a dashboard to review all submissions and their evaluation results.

### Target User
Examiners, Coaches, Students

### Type
- [x] SaaS (Software as a Service)

---

## TECH STACK

### Backend
- [x] FastAPI + Python 3.11+

### Frontend
- [x] React + TypeScript + Vite

### Database
- [x] PostgreSQL + SQLAlchemy

### Authentication
- [x] Email/Password + Google OAuth

### UI Framework
- [x] Chakra UI

### Payments
- [ ] None (not needed for MVP)

---

## MODULES

### Module 1: Authentication (Required)

**Description:** User authentication and authorization for students, examiners, and coaches.

**Models:**
- User: id, email, hashed_password, full_name, role (student | examiner | coach), is_active, is_verified, oauth_provider, created_at
- RefreshToken: id, user_id, token, expires_at, revoked

**API Endpoints:**
- POST /auth/register - Create new account (with role)
- POST /auth/login - Login with email/password
- POST /auth/refresh - Refresh access token
- POST /auth/logout - Revoke refresh token
- GET /auth/google - Start Google OAuth flow
- GET /auth/google/callback - Google OAuth callback
- GET /auth/me - Get current user profile
- PUT /auth/me - Update profile

**Frontend Pages:**
- /login - Login page
- /register - Registration page
- /forgot-password - Forgot password page
- /profile - User profile page (protected)

---

### Module 2: Submissions

**Description:** Ingests assignment submissions from an external Google Form (no custom in-app submission form). A background sync service polls the Google Sheet behind the Form via the Google Sheets API, matches each response to an existing student account by email, and creates a `Submission` record. Sync is idempotent — re-running it must never create duplicate submissions for the same Form response.

**Models:**
```
Submission:
  - id, user_id (FK -> User, the student)
  - student_name: str
  - student_email: str
  - assignment_name: str
  - github_repo_url: str
  - google_form_response_id: str (unique)
  - sync_status: enum (pending, synced, error)
  - submitted_at: datetime
  - created_at, updated_at
```

**API Endpoints:**
```
GET    /api/submissions          - List submissions (students see only their own; examiners/coaches see all)
GET    /api/submissions/{id}     - Get one submission + its evaluation
POST   /api/submissions/sync     - Manually trigger a Google Form sync (examiner/coach only)
```

**Frontend Pages:**
```
/submissions           - List (role-scoped)
/submissions/{id}       - Detail (submission info + evaluation result)
```

---

### Module 3: Evaluation

**Description:** Runs automatically as a background task immediately after a submission is synced in. Pipeline: fetch the GitHub repo's file tree/contents via the GitHub API (capped file count and total size, with a timeout), send the code to an LLM for an AI-generated "roast" review and score, run language-aware static analysis (e.g. `ruff` for Python, generic file-count/LOC metrics for other languages), then combine both into a weighted overall score.

**Models:**
```
Evaluation:
  - id, submission_id (FK -> Submission, one-to-one)
  - ai_roast_text: text
  - ai_score: float
  - static_analysis_report: JSON
  - static_analysis_score: float
  - overall_score: float
  - status: enum (pending, running, completed, failed)
  - evaluated_at: datetime
  - created_at, updated_at
```

**API Endpoints:**
```
GET    /api/evaluations/{submission_id}        - Get evaluation result for a submission
POST   /api/evaluations/{submission_id}/retry   - Re-run evaluation (examiner/coach only)
PUT    /api/evaluations/{submission_id}          - Add manual comment / override score (examiner/coach only)
```

**Frontend Pages:**
```
(embedded in /submissions/{id} - roast text, scores, static analysis report, examiner comments)
```

---

### Module 4: Notifications

**Description:** Sends the student an email once their evaluation completes. Email sending always runs as a background task and must never block the submission sync or evaluation pipeline.

**API Endpoints:**
```
(no public endpoints - internal service triggered by Evaluation completion)
```

---

### Module 5: Dashboard

**Description:** Role-scoped overview. Examiners/Coaches see all submissions, evaluation stats, and (post-MVP) an admin panel and analytics charts. Students see their own submission history and latest result.

**Frontend Pages:**
- /dashboard - Overview (role-scoped stats and recent submissions)
- /settings - User settings and preferences
- /admin - Admin dashboard (protected, examiner/coach only) *(post-MVP)*
- /admin/users - User & role management *(post-MVP)*
- /analytics - Score distribution, submissions over time *(post-MVP)*

---

## MVP SCOPE

### Must Have (MVP)
- [x] User registration and login (email/password + Google OAuth) with role: student/examiner/coach
- [ ] Google Form -> Sheets sync creates Submission records (idempotent on google_form_response_id)
- [ ] Automatic evaluation: GitHub fetch + AI roast + static analysis -> overall score
- [ ] Email notification to student when evaluation completes
- [ ] Examiner/Coach dashboard listing submissions + evaluation detail view
- [ ] Student view of their own submission and result

### Nice to Have (Post-MVP)
- [ ] Admin panel (user/role management)
- [ ] Analytics dashboard (score distribution, submissions over time)
- [ ] File uploads (supplementary documents alongside the GitHub link)
- [ ] Manual re-evaluation / score override by examiner
- [ ] Coach comments / discussion thread per submission

---

## ACCEPTANCE CRITERIA

### Authentication
- [ ] User can register with email/password and a role
- [ ] User can login with email/password
- [ ] User can sign in with Google OAuth
- [ ] JWT tokens work correctly with refresh
- [ ] Protected routes redirect to login
- [ ] Students can only access their own submissions/evaluations; examiners/coaches can access all

### Submissions
- [ ] New Google Form responses are synced into Submission records without duplicates
- [ ] Unmatched student emails are flagged with sync_status = error rather than silently dropped
- [ ] Submission list is correctly scoped by role

### Evaluation
- [ ] Evaluation runs automatically right after a submission is synced
- [ ] GitHub fetch enforces file count/size/time caps and fails gracefully on invalid or private repos
- [ ] ai_score and static_analysis_score are both stored, and overall_score is a defined weighted combination
- [ ] Evaluation status transitions correctly: pending -> running -> completed/failed

### Notifications
- [ ] Student receives an email after evaluation completes
- [ ] Email sending failures do not affect submission/evaluation state

### Quality
- [ ] All API endpoints documented in OpenAPI
- [ ] Backend test coverage 80%+
- [ ] Frontend TypeScript strict mode passes
- [ ] Docker builds and runs successfully

---

## SPECIAL REQUIREMENTS

### Security
- [x] Rate limiting on auth endpoints
- [x] Input validation on all endpoints
- [x] SQL injection prevention
- [x] XSS prevention
- [x] CSRF protection (state parameter) for Google OAuth
- [x] Validate/sanitize submitted GitHub URLs before fetching
- [x] Cap GitHub repo fetch size, file count, and request timeout to prevent abuse

### Integrations
- [x] Google Sheets/Forms API for submission sync (service account credentials)
- [x] GitHub API for fetching repo contents (token for higher rate limits)
- [x] LLM provider (e.g. Anthropic Claude) for AI roast generation
- [x] Email service (SMTP or SendGrid) for notifications

---

## AGENTS

> These 6 agents will build your product in parallel:

| Agent | Role | Works On |
|-------|------|----------|
| DATABASE-AGENT | Creates all models and migrations | User (role), Submission, Evaluation |
| BACKEND-AGENT | Builds API endpoints and services | Auth, Submissions sync, Evaluation pipeline, Notifications |
| FRONTEND-AGENT | Creates UI pages and components | Login/Register, Submissions list/detail, Dashboard |
| DEVOPS-AGENT | Sets up Docker, CI/CD, environments | Infrastructure, scheduled sync job |
| TEST-AGENT | Writes unit and integration tests | All code |
| REVIEW-AGENT | Security and code quality audit | All code |

---

# READY?

```bash
/generate-prp INITIAL.md
```

Then:

```bash
/execute-prp PRPs/assignment-evaluator-prp.md
```

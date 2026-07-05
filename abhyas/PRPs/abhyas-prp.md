# PRP: Abhyas

> Implementation blueprint for parallel agent execution

---

## METADATA

| Field | Value |
|-------|-------|
| **Product** | Abhyas |
| **Type** | SaaS (Student Portal) |
| **Version** | 1.0 |
| **Created** | 2026-07-04 |
| **Complexity** | Medium-High |

---

## PRODUCT OVERVIEW

**Description:** Abhyas is a student portal used by teachers/institutes to manage their student database, track daily attendance, and handle fee collection and reminders. Parents get read-only access to view their child's attendance and fee status via an invite-based account link. Future phases add Google Classroom integration for materials, assignments, and tests.

**Value Proposition:** Teachers/institutes currently track students, attendance, and fees manually (spreadsheets, notebooks, WhatsApp). Abhyas centralizes this into one portal, automates fee reminders, and gives parents self-serve visibility — reducing admin overhead and late payments.

**MVP Scope:**
- [ ] Teacher auth (email/password + Google OAuth) and parent auth (invite-based, read-only)
- [ ] Student roster CRUD, scoped to the creating teacher
- [ ] Daily attendance marking + history + per-student summary
- [ ] Fee structure setup, Razorpay payment collection, payment history
- [ ] Automated email reminders for overdue fees
- [ ] Dashboard with attendance/fee stats
- [ ] Admin panel for institute-level user management

---

## TECH STACK

| Layer | Technology | Skill Reference |
|-------|------------|-----------------|
| Backend | FastAPI + Python 3.11+ | skills/BACKEND.md |
| Frontend | React + TypeScript + Vite | skills/FRONTEND.md |
| Database | PostgreSQL + SQLAlchemy | skills/DATABASE.md |
| Auth | JWT + bcrypt + Google OAuth | skills/BACKEND.md |
| UI | Chakra UI | skills/FRONTEND.md |
| Payments | Razorpay | skills/BACKEND.md |
| Testing | pytest + React Testing Library | skills/TESTING.md |
| Deployment | Docker + GitHub Actions | skills/DEPLOYMENT.md |

---

## DATABASE MODELS

### User
- id, email, hashed_password, full_name, role (`teacher` \| `parent` \| `admin`), is_active, is_verified, oauth_provider, created_at

### RefreshToken
- id, user_id (FK -> User), token, expires_at, revoked

### Student
- id, teacher_id (FK -> User), full_name, date_of_birth, class_grade, section, roll_number, photo_url, parent_name, parent_email, parent_phone, parent_user_id (FK -> User, nullable), enrollment_date, is_active, created_at, updated_at

### AttendanceRecord
- id, student_id (FK -> Student), teacher_id (FK -> User), date, status (`present` \| `absent` \| `late`), notes, created_at, updated_at
- Unique constraint: (student_id, date)

### FeeStructure
- id, student_id (FK -> Student), amount, frequency (`monthly` \| `term` \| `one_time`), due_date, description, created_at, updated_at

### Payment
- id, fee_structure_id (FK -> FeeStructure), student_id (FK -> Student), amount_paid, payment_date, method (`razorpay` \| `cash` \| `bank_transfer`), razorpay_payment_id (nullable), razorpay_order_id (nullable), status (`pending` \| `completed` \| `failed`), created_at

### FeeReminder
- id, student_id (FK -> Student), fee_structure_id (FK -> FeeStructure), sent_at, channel (`email`), status (`sent` \| `failed`)

**Relationships:**
- User (teacher) 1—N Student
- User (parent) 1—N Student (via parent_user_id, nullable until invite accepted)
- Student 1—N AttendanceRecord
- Student 1—N FeeStructure 1—N Payment
- Student/FeeStructure 1—N FeeReminder

---

## MODULES

### Module 1: Authentication
**Agents:** DATABASE-AGENT + BACKEND-AGENT + FRONTEND-AGENT

**Backend Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/register | Create account (teacher self-signup) |
| POST | /auth/login | Login with email/password |
| POST | /auth/refresh | Refresh access token |
| POST | /auth/logout | Revoke refresh token |
| GET | /auth/google | Google OAuth login (teachers) |
| GET | /auth/me | Current user profile |
| PUT | /auth/me | Update profile |

**Frontend Pages:**
| Route | Page | Components |
|-------|------|------------|
| /login | LoginPage | LoginForm, GoogleOAuthButton |
| /register | RegisterPage | RegisterForm |
| /forgot-password | ForgotPasswordPage | ForgotPasswordForm |
| /profile | ProfilePage | ProfileForm |

---

### Module 2: Students
**Agents:** BACKEND-AGENT + FRONTEND-AGENT

**Backend Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/students | List students (teacher: own; parent: own children) |
| POST | /api/students | Create student |
| GET | /api/students/{id} | Get one student |
| PUT | /api/students/{id} | Update student |
| DELETE | /api/students/{id} | Deactivate student |
| POST | /api/students/{id}/invite-parent | Send parent invite email |

**Frontend Pages:**
| Route | Page | Components |
|-------|------|------------|
| /students | StudentListPage | StudentTable, StudentFilterBar |
| /students/new | StudentCreatePage | StudentForm |
| /students/{id} | StudentDetailPage | StudentProfile, AttendanceSummary, FeeSummary |
| /students/{id}/edit | StudentEditPage | StudentForm |

---

### Module 3: Attendance
**Agents:** BACKEND-AGENT + FRONTEND-AGENT

**Backend Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/attendance | Query attendance (filter by date, class_grade, student_id) |
| POST | /api/attendance | Mark attendance (single or bulk for class/day) |
| PUT | /api/attendance/{id} | Update a record |
| GET | /api/attendance/student/{student_id}/summary | Attendance % summary |

**Frontend Pages:**
| Route | Page | Components |
|-------|------|------------|
| /attendance | AttendanceMarkingPage | AttendanceGrid (by class/section) |
| /attendance/history | AttendanceHistoryPage | AttendanceFilter, AttendanceTable |

---

### Module 4: Fees & Payments
**Agents:** BACKEND-AGENT + FRONTEND-AGENT

**Backend Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/fees/students/{student_id} | Fee structure + payment history + balance |
| POST | /api/fees | Create fee structure |
| PUT | /api/fees/{id} | Update fee structure |
| POST | /api/payments/razorpay/order | Create Razorpay order |
| POST | /api/payments/razorpay/webhook | Razorpay webhook (verify + record payment) |
| GET | /api/payments/student/{student_id} | Payment history |
| POST | /api/fees/{id}/remind | Manually trigger fee reminder email |
| GET | /api/fees/overdue | List overdue fees (for reminder job) |

**Frontend Pages:**
| Route | Page | Components |
|-------|------|------------|
| /fees | FeeOverviewPage | FeeTable, OverdueBadge |
| /fees/{student_id} | FeeDetailPage | FeeStructureCard, PaymentHistoryTable |
| /fees/{student_id}/pay | PaymentPage | RazorpayCheckoutButton |

---

### Module 5: Dashboard
**Agents:** BACKEND-AGENT + FRONTEND-AGENT

**Frontend Pages:**
| Route | Page | Components |
|-------|------|------------|
| /dashboard | DashboardPage | AttendanceTrendChart, FeeCollectionChart, OverdueCountCard |
| /settings | SettingsPage | SettingsForm |

---

### Module 6: Admin Panel
**Agents:** BACKEND-AGENT + FRONTEND-AGENT

**Backend Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /admin/users | List all users |
| PUT | /admin/users/{id} | Update user status/role |
| GET | /admin/stats | Platform statistics |

**Frontend Pages:**
| Route | Page | Components |
|-------|------|------------|
| /admin | AdminDashboardPage | StatsCards |
| /admin/users | AdminUserListPage | UserTable |

---

## PHASE EXECUTION PLAN

**Phase 1: Foundation (4 agents in parallel)**
- DATABASE-AGENT: User, RefreshToken, Student, AttendanceRecord, FeeStructure, Payment, FeeReminder models + Alembic migrations
- BACKEND-AGENT: main.py, config.py, database.py, project structure, role-based auth dependency (`require_role`)
- FRONTEND-AGENT: Vite setup, folder structure, base Chakra UI theme, routing skeleton
- DEVOPS-AGENT: Docker, docker-compose (Postgres + backend + frontend), CI/CD, env files

**Validation Gate 1:** `alembic upgrade head`, `npm install`, `docker-compose config`

**Phase 2: Modules (backend + frontend parallel per module)**
- Auth Module: JWT + Google OAuth endpoints + Login/Register/Profile pages
- Students Module: CRUD + parent-invite endpoint + Student list/detail/form pages
- Attendance Module: Marking + query + summary endpoints + Attendance grid/history pages
- Fees Module: Fee structure + Razorpay order/webhook + reminder endpoints + Fee overview/detail/payment pages
- Dashboard Module: Stats aggregation endpoints + Dashboard charts
- Admin Module: User management endpoints + Admin pages

**Validation Gate 2:** `ruff check backend/`, `npm run type-check`

**Phase 3: Quality (3 agents in parallel)**
- TEST-AGENT: pytest (models, routers, Razorpay webhook signature verification, role-based access) + RTL tests, 80%+ coverage
- REVIEW-AGENT: Security audit (webhook signature checks, role-based access enforcement, secrets handling), performance review
- RESEARCH-AGENT: Validate Razorpay integration patterns and FastAPI/Chakra best practices

**Final Validation:** Full test suite, `docker-compose up -d`, health check

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

## NEXT STEP

Execute with parallel agents:
/execute-prp PRPs/abhyas-prp.md

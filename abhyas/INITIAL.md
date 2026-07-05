# INITIAL.md - Abhyas Product Definition

> A student portal for teachers/institutes to manage student records, attendance, and fee collection.

---

## PRODUCT

### Name
Abhyas

### Description
Abhyas is a student portal used by teachers/institutes to manage their student database, track daily attendance, and handle fee collection and reminders. Parents get read-only access to view their child's attendance and fee status. Future phases will integrate with Google Classroom/Colab for course materials, assignments, tests, and feedback.

### Target User
Teachers and coaching/tuition institutes (primary/admin users) who manage students; parents (secondary, read-only users) who track their child's attendance and pay fees.

### Type
- [x] SaaS (Software as a Service)

---

## TECH STACK

### Backend
- [x] FastAPI + Python

### Frontend
- [x] React + TypeScript + Vite

### Database
- [x] PostgreSQL + SQLAlchemy

### Authentication
- [x] Email/Password + Google OAuth (teachers). Parents authenticate via email/password (read-only role).

### UI Framework
- [x] Chakra UI

### Payments
- [x] Razorpay (fee collection from parents)

---

## MODULES

### Module 1: Authentication (Required)

**Description:** User authentication and role-based authorization (Teacher/Admin vs Parent)

**Models:**
- User: id, email, hashed_password, full_name, role (teacher | parent | admin), is_active, is_verified, oauth_provider, created_at
- RefreshToken: id, user_id, token, expires_at, revoked

**API Endpoints:**
- POST /auth/register - Create new account
- POST /auth/login - Login with email/password
- POST /auth/refresh - Refresh access token
- POST /auth/logout - Revoke refresh token
- GET /auth/google - Google OAuth login (teachers)
- GET /auth/me - Get current user profile
- PUT /auth/me - Update profile

**Frontend Pages:**
- /login - Login page
- /register - Registration page
- /forgot-password - Forgot password page
- /profile - User profile page (protected)

---

### Module 2: Students

**Description:** Student roster management. Each student is linked to the teacher/institute that created them, and optionally linked to a parent user account.

**Models:**
```
Student:
  - id, teacher_id (FK -> User)
  - full_name, date_of_birth
  - class_grade, section, roll_number
  - photo_url
  - parent_name, parent_email, parent_phone
  - parent_user_id (FK -> User, nullable - linked once parent registers)
  - enrollment_date
  - is_active
  - created_at, updated_at
```

**API Endpoints:**
```
GET    /api/students          - List all students (teacher: own students; parent: own children)
POST   /api/students          - Create student
GET    /api/students/{id}     - Get one student
PUT    /api/students/{id}     - Update student
DELETE /api/students/{id}     - Delete/deactivate student
POST   /api/students/{id}/invite-parent - Send parent an invite to create their read-only account
```

**Frontend Pages:**
```
/students             - List (teacher view)
/students/new         - Create
/students/{id}        - Detail (profile, attendance %, fee status)
/students/{id}/edit   - Edit
```

---

### Module 3: Attendance

**Description:** Daily present/absent/late tracking per student, per class day.

**Models:**
```
AttendanceRecord:
  - id, student_id (FK), teacher_id (FK)
  - date
  - status (present | absent | late)
  - notes
  - created_at, updated_at
  (unique constraint: student_id + date)
```

**API Endpoints:**
```
GET    /api/attendance?date=&class_grade=&student_id=  - Query attendance
POST   /api/attendance                                  - Mark attendance (single or bulk for a class/day)
PUT    /api/attendance/{id}                             - Update a record
GET    /api/attendance/student/{student_id}/summary     - Attendance % summary for a student
```

**Frontend Pages:**
```
/attendance                  - Daily attendance marking view (grid by class/section)
/attendance/history          - Historical view/filter by student or date range
```

---

### Module 4: Fees & Payments

**Description:** Fee structure definition, payment tracking via Razorpay, outstanding balance calculation, and email reminders to parents.

**Models:**
```
FeeStructure:
  - id, student_id (FK)
  - amount, frequency (monthly | term | one_time)
  - due_date
  - description
  - created_at, updated_at

Payment:
  - id, fee_structure_id (FK), student_id (FK)
  - amount_paid, payment_date
  - method (razorpay | cash | bank_transfer)
  - razorpay_payment_id, razorpay_order_id (nullable)
  - status (pending | completed | failed)
  - created_at

FeeReminder:
  - id, student_id (FK), fee_structure_id (FK)
  - sent_at, channel (email)
  - status (sent | failed)
```

**API Endpoints:**
```
GET    /api/fees/students/{student_id}         - Get fee structure + payment history + balance
POST   /api/fees                               - Create fee structure for a student
PUT    /api/fees/{id}                          - Update fee structure
POST   /api/payments/razorpay/order            - Create Razorpay order for a fee
POST   /api/payments/razorpay/webhook          - Razorpay payment webhook (verify + record payment)
GET    /api/payments/student/{student_id}      - List payment history
POST   /api/fees/{id}/remind                   - Manually trigger a fee reminder email
GET    /api/fees/overdue                       - List all overdue fees (for reminder job)
```

**Frontend Pages:**
```
/fees                    - Fee overview across all students (teacher view)
/fees/{student_id}       - Fee detail + payment history for one student
/fees/{student_id}/pay   - Payment page (Razorpay checkout) - parent view
```

---

### Module 5: Dashboard

**Description:** Overview and stats for the teacher/institute.

**Frontend Pages:**
- /dashboard - Attendance trends, fee collection stats, overdue fee count, recent activity
- /settings - User settings and preferences

---

### Module 6: Admin Panel

**Description:** Admin-only management interface (institute owner managing teacher accounts).

**API Endpoints:**
- GET /admin/users - List all users
- PUT /admin/users/{id} - Update user status/role
- GET /admin/stats - Platform statistics

**Frontend Pages:**
- /admin - Admin dashboard (protected, admin only)
- /admin/users - User management

---

## MVP SCOPE

### Must Have (MVP)
- [x] User registration and login (Email/Password + Google OAuth for teachers)
- [x] Parent read-only login (invited by teacher)
- [x] Student roster CRUD
- [x] Daily attendance marking + history
- [x] Fee structure setup + Razorpay payment collection
- [x] Email fee reminders for overdue payments
- [x] Basic dashboard with attendance/fee stats

### Nice to Have (Post-MVP)
- [ ] Google Classroom / Colab integration for course materials
- [ ] Assignments and test-taking
- [ ] Student feedback module
- [ ] SMS/WhatsApp reminders
- [ ] Per-subject/period attendance granularity

---

## ACCEPTANCE CRITERIA

### Authentication
- [ ] Teacher can register/login with email/password or Google OAuth
- [ ] Parent can register via invite link (read-only role) and login
- [ ] JWT tokens work correctly with refresh
- [ ] Protected routes redirect to login
- [ ] Role-based access: parents can only view their own child's data

### Students
- [ ] Teacher can create, view, edit, and deactivate students
- [ ] Teacher can invite a parent to link to a student
- [ ] Parent sees only their linked student(s)

### Attendance
- [ ] Teacher can mark attendance per student per day (present/absent/late)
- [ ] Attendance % summary is calculated correctly per student
- [ ] Parent can view their child's attendance history (read-only)

### Fees & Payments
- [ ] Teacher can define a fee structure per student
- [ ] Parent can pay via Razorpay checkout
- [ ] Payment status updates correctly via Razorpay webhook
- [ ] Overdue fees trigger an email reminder to the parent
- [ ] Outstanding balance is calculated correctly

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
- [x] CSRF protection for OAuth flow
- [x] Razorpay webhook signature verification

### Integrations
- [x] Email service for fee reminders and notifications
- [x] Razorpay for fee payments
- [ ] Google Classroom/Colab (post-MVP)

---

## AGENTS

> These agents build Abhyas in parallel:

| Agent | Role | Works On |
|-------|------|----------|
| DATABASE-AGENT | Creates all models and migrations | User, Student, AttendanceRecord, FeeStructure, Payment, FeeReminder |
| BACKEND-AGENT | Builds API endpoints and services | Auth, Students, Attendance, Fees, Payments (Razorpay), Reminders |
| FRONTEND-AGENT | Creates UI pages and components | Login/Register, Students, Attendance, Fees, Dashboard, Admin |
| DEVOPS-AGENT | Sets up Docker, CI/CD, environments | Infrastructure |
| TEST-AGENT | Writes unit and integration tests | All code |
| REVIEW-AGENT | Security and code quality audit | All code |

---

# READY?

```bash
/generate-prp INITIAL.md
```

Then:

```bash
/execute-prp PRPs/abhyas-prp.md
```

# Incremental Migration Plan: KDTechX Platform
**Document ID:** `MIG-KDTECHX-2026-01`  
**Date:** September 29, 2026  
**Architect:** Principal Software Architect  
**Objective:** Non-Destructive Cutover from React SPA to Premium Django Full-Stack  

---

## 1. Migration Strategy Principles

1. **Non-Destructive Evolution:** Never drop tables, wipe data, or alter existing column constraints without strict backwards compatibility.
2. **Dual-Stack Coexistence:** The existing Django REST Framework endpoints (`/api/*`) remain operational throughout the migration to ensure zero disruption to the active Vercel frontend.
3. **Additive Templating:** Build the Django Template layer incrementally inside `backend/templates/` and `backend/static/`.
4. **Verification-Driven Progress:** Each migration phase must be verified with browser tests, console audits, and database checks before advancing to the next phase.

---

## 2. Phase-by-Phase Migration Roadmap

```
PHASE 0: Comprehensive Audit & Baseline Documentation (Completed)
   │
   ▼
PHASE 1: Target Architecture & Design Foundation
   ├─► Configure Template Engine (`DIRS: [BASE_DIR / 'templates']`)
   ├─► Configure Static Pipeline (`BASE_DIR / 'static'`)
   └─► Build Design System CSS Tokens (`tokens.css`, `base.css`, `layout.css`)
   │
   ▼
PHASE 2: Core Layouts & Authentication Layer
   ├─► Base Shell (`base.html`, `base_admin.html`, `base_student.html`)
   ├─► Includes (`navbar.html`, `admin_sidebar.html`, `student_sidebar.html`, `footer.html`)
   ├─► Admin & Student Session Login Views (`/accounts/login/admin/`, `/accounts/login/student/`)
   └─► Role-Based Access Control Middleware & Decorators (`@admin_required`, `@student_required`)
   │
   ▼
PHASE 3: Public Landing Page & Common Shell
   ├─► High-Converting Tech Landing Page (`public/index.html`)
   └─► Dark/Light Theme Switching Engine (`theme.js`)
   │
   ▼
PHASE 4: Admin Workspace Migration
   ├─► Admin Executive Dashboard (`admin/dashboard.html`) with real-time aggregates
   ├─► Batch Management (`admin/batches/`)
   ├─► Student Management & Enrollment (`admin/students/`)
   ├─► Course Management & Curriculum Builder (`admin/courses/`, `admin/curriculum/`)
   ├─► Question Bank & Filterable Repository (`admin/questions/`)
   ├─► Excel Batch Importer with Pre-Validation (`admin/questions/import/`)
   ├─► Quiz Stepper Builder (`admin/quizzes/create/`)
   ├─► Quiz Monitoring & Detail Hub (`admin/quizzes/<id>/`)
   ├─► Cohort Results & Export (`admin/results/`)
   ├─► Chart.js Cohort Analytics (`admin/analytics/`)
   └─► Announcements & Audit Logs (`admin/announcements/`, `admin/audit/`)
   │
   ▼
PHASE 5: Student Workspace Migration
   ├─► Student Action-Oriented Dashboard (`student/dashboard.html`)
   ├─► My Courses & Curriculum Browser (`student/courses/`)
   ├─► Distraction-Free Exam Engine (`student/quiz/<id>/`)
   │     ├─ Server-Authoritative Timer
   │     ├─ Option Scrambling Decoder
   │     ├─ Local Persistence Safeguard
   │     └─ Anti-Cheat & Security Deterrent Listeners
   ├─► Comprehensive Result Breakdown (`student/results/<id>/`)
   ├─► Assessment History & Analytics (`student/history/`, `student/progress/`)
   └─► Student Profile & Password Management (`student/profile/`)
   │
   ▼
PHASE 6: Verification, Performance & Security Hardening
   ├─► Cross-Device & Responsive Viewport Audits (320px to 2560px)
   ├─► WCAG 2.1 AA Accessibility Pass
   ├─► WhiteNoise Asset Compression & Cache Headers
   └─► End-to-End Functional Test Suite (`tests/`)
   │
   ▼
PHASE 7: Production Cutover & Deployment Verification
   ├─► Render Web Service Single-Origin Deployment
   ├─► Smoke Testing in Production
   └─► Retirement of Vercel Frontend (Upon Final Approval)
```

---

## 3. Rollback Strategy

At every stage of the migration, rollback safety is guaranteed:
* **Code Rollback:** Since all Django template routes are mounted on distinct paths (`/` for landing, `/portal/admin/*`, `/portal/student/*`), existing `/api/*` endpoints remain untouched. A revert is as simple as a Git checkout of the `main` branch.
* **Database Rollback:** No existing columns are renamed or deleted. Any new indexes or columns added must be nullable or possess safe default values.
* **Presentation Rollback:** If any issue arises with the Django templates, traffic can immediately be redirected back to the Vercel SPA without database modifications.

---

## 4. Cutover Criteria (Zero-Defect Release Gate)

The cutover from Vercel to Render full-stack will occur only when:
1. All 17 Admin views and 8 Student views are fully functional in Django Templates.
2. Excel question import processes XLSX/CSV with row-level validation and zero errors.
3. Quiz engine executes randomized attempts, evaluates answers server-side, records security events, and calculates pass/fail status with 100% accuracy.
4. Mobile responsiveness is validated across small (375px), medium (768px), and large (1440px) viewports.
5. All automated backend tests pass (`python manage.py test`).

# System Architecture Document: Target Unified Full-Stack Architecture
## KDTechX Learning & Assessment Portal
**Version:** 2.0.0-ENTERPRISE  
**Engine:** Python 3.12+ / Django 5.1+ / PostgreSQL 16+ / Bootstrap 5.3 / Vanilla JS  
**Hosting Environment:** Render Unified Web Service  

---

## 1. Architectural Blueprint

The target architecture transitions the KDTechX platform from a decoupled SPA/API model to a cohesive, high-performance, server-rendered Django full-stack application. By unifying templates, forms, session security, and data access into a single runtime on Render, we eliminate cross-origin complexity, CORS latency, and client-side token vulnerabilities.

```
                           INTERNET / CLIENTS
             (Desktop, Laptop, Tablet, iOS Safari, Android Chrome)
                                    │
                                    │ HTTPS (TLS 1.3)
                                    ▼
       ┌─────────────────────────────────────────────────────────────┐
       │                   RENDER EDGE / REVERSE PROXY               │
       │                   SSL Termination, DDoS Filter              │
       └────────────────────────────┬────────────────────────────────┘
                                    │
                                    │ HTTP :$PORT
                                    ▼
       ┌─────────────────────────────────────────────────────────────┐
       │                  UNIFIED DJANGO APPLICATION                 │
       │                                                             │
       │   ┌──────────────────────────────────────────────────────┐  │
       │   │                PRESENTATION LAYER                    │  │
       │   │  - Django Templates (Jinja-style inheritance)        │  │
       │   │  - Semantic HTML5 + Vanilla JavaScript              │  │
       │   │  - Bootstrap 5.3 Grid + Custom KDTechX Tokens       │  │
       │   │  - WhiteNoise Compressed Static Asset Pipeline       │  │
       │   │  - Chart.js Responsive Analytics Canvas              │  │
       │   └──────────────────────────┬───────────────────────────┘  │
       │                              │                              │
       │   ┌──────────────────────────▼───────────────────────────┐  │
       │   │                APPLICATION CONTROLLERS               │  │
       │   │  - Django Views (Class-Based & Functional Views)     │  │
       │   │  - Django Forms & ModelForms with CSRF Tokens        │  │
       │   │  - Role Guards (`@admin_required`, `@student_guard`) │  │
       │   │  - Session Authentication (HttpOnly, Secure Cookies) │  │
       │   │  - REST Endpoints (DRF preserved for API consumers)  │  │
       │   └──────────────────────────┬───────────────────────────┘  │
       │                              │                              │
       │   ┌──────────────────────────▼───────────────────────────┐  │
       │   │                 DOMAIN & BUSINESS SERVICES           │  │
       │   │  - Quiz Engine & Server-Authoritative Evaluator      │  │
       │   │  - Question Scrambler & Snapshot Mapper              │  │
       │   │  - Excel/CSV Batch Ingestion & Validation Pipeline   │  │
       │   │  - Audit & Anti-Cheat Security Event Logger          │  │
       │   └──────────────────────────┬───────────────────────────┘  │
       │                              │                              │
       │   ┌──────────────────────────▼───────────────────────────┐  │
       │   │                 DATA ACCESS & ORM LAYER              │  │
       │   │  - Django ORM (select_related, prefetch_related)     │  │
       │   │  - Atomic Database Transactions                      │  │
       │   │  - Database Connection Pooling (conn_max_age=600)    │  │
       │   └──────────────────────────┬───────────────────────────┘  │
       └──────────────────────────────┼──────────────────────────────┘
                                      │
                                      │ TCP/SSL (Pooled)
                                      ▼
       ┌─────────────────────────────────────────────────────────────┐
       │                  DATA STORAGE / POSTGRESQL                  │
       │                   Managed PostgreSQL 16+                    │
       │          Source of Truth, ACID Enforced, Indexed            │
       └─────────────────────────────────────────────────────────────┘
```

---

## 2. Core Architectural Subsystems

### 2.1 Presentation & Design System
* **Templates:** Modular layout inheritance via `templates/base.html`, `templates/base_admin.html`, and `templates/base_student.html`.
* **CSS Architecture:** Vanilla CSS design tokens (`static/css/tokens.css`) defining the KDTechX enterprise dark/light color systems, typography scales, radius values, and elevation layers.
* **Component Framework:** Bootstrap 5.3 utilized strictly for responsive grid layouts and offcanvas navigation, completely styled with KDTechX tokens to prevent generic template appearances.
* **Client-Side Behavior:** Modular Vanilla JavaScript (`theme.js`, `quiz-engine.js`, `modals.js`, `charts.js`, `tables.js`) with zero heavy framework overhead.

### 2.2 Dual-Mode API & Server-Rendered Views
* **Server-Rendered Workspace Routes:**
  - `/` -> Public Landing Page
  - `/accounts/login/admin/` & `/accounts/login/student/` -> Role-partitioned authentication
  - `/portal/admin/*` -> Admin management hub (Courses, Students, Batches, Quizzes, Analytics)
  - `/portal/student/*` -> Student workspace (Courses, Assessment Engine, Results, History)
* **Preserved DRF REST APIs:** All existing `/api/*` endpoints remain intact, providing programmatic access and ensuring backwards compatibility during transition.

### 2.3 Assessment Engine Subsystem
* **Snapshot Architecture:** When an assessment is initiated, an atomic snapshot is constructed in `attempts_attemptquestion`, mapping scrambled option letters (A, B, C, D) to original question choices.
* **Server Authority:** The countdown timer, question presentation, answer submission, and scoring are validated strictly on the server. Client-submitted answers are evaluated against the persisted snapshot mapping with penalty deductions applied atomically.
* **Anti-Cheat Deterrents:** Browser-level listeners report window blur, tab switching, and fullscreen exit events to `/portal/student/quiz/<id>/security-event/`, logged in `audit_securityevent`.

---

## 3. Data Integrity & Concurrency

1. **Transactional Boundaries:** All multi-step operations (Quiz submission, Excel question importation, Student enrollment) execute within `@transaction.atomic()` blocks.
2. **Deterministic Evaluation:** Student scores are computed exclusively from database records. Pass/fail determinations, percentage calculations, and time tracking happen server-side upon submission.
3. **Query Optimization:** Strict avoidance of N+1 database queries through proactive use of `select_related()` (for foreign keys) and `prefetch_related()` (for reverse relations and many-to-many sets).

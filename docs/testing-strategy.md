# Quality Assurance & Testing Strategy
## KDTechX Learning & Assessment Portal
**Document ID:** `QA-KDTECHX-2026-01`  
**Standard:** Enterprise Zero-Defect Release Gate  
**Lead:** QA Automation & Performance Engineer  

---

## 1. Testing Framework & Philosophy

Quality assurance in KDTechX is continuous, multi-tiered, and evidence-driven. No release candidate is certified for production without passing the zero-known-critical-defect gate.

### Testing Pyramid
```
            ▲
           / \     End-to-End Workflow Verification (Simulated User Flows)
          /   \    Cross-Device Multi-Session Synchronization
         /─────\   Integration Tests (Views, Services, Forms, Auth Guards)
        /       \  Unit Tests (Evaluation Engine, Excel Handler, Models)
       /─────────\
```

---

## 2. Test Execution Domains

### 2.1 Backend Unit & Integration Tests
* **Model Integrity:** Validate constraints (unique student IDs, composite unique attempt numbers, foreign key cascades).
* **Evaluation Engine:**
  - Verify exact score calculation with positive marks.
  - Verify fractional penalty deductions when `negative_marking=True`.
  - Verify boundary clamping at `0.00` (scores never go negative).
  - Verify scrambled option mapping inversion (candidate selection translated accurately back to question choice).
* **Excel Importer:**
  - Test valid XLSX ingestion with 100% success.
  - Test malformed rows (missing question, invalid choice "E", negative marks) with row-level error reporting.
  - Test atomic rollback on corrupt upload files.
* **Authentication & Authorization:**
  - Anonymous user redirected to appropriate login screen.
  - Student user blocked from accessing `/portal/admin/*` (HTTP 403 or redirect).
  - Admin user granted access to dashboard, batches, courses, and questions.

### 2.2 End-to-End Workflow Test Sequence
The end-to-end verification validates the entire lifecycle in PostgreSQL:
1. **Admin Authentication:** Trainer logs in at `/accounts/login/admin/`.
2. **Cohort Provisioning:** Create Batch `B-2026-QA` and register Student `STU-QA-01`.
3. **Course & Curriculum Build:** Create Course `Full Stack Python`, Week 1, and Topic `Data Structures`.
4. **Question Bank & Ingestion:** Upload 10 questions via Excel and verify in Question Bank.
5. **Assessment Orchestration:** Create a 10-minute quiz linked to Week 1, set pass percentage to 60%, and publish.
6. **Enrollment:** Enroll Student `STU-QA-01` in the course.
7. **Student Experience:**
   - Student logs in at `/accounts/login/student/`.
   - Navigates to Course, opens Week 1 Assessment.
   - Starts exam, verifies timer initiation and distraction-free fullscreen.
   - Answers questions, navigates question numbers, and submits.
8. **Automated Evaluation & Feedback:**
   - Server evaluates submission, marks status `SUBMITTED`, sets score and pass/fail.
   - Student instantly views detailed score breakdown and review.
9. **Trainer Analytics Verification:**
   - Admin refreshes `/portal/admin/results/` and `/portal/admin/analytics/`.
   - Student submission appears in real-time with verified accuracy.

---

## 3. Responsive & Cross-Device Matrix

Every template view must be tested and validated across standard device breakpoints:
* **Mobile Small (320px - 375px):** iPhone SE, small Androids. Collapsible offcanvas navigation, single-column KPI cards, card-based tabular views.
* **Mobile Medium (390px - 414px):** iPhone 14/15/16 Pro, Samsung Galaxy.
* **Tablet (768px - 834px):** iPad Mini, iPad Air. Two-column grid, compact sidebar.
* **Desktop Laptop (1024px - 1440px):** MacBook Air/Pro, Windows laptop. Standard sidebar layout, sticky topbar.
* **Ultrawide & 4K (1920px - 2560px):** Max-width content containers (`1440px`) to prevent visual stretching.

---

## 4. Zero-Defect Release Gate Criteria

A deployment to production is **BLOCKED** if any of the following occur:
* [x] Any unhandled 500 server error on any view.
* [x] Any console JavaScript syntax error or unhandled promise rejection.
* [x] Broken CSRF token on any state-changing POST form.
* [x] Any scoring discrepancy between candidate answer and database evaluation.
* [x] Layout horizontal scrollbar overflow on mobile devices under 768px.
* [x] Hardcoded credentials or non-environment-driven secrets.

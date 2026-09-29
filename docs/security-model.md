# Application Security Model & Defense Architecture
## KDTechX Learning & Assessment Portal
**Document ID:** `SEC-KDTECHX-2026-01`  
**Standard:** OWASP Top 10 Enterprise Compliance  
**Auditor:** Application Security Engineer  

---

## 1. Authentication Architecture: Transitioning to Secure Sessions

### 1.1 Vulnerability of the Legacy JWT Model
In the decoupled React SPA architecture, JWT access and refresh tokens were stored in `localStorage`. This presented two major attack vectors:
1. **XSS Exfiltration:** Any injected client script or vulnerable npm package could extract the Bearer tokens and hijack sessions indefinitely.
2. **Revocation Latency:** Immediate revocation of an active JWT access token requires complex distributed token blacklisting.

### 1.2 The Django Enterprise Session Standard
The new full-stack Django architecture switches browser users to hardened HTTP session cookies:
* `SESSION_COOKIE_HTTPONLY = True`: Blocks all JavaScript access via `document.cookie`.
* `SESSION_COOKIE_SECURE = True`: Enforces transmission exclusively over TLS/HTTPS in production.
* `SESSION_COOKIE_SAMESITE = 'Lax'`: Mitigates Cross-Site Request Forgery (CSRF).
* `CSRF_COOKIE_HTTPONLY = False`: Allows safe CSRF token inspection where needed while securing the session cookie.
* Dual Support: SimpleJWT remains mounted on `/api/auth/` for backward compatibility with external headless clients, while the primary web portal operates on session authentication.

---

## 2. Server-Side Role-Based Access Control (RBAC)

Never rely on hidden UI buttons or client-side guards for authorization. The KDTechX backend enforces strict permission decorators and class mixins on every single route:

```python
# Core Authorization Decorators in apps.accounts.decorators
def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:admin_login')
        if not request.user.is_admin_user:
            messages.error(request, "Access denied. Trainer privileges required.")
            return redirect('student:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def student_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:student_login')
        if not request.user.is_student_user:
            return redirect('admin:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
```

### RBAC Matrix
| Capability | Admin / Trainer | Student / Candidate | Anonymous |
|---|---|---|---|
| Access Landing Page | Yes | Yes | Yes |
| View Admin Dashboard | **Yes** | No (Redirect / 403) | No (Redirect) |
| Manage Courses & Batches | **Yes** | No | No |
| Upload Excel Questions | **Yes** | No | No |
| Create / Edit Quizzes | **Yes** | No | No |
| View Any Student Results | **Yes** | No | No |
| View Own Course Curriculum | Yes | **Yes** | No |
| Take Enrolled Assessment | No | **Yes** (If enrolled & open) | No |
| View Own Results & History | Yes | **Yes** | No |

---

## 3. Assessment Integrity & Anti-Cheat Subsystem

### 3.1 Server Authority Over Quiz State
* **Timer Enforcement:** The expiration deadline (`deadline_at`) is persisted in the database at quiz start. Client-side timers are purely cosmetic for candidate awareness; any submission received after `deadline_at + 15s grace period` is marked as `TIMED_OUT`.
* **Zero Answers Exposed:** The candidate's browser receives only question text and options A/B/C/D. Correct answers and explanations are never serialized to the client during an active attempt.
* **Option Scrambling:** Options are shuffled per student and mapped in `AttemptQuestion.option_mapping`. Even if two students sit next to each other, Option A on one screen is Option C on the other.

### 3.2 Browser Deterrents & Telemetry
While acknowledging that 100% client isolation is impossible in modern browsers, KDTechX deploys a multi-layered deterrent suite:
1. **Fullscreen Enforcement:** Quiz opens in distraction-free fullscreen. Exiting triggers a warning modal and dispatches a telemetry payload.
2. **Tab Switch & Visibility Detection:** Utilizing `document.visibilityState` and `window.onblur`, every unfocus event logs a `TAB_SWITCH` record in `audit_securityevent`.
3. **Clipboard Shield:** Right-click context menus (`contextmenu`), text copy (`copy`), cut (`cut`), and paste (`paste`) events are intercepted and blocked with user notifications.
4. **Auto-Submission Threshold:** If `attempt.tab_violations >= quiz.tab_warning_limit`, the server flags the attempt and can auto-submit the exam upon the next infraction.

---

## 4. Excel/CSV File Upload Security

1. **Format Validation:** Accept only `.xlsx` and `.csv` extensions with verified MIME types.
2. **Size Enforcement:** Maximum upload size hard-capped at 5MB.
3. **In-Memory Parsing:** Openpyxl and Python `csv` parse streams in memory without writing unverified user files to the filesystem.
4. **Content Sanitization:** Every row is validated for required columns (`question`, `optiona`, `optionb`, `optionc`, `optiond`, `answer`), valid answer choices (`A`, `B`, `C`, `D`), and difficulty levels (`easy`, `medium`, `hard`). Malicious formulas (e.g. leading `=`, `+`, `@`) are stripped to prevent CSV Injection.
5. **Atomic Ingestion:** Ingestion occurs inside `transaction.atomic()`. If validation fails, zero partial questions are committed.

---

## 5. Defense Against Common Web Vulnerabilities

* **CSRF Protection:** Every state-changing HTML form includes `{% csrf_token %}` checked by Django's `CsrfViewMiddleware`.
* **SQL Injection:** Exclusively utilize the Django ORM parameterized queries. Never invoke `raw()` with unsanitized format strings.
* **XSS Defense:** Django's auto-escaping is active across all template files. User-generated text (student names, forum posts, question text) is escaped automatically.
* **Clickjacking:** `XFrameOptionsMiddleware` sets `X-Frame-Options: DENY` globally.
* **Password Storage:** Uses PBKDF2 with SHA-256 and salt rounds conforming to OWASP recommendations. Passwords are never logged or transmitted in cleartext.

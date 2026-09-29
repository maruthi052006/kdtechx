# Production Deployment & Infrastructure Plan
## KDTechX Learning & Assessment Portal
**Document ID:** `DEP-KDTECHX-2026-01`  
**Target Platform:** Render Cloud Application Platform  
**Architecture:** Single-Origin Unified Full-Stack Service  

---

## 1. Production Architecture Overview

The target production infrastructure hosts the entire KDTechX portal on a unified Render Web Service backed by Render Managed PostgreSQL. This eliminates cross-origin latency, CORS configuration fragility, and secondary frontend host costs.

```
                      INCOMING TRAFFIC (HTTPS)
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   RENDER CLOUD EDGE   │
                     │  Auto SSL / TLS 1.3   │
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   GUNICORN (WSGI)     │
                     │  4 Worker Processes   │
                     └───────────┬───────────┘
                                 │
                ┌────────────────┴────────────────┐
                ▼                                 ▼
      ┌──────────────────┐              ┌──────────────────┐
      │    WHITENOISE    │              │  DJANGO 5.1 APP  │
      │ Static Assets    │              │ Full-Stack Views │
      │ Compressed / CDN │              │ & REST APIs      │
      └──────────────────┘              └─────────┬────────┘
                                                  │
                                                  │ Connection Pool
                                                  ▼
                                        ┌──────────────────┐
                                        │    POSTGRESQL    │
                                        │ Managed Instance │
                                        └──────────────────┘
```

---

## 2. Render Blueprint Specification (`render.yaml`)

```yaml
services:
  - type: web
    name: kdtechplatform-web
    env: python
    region: oregon
    plan: starter
    branch: main
    buildCommand: |
      pip install -r backend/requirements.txt
      python backend/manage.py collectstatic --no-input
      python backend/manage.py migrate
    startCommand: gunicorn config.wsgi:application --chdir backend --bind 0.0.0.0:$PORT --workers 4 --threads 2 --timeout 60
    healthCheckPath: /api/health/
    envVars:
      - key: DJANGO_SETTINGS_MODULE
        value: config.settings.production
      - key: PYTHON_VERSION
        value: 3.12.3
      - key: DEBUG
        value: "False"
      - key: SECRET_KEY
        generateValue: true
      - key: ALLOWED_HOSTS
        value: ".onrender.com,localhost,127.0.0.1"
      - key: DATABASE_URL
        fromDatabase:
          name: kdtechplatform-postgres
          property: connectionString
      - key: CSRF_TRUSTED_ORIGINS
        value: "https://*.onrender.com"

databases:
  - name: kdtechplatform-postgres
    plan: starter
    region: oregon
    postgresMajorVersion: "16"
```

---

## 3. Production Environment Variables Reference

| Variable | Required | Description | Example / Production Value |
|---|---|---|---|
| `DJANGO_SETTINGS_MODULE` | Yes | Django settings module | `config.settings.production` |
| `DEBUG` | Yes | Debug mode switch | `False` |
| `SECRET_KEY` | Yes | Cryptographic signing key | High-entropy 50+ character string |
| `ALLOWED_HOSTS` | Yes | Comma-delimited valid hosts | `.onrender.com,kdtechplatform.com` |
| `DATABASE_URL` | Yes | PostgreSQL connection URI | `postgres://user:pass@host:5432/dbname` |
| `CSRF_TRUSTED_ORIGINS`| Yes | Trusted origins for CSRF | `https://*.onrender.com` |
| `SECURE_SSL_REDIRECT` | Yes | Force HTTPS redirect | `True` |

---

## 4. Static Asset Delivery Pipeline

* **Engine:** WhiteNoise (`CompressedManifestStaticFilesStorage`)
* **Pipeline Execution:** `python manage.py collectstatic --no-input` compiles all CSS, Vanilla JS, and media assets into `backend/staticfiles/` during the build phase.
* **Cache Headers:** WhiteNoise automatically appends unique content hashes to filenames and injects long-lived immutable cache-control headers (`max-age=31536000, immutable`), ensuring instantaneous repeat-visit loads.

---

## 5. System Health Check Endpoint

* **Endpoint:** `GET /api/health/`
* **Response:**
  ```json
  {
    "status": "ok",
    "database": "ok",
    "timestamp": "2026-09-29T10:30:00Z"
  }
  ```
* **Failure Trigger:** If database connectivity drops or migrations fail, the health check returns HTTP 503, preventing Render from routing traffic to an unhealthy container.

---

## 6. Vercel Cutover & Retirement Protocol

1. **Step 1:** Complete and verify all Django Templates views on the Render web service.
2. **Step 2:** Conduct thorough end-to-end testing across Admin and Student workflows.
3. **Step 3:** Update DNS records or primary links to point to the unified Render web service.
4. **Step 4:** Once confirmed operational and approved by the team, the legacy Vercel frontend deployment may be safely archived or redirected.

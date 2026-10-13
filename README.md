# FarmConnect (விவசாய இணைப்பு)

> **Empowering farmers with seamless, localized agricultural machinery rental services.**

FarmConnect is a responsive, bilingual (English & Tamil) web platform designed to bridge the gap between rural farmers and agricultural equipment owners. Smallholder farmers can discover, evaluate, and book nearby tractors, harvesters, tillers, and sprayers with flexible packages, transparent pricing, and direct communication.

---

## 📚 Core Architecture Documents

- **[PROJECT_PLAN.md](PROJECT_PLAN.md)**: Comprehensive architectural plan, user roles, API specifications, security protocols, and Phase 1 MVP implementation milestones.
- **[DATABASE_ER_DIAGRAM.md](DATABASE_ER_DIAGRAM.md)**: Mermaid Entity Relationship Diagram (ERD), table schemas, PostgreSQL exclusion constraints, and index designs.

---

## 🚜 Key Features (Phase 1 MVP)

1. **Bilingual User Interface**:
   - Complete Tamil (`ta`) and English (`en`) localized experience with one-click toggling and persisted preference.
2. **Three Flexible Machinery Rental Options**:
   - `MACHINE_ONLY`: Machine rental without personnel.
   - `MACHINE_OPERATOR`: Machine rental including a skilled operator.
   - `MACHINE_OPERATOR_LABOUR`: Machine rental including an operator and supplementary farm field labourers.
3. **Dual Location Discovery**:
   - **Manual Search**: Administrative lookup by Village/Town, District, or PIN code.
   - **GPS Nearby Search**: Optional browser geolocation with explicit user permission.
4. **Six-State Booking Lifecycle & Double-Booking Protection**:
   - Explicit lifecycle: `PENDING` &rarr; `APPROVED` &rarr; `IN_PROGRESS` &rarr; `COMPLETED`, plus terminal states `REJECTED` and `CANCELLED`.
   - Guaranteed overlapping booking prevention at the database layer via PostgreSQL `EXCLUDE USING gist` with the `btree_gist` extension and application row-level locking.
5. **Direct Farmer-Provider Communication**:
   - Telephonic click-to-call button using verified provider phone numbers.
   - Optional WhatsApp direct-chat button enabled only with explicit provider consent.
6. **Support & Governance**:
   - Public "Contact Us" form with admin inquiry triage and audit tracking.
   - Provider dashboard and administrative metrics.

---

## 🛠️ Technology Stack

| Layer | Component | Notes |
| :--- | :--- | :--- |
| **Frontend** | HTML5, Vanilla CSS, Vanilla JavaScript | High performance on low-bandwidth rural connections; custom earthy agricultural design system. |
| **Backend** | Python Flask (v3.x) | Application Factory pattern (`create_app`) with modular Blueprints. |
| **Database** | PostgreSQL | Relational integrity, ACID compliance, and native `tsrange` exclusion constraints. |
| **ORM & Migrations** | Flask-SQLAlchemy & Flask-Migrate (Alembic) | Pythonic models and reversible schema migrations. |
| **Authentication** | Mobile Phone OTP via SMS | Session cookies (`HttpOnly`, `SameSite=Lax`); mock OTP strictly isolated to local development. |
| **Version Control** | Git & GitHub | Environment secrets protected via `.env` and `.gitignore`. |

---

## ⚙️ Local Development Setup Guide

### 1. Prerequisites
- **Python 3.10+**
- **PostgreSQL 14+**
- **Git**

### 2. Clone and Setup Environment
```bash
# Navigate to project directory
cd farm-connect

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Windows (cmd):
.\venv\Scripts\activate.bat
# On Linux/macOS:
source venv/bin/activate

# Install dependencies (when requirements.txt is provided)
pip install -r requirements.txt
```

### 3. Database Configuration
1. Open PostgreSQL (`psql` or pgAdmin) and create a database:
   ```sql
   CREATE DATABASE farmconnect_db;
   \c farmconnect_db
   CREATE EXTENSION IF NOT EXISTS btree_gist;
   ```
2. Copy the sample environment template:
   ```bash
   cp .env.example .env
   ```
3. Update `.env` with your database credentials:
   ```ini
   FLASK_APP=run.py
   APP_ENV=development
   FLASK_DEBUG=1
   SECRET_KEY=your-dev-secret-key-change-in-production
   DATABASE_URL=postgresql://postgres:your_password@localhost:5432/farmconnect_db
   MOCK_OTP_ENABLED=True
   ```

### 4. Database Migrations
Initialize and apply the database schema migrations:
```bash
flask --app run.py db upgrade
```

### 5. Run the Local Development Server
```bash
flask --app run.py run --host=127.0.0.1 --port=5000 --debug
```
Access the application at `http://127.0.0.1:5000`.

### 6. Obtaining the Mock OTP in Local Development
When registering or signing in via phone in local development (`APP_ENV=development` & `MOCK_OTP_ENABLED=True`):
1. Enter your 10-digit mobile number on the web interface.
2. Check your active Flask server terminal / console.
3. You will see an explicit OTP banner:
   ```text
   ======================================================================
   [DEV MOCK SMS] Phone: +919876543210 | OTP: 123456 | Expires in: 5m
   ======================================================================
   ```
4. Enter this 6-digit code on the phone verification page to authenticate.
*Note: OTP codes are never displayed in the browser, flash messages, or network responses.*

### 7. Run Automated Tests
```bash
pytest -v
```

---

## 🔒 Security & Mock OTP Isolation

- **Environment Configuration (`APP_ENV`)**:
  - Flask 3.x does not support `FLASK_ENV`. The application uses an explicit `APP_ENV` configuration (`development`, `testing`, `production`).
  - The application factory explicitly validates the environment on startup and strictly rejects `MOCK_OTP_ENABLED=True` when `APP_ENV=production`, raising a fatal `RuntimeError`.
- **Local Development Mode**:
  - When `APP_ENV=development` and `MOCK_OTP_ENABLED=True`, generated 6-digit OTP codes are logged **strictly to the local server console/terminal** for effortless testing.
  - Mock OTP codes are **never** returned in API JSON response bodies.
- **Production Mode**:
  - In production (`APP_ENV=production`), `MOCK_OTP_ENABLED` is strictly rejected during application startup.
  - If the external SMS provider is unavailable, the service safely fails with HTTP 503 instead of falling back to mock authentication.
- **Credentials & Secrets**:
  - `.env` is strictly ignored by `.gitignore`.
  - Passwords (admin accounts) are hashed using `scrypt` or `pbkdf2:sha256`; plaintext passwords are never stored or logged.

---

## 🗺️ Product Roadmap

```
+---------------------------------------------------------------------------------+
| Project Roadmap                                                                 |
+---------------------------------------------------------------------------------+
| Phase 1 (Active MVP): Machinery Rental Core, Bilingual UI, Manual & GPS Search  |
| Phase 2: Star Ratings, Farmer Reviews & Push Notifications                      |
| Phase 3: Farm Labour Profiles & Crew Booking                                    |
| Phase 4: AnimalConnect (Livestock Marketplace for Cattle, Goats & Sheep)        |
| Phase 5: Digital Finance, UPI/NetBanking Escrow & Security Deposits             |
+---------------------------------------------------------------------------------+
```

---

## 📄 License
FarmConnect is developed for agricultural community empowerment. All rights reserved.

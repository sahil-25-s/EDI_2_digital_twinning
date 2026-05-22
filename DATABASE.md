# PostgreSQL setup for EDI Digital Twinning

## 1. Set your connection URL

Edit `env_files/.env`:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/edi_digital_twin
```

Use the same username/password you use in pgAdmin.

## 2. Create the database

**Option A — Python script (from project root):**

```powershell
pip install -r requirements.txt
python scripts/create_database.py
```

**Option B — pgAdmin:** open Query Tool on the `postgres` database and run `scripts/init_db.sql`.

## 3. Create tables (migrations)

```powershell
$env:FLASK_APP = "app.py"
flask db init
flask db migrate -m "Initial user and simulation tables"
flask db upgrade
```

(`flask db init` only once; skip if `migrations/` already exists.)

## 4. Verify

```powershell
python app.py
```

Visit: http://127.0.0.1:5000/db-health — should return `{"database": "ok"}`.

If you already ran `001_initial` before `name` was added:

```powershell
python -m flask db upgrade
```

(applies `002_add_user_name`).

## 5. Auth

- Register: http://127.0.0.1:5000/register (saves user + profile + clinical + habits)
- Login: http://127.0.0.1:5000/login
- Digital twin: http://127.0.0.1:5000/twin (requires login)

## Tables

| Table | Purpose |
|-------|---------|
| `users` | Login (email, password_hash) — for future auth |
| `user_profiles` | Static lifestyle: age, BMI, diet, exercise, etc. |
| `user_clinical_baselines` | Labs, symptoms, symptom flags |
| `user_daily_habits` | Default daily calories, sleep, water, micronutrients |
| `simulation_runs` | Each twin run: diagnosis, symptoms, JSON state, Gemini text |

Simulations are saved automatically when `DATABASE_URL` is set (`simulation_run_id` in API response).

# Deploying to cPanel via Git

This guide covers the full deployment of this Flask app on a cPanel host using cPanel's **Git Version Control** and **Setup Python App** features.

---

## Prerequisites

- cPanel hosting with Python support (Passenger/WSGI)
- SSH access enabled on your cPanel account
- This repo pushed to GitHub (or any remote Git host)
- A MySQL database already created in cPanel

---

## Step 1 — Create the Database Tables

In cPanel → **phpMyAdmin**, select your database and run:

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

---

## Step 2 — Clone the Repo via cPanel Git Version Control

1. In cPanel → **Git Version Control** → click **Create**
2. Toggle **Clone a Repository**
3. Fill in:
   - **Clone URL**: your GitHub repo URL (e.g. `https://github.com/youruser/yourrepo.git`)
   - **Repository Path**: the directory where the app will live, e.g. `/home/yourusername/flask_backend`
4. Click **Create** — cPanel will clone the repo

> If the repo is private, use an HTTPS URL with a personal access token:
> `https://<token>@github.com/youruser/yourrepo.git`

---

## Step 3 — Set Up the Python App

1. In cPanel → **Setup Python App** → click **Create Application**
2. Fill in:
   - **Python version**: 3.x (choose the highest available)
   - **Application root**: same path you used above (e.g. `flask_backend`)
   - **Application URL**: the domain or subdomain for the API
   - **Application startup file**: `app.py`
   - **Application Entry point**: `application`
3. Click **Create** — cPanel creates a virtualenv and generates a Passenger config

> `application = app` is already set in `app.py` — this is what Passenger looks for.

---

## Step 4 — Install Dependencies

After creating the Python app, cPanel shows a command to activate the app's virtualenv. Copy and run it via **cPanel Terminal** (or SSH):

```bash
source /home/yourusername/virtualenv/flask_backend/3.x/bin/activate && cd /home/yourusername/flask_backend
```

Then install dependencies:

```bash
pip install -r requirements.txt
```

---

## Step 5 — Set Environment Variables

In **Setup Python App** → click your app → scroll to **Environment Variables**, then add each one:

| Key | Value |
|-----|-------|
| `DB_HOST` | `localhost` |
| `DB_PORT` | `3306` |
| `DB_NAME` | your cPanel database name |
| `DB_USER` | your cPanel database user |
| `DB_PASSWORD` | your database password |
| `ADMIN_API_KEY` | a strong secret key for admin endpoints |
| `CORS_ORIGINS` | `https://yourdomain.com` (or `*` to allow all) |

Click **Save** after adding all variables.

> Do NOT set `PORT` — cPanel manages the port automatically.

---

## Step 6 — Restart the App

In **Setup Python App** → click **Restart** next to your app. The API should now be live at your configured URL.

Verify with:
```
GET https://yourdomain.com/health
→ {"status": "ok"}
```

---

## Step 7 — Create the First Admin User

On your local machine, edit `create_admin.py` with the desired admin username and password, then run:

```bash
python create_admin.py
```

Copy the printed SQL `INSERT` statement and run it in **phpMyAdmin → SQL tab**.

---

## Updating the App (Git Pull)

When you push new changes to GitHub:

1. In cPanel → **Git Version Control** → find your repo → click **Manage**
2. Click **Update from Remote** (this runs `git pull`)
3. Go to **Setup Python App** → click **Restart**

Or via SSH/Terminal:

```bash
cd /home/yourusername/flask_backend
git pull origin main
```

Then restart the app from **Setup Python App**.

---

## Troubleshooting

**CORS preflight errors (OPTIONS blocked)**
The `.htaccess` file in the repo handles this. If you're still seeing CORS errors, confirm the file was pulled and that `mod_rewrite` is enabled on the host.

**500 errors on startup**
Check the error log: cPanel → **Errors** or look in `~/logs/`. Usually caused by missing env vars or failed pip install.

**App not restarting after git pull**
Passenger serves the old process until restarted. Always click **Restart** in Setup Python App after pulling changes, or touch the restart file:
```bash
touch /home/yourusername/flask_backend/tmp/restart.txt
```
(Create the `tmp/` directory first if it doesn't exist.)

**Dependencies not found after pull**
New packages in `requirements.txt` won't install automatically. After pulling, re-run `pip install -r requirements.txt` from within the activated virtualenv.

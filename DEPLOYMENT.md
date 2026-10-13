# Charlady – Deployment steps (Render)

## 1. Commit and push your code

```powershell
cd c:\Users\USER\Desktop\omega-main\omega-main
git add .
git commit -m "Ready for deployment"
git push origin main
```
(Use your real branch name if it’s not `main`.)

---

## 2. Set environment variables on Render

In your **Render web service** → **Environment** tab.

Add these (required):

| Variable        | Value / Notes |
|----------------|---------------|
| `DATABASE_URL` | Your Postgres URL (from the Postgres service; use “Add variable reference” or paste the URL). |
| `SECRET_KEY`   | A long random string, e.g. from: `python -c "import secrets; print(secrets.token_urlsafe(50))"` |

Optional (for full functionality):

| Variable             | Purpose |
|---------------------|---------|
| `DEBUG`             | Set to `False` in production. |
| `EMAIL_HOST_USER`   | Gmail (or SMTP) address for sending emails. |
| `EMAIL_HOST_PASSWORD` | App password for that email. |
| `MPESA_TILL_NUMBER` | If you use M-Pesa; defaults in code if not set. |

Save; Render will redeploy if needed.

---

## 3. Build and run (Render)

- **Build:** Render uses `./build.sh`, which installs dependencies and runs migrations.
- **Release (if using Procfile):** `release` runs:  
  `python manage.py migrate && python manage.py collectstatic --noinput`
- **Start:** Either:
  - **Procfile:** `web: gunicorn housekeeper_connect.wsgi:application --bind 0.0.0.0:$PORT`
  - **Nixpacks:** `python manage.py migrate --noinput && gunicorn ... --bind 0.0.0.0:$PORT`

No extra step needed if one of these is active.

---

## 4. Create admin user on production (one-time)

If you haven’t already created a superuser **on the Render/Postgres database**:

**Option A – Render shell (if available)**
Open a shell for your app and run:

```bash
python manage.py createsuperuser
```
Enter username, email, **phone number** (unique), and password.

**Option B – One-off run**  
In Render, run a one-off command:

```bash
python manage.py createsuperuser --noinput --username Admin --email your@email.com
```
Then set the password:

```bash
python manage.py shell -c "from accounts.models import CustomUser; u=CustomUser.objects.get(username='Admin'); u.set_password('YourSecurePassword'); u.save()"
```
(Or use `createsuperuser` interactively in a shell if your platform supports it.)

---

## 5. After deploy

1. Open your Render service URL.
2. Test: home, signup, login, admin (`/admin/`).
3. If you use a custom domain, add it in Render and set DNS as instructed.

---

## Quick checklist

- [ ] Code pushed to the branch Render deploys from
- [ ] `DATABASE_URL` set (Postgres)
- [ ] `SECRET_KEY` set
- [ ] `DEBUG=False` in production
- [ ] Migrations run (automatic via release or start command)
- [ ] Superuser created on production DB (one-time)
- [ ] Admin and main site tested

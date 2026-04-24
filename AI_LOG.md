# AI Usage Log

This file records meaningful uses of AI tooling (GitHub Copilot, Claude, etc.) during
the Database App with Django assignment. For each entry:

- **Prompt** — what I asked the AI to do
- **Result** — what the AI produced
- **My changes** — what I edited after reviewing
- **Verification** — how I confirmed it worked

---

## Mission 1: Project setup

No AI assistance needed for this mission — it was GitHub repo creation, cloning the
template, and editing the starter `index.html` headline.

---

## Mission 3: Connect Django to Supabase

### Configuring `settings.py` to read `DATABASE_URL`

**Prompt:** Asked Claude to update `settings.py` so Django reads its PostgreSQL
connection from a `DATABASE_URL` environment variable (stored as a GitHub
Codespaces secret in production, and as a Windows User-scope env var locally),
without hard-coding any credentials in the repo. Also asked it to identify the
Python packages needed and update `requirements.txt`.

**Result:** Claude:
- Added `psycopg[binary]~=3.3` and `dj-database-url~=3.1` to `requirements.txt`.
- Imported `dj_database_url` in `settings.py`.
- Replaced the hard-coded SQLite `DATABASES` dict with
  `dj_database_url.config(default="sqlite:///...", conn_max_age=600, conn_health_checks=True)`,
  so the env var is the primary source and SQLite is only a fallback.
- Added a comment block above `DATABASES` documenting that `DATABASE_URL` is a
  secret and is never stored in the repo.

**My changes:** Kept Claude's structure as-is — the SQLite fallback is useful so the
project doesn't completely break in environments where the secret isn't set.

**Verification:**
1. Ran `python manage.py check --database default` — passed.
2. Ran a raw psycopg connection test against the `patient` table — got
   `CONNECTED -- patient count: 60`, matching the row counts seen in Supabase
   after Mission 2.
3. Ran `python manage.py migrate` — Django created its `auth_*`,
   `django_admin_log`, `django_content_type`, and `django_session` tables in
   Supabase (visible in the Supabase Table Editor).
4. Ran `python manage.py createsuperuser` and confirmed I can log into `/admin/`.

### Debugging the `DATABASE_URL` connection (encoding / placeholder issues)

**Prompt:** When Django couldn't parse the `DATABASE_URL`, asked Claude to help
diagnose what was wrong without me pasting the connection string into chat.

**Result:** Claude wrote PowerShell + Python diagnostic snippets that read the env
var, counted structural characters (`@`, `:`, `/`), and printed a non-alphanumeric
"mask" of the password — enough to debug encoding issues without exposing the
password itself. It identified two problems:
1. The literal `[` / `]` from Supabase's `[YOUR-PASSWORD]` placeholder were
   accidentally left in the URL — they're placeholder syntax that must be removed.
   (Verified against Supabase's official docs.)
2. Special characters (`!`, `@`, `#`, `$`, `%`) needed percent-encoding for the
   URL parser.

**My changes:** After several rounds of manual percent-encoding still failing
authentication, I just reset the Supabase database password to alphanumeric only.
Way faster than continuing to chase encoding bugs.

**Verification:** After the password reset and updating both `DATABASE_URL`
locations (Windows User env var + GitHub Codespaces secret), the psycopg
connection test succeeded and migrations ran cleanly.

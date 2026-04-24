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

---

## Mission 4: Generate models with `inspectdb`

**Prompt:** Asked Claude to (1) create the `mythical_mane` Django app, (2) add it
to `INSTALLED_APPS`, (3) run `python manage.py inspectdb > mythical_mane/models.py`,
and (4) review and explain the generated models.

**Result:** Claude scaffolded the app, registered it, and ran `inspectdb`. The
generated file had 307 lines and included 25 model classes — but ~10 of those
were Django's own internal tables (`AuthGroup`, `AuthUser`, `AuthPermission`,
`AuthUserGroups`, `AuthUserUserPermissions`, `AuthGroupPermissions`,
`DjangoAdminLog`, `DjangoContentType`, `DjangoMigrations`, `DjangoSession`),
which Django already defines through `django.contrib.auth`,
`django.contrib.admin`, `django.contrib.contenttypes`, and
`django.contrib.sessions`. Having those duplicated in our app would be confusing
and serve no purpose.

Claude also explained the `managed = False` lines: every Mythical Mane table was
created by `mm-schema.sql` directly in Supabase, so Django shouldn't try to
create or alter them. Flipping `managed = True` would make Django attempt to
take ownership and would break things.

**My changes:**
- Removed all 10 Django-internal model classes — kept only the 15 Mythical Mane
  domain models (Ability, Diagnosis, Employee, Invoice, LineItem, Observation,
  Owner, Patient, PatientAbility, Payment, ProcedureDefinition, Universe, Visit,
  VisitDiagnosis, VisitProcedure).
- Added a header comment explaining what was trimmed and why `managed = False`
  must be preserved.
- Added `__str__` methods on the user-facing models (Patient, Owner, Universe,
  Employee, Diagnosis, ProcedureDefinition, Visit, Ability) so the admin and
  shell show readable labels instead of `<Patient: Patient object (1)>`.
- Added `verbose_name_plural` for models whose default plural form is wrong
  ("Diagnosises", "Visit diagnosises", etc.).

**Verification:**
- `python manage.py check` → no issues.
- ORM smoke test: `Patient.objects.count()` returned 60, matching what Supabase
  showed in Mission 2 (also Owner=36, Universe=3, Employee=10, Visit=120).
- Pulled three sample patients via
  `Patient.objects.select_related('owner', 'universe')[:3]` and got real
  Mythical Mane data: Phoenix 001 (Ember) owned by Ariadne Mooncrest 01 in
  Olympus Court, etc.

---

## Mission 5: Register models with Django admin

**Prompt:** Asked Claude to register all the Mythical Mane models in
`mythical_mane/admin.py` with useful `list_display`, `search_fields`,
`list_filter`, and `date_hierarchy` settings, and to explain its assumptions.

**Result:** Claude registered all 15 domain models (the assignment only requires
seven — Universe, Owner, Patient, Employee, Visit, Diagnosis,
ProcedureDefinition — but registering them all gives a complete admin). For each
model it picked:
- `list_display` — primary key plus the few columns most useful for scanning
  the change list at a glance.
- `search_fields` — text columns plus traversal into FK names (e.g. on Patient,
  `"owner__name"` so I can search for a patient by their owner's name).
- `list_filter` — low-cardinality columns like Patient's `universe`, Employee's
  `job_role`, Invoice's `status`, etc.
- `date_hierarchy` — wherever there's a meaningful timeline (Patient.dob,
  Employee.hire_date, Visit.start_at, Invoice.issue_date, Payment.payment_date,
  VisitProcedure.performed_at, VisitDiagnosis.recorded_at).
- `list_select_related` — on models with FKs that show up in `list_display`,
  so the change-list page doesn't fire one extra query per row.
- `raw_id_fields` — on FKs to large tables (Visit's patient/vet, line items'
  invoice/visit_procedure) to avoid Django rendering a giant `<select>`.

**My changes:** Accepted the structure as-is — it's exactly what the assignment
asks for. No edits.

**Verification:**
- `python manage.py check` → no issues, all admin classes registered cleanly.
- The next visual verification (logging into `/admin/` and confirming each model
  is listed, then editing a record and seeing the change in Supabase) happens
  when the Django dev server is run in the Codespace.

---

## Mission 6: Patient list page

**Prompt:** Asked Claude to build the `/patients/` page end-to-end: view, URL
route, and Tailwind-styled template that lists patients with their owner and
universe. Specifically asked it to use `select_related` so the page doesn't fire
one query per patient.

**Result:** Claude produced:
- `mythical_mane/views.py::patient_list` — a function-based view that queries
  `Patient.objects.select_related("owner", "universe").order_by("universe__name", "name")`,
  passes the queryset and a `patient_count` to the template.
- `mythical_mane/urls.py` — defines the `/patients/` route with namespace
  `mythical_mane`.
- `hello_world/urls.py` — `include("mythical_mane.urls")` mounted at the root.
- `mythical_mane/templates/mythical_mane/patient_list.html` — Tailwind via CDN
  (per the assignment's note that CDN is fine), responsive table with name,
  color, date of birth, owner, and universe; styled badges for the universe and
  patient count; em-dash fallbacks for blank colors and "unknown" for blank DOBs.

**My changes:** Accepted Claude's structure. Touched up minor things — used
`order_by("universe__name", "name")` so universes group together visually, and
made the empty-state message a dashed-border card rather than just a paragraph.

**Verification:** Wrote a script that called the view directly via Django's
`RequestFactory` and counted SQL queries through `connection.queries`:
- HTTP status: 200
- Response length: 70 KB
- **Total queries: 2** (one `COUNT(*)` for the header badge, one big SELECT
  with the JOIN). Definitely no N+1 — without `select_related` this would be 61
  queries for 60 patients.
- Page contains the "60 patients" badge text and the Tailwind CDN script tag.
- Confirmed the page survives missing `dob` (template uses `{% if patient.dob %}`
  with an "unknown" italic fallback).

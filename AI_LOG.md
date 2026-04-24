# AI Usage Log

This file records meaningful uses of AI tooling during the Database App with
Django assignment. My primary AI tool was Claude (acting as a coding partner /
guide). The workflow was collaborative throughout — I asked Claude to draft
code or explain options, I reviewed every change, I pushed back when something
looked wrong (and made Claude verify against documentation rather than guess),
and I made the final calls on design and configuration. Nothing landed in the
repo without me reading it first.

For each entry below:

- **Prompt** — what I asked the AI to do
- **Result** — what code or explanation it produced
- **My changes** — what I edited, decided differently, or pushed back on after
  reviewing
- **Verification** — how I confirmed it actually worked (commands run, things I
  clicked, what I checked in Supabase / the browser)

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

**Prompt:** When Django couldn't parse the `DATABASE_URL` (it threw a
`dj_database_url.ParseError`), I asked Claude to help diagnose without me
pasting the secret string into chat. Then later, when Claude told me to remove
the square brackets from `[YOUR-PASSWORD]`, I pushed back and explicitly told
it to "verify that information on the internet" before I'd make another change
— I wasn't going to keep editing the URL on its word alone.

**Result:** Claude wrote PowerShell + Python diagnostic snippets that read the
env var, counted structural characters (`@`, `:`, `/`), and printed a
non-alphanumeric "mask" of the password — enough to debug encoding issues
without exposing the password itself. The diagnostics walked through three
problems in sequence:
1. **First round:** my password contained an unencoded `@`, which broke URL
   parsing entirely (the parser saw 2 `@` symbols when there should be 1).
   Claude told me to percent-encode special chars (`@` → `%40`, etc.).
2. **Second round:** after I encoded a few characters, the URL parsed
   structurally but Python 3.14's stricter `urlsplit` choked on `[` `]` chars
   in the password section. Claude initially said those were part of my
   password — I corrected it, those brackets came from Supabase's
   `[YOUR-PASSWORD]` *placeholder* and weren't supposed to be in the URL at
   all.
3. **Third round:** when Claude told me to delete the brackets, I demanded it
   verify against the Supabase documentation before I made another edit. Claude
   fetched the official Supabase "Connect to your database" docs and quoted the
   relevant section: *"The brackets themselves are not part of the actual
   syntax — they're a conventional way to denote where you should insert your
   specific information."* That settled it.

**My changes:** I made the call to **stop chasing manual percent-encoding** and
just **reset the Supabase database password to alphanumeric only**. Three
rounds of manual `%XX` encoding had failed authentication, and even though the
URL parsed correctly the third time, the auth was rejecting it — likely
because one of the `%XX` sequences was mistyped. An alphanumeric password
sidesteps the entire encoding problem class. I told Claude "3rd time's a
charm" when I updated it, and the connection worked first try after that.

**Verification:**
1. Ran a real `psycopg.connect(...)` test that opened a connection, executed
   `SELECT COUNT(*) FROM patient`, and printed the result. Got
   `CONNECTED -- patient count: 60`. This wasn't just URL parsing — it
   actually authenticated against Supabase and ran a query.
2. Ran `python manage.py migrate` and watched the `auth_*`, `admin`,
   `contenttypes`, and `sessions` migrations apply against Supabase
   one-by-one with `OK` status.
3. Confirmed the new tables existed in the Supabase Table Editor.

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
- Cross-checked the trimmed model list against the table list in the Supabase
  Table Editor to make sure I hadn't accidentally removed a Mythical Mane
  domain table when removing the Django-internal ones. All 15 domain tables
  matched.
- ORM smoke test: `Patient.objects.count()` returned 60, matching what Supabase
  showed in Mission 2 (also Owner=36, Universe=3, Employee=10, Visit=120). I
  ran the same `SELECT COUNT(*)` directly in the Supabase SQL Editor as a
  belt-and-suspenders check and got the same numbers.
- Pulled three sample patients via
  `Patient.objects.select_related('owner', 'universe')[:3]` and got real
  Mythical Mane data: Phoenix 001 (Ember) owned by Ariadne Mooncrest 01 in
  Olympus Court, etc. Confirmed the relationships traversed correctly (the
  `__str__` overrides showed real names instead of `Patient object (1)`).

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

**My changes:**
- Reviewed each ModelAdmin against the seven required models in the assignment
  — Universe, Owner, Patient, Employee, Visit, Diagnosis, ProcedureDefinition
  are all present plus the eight supporting ones. Decided to keep the extras
  registered because removing them would have hidden tables I can see in
  Supabase, which felt inconsistent.
- Confirmed the Patient admin's `search_fields` includes `owner__name` (FK
  traversal) so I can search patients by their owner — useful when the admin
  has 60 rows.
- Left Claude's `raw_id_fields` choices alone after weighing them against the
  default `<select>` widget — for Visit's `patient` field, the dropdown would
  have 60 entries which is borderline annoying, so the magnifying-glass picker
  is the right call.

**Verification:**
1. `python manage.py check` → no issues.
2. Inside the Codespace, the dev server auto-started via the devcontainer's
   `postAttachCommand`. Logged into `/admin/` with my superuser. All 15
   Mythical Mane models appeared under the "Mythical Mane" section.
3. Click-tested a few admins: searched the Patient list for a patient name to
   confirm `search_fields` worked, clicked the date-hierarchy bar on Patient
   to confirm `dob` filtering by year worked, and opened the Visit admin to
   make sure the `raw_id_fields` for `patient` and `vet` rendered the
   magnifying-glass picker (instead of a giant 60-row dropdown).
4. Took a screenshot of the Patient change list (saved as
   `Mission 5 Screenshot.png`) — shows the styled admin with the columns from
   `list_display`.
5. Edited one Patient and changed its `color` field to confirm the write path.
   Hit Save, then opened Supabase Table Editor → `patient` table → confirmed
   the new color value showed up there. This proves Django admin reads from AND
   writes to Supabase.

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

**My changes:**
- Asked Claude to add `order_by("universe__name", "name")` so universes group
  together visually instead of being mixed; the page reads more like a roster
  this way.
- Asked it to make the empty-state message a dashed-border card rather than
  just a paragraph — prettier when there are no patients.
- Reviewed the template and added an italic em-dash fallback for blank `color`
  values (a couple of patients in the seed data have `color = NULL`) and an
  italic "unknown" fallback for blank `dob`. The assignment specifically called
  out that the page must still work when a field like date of birth is blank.
- Considered moving the Tailwind CDN script tag to a base template, but since
  this is the only page using it I left it inline.

**Verification:**
1. Smoke-tested the view BEFORE pushing by calling it directly via Django's
   `RequestFactory` and counting SQL queries through `connection.queries`:
   - HTTP status: 200, response length: 70 KB.
   - **Total queries: 2** (one `COUNT(*)` for the header badge, one big SELECT
     with the JOIN). No N+1 — without `select_related` this would be 61 queries
     for 60 patients. Assignment specifically called this out as a grading
     criterion.
   - Confirmed the rendered HTML contains the "60 patients" badge text and the
     Tailwind CDN script tag.
2. Inside the Codespace, opened `/patients/` in the browser. The page rendered
   the styled table with all 60 patients, their colors, dates of birth, owner
   names, and universe-name badges (color-coded with Tailwind's indigo theme).
3. Spot-checked a few rows by eye to confirm the data lined up with what I saw
   in the Supabase Table Editor — same patient names, same owner names, same
   universes. The "60 patients" badge in the header matched the count.
4. Scrolled down looking for any row with a missing `dob` or `color` to make
   sure the fallback rendering ("unknown" italic / em-dash) actually fired
   instead of the page crashing. Saw both fallbacks appear on real rows.
5. Took a screenshot of the rendered page (saved as `Mission 6 Screenshot.png`)
   for the deliverable.

---

## Mission 7: Django-owned `CareNote` model + migration

**Prompt:** Asked Claude to add a Django-managed `CareNote` model attached to
Patient (note text, created timestamp, optional follow-up date, resolved flag),
generate the migration, run it against Supabase, and register the model in the
admin.

**Result:** Claude:
- Added `CareNote` to `mythical_mane/models.py` with explicit `db_table = "care_note"`,
  `ordering = ("-created_at",)`, FK `patient` → Patient with
  `on_delete=CASCADE` and `related_name="care_notes"`. Crucially, no
  `managed = False` — this model IS owned by Django.
- Ran `python manage.py makemigrations mythical_mane` → `0001_initial.py`. The
  output looked alarming because it said "Create model X" for every Mythical
  Mane model, but inspecting the file shows every unmanaged model has
  `'managed': False` in its options block, meaning `migrate` skips the database
  operation and only updates Django's migration state. The only operation that
  actually hits the DB is `CareNote`.
- Ran `python manage.py migrate mythical_mane` → applied 0001_initial cleanly.
- Registered `CareNote` in `admin.py` with `list_display`, `list_filter`,
  `search_fields`, `date_hierarchy="created_at"`, `raw_id_fields=("patient",)`,
  and a custom `short_note` display method.

**My changes:**
- Thought about the `on_delete` choice. `PROTECT` would prevent accidental data
  loss but feels wrong for a NOTE (notes about a deleted patient are
  meaningless). `SET_NULL` doesn't apply because `patient` is non-nullable.
  Stuck with Claude's `CASCADE` — if a patient record is removed, their care
  notes should go too.
- Asked for `auto_now_add=True` on `created_at` so I never have to set it by
  hand in the admin form. Confirmed the admin shows it as `readonly_fields`
  (otherwise the form would let me edit a timestamp that's supposed to be
  immutable).
- Picked a `db_table = "care_note"` (snake_case) to match the naming
  convention of the existing Mythical Mane tables (`patient`, `owner`,
  `visit_procedure`, etc.) rather than letting Django default to
  `mythical_mane_carenote`.

**Verification:**
1. Before running migrations, eyeballed the generated `0001_initial.py` to
   confirm every unmanaged model had `'managed': False` in its `options` block
   — that's what tells `migrate` to skip the database CREATE for those tables
   while still tracking the model schema in Django's migration state.
2. Ran a Python harness that:
   - Queried `information_schema.columns` to confirm `care_note` has the right
     columns: `id`, `note`, `created_at`, `follow_up_date`, `resolved`,
     `patient_id`. Types and nullability all match the model.
   - Queried `information_schema.table_constraints` and confirmed the FK
     constraint `care_note_patient_id_c9341b34_fk_patient_patient_id` exists,
     pointing to the unmanaged `patient` table — proves you can FK from a
     Django-managed table to a legacy unmanaged one.
   - Confirmed `Patient.objects.count()` was still 60 — no unmanaged tables
     were touched.
   - Created a CareNote via the ORM (`CareNote.objects.create(...)`), got back
     `id=1`, then deleted it.
3. Right after migrating, opened Supabase Table Editor and confirmed
   `care_note` appeared in the table list as a brand-new empty table — proof
   that Django (not me, not the seed SQL) created it via migration. This was
   important because the assignment specifically requires evidence of a
   Django-created table.
4. Inside the Codespace admin, used the "Add care note" form to create two
   real records:
   - One unresolved follow-up note about flame intensity readings (with no
     follow-up date set, just to test the optional field).
   - One resolved note about a routine wing trim (with the resolved checkbox
     ticked).
   Confirmed the form's `Patient` picker (raw_id_fields) opened the
   magnifying-glass picker correctly, and the `Created at` field was greyed
   out (readonly_fields) as I'd configured.
5. Refreshed the Supabase Table Editor's `care_note` view → confirmed both
   rows appeared with the right `note` text, the `created_at` timestamps
   matched roughly when I clicked Save, and the `resolved` flags were `true`
   for the wing trim and `false` for the flame intensity note. Took a
   screenshot (saved as `Mission 7 Screenshot.png`) for the deliverable.

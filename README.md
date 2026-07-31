# Task Manager

Personal task manager. Each user only sees and manages their own tasks.

**Stack:** Django 6 + Django REST Framework · React 19 + Vite · SQLite

## How to run it

You need two terminals: one for the backend, one for the frontend.

### 1. Backend (http://localhost:8000)

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

Optional, to browse the data in the Django admin:

```bash
.venv/bin/python manage.py createsuperuser
```

Run the tests (12 tests covering auth, permissions and filters):

```bash
.venv/bin/python manage.py test
```

### 2. Frontend (http://localhost:5173)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173, register a user and start adding tasks.

> If requests return **502**, the backend is not running — Vite proxies `/api`
> to port 8000 and returns 502 when nothing answers there.

### API

| Method               | Endpoint                    | Description                                     |
| -------------------- | --------------------------- | ----------------------------------------------- |
| POST                 | `/api/auth/register/`     | Create a user                                   |
| POST                 | `/api/auth/login/`        | Get`access` + `refresh` tokens              |
| POST                 | `/api/auth/refresh/`      | Exchange a refresh token for a new access token |
| GET/POST             | `/api/tasks/`             | List (own tasks only) / create                  |
| GET/PUT/PATCH/DELETE | `/api/tasks/<id>/`        | Retrieve / update / delete                      |
| POST                 | `/api/tasks/<id>/toggle/` | Flip`completed`                               |

Filters: `/api/tasks/?completed=true&priority=HIGH` (`LOW` / `MEDIUM` / `HIGH`).

## Technical decisions

### Why JWT instead of DRF Token?

I chose **JWT** (`djangorestframework-simplejwt`).

DRF's built-in `TokenAuthentication` stores one non-expiring token per user in
the database, which means a leaked token stays valid forever unless it is
manually deleted, and every single request costs a database lookup to resolve
it.

JWT tokens are signed and self-contained: the server validates the signature
without touching the database, and they expire on their own (5 minutes for the
access token, 1 day for the refresh token, which are simplejwt's defaults). The
access/refresh pair also gives short-lived credentials without forcing the user
to log in every 5 minutes.

The honest trade-off: a JWT **cannot be revoked** before it expires, because
there is no server-side record of it. For a logout that must invalidate
immediately, you need the token blacklist app. Given the 5-minute lifetime and
the scope of this assessment, I left it out.

### How I structured the frontend folders

```
frontend/src/
├── api.js              # fetch wrapper: attaches the token, normalizes errors
├── App.jsx             # routes + protected route guard
├── index.css           # all styles (plain CSS, no framework)
├── components/
│   └── TaskForm.jsx    # shared create/edit form
└── pages/
    ├── Login.jsx
    ├── Register.jsx
    └── Tasks.jsx
```

`pages/` holds what a route renders, `components/` holds what pages reuse, and
`api.js` is the only place that knows about HTTP. If the auth scheme changes,
one file changes.

I deliberately did not add `services/`, `hooks/` or `context/` folders. With
three pages they would be empty ceremony — folders should appear when there is
something to put in them.

### ViewSets or separate views? Why?

**A single `ModelViewSet`** for tasks (`backend/tasks/views.py`), registered with
a `DefaultRouter`.

All five CRUD operations share the exact same queryset and permissions, and the
router generates the URLs. Writing five separate views would mean repeating the
`owner=request.user` filter five times — and the one place I forget it is a data
leak between users. With a ViewSet the rule lives in `get_queryset()` and
applies everywhere by construction.

For auth I used **separate generic views** instead, because registration and
login are not CRUD over one resource and share nothing.

### How I handled authentication on the frontend

- **Where the token is stored:** `localStorage`, under the key `access`. This
  survives a page reload, which `useState` or a module variable would not.
- **How it is sent:** `api.js` reads the token on every call and adds an
  `Authorization: Bearer <token>` header. No page builds that header by hand.
- **Route protection:** the `<Protected>` wrapper in `App.jsx` redirects to
  `/login` when there is no token. It is a UX guard only — the real enforcement
  is in DRF, which returns 401 regardless of what the frontend does.
- **Logout:** removes the token and redirects to `/login`.

The trade-off I want to be explicit about: `localStorage` **is readable by any
JavaScript running on the page**, so an XSS vulnerability means a stolen token.
The safer option is an httpOnly cookie, which JavaScript cannot read — but that
requires CSRF protection and a backend that issues cookies instead of a JSON
token. I chose the simpler option knowingly, not by default.

### Other decisions worth mentioning

- **No CORS package.** The Vite dev server proxies `/api` to Django, so the
  browser only ever talks to one origin. A deployment would serve both behind
  the same domain, or add `django-cors-headers` then.
- **Filters written by hand** in `get_queryset()` instead of `django-filter`.
  Two query params, six lines, one less dependency. An invalid value is ignored
  rather than returning 400, which is what a frontend sending an empty "all"
  filter expects.
- **`accounts/` is not in `INSTALLED_APPS`.** It has no models, templates or
  migrations, so Django does not need to know about it.
- **Secrets come from the environment** (`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`,
  `DJANGO_ALLOWED_HOSTS`) with dev-friendly defaults, so cloning and running
  needs no setup while a deployment can override everything. See
  `backend/.env.example`.
- **Auth endpoints are rate limited** to 10 requests/minute per client, so the
  login endpoint is not an open door for brute forcing.

## What I would do differently with more time

1. **Handle expired tokens automatically.** Right now, when the 5-minute access
   token expires, the next request just fails with an error message and the user
   has to log in again — even though a valid refresh token is sitting in
   `localStorage` and the `/api/auth/refresh/` endpoint already exists. I would
   make `api.js` catch a 401, retry once with a refreshed token, and only send
   the user to `/login` if that also fails.
2. **Move the token to an httpOnly cookie.** As explained above, `localStorage`
   is exposed to XSS. I would have the backend set the refresh token as an
   httpOnly cookie, keep the access token in memory only, and add CSRF
   protection. It is the single biggest security improvement available here.
3. **Paginate and search the task list.** The endpoint currently returns every
   task the user owns in one response. With a few hundred tasks that gets slow
   and unusable. I would add DRF pagination plus a `search` query param over
   title and description, and a debounced search input in the UI.
4. **Add frontend tests.** The backend has 12 tests; the frontend has none. I
   would add React Testing Library tests for the flows that are easy to break:
   login stores the token and redirects, an expired session sends the user back
   to `/login`, and filters actually refetch.
5. **Confirm before deleting.** Delete is immediate and irreversible. A
   confirmation step — or better, an undo toast — would prevent losing a task to
   a misclick.

## Difficulties I encountered

**The hardest part was making sure a user genuinely cannot reach another user's
tasks.** My first instinct was to write a custom permission class checking
`obj.owner == request.user`. It works for detail routes, but it is the wrong
layer: the list endpoint never calls object permissions, so a mistake there
leaks every user's tasks at once. The fix was to filter at the source —
`get_queryset()` returns only `Task.objects.filter(owner=self.request.user)`,
and DRF builds list, retrieve, update and delete from that same queryset. A
request for someone else's task now returns **404** instead of 403, which is
also better because it does not reveal that the ID exists. I wrote tests for
exactly this (`tasks/tests.py`) because it is the kind of bug that is invisible
when you test with a single user.

**The second one was a React re-render subtlety.** I reuse one form for creating
and editing. When I clicked "Edit", the inputs stayed empty — `useState(task.title)`
only reads its initial value on the first render, and switching from create to
edit does not remount the component. I first reached for a `useEffect` syncing
props into state, which worked but felt like the kind of code that breaks later.
The clean fix was `key={editing?.id ?? "new"}`: changing the key makes React
remount the component, so the state re-initializes on its own.

**The third was a self-inflicted debugging detour.** The frontend started
returning `502 Bad Gateway` on every request. I looked at the proxy config and
the fetch code before noticing the response time: 1ms. Nothing real answers that
fast — the connection was being refused instantly because I had stopped the
Django server. A 502 always means the proxy could not reach the backend, never
that the request itself is wrong. Reading the error properly would have saved me
the detour.

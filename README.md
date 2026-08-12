# Project & Team Task Manager

A collaborative organization, project, and task management application built with Django REST Framework and React.

**Stack:** Django, Django REST Framework, SimpleJWT, React, Vite, and SQLite.

## Run locally

### Backend

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py test
.venv/bin/python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Optional environment variables are documented in `backend/.env.example`:
`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, and `DJANGO_ALLOWED_HOSTS`.

## Data model and roles

`Organization 1-N Project 1-N Task`. `Membership` joins users to organizations and has a unique `(user, organization)` constraint. A task has a creator, optional assignee, status, priority, due date, timestamps, soft deletion, and activity entries.

| Role | Projects and members | Tasks |
| --- | --- | --- |
| OWNER | Full organization, project, and member administration | Can manage every task |
| ADMIN | Can manage projects and non-owner memberships | Can manage every task |
| MEMBER | Read-only | Can create and manage only tasks they created |
| VIEWER | Read-only | Read-only |

All resource querysets are membership-scoped, so resources outside a user's organizations return 404. A task creator or an ADMIN/OWNER can reassign a task, but the assignee must belong to the organization. Tasks cannot be moved between projects.

## API

- Authentication: `POST /api/auth/register/`, `login/`, and `refresh/`.
- CRUD: `/api/organizations/`, `/api/memberships/`, `/api/projects/`, and `/api/tasks/`.
- User search for membership: `GET /api/memberships/users/?q=name`.
- Project summary: `GET /api/projects/<id>/summary/`.
- Task activity: `GET /api/tasks/<id>/activity/`.
- Deleted tasks and restore: `GET /api/tasks/deleted/`, `POST /api/tasks/<id>/restore/`.
- Task filters: `?project=<id>&status=TODO&priority=HIGH&assignee=<id>&search=text&page=2`.

Projects and tasks use DRF pagination. Task list queries use `select_related` for project, organization, creator, and assignee. Login and registration are rate-limited to 10 requests per minute.

## Technical decisions and trade-offs

JWT was chosen because signed access tokens avoid a database lookup on every authenticated request. The frontend stores access and refresh tokens in `localStorage` and retries one failed request after refreshing the access token. For production, I would use an httpOnly refresh cookie, an in-memory access token, and CSRF protection to reduce XSS exposure.

ModelViewSets keep CRUD and membership-scoped querysets in one place. `require_role` centralizes write authorization, while serializers enforce cross-resource validations such as requiring task assignees to be organization members.

The frontend separates pages, the HTTP client, and small UI pieces without adding a component library. Server-side pagination and query-string filters prevent large task lists from being loaded at once. The task status update is optimistic and rolls back if the request fails.

Soft deletion preserves tasks for recovery, and `TaskActivity` records create, update, delete, and restore actions. The activity log is intentionally simple; it does not store a complete field-by-field diff.

## Design questions

1. `select_related('assignee', 'project')` prevents N+1 queries for ForeignKey relations; `prefetch_related` is appropriate for collections.
2. For tens of thousands of tasks, I would use cursor pagination, indexes for organization/project/status/date, full-text search, and a virtualized frontend list.
3. The serializer validates assignees because it sees the project and payload together, can return a useful 400 response, and protects all API writes. A database constraint cannot easily express this cross-table rule.
4. Two users can overwrite each other's changes. A practical next step is optimistic concurrency: send `updated_at` as a version and return 409 when it is stale.
5. For real-time notifications, I would first publish task-change events and add a WebSocket consumer. Presence, a full notification history, and delivery guarantees would remain out of scope initially.

## Improvements with more time

1. Store refresh tokens in httpOnly cookies and add CSRF protection.
2. Add frontend tests for role-specific flows, task editing, and refresh behavior.
3. Add audit retention policies and field-level change diffs.
4. Move from SQLite to PostgreSQL and add production monitoring.

## Difficulties

The migration from a personal task manager preserves existing data by creating an imported workspace and project per user. The hardest part was preventing cross-organization access: membership-scoped querysets protect list and detail endpoints, while role and serializer validation protect writes.

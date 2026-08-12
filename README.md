# Project & Team Task Manager

A small collaborative task manager for teams. Users create organizations, invite teammates with a role, create projects, and manage the work inside each project.

The goal of this project was to keep the core rules clear: no cross-organization access, roles are enforced on the API, and the frontend makes those rules understandable instead of trying to replace them.

**Stack:** Django, Django REST Framework, SimpleJWT, React, Vite, and SQLite.

## Running the project

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

The frontend runs on `http://localhost:5173` and proxies `/api` requests to Django on port 8000.

Optional environment variables are listed in `backend/.env.example`:

```text
DJANGO_SECRET_KEY
DJANGO_DEBUG
DJANGO_ALLOWED_HOSTS
```

## What the application does

The normal flow is:

```text
User -> Organization -> Project -> Task
              |
          Memberships
```

- Register or sign in.
- Create an organization. The creator becomes its `OWNER`.
- Add existing users by searching their username and selecting a role.
- Create projects inside the organization.
- Create tasks with a status, priority, description, assignee, and optional due date.
- Filter and paginate tasks, inspect task details/activity, or restore a deleted task.

## Data model and authorization

`Membership` is the relationship between a user and an organization. It has a database uniqueness constraint on `(user, organization)`. A task belongs to a project, and a project belongs to an organization.

| Role | Can do | Cannot do |
| --- | --- | --- |
| `OWNER` | Manage the organization, projects, members, and all tasks. | Remove or downgrade the last owner. |
| `ADMIN` | Manage projects, non-owner memberships, and all tasks. | Promote someone to owner, change/remove an owner, or delete the organization. |
| `MEMBER` | Read the organization and create/update/delete tasks they created. | Manage projects, memberships, or other users' tasks. |
| `VIEWER` | Read organizations, projects, members, and tasks. | Create or change anything. |

Authorization is enforced in the backend, not only hidden in the UI. Every organization, project, membership, and task queryset is scoped to the current user's memberships. A request for a resource in another organization returns `404`, which avoids exposing that it exists.

For reassignment, the task creator and organization `ADMIN`/`OWNER` can change the assignee. The assignee must already be a member of the task's organization. Tasks cannot be moved between projects through the task update endpoint.

## API overview

| Area | Endpoints |
| --- | --- |
| Auth | `POST /api/auth/register/`, `login/`, `refresh/` |
| Organizations | CRUD at `/api/organizations/` |
| Members | CRUD at `/api/memberships/`, user search at `GET /api/memberships/users/?q=name` |
| Projects | CRUD at `/api/projects/`, summary at `GET /api/projects/<id>/summary/` |
| Tasks | CRUD at `/api/tasks/`, activity at `GET /api/tasks/<id>/activity/` |
| Trash | `GET /api/tasks/deleted/`, `POST /api/tasks/<id>/restore/` |

Task filters can be combined:

```text
/api/tasks/?project=4&status=TODO&priority=HIGH&assignee=8&search=invoice&page=2
```

Projects and tasks use DRF pagination. Task lists use `select_related` for project, organization, creator, and assignee to avoid per-row lookup queries.

## Frontend behavior

The UI has protected routes, loading/error/empty states, client-side required fields, confirmation before deleting, and responsive layouts.

- Organization cards lead to a project and member management view.
- The member panel is shown as a side card on wider screens and stacks below projects on narrow screens.
- Member and viewer roles see read-only membership information; they do not see member-management controls.
- Admins do not see controls that would let them modify an owner or assign the owner role.
- Project views include task filters, assignee information, expandable task details, activity history, a task-count summary, and a restorable trash panel.
- Task status changes update optimistically and revert if the API call fails.

## Technical decisions

### JWT authentication

SimpleJWT provides an access/refresh pair. The client sends the access token as a Bearer token and retries one failed authenticated request after using the refresh token. Registration and login are throttled to 10 requests per minute.

For this exercise, both tokens are stored in `localStorage` because it keeps the client simple and survives reloads. The trade-off is XSS exposure. In production I would use an httpOnly refresh cookie, keep the access token in memory, and add CSRF protection.

### ViewSets and permission strategy

The domain endpoints use `ModelViewSet` because CRUD operations share serializers and membership-scoped querysets. Keeping the scope in `get_queryset()` makes list, retrieve, update, and delete start from the same safe set of records.

`require_role` is used for write rules that depend on a role. Serializer validation is used for the assignment rule because it has both the target project and assignee available and can return a helpful `400` response. Authentication endpoints are separate views because they are not CRUD resources.

### Query performance

`select_related` is used for single-value relations in the task list. The current user's organization roles are loaded once per request for serializer fields such as `my_role` and `can_edit`, avoiding one membership query for every task or project returned.

### Soft deletion and activity

Deleting a task sets `deleted_at` instead of removing the row. Deleted tasks are excluded from the normal list, remain available in the trash panel, and can be restored. `TaskActivity` records create, update, delete, and restore actions.

This is intentionally a basic audit trail. It records the action and actor, not a full before/after JSON diff of every field.

## Design questions

1. **Avoiding N+1:** use `select_related('assignee', 'project')` for ForeignKey relationships and `prefetch_related` for collections. The project already uses the first approach in task listings.
2. **Very large task lists:** use cursor pagination, indexes around organization/project/status/date, full-text search, and a virtualized task list on the frontend.
3. **Assignment validation:** the serializer is the best fit here. It sees the payload and project together, gives a useful validation error, and covers all API writes without hiding the business rule in a signal.
4. **Concurrent edits:** the current behavior is last write wins. A practical next step is optimistic concurrency using `updated_at` as a version, returning `409 Conflict` when the submitted version is stale.
5. **Real-time notifications:** start by publishing task-change events and consuming them over WebSockets. Presence, delivery guarantees, and a complete notification center would stay outside the first iteration.

## Trade-offs and next steps

1. Move refresh tokens to httpOnly cookies and add CSRF protection.
2. Add frontend tests for role-specific behavior, edits, and token refresh.
3. Use PostgreSQL, add production indexes, and add basic monitoring before scaling the task list.
4. Extend the activity log with field-level diffs and retention rules if audit requirements become stricter.

## Notes from implementation

The original application was a personal task manager. The migration keeps existing data by creating an imported organization and project for each existing user.

The main source of complexity was authorization across several relationships. Scoping querysets by membership solved the read side, while role checks and serializer validation handled changes. Keeping those rules close to the ViewSets and serializers made them easier to test and explain than spreading checks across the frontend.

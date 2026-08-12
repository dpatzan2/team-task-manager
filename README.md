# Project & Team Task Manager

Aplicación colaborativa de organizaciones, proyectos y tareas. Stack: Django + DRF, JWT, React + Vite y SQLite.

## Ejecutar

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py test
.venv/bin/python manage.py runserver
```

En otra terminal:

```bash
cd frontend
npm install
npm run dev
```

Variables opcionales en `backend/.env.example`: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`.

## Modelo y permisos

`Organization 1—N Project 1—N Task`; `Membership` relaciona usuarios y organizaciones, con una restricción única por usuario/organización. Cada tarea tiene `created_by`, asignado opcional, estado, prioridad y fecha límite.

| Rol | Proyectos y miembros | Tareas |
| --- | --- | --- |
| OWNER | Crear, editar y eliminar; administración completa | Todas |
| ADMIN | Crear y editar; no modifica ni elimina owners | Todas |
| MEMBER | Solo lectura | Crea y edita sus propias tareas |
| VIEWER | Solo lectura | Solo lectura |

Las consultas se filtran por membresía: recursos fuera de una organización del usuario devuelven 404. Un creador de tarea o ADMIN/OWNER puede reasignarla; el nuevo asignado debe ser miembro de la organización. Las tareas no se mueven entre proyectos para evitar un cambio de organización no autorizado.

## API

- `POST /api/auth/register/`, `login/`, `refresh/`
- CRUD: `/api/organizations/`, `/api/memberships/`, `/api/projects/`, `/api/tasks/`
- Proyectos: `?organization=<id>`; membresías: `?organization=<id>`.
- Tareas: `?project=<id>&status=TODO&priority=HIGH&assignee=<id>&search=texto&page=2`.

Las listas de proyectos y tareas usan paginación DRF. Las tareas cargan proyecto, organización, creador y asignado con `select_related` para evitar N+1. Registro/login están limitados a 10 solicitudes por minuto.

## Decisiones y trade-offs

JWT mantiene el backend sin consulta a base de datos por cada token; se almacena el access token en `localStorage` para simplificar el alcance. En producción preferiría refresh token httpOnly y CSRF. Los ViewSets concentran el CRUD y los querysets restringidos; `require_role` concentra la autorización de escritura. El frontend separa `pages`, cliente HTTP y componentes simples, sin librería UI.

Se usa paginación de servidor y filtros por query params: evita cargar miles de tareas, a cambio de más peticiones. La UI confirma eliminaciones, pero no usa actualización optimista ni refresh automático de JWT.

## Preguntas de diseño

1. Usaría `select_related('assignee', 'project')`; ya se aplica, y `prefetch_related` solo para relaciones de colección.
2. Cambiaría a paginación cursor, índices por organización/estado/fecha, búsqueda de texto y una lista virtualizada en React.
3. Se valida en el serializer porque conoce el proyecto y el payload completo, devuelve un 400 útil y protege toda entrada API; una restricción de base de datos no puede expresar esta relación transversal fácilmente.
4. Dos ediciones pueden sobrescribirse. Añadiría `updated_at` como versión y rechazaría un PATCH con versión antigua (409), mostrando recarga al usuario.
5. Primero añadiría un servicio/evento al cambio de estado y un consumidor WebSocket; dejaría fuera presencia, historial completo y garantías de entrega en la primera entrega.

## Con más tiempo

1. Refresh JWT con cookie httpOnly y CSRF.
2. Selector de usuarios por búsqueda en vez de pedir ID al agregar un miembro.
3. Auditoría de cambios y restauración/soft delete.
4. Pruebas de interfaz y actualización optimista de estado.

## Dificultades reales

La migración desde tareas personales conserva datos: crea un espacio y proyecto importado por usuario. El punto más delicado fue la autorización transversal: filtrar querysets impide fugas de lectura y las validaciones de rol/organización bloquean cambios de proyecto, roles de owner y asignaciones externas.

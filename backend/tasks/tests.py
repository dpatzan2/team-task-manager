from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from .models import Membership, Organization, Project, Task


class CollaborativeDomainTests(APITestCase):
    def test_membership_is_unique_and_tasks_belong_to_projects(self):
        user = User.objects.create_user("member", password="Str0ngPass!23")
        organization = Organization.objects.create(name="Acme", slug="acme")
        Membership.objects.create(user=user, organization=organization)
        project = Project.objects.create(organization=organization, name="Website")
        task = Task.objects.create(project=project, created_by=user, title="Ship")

        self.assertEqual(task.project, project)
        self.assertEqual(task.created_by, user)
        with self.assertRaises(Exception):
            Membership.objects.create(user=user, organization=organization)


class TaskAPITests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user("owner", password="Str0ngPass!23")
        self.other = User.objects.create_user("other", password="Str0ngPass!23")
        self.task = Task.objects.create(owner=self.owner, title="Mine")
        Task.objects.create(owner=self.other, title="Theirs")
        self.client.force_authenticate(self.owner)

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/tasks/").status_code, 401)

    def test_lists_only_own_tasks(self):
        response = self.client.get("/api/tasks/")
        titles = [task["title"] for task in response.data]
        self.assertEqual(titles, ["Mine"])

    def test_cannot_access_another_users_task(self):
        theirs = Task.objects.get(title="Theirs")
        self.assertEqual(self.client.get(f"/api/tasks/{theirs.pk}/").status_code, 404)
        self.assertEqual(
            self.client.delete(f"/api/tasks/{theirs.pk}/").status_code, 404
        )

    def test_create_assigns_owner(self):
        response = self.client.post("/api/tasks/", {"title": "New"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Task.objects.get(pk=response.data["id"]).owner, self.owner)

    def test_toggle_flips_completed(self):
        response = self.client.post(f"/api/tasks/{self.task.pk}/toggle/")
        self.assertTrue(response.data["completed"])
        self.task.refresh_from_db()
        self.assertTrue(self.task.completed)

    def test_filters_by_completed_and_priority(self):
        Task.objects.create(
            owner=self.owner, title="Done", completed=True, priority=Task.Priority.HIGH
        )
        self.assertEqual(len(self.client.get("/api/tasks/?completed=true").data), 1)
        self.assertEqual(len(self.client.get("/api/tasks/?completed=false").data), 1)
        self.assertEqual(len(self.client.get("/api/tasks/?priority=HIGH").data), 1)
        # Unknown values are ignored rather than erroring out.
        self.assertEqual(len(self.client.get("/api/tasks/?priority=nope").data), 2)

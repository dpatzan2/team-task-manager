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


class CollaborativeAPITests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user("owner", password="Str0ngPass!23")
        self.member = User.objects.create_user("member", password="Str0ngPass!23")
        self.viewer = User.objects.create_user("viewer", password="Str0ngPass!23")
        self.outsider = User.objects.create_user("outsider", password="Str0ngPass!23")
        self.organization = Organization.objects.create(name="Acme", slug="acme")
        Membership.objects.create(user=self.owner, organization=self.organization, role="OWNER")
        Membership.objects.create(user=self.member, organization=self.organization, role="MEMBER")
        Membership.objects.create(user=self.viewer, organization=self.organization, role="VIEWER")
        self.project = Project.objects.create(organization=self.organization, name="Website")
        self.task = Task.objects.create(project=self.project, created_by=self.owner, title="Mine")

    def test_non_member_cannot_read_organization(self):
        self.client.force_authenticate(self.outsider)
        self.assertEqual(self.client.get(f"/api/organizations/{self.organization.pk}/").status_code, 404)

    def test_viewer_cannot_create_task(self):
        self.client.force_authenticate(self.viewer)
        response = self.client.post("/api/tasks/", {"project": self.project.pk, "title": "Nope"})
        self.assertEqual(response.status_code, 403)

    def test_member_cannot_create_project(self):
        self.client.force_authenticate(self.member)
        response = self.client.post("/api/projects/", {"organization": self.organization.pk, "name": "Nope"})
        self.assertEqual(response.status_code, 403)

    def test_owner_can_add_member(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post("/api/memberships/", {"organization": self.organization.pk, "user": self.outsider.pk, "role": "ADMIN"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Membership.objects.get(user=self.outsider, organization=self.organization).role, "ADMIN")

    def test_task_cannot_be_assigned_to_non_member(self):
        self.client.force_authenticate(self.owner)
        response = self.client.patch(f"/api/tasks/{self.task.pk}/", {"assignee": self.outsider.pk})
        self.assertEqual(response.status_code, 400)

    def test_task_list_paginates_and_searches(self):
        Task.objects.bulk_create([Task(project=self.project, created_by=self.owner, title=f"Fix {number}") for number in range(12)])
        self.client.force_authenticate(self.owner)
        response = self.client.get(f"/api/tasks/?project={self.project.pk}&search=Fix&page=2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 12)
        self.assertEqual(len(response.data["results"]), 2)

    def test_member_cannot_move_task_to_a_project_in_another_organization(self):
        other = Organization.objects.create(name="Other", slug="other")
        other_project = Project.objects.create(organization=other, name="Secret")
        self.client.force_authenticate(self.member)
        response = self.client.patch(f"/api/tasks/{self.task.pk}/", {"project": other_project.pk})
        self.assertEqual(response.status_code, 403)

    def test_member_cannot_rename_organization(self):
        self.client.force_authenticate(self.member)
        response = self.client.patch(f"/api/organizations/{self.organization.pk}/", {"name": "Nope"})
        self.assertEqual(response.status_code, 403)

    def test_admin_cannot_change_or_remove_owner_membership(self):
        admin = User.objects.create_user("admin", password="Str0ngPass!23")
        Membership.objects.create(user=admin, organization=self.organization, role="ADMIN")
        self.client.force_authenticate(admin)
        owner_membership = Membership.objects.get(user=self.owner, organization=self.organization)
        self.assertEqual(self.client.patch(f"/api/memberships/{owner_membership.pk}/", {"role": "VIEWER"}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/memberships/{owner_membership.pk}/").status_code, 403)

    def test_member_search_returns_matching_users(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get("/api/memberships/users/?q=outs")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][0]["username"], "outsider")

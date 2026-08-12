from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import exceptions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Membership, Organization, Project, Task, TaskActivity
from .serializers import MembershipSerializer, OrganizationSerializer, ProjectSerializer, TaskSerializer


def membership(user, organization):
    return Membership.objects.filter(user=user, organization=organization).first()


def require_role(user, organization, *roles):
    member = membership(user, organization)
    if not member or member.role not in roles:
        raise exceptions.PermissionDenied()
    return member


class OrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        return Organization.objects.filter(memberships__user=self.request.user).distinct()

    def perform_create(self, serializer):
        organization = serializer.save()
        Membership.objects.create(organization=organization, user=self.request.user, role=Membership.Role.OWNER)

    def perform_update(self, serializer):
        require_role(self.request.user, serializer.instance, "OWNER", "ADMIN")
        serializer.save()

    def perform_destroy(self, instance):
        require_role(self.request.user, instance, "OWNER")
        instance.delete()


class MembershipViewSet(viewsets.ModelViewSet):
    serializer_class = MembershipSerializer

    def get_queryset(self):
        queryset = Membership.objects.filter(organization__memberships__user=self.request.user).select_related("user", "organization").distinct()
        if organization := self.request.query_params.get("organization"):
            queryset = queryset.filter(organization_id=organization)
        return queryset

    @action(detail=False, methods=["get"], url_path="users")
    def users(self, request):
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Response({"results": []})
        users = get_user_model().objects.filter(username__icontains=query).values("id", "username")[:10]
        return Response({"results": list(users)})

    def perform_create(self, serializer):
        require_role(self.request.user, serializer.validated_data["organization"], "OWNER", "ADMIN")
        serializer.save()

    def perform_update(self, serializer):
        actor = require_role(self.request.user, serializer.instance.organization, "OWNER", "ADMIN")
        if serializer.validated_data.get("role") == "OWNER" and actor.role != "OWNER":
            raise exceptions.PermissionDenied()
        if serializer.instance.role == "OWNER" and actor.role != "OWNER":
            raise exceptions.PermissionDenied()
        if serializer.instance.role == "OWNER" and serializer.validated_data.get("role") != "OWNER" and Membership.objects.filter(organization=serializer.instance.organization, role="OWNER").count() == 1:
            raise exceptions.ValidationError("An organization must keep an owner.")
        serializer.save()

    def perform_destroy(self, instance):
        require_role(self.request.user, instance.organization, "OWNER", "ADMIN")
        actor = membership(self.request.user, instance.organization)
        if instance.role == "OWNER" and actor.role != "OWNER":
            raise exceptions.PermissionDenied()
        if instance.role == "OWNER" and Membership.objects.filter(organization=instance.organization, role="OWNER").count() == 1:
            raise exceptions.ValidationError("An organization must keep an owner.")
        instance.delete()


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        queryset = Project.objects.filter(organization__memberships__user=self.request.user).select_related("organization").distinct()
        if organization := self.request.query_params.get("organization"):
            queryset = queryset.filter(organization_id=organization)
        return queryset

    def perform_create(self, serializer):
        require_role(self.request.user, serializer.validated_data["organization"], "OWNER", "ADMIN")
        serializer.save()

    def perform_update(self, serializer):
        require_role(self.request.user, serializer.instance.organization, "OWNER", "ADMIN")
        serializer.save()

    perform_destroy = lambda self, instance: (require_role(self.request.user, instance.organization, "OWNER", "ADMIN"), instance.delete())

    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        project = self.get_object()
        counts = dict(project.tasks.values_list("status").annotate(total=Count("id")))
        return Response({"TODO": counts.get("TODO", 0), "IN_PROGRESS": counts.get("IN_PROGRESS", 0), "DONE": counts.get("DONE", 0)})


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer

    def get_queryset(self):
        queryset = Task.objects.filter(deleted_at__isnull=True, project__organization__memberships__user=self.request.user).select_related("project", "project__organization", "created_by", "assignee").distinct()
        for field in ("project", "status", "priority", "assignee"):
            if value := self.request.query_params.get(field):
                queryset = queryset.filter(**{f"{field}_id" if field in ("project", "assignee") else field: value})
        if search := self.request.query_params.get("search"):
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))
        return queryset

    def perform_create(self, serializer):
        require_role(self.request.user, serializer.validated_data["project"].organization, "OWNER", "ADMIN", "MEMBER")
        task = serializer.save(created_by=self.request.user)
        TaskActivity.objects.create(task=task, actor=self.request.user, action="CREATED")

    def perform_update(self, serializer):
        task = serializer.instance
        member = require_role(self.request.user, task.project.organization, "OWNER", "ADMIN", "MEMBER")
        if member.role == "MEMBER" and task.created_by_id != self.request.user.id:
            raise exceptions.PermissionDenied()
        if serializer.validated_data.get("project", task.project) != task.project:
            raise exceptions.PermissionDenied("Tasks cannot be moved between projects.")
        task = serializer.save()
        TaskActivity.objects.create(task=task, actor=self.request.user, action="UPDATED")

    def perform_destroy(self, instance):
        member = require_role(self.request.user, instance.project.organization, "OWNER", "ADMIN", "MEMBER")
        if member.role == "MEMBER" and instance.created_by_id != self.request.user.id:
            raise exceptions.PermissionDenied()
        instance.deleted_at = timezone.now()
        instance.save(update_fields=["deleted_at"])
        TaskActivity.objects.create(task=instance, actor=self.request.user, action="DELETED")

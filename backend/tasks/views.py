from django.db.models import Q
from rest_framework import exceptions, viewsets

from .models import Membership, Organization, Project, Task
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

    def perform_create(self, serializer):
        require_role(self.request.user, serializer.validated_data["organization"], "OWNER", "ADMIN")
        serializer.save()

    def perform_update(self, serializer):
        require_role(self.request.user, serializer.instance.organization, "OWNER", "ADMIN")
        if serializer.instance.role == "OWNER" and membership(self.request.user, serializer.instance.organization).role != "OWNER":
            raise exceptions.PermissionDenied()
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


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer

    def get_queryset(self):
        queryset = Task.objects.filter(project__organization__memberships__user=self.request.user).select_related("project", "project__organization", "created_by", "assignee").distinct()
        for field in ("project", "status", "priority", "assignee"):
            if value := self.request.query_params.get(field):
                queryset = queryset.filter(**{f"{field}_id" if field in ("project", "assignee") else field: value})
        if search := self.request.query_params.get("search"):
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))
        return queryset

    def perform_create(self, serializer):
        require_role(self.request.user, serializer.validated_data["project"].organization, "OWNER", "ADMIN", "MEMBER")
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        task = serializer.instance
        member = require_role(self.request.user, task.project.organization, "OWNER", "ADMIN", "MEMBER")
        if member.role == "MEMBER" and task.created_by_id != self.request.user.id:
            raise exceptions.PermissionDenied()
        if serializer.validated_data.get("project", task.project) != task.project:
            raise exceptions.PermissionDenied("Tasks cannot be moved between projects.")
        serializer.save()

    def perform_destroy(self, instance):
        member = require_role(self.request.user, instance.project.organization, "OWNER", "ADMIN", "MEMBER")
        if member.role == "MEMBER" and instance.created_by_id != self.request.user.id:
            raise exceptions.PermissionDenied()
        instance.delete()

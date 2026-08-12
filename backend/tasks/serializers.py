from rest_framework import serializers

from .models import Membership, Organization, Project, Task


def role_for(request, organization_id):
    if not hasattr(request, "_organization_roles"):
        request._organization_roles = dict(Membership.objects.filter(user=request.user).values_list("organization_id", "role"))
    return request._organization_roles.get(organization_id)


class OrganizationSerializer(serializers.ModelSerializer):
    my_role = serializers.SerializerMethodField()

    def get_my_role(self, organization):
        return role_for(self.context["request"], organization.id)
    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "created_at", "my_role"]
        read_only_fields = ["id", "created_at"]


class MembershipSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "organization", "user", "username", "role"]
        read_only_fields = ["id"]


class ProjectSerializer(serializers.ModelSerializer):
    my_role = serializers.SerializerMethodField()

    def get_my_role(self, project):
        return role_for(self.context["request"], project.organization_id)

    class Meta:
        model = Project
        fields = ["id", "organization", "name", "description", "status", "my_role"]
        read_only_fields = ["id"]


class TaskSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)
    assignee_name = serializers.CharField(source="assignee.username", read_only=True)
    can_edit = serializers.SerializerMethodField()

    def get_can_edit(self, task):
        request = self.context["request"]
        role = role_for(request, task.project.organization_id)
        return role in ("OWNER", "ADMIN") or (role == "MEMBER" and task.created_by_id == request.user.id)

    class Meta:
        model = Task
        fields = ["id", "project", "title", "description", "status", "priority", "assignee", "assignee_name", "due_date", "created_by", "created_by_name", "can_edit", "created_at", "updated_at"]
        read_only_fields = ["id", "created_by", "created_by_name", "assignee_name", "created_at", "updated_at"]

    def validate(self, attrs):
        project = attrs.get("project", getattr(self.instance, "project", None))
        assignee = attrs.get("assignee", getattr(self.instance, "assignee", None))
        if assignee and not Membership.objects.filter(organization=project.organization, user=assignee).exists():
            raise serializers.ValidationError({"assignee": "Assignee must belong to the organization."})
        return attrs

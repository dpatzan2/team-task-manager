from rest_framework import serializers

from .models import Membership, Organization, Project, Task


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "created_at"]
        read_only_fields = ["id", "created_at"]


class MembershipSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "organization", "user", "username", "role"]
        read_only_fields = ["id"]


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "organization", "name", "description", "status"]
        read_only_fields = ["id"]


class TaskSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)
    assignee_name = serializers.CharField(source="assignee.username", read_only=True)

    class Meta:
        model = Task
        fields = ["id", "project", "title", "description", "status", "priority", "assignee", "assignee_name", "due_date", "created_by", "created_by_name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_by", "created_by_name", "assignee_name", "created_at", "updated_at"]

    def validate(self, attrs):
        project = attrs.get("project", getattr(self.instance, "project", None))
        assignee = attrs.get("assignee", getattr(self.instance, "assignee", None))
        if assignee and not Membership.objects.filter(organization=project.organization, user=assignee).exists():
            raise serializers.ValidationError({"assignee": "Assignee must belong to the organization."})
        return attrs

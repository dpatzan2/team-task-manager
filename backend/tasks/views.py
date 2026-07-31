from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Task
from .serializers import TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer

    def get_queryset(self):
        """Only the requesting user's tasks, optionally filtered by query params."""
        queryset = Task.objects.filter(owner=self.request.user)

        completed = self.request.query_params.get("completed")
        if completed in ("true", "false"):
            queryset = queryset.filter(completed=completed == "true")

        priority = self.request.query_params.get("priority")
        if priority in Task.Priority.values:
            queryset = queryset.filter(priority=priority)

        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        task = self.get_object()
        task.completed = not task.completed
        task.save(update_fields=["completed", "updated_at"])
        return Response(self.get_serializer(task).data)

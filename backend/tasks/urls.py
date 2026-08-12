from rest_framework.routers import DefaultRouter

from .views import MembershipViewSet, OrganizationViewSet, ProjectViewSet, TaskViewSet

router = DefaultRouter()
router.register("organizations", OrganizationViewSet, basename="organization")
router.register("memberships", MembershipViewSet, basename="membership")
router.register("projects", ProjectViewSet, basename="project")
router.register("tasks", TaskViewSet, basename="task")

urlpatterns = router.urls

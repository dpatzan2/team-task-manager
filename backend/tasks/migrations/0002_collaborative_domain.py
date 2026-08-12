from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_existing_tasks(apps, schema_editor):
    Organization = apps.get_model("tasks", "Organization")
    Membership = apps.get_model("tasks", "Membership")
    Project = apps.get_model("tasks", "Project")
    Task = apps.get_model("tasks", "Task")
    for task in Task.objects.select_related("created_by"):
        slug = f"personal-{task.created_by_id}"
        organization, _ = Organization.objects.get_or_create(
            slug=slug, defaults={"name": f"{task.created_by.username}'s workspace"}
        )
        Membership.objects.get_or_create(user_id=task.created_by_id, organization=organization, defaults={"role": "OWNER"})
        project, _ = Project.objects.get_or_create(organization=organization, name="Imported tasks")
        task.project = project
        task.status = "DONE" if task.completed else "TODO"
        task.save(update_fields=["project", "status"])


class Migration(migrations.Migration):
    dependencies = [("tasks", "0001_initial"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(name="Organization", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("name", models.CharField(max_length=120)), ("slug", models.SlugField(unique=True)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
        ]),
        migrations.CreateModel(name="Project", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("name", models.CharField(max_length=160)), ("description", models.TextField(blank=True)),
            ("status", models.CharField(choices=[("ACTIVE", "Active"), ("ARCHIVED", "Archived")], default="ACTIVE", max_length=8)),
            ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="projects", to="tasks.organization")),
        ]),
        migrations.CreateModel(name="Membership", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("role", models.CharField(choices=[("OWNER", "Owner"), ("ADMIN", "Admin"), ("MEMBER", "Member"), ("VIEWER", "Viewer")], default="MEMBER", max_length=6)),
            ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="tasks.organization")),
            ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
        ], options={"constraints": [models.UniqueConstraint(fields=("user", "organization"), name="unique_membership")]}),
        migrations.RenameField(model_name="task", old_name="owner", new_name="created_by"),
        migrations.AlterField(model_name="task", name="created_by", field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="created_tasks", to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name="task", name="assignee", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_tasks", to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name="task", name="due_date", field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name="task", name="project", field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name="tasks", to="tasks.project")),
        migrations.AddField(model_name="task", name="status", field=models.CharField(choices=[("TODO", "To do"), ("IN_PROGRESS", "In progress"), ("DONE", "Done")], default="TODO", max_length=11)),
        migrations.RunPython(migrate_existing_tasks, migrations.RunPython.noop),
        migrations.RemoveField(model_name="task", name="completed"),
        migrations.AlterField(model_name="task", name="project", field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tasks", to="tasks.project")),
    ]

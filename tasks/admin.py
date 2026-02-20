from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Task

User = get_user_model()


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    # Fields to show in the admin list view
    list_display = (
        "title",
        "priority",
        "status",  # visually editable via list_editable, but backend does not block changes
        "get_department",
        "assigned_to",
        "assigned_by",
        "created_at",
        "status_updated_at",
        "deadline",
    )

    # Filters in the sidebar
    list_filter = ("priority",)
    list_editable = ("priority", "status") 
    search_fields = ("title", "description", "assigned_to__username", "assigned_to__first_name")
    exclude = ('assigned_by',)

    # Autocomplete for foreign key fields
    # autocomplete_fields = ["assigned_to"]


    @admin.display(description="Department", ordering="assigned_to__department")
    def get_department(self, obj):
        return obj.assigned_to.department

    def save_model(self, request, obj, form, change):
        if not obj.assigned_by:
            obj.assigned_by = request.user  # assign current user
        super().save_model(request, obj, form, change)

    # Limit queryset based on user role
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.role == User.Role.ADMIN:
            return qs  # Admins see all tasks
        if request.user.role == User.Role.MANAGER and request.user.department:
            return qs.filter(assigned_to__department=request.user.department)  # Managers see their department tasks
        return qs.none()  # Others see nothing

    # Limit foreign key choices in forms based on user role
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if request.user.is_superuser or request.user.role == User.Role.ADMIN:
            return super().formfield_for_foreignkey(db_field, request, **kwargs)
        if request.user.role == User.Role.MANAGER and request.user.department:
            if db_field.name == "assigned_to":
                # Managers can assign only to users in their department
                kwargs["queryset"] = User.objects.filter(department=request.user.department)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# Status field is editable in list_editable for all tasks,
# but JS (custom_admin.js / Jazzmin "custom_js") is used to visually disable
# the status dropdown for tasks not assigned to the current user.
# Backend does NOT enforce any restriction — this is purely visual.




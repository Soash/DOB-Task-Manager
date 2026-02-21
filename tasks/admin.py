from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Task
from django import forms

User = get_user_model()


# 👇 Custom ModelForm for Task change page
# This handles field-level restrictions (disabled fields) based on the current user
class TaskChangeForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        # Extract the current user for permission checks
        self.current_user = kwargs.pop("current_user", None)
        super().__init__(*args, **kwargs)

        # Skip if this is a new instance or no current_user provided
        if not self.instance.pk or not self.current_user:
            return

        # PRIORITY rule:
        # If a Manager is viewing a task assigned by an Admin,
        # they should NOT be able to edit the priority field
        if (
            self.current_user.role == User.Role.MANAGER
            and self.instance.assigned_by
            and self.instance.assigned_by.role == User.Role.ADMIN
        ):
            self.fields["priority"].disabled = True


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = (
        "title",
        "priority",
        "status",
        "get_department",
        "assigned_to",
        "assigned_by",
        "created_at",
        "status_updated_at",
        "deadline",
    )

    # Filters available in the sidebar
    list_filter = ("priority",)
    # Fields editable directly in the list view
    list_editable = ("priority", "status") 
    # Fields searchable via the search box
    search_fields = ("title", "description", "assigned_to__username", "assigned_to__first_name")
    # Exclude assigned_by from default forms (will be set automatically)
    exclude = ('assigned_by',)
    # Use custom form for the change page
    form = TaskChangeForm

    # 👇 Optional: autocomplete for foreign keys (commented out here)
    # autocomplete_fields = ["assigned_to"]

    # Custom display for Department in list view
    @admin.display(description="Department", ordering="assigned_to__department")
    def get_department(self, obj):
        return obj.assigned_to.department

    # Save method: sets assigned_by automatically, updates fields, and sends emails
    def save_model(self, request, obj, form, change):
        if change:
            # Fetch the old object for comparison
            old = Task.objects.get(pk=obj.pk)

            # PRIORITY rule enforcement:
            # If a Manager tries to edit a task assigned by Admin, revert any changes
            if (
                request.user.role == User.Role.MANAGER
                and old.assigned_by
                and old.assigned_by.role == User.Role.ADMIN
            ):
                obj.priority = old.priority
            
        # Automatically set assigned_by on creation
        if not obj.assigned_by:
            obj.assigned_by = request.user

        super().save_model(request, obj, form, change)
        
        # Send notification email if new task or reassigned
        if not change or "assigned_to" in form.changed_data:
            subject = f"New Task Assigned: {obj.title}"
            message = (
                f"Hello {obj.assigned_to.first_name},\n\n"
                f"You have been assigned a new task: {obj.title}\n"
                f"Priority: {obj.get_priority_display()}\n"
                f"Deadline: {obj.deadline}\n\n"
                f"Description:\n{obj.description}\n\n"
                f"Link: http://task.dobltd.com \n\n"
                f"Please log in to your dashboard to view details."
            )
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [obj.assigned_to.email or obj.assigned_to.username],
                    fail_silently=False,
                )
            except Exception as e:
                # Show warning in admin if email fails
                self.message_user(request, f"Task saved but email failed: {e}", level="WARNING")

    # Limit queryset based on user role
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Admins see all tasks
        if request.user.is_superuser or request.user.role == User.Role.ADMIN:
            return qs
        # Managers see only tasks assigned to their department
        if request.user.role == User.Role.MANAGER and request.user.department:
            return qs.filter(assigned_to__department=request.user.department)
        # Others see nothing
        return qs.none()

    # Limit foreign key choices in forms based on user role
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Admins see all choices
        if request.user.is_superuser or request.user.role == User.Role.ADMIN:
            return super().formfield_for_foreignkey(db_field, request, **kwargs)
        # Managers see only users in their department
        if request.user.role == User.Role.MANAGER and request.user.department:
            if db_field.name == "assigned_to":
                kwargs["queryset"] = User.objects.filter(department=request.user.department)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    # Make priority readonly in change form for Managers if assigned by Admin
    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj) or [])
        if obj:
            if (
                request.user.role == User.Role.MANAGER
                and obj.assigned_by
                and obj.assigned_by.role == User.Role.ADMIN
            ):
                readonly.append("priority")
        return readonly
        
    # 👇 Lock priority field in list_editable rows for Managers if assigned by Admin
    def get_changelist_formset(self, request, **kwargs):
        # Get the original formset
        FormSet = super().get_changelist_formset(request, **kwargs)

        class PriorityLockedFormSet(FormSet):
            # Hook into form construction per row
            def _construct_form(self, i, **form_kwargs):
                form = super()._construct_form(i, **form_kwargs)
                instance = form.instance

                # PRIORITY rule for list display
                if (
                    request.user.role == User.Role.MANAGER
                    and instance.pk
                    and instance.assigned_by
                    and instance.assigned_by.role == User.Role.ADMIN
                ):
                    form.fields["priority"].disabled = True

                return form

        return PriorityLockedFormSet
    
    
    
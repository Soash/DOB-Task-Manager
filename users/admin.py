from django.contrib.auth.models import Group
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Department, PrimarySetting

admin.site.unregister(Group)

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'role', 'department', 'is_staff', 'is_active',)
    list_editable = ('role',)
    list_filter = ('role', 'department', 'is_staff', 'is_superuser')
    search_fields = ('username', 'first_name')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'email')}),
        ('Permissions', {
            # 'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions', 'groups'),
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Custom Fields', {'fields': ('role', 'department', 'dob_id')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('first_name', 'role', 'department', 'dob_id')}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.role == CustomUser.Role.ADMIN:
            return qs
        if request.user.role == CustomUser.Role.MANAGER and request.user.department:
            return qs.filter(department=request.user.department)
        return qs.none() 

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    # search_fields = ('name',)

@admin.register(PrimarySetting)
class PrimarySettingAdmin(admin.ModelAdmin):
    list_display = ('id', 'auto_approve',)
    list_editable = ('auto_approve',)
    list_display_links = ('id',)

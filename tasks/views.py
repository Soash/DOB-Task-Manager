from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Task
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from users.models import CustomUser

@login_required
def dashboard(request):
    if request.user.role in [CustomUser.Role.ADMIN, CustomUser.Role.MANAGER] or request.user.is_superuser:
        return redirect("/admin/tasks/task/")
    
    return redirect("task_list_default")

@login_required
def task_list_by_status(request, status=None):
    if not status:
        return redirect("task_list_by_status", status=Task.Status.PENDING)

    if status not in Task.Status.values:
        messages.error(request, "Invalid task status.")
        return redirect("task_list_by_status", status=Task.Status.PENDING)

    tasks = Task.objects.filter(
        assigned_to=request.user,
        status=status
    )

    return render(
        request,
        "tasks/task_list.html",
        {
            "tasks": tasks,
            "current_status": status,
            "status_label": dict(Task.Status.choices)[status],
        }
    )

@login_required
def update_task_status(request):
    if request.method != "POST":
        return redirect("user_dashboard")

    task = get_object_or_404(
        Task,
        id=request.POST.get("task_id"),
        assigned_to=request.user
    )

    old_status = task.status
    form = TaskStatusUpdateForm(request.POST, instance=task)

    if not form.is_valid():
        messages.error(request, "Invalid status selection.")
        return redirect("user_dashboard")

    new_status = form.cleaned_data["status"]

    # 🔒 Enforce status rules
    allowed_next = ALLOWED_STATUS_TRANSITIONS.get(old_status, [])

    if new_status not in allowed_next:
        messages.error(
            request,
            f"Cannot change task from {old_status.replace('_', ' ').title()} "
            f"to {new_status.replace('_', ' ').title()}."
        )
        return redirect("user_dashboard")

    task.status = new_status
    task.save()

    messages.success(
        request,
        f"Task '{task.title}' marked as {new_status.replace('_', ' ').title()}."
    )

    return redirect("user_dashboard")

@login_required
def update_task_status(request):
    if request.method != "POST":
        return redirect("dashboard")

    task_id = request.POST.get("task_id")
    new_status = request.POST.get("status")

    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)

    # Enforce status rules
    if task.status == "PENDING" and new_status == "IN_PROGRESS":
        task.status = new_status
    elif task.status == "IN_PROGRESS" and new_status == "COMPLETED":
        task.status = new_status
    else:
        messages.error(
            request,
            f"Cannot change task from {task.get_status_display()} "
            f"to {new_status.replace('_', ' ').title()}."
        )
        return redirect("task_list_by_status", status=task.status)

    task.save()
    messages.success(
        request,
        f"Task '{task.title}' updated to {task.get_status_display()}."
    )

    return redirect("task_list_by_status", status=task.status)
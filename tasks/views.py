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
        return redirect("dashboard")

    task_id = request.POST.get("task_id")
    new_status = request.POST.get("status")

    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)

    # Enforce status rules
    if task.status == "PENDING" and new_status == "IN_PROGRESS":
        task.status = new_status
    elif task.status == "IN_PROGRESS" and new_status == "REVIEW":
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




from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import user_passes_test

@login_required
@user_passes_test(lambda u: u.is_staff)
def send_deadline_reminders(request):
    tomorrow = timezone.localdate() + timedelta(days=1)
    tasks_due_tomorrow = Task.objects.filter(
        deadline=tomorrow,
        status__in=[Task.Status.PENDING, Task.Status.IN_PROGRESS]
    )

    sent_count = 0
    for task in tasks_due_tomorrow:
        if task.assigned_to and task.assigned_to.email:
            subject = f"Reminder: Task '{task.title}' is due tomorrow!"
            message = (
                f"Hello {task.assigned_to.first_name or task.assigned_to.username},\n\n"
                f"This is a reminder that your task '{task.title}' is due tomorrow ({task.deadline}).\n"
                f"Current Status: {task.get_status_display()}\n\n"
                f"Please ensure it is completed on time.\n\n"
                f"Regards,\nDOB Task Manager"
            )
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [task.assigned_to.email],
                    fail_silently=True,
                )
                sent_count += 1
            except Exception:
                pass

    messages.success(request, f"Successfully sent {sent_count} deadline reminder(s).")
    return redirect("/admin/tasks/task/?status__exact=PENDING")


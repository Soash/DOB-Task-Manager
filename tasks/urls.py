from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("tasks/", views.task_list_by_status, name="task_list_default"),
    path("tasks/<str:status>/", views.task_list_by_status, name="task_list_by_status"),
    path("update_task_status", views.update_task_status, name="update_task_status"),
    path("admin-action/send-reminders/", views.send_deadline_reminders, name="send_deadline_reminders"),
]
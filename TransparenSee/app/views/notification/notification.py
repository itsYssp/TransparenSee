from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from app.models import Notification


ROLE_TEMPLATES = {
    "treasurer":  "app/officer/treasurer/sidebar.html",
    "auditor":    "app/officer/auditor/sidebar.html",
    "secretary":    "app/officer/secretary/sidebar.html",
    "president":  "app/officer/president/sidebar.html",
    "vice_president":  "app/officer/president/sidebar.html",
    "adviser":    "app/adviser/sidebar.html",
    "co_adviser": "app/adviser/sidebar.html",
    "head":       "app/heads/sidebar.html",
    "student":    "app/student/sidebar.html",
}


def get_base_template(user):
    return ROLE_TEMPLATES.get(user.role, 'app/base.html')


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by("-created_at")

    unread_count = notifications.filter(is_read=False).count()

    return render(
        request,
        "app/notification_list.html",
        {
            "notifications": notifications,
            "unread_count": unread_count,
            "base_template": get_base_template(request.user),
        },
    )


@login_required
def notification_redirect(request, pk):
    notification = get_object_or_404(
        Notification,
        pk=pk,
        recipient=request.user,
    )

    if not notification.is_read:
        notification.is_read = True
        notification.save()

    if notification.url:
        return redirect(notification.url)

    return redirect("notification_list")


@login_required
@require_POST
def mark_all_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return redirect("notification_list")
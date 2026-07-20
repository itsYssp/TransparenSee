from .models import Notification

def notifications(request):
    if request.user.is_authenticated:
        # Latest 5 notifications for dropdown
        notifications = Notification.objects.filter(
            recipient=request.user
        ).order_by("-created_at")[:5]

        # Count unread notifications separately
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()

        return {
            "notifications": notifications,
            "unread_count": unread_count,
        }

    return {
        "notifications": [],
        "unread_count": 0,
    }
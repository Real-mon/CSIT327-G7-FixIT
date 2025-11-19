# accounts/utils.py
from .models import Notification

def create_notification(ticket, sender, message):
    Notification.objects.create(
        recipient=ticket.user,   # The ticket owner
        sender=sender,           # The helper responding
        ticket=ticket,
        message=message
    )

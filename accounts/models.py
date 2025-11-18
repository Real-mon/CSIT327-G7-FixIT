from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    """
    Extended user profile to store additional information.
    OneToOne relationship with Django's built-in User model.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_technician = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/', 
        blank=True, 
        null=True,
        max_length=500  # Increase max_length for file paths
    )
    date_of_birth = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

def get_profile_picture_url(self):
        """Safe method to get profile picture URL"""
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return None

# Signals to automatically create/update profile when user is created/updated
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when a new User is created"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()

 
#SPRINT 2
class Ticket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('pending', 'Pending'),
        ('solved', 'Solved'),
    ]

    # If your Supabase table already has a column named "user_id", this will link correctly.
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')

    title = models.CharField(max_length=100)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:

        db_table = 'ticket'

    def __str__(self):
        return f"{self.title} ({self.status})"


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'user_settings'  # Use your existing Supabase table name

    def __str__(self):
        return f"{self.user.username}'s Settings"
    
    
class Contact(models.Model):
    """
    Model to store user's contacts (technicians they can message) and bot chats
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_contacts')
    contact_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='added_as_contact', null=True, blank=True)
    contact_name = models.CharField(max_length=255)
    is_bot_chat = models.BooleanField(default=False)  # New field to identify bot chats
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'contact_user']
        db_table = 'contacts'
    
    def __str__(self):
        return f"{self.user.username} -> {self.contact_name}"
    

class Message(models.Model):
    """
    Model to store messages between users
    """
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'messages'
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender.username} to {self.receiver.username}: {self.content[:50]}"
    
    
class BotChat(models.Model):
    """
    Model to store bot chat sessions
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bot_chats')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'bot_chats'
    
    def __str__(self):
        return f"Bot Chat - {self.user.username}"

class BotMessage(models.Model):
    """
    Model to store messages in bot chats
    """
    chat = models.ForeignKey(BotChat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_bot = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'bot_messages'
        ordering = ['timestamp']
    
    def __str__(self):
        sender = "Bot" if self.is_bot else self.sender.username
        return f"{sender}: {self.content[:50]}"
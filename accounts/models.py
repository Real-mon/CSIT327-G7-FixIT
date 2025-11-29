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
        max_length=500
    )
    date_of_birth = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    two_factor_enabled = models.BooleanField(default=False)
    sms_recovery_enabled = models.BooleanField(default=False)
    email_recovery_enabled = models.BooleanField(default=False)

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

class NotificationSettings(models.Model):
    """
    Model for user notification preferences
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_settings')
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    promotions = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Notification Settings"
    
    class Meta:
        db_table = 'notification_settings'
        verbose_name = 'Notification Setting'
        verbose_name_plural = 'Notification Settings'

class TechnicianSpecialty(models.Model):
    """
    Model for technician specialties/skills
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    icon_class = models.CharField(max_length=50, blank=True, null=True, 
                                 help_text="Font Awesome icon class (e.g., 'fa-laptop')")
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Technician Specialty'
        verbose_name_plural = 'Technician Specialties'

class Technician(models.Model):
    """
    Technician profile extending UserProfile with technician-specific fields
    """
    user_profile = models.OneToOneField(
        UserProfile, 
        on_delete=models.CASCADE, 
        related_name='technician_profile'
    )
    bio = models.TextField(blank=True, null=True, help_text="Professional bio or description")
    specialties = models.ManyToManyField(TechnicianSpecialty, related_name='technicians', blank=True)
    is_available = models.BooleanField(default=True)
    average_rating = models.FloatField(default=4.0)
    review_count = models.IntegerField(default=0)
    experience_years = models.IntegerField(default=0)
    average_response_time = models.FloatField(default=2.0, help_text="Average response time in hours")
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    certification = models.CharField(max_length=200, blank=True, null=True)
    languages = models.CharField(max_length=200, blank=True, null=True, help_text="Comma-separated list of languages")
    
    # Availability settings
    working_hours_start = models.TimeField(default='09:00')
    working_hours_end = models.TimeField(default='17:00')
    accepts_emergency_calls = models.BooleanField(default=False)
    
    # Statistics
    completed_tickets = models.IntegerField(default=0)
    success_rate = models.FloatField(default=95.0, help_text="Success rate percentage")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Technician: {self.user_profile.user.get_full_name() or self.user_profile.user.username}"

    class Meta:
        verbose_name = 'Technician'
        verbose_name_plural = 'Technicians'

    @property
    def user(self):
        """Quick access to the user object"""
        return self.user_profile.user

    @property
    def full_name(self):
        """Get technician's full name"""
        return self.user_profile.user.get_full_name()

    @property
    def email(self):
        """Get technician's email"""
        return self.user_profile.user.email

    @property
    def profile_picture_url(self):
        """Get profile picture URL"""
        return self.user_profile.get_profile_picture_url()

    @property
    def initials(self):
        """Generate initials for profile picture placeholder"""
        user = self.user_profile.user
        if user.first_name and user.last_name:
            return f"{user.first_name[0]}{user.last_name[0]}".upper()
        elif user.first_name:
            return user.first_name[0].upper()
        elif user.last_name:
            return user.last_name[0].upper()
        else:
            return user.username[0:2].upper() if user.username else "US"

    @property
    def availability_status(self):
        """Get formatted availability status"""
        return "Available" if self.is_available else "Busy"

    @property
    def availability_class(self):
        """Get CSS class for availability status"""
        return "bg-green-100 text-green-800" if self.is_available else "bg-red-100 text-red-800"

    def get_specialties_list(self):
        """Get list of specialty names"""
        return [specialty.name for specialty in self.specialties.all()]

    def update_rating(self, new_rating):
        """Update average rating when new review is added"""
        total_rating = (self.average_rating * self.review_count) + new_rating
        self.review_count += 1
        self.average_rating = total_rating / self.review_count
        self.save()

    def increment_completed_tickets(self):
        """Increment completed tickets count"""
        self.completed_tickets += 1
        self.save()

class TechnicianReview(models.Model):
    """
    Model for technician reviews and ratings
    """
    technician = models.ForeignKey(Technician, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='technician_reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['technician', 'user']
        verbose_name = 'Technician Review'
        verbose_name_plural = 'Technician Reviews'

    def __str__(self):
        return f"Review for {self.technician} by {self.user.username}"

class AssistanceRequest(models.Model):
    """
    Model for assistance requests to technicians
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assistance_requests')
    technician = models.ForeignKey(Technician, on_delete=models.CASCADE, related_name='assistance_requests')
    ticket = models.ForeignKey(
        'CreateTicket', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='assistance_requests'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Assistance Request: {self.title}"

    class Meta:
        verbose_name = 'Assistance Request'
        verbose_name_plural = 'Assistance Requests'

# Signals
# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#    """Create UserProfile when a new User is created"""
#    if created:
#        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()

@receiver(post_save, sender=UserProfile)
def create_technician_profile(sender, instance, created, **kwargs):
    """Create Technician profile when UserProfile is marked as technician"""
    if instance.is_technician:
        Technician.objects.get_or_create(user_profile=instance)


#SPRINT 2
PRIORITY_CHOICES = [
    ('Low', 'Low'),
    ('Medium', 'Medium'),
    ('High', 'High'),
]

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('pending', 'Pending'),
        ('solved', 'Solved'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    technician = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ticket_assigned',  # changed
        db_column='technician_id'
    )

    title = models.CharField(max_length=100)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='Medium'  # ✅ important for existing rows
    )  # ✅ New field
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
    promotions = models.BooleanField(default=False)
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


 #Create Ticket
from django.db import models
from django.conf import settings  # If you use custom user models


class CreateTicket(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High (Service Degradation)'),
        ('critical', 'Critical (Service Down)'),
    ]

    CATEGORY_CHOICES = [
        ('hardware', 'Hardware'),
        ('software', 'Software'),
        ('network', 'Network'),
        ('other', 'Other'),
    ]

    # Link ticket to the user who created it (assuming a User model exists)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=50, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    technician = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='create_ticket_assigned',  # changed
    )

    def __str__(self):
        return f"Ticket {self.id}: {self.title}"


from django.db import models
from django.contrib.auth.models import User

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', null=True, blank=True)
    ticket = models.ForeignKey('CreateTicket', on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()  # e.g., "Technician replied to your ticket"
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification to {self.recipient.username}: {self.message}"


#TECHNICIAN NOTIFICATION
class Notifications_Technician(models.Model):
    technician = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    message = models.CharField(max_length=255)
    ticket = models.ForeignKey('Ticket', on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications_technician'



from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings

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
    ticket = models.ForeignKey('CreateTicket', on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['technician', 'user', 'ticket']
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

# SPRINT 2 Models
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
        related_name='ticket_assigned',
        db_column='technician_id'
    )

    title = models.CharField(max_length=100)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='Medium'
    )
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
        db_table = 'user_settings'

    def __str__(self):
        return f"{self.user.username}'s Settings"

class Contact(models.Model):
    """
    Model to store user's contacts (technicians they can message) and bot chats
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_contacts')
    contact_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='added_as_contact', null=True, blank=True)
    contact_name = models.CharField(max_length=255)
    is_bot_chat = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'contact_user']
        db_table = 'contacts'
    
    def __str__(self):
        return f"{self.user.username} -> {self.contact_name}"

class ChatSession(models.Model):
    """
    Unified chat session model for user-technician conversations
    """
    CHAT_TYPES = [
        ('user_tech', 'User-Technician'),
        ('user_bot', 'User-Bot'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
        ('deleted', 'Deleted'),  # ADD THIS FOR SOFT DELETE
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_chat_sessions')
    technician = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='technician_chat_sessions',
        null=True,
        blank=True
    )
    ticket = models.ForeignKey(
        'CreateTicket',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='chat_sessions'
    )
    chat_type = models.CharField(max_length=20, choices=CHAT_TYPES, default='user_tech')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)  # ADD THIS FOR SOFT DELETE
    
    class Meta:
        db_table = 'chat_sessions'
        unique_together = ['user', 'technician', 'ticket']
        ordering = ['-last_message_at', '-created_at']
    
    def __str__(self):
        if self.chat_type == 'user_bot':
            return f"Bot Chat - {self.user.username}"
        else:
            tech_name = self.technician.get_full_name() if self.technician else "No Technician"
            return f"Chat: {self.user.username} - {tech_name} (Ticket: {self.ticket.id if self.ticket else 'No Ticket'})"

    @property
    def other_party_name(self):
        """Get the name of the other party in the chat"""
        if self.chat_type == 'user_bot':
            return "FixIT Assistant"
        elif self.technician:
            return f"{self.technician.first_name} {self.technician.last_name}".strip() or self.technician.username
        return "Unknown"

    @property
    def unread_count_for_user(self):
        """Count unread messages for the user"""
        return self.messages.filter(is_read=False, receiver=self.user).count()

    @property
    def unread_count_for_technician(self):
        """Count unread messages for the technician"""
        return self.messages.filter(is_read=False, receiver=self.technician).count()

    def get_last_message(self):
        """Get the most recent message in the chat"""
        return self.messages.filter(is_deleted=False).order_by('-created_at').first()

    def mark_messages_as_read(self, user):
        """Mark all messages as read for a user"""
        self.messages.filter(receiver=user, is_read=False).update(is_read=True)

class Message(models.Model):
    """
    Enhanced Message model with full CRUD functionality
    """
    MESSAGE_TYPES = [
        ('user_to_tech', 'User to Technician'),
        ('tech_to_user', 'Technician to User'),
        ('user_to_bot', 'User to Bot'),
        ('bot_to_user', 'Bot to User'),
    ]
    
    chat_session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
        null=True,  # Add this temporarily
        blank=True  
    )
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_messages',
        null=True,
        blank=True
    )
    receiver = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='received_messages',
        null=True,
        blank=True
    )
    content = models.TextField()
    bot_response_data = models.JSONField(
        null=True, 
        blank=True,
        help_text="Structured data for bot responses (buttons, related FAQs, etc.)"
    )
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='deleted_messages'
    )
    
    class Meta:
        db_table = 'messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['chat_session', 'created_at']),
            models.Index(fields=['sender', 'receiver', 'created_at']),
        ]
    
    def __str__(self):
        sender_name = self.sender.username if self.sender else 'System'
        receiver_name = self.receiver.username if self.receiver else 'Unknown'
        return f"{sender_name} to {receiver_name}: {self.content[:50]}"
    def __str__(self):
        sender_name = self.sender.username if self.sender else 'System'
        receiver_name = self.receiver.username if self.receiver else 'Unknown'
        return f"{sender_name} to {receiver_name}: {self.content[:50]}"
    
    @property
    def has_bot_data(self):
        """Check if message has bot response data"""
        return bool(self.bot_response_data) and self.message_type == 'bot_to_user'
    
    @property
    def bot_buttons(self):
        """Get bot buttons from response data"""
        if self.has_bot_data:
            return self.bot_response_data.get('buttons', [])
        return []
    
    @property
    def related_faqs(self):
        """Get related FAQs from response data"""
        if self.has_bot_data:
            return self.bot_response_data.get('related_faqs', [])
        return []
    
    @property
    def response_type(self):
        """Get response type"""
        if self.has_bot_data:
            return self.bot_response_data.get('type', 'default')
        return 'default'

    def soft_delete(self, user):
        """Soft delete the message"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save()

    def update_content(self, new_content, user):
        """Update message content with permission check"""
        if self.sender != user:
            raise PermissionError("You can only edit your own messages")
        
        self.content = new_content
        self.save()

class MessageEditHistory(models.Model):
    """
    Track message edit history
    """
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='edit_history')
    old_content = models.TextField()
    new_content = models.TextField()
    edited_by = models.ForeignKey(User, on_delete=models.CASCADE)
    edited_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'message_edit_history'
        ordering = ['-edited_at']

class Attachment(models.Model):
    """
    Model for message attachments
    """
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='message_attachments/%Y/%m/%d/')
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()
    file_type = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'message_attachments'

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
        related_name='create_ticket_assigned',
    )

    def __str__(self):
        return f"Ticket {self.id}: {self.title}"

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', null=True, blank=True)
    ticket = models.ForeignKey('CreateTicket', on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification to {self.recipient.username}: {self.message}"

class Notifications_Technician(models.Model):
    technician = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    message = models.CharField(max_length=255)
    ticket = models.ForeignKey('Ticket', on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications_technician'

# Remove duplicate BotChat and BotMessage models since we're using ChatSession and Message

# Signals
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

@receiver(post_save, sender=AssistanceRequest)
def create_chat_session_on_assistance_request(sender, instance, created, **kwargs):
    """
    Automatically create a chat session when an assistance request is created
    """
    if created and instance.status == 'accepted':
        # Create chat session for user-technician communication
        chat_session, created = ChatSession.objects.get_or_create(
            user=instance.user,
            technician=instance.technician.user_profile.user,
            ticket=instance.ticket,
            defaults={
                'chat_type': 'user_tech',
                'status': 'active'
            }
        )
        
        # Create initial message
        if created:
            Message.objects.create(
                chat_session=chat_session,
                sender=instance.user,
                receiver=instance.technician.user_profile.user,
                content=f"Assistance request created for ticket: {instance.ticket.title}",
                message_type='user_to_tech'
            )



# models.py - Enhanced FAQ models
class FAQCategory(models.Model):
    """Categories for organizing FAQ items"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    icon = models.CharField(max_length=50, default='fa-question-circle')
    
    class Meta:
        verbose_name_plural = "FAQ Categories"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class FAQItem(models.Model):
    """FAQ items that can be used in both help center and bot responses"""
    category = models.ForeignKey(FAQCategory, on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=255)
    short_question = models.CharField(max_length=100, help_text="Short version for bot buttons")
    answer = models.TextField()
    short_answer = models.TextField(help_text="Brief answer for quick responses")
    read_time = models.CharField(max_length=20, default="5 min read")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    keywords = models.TextField(help_text="Comma-separated keywords for bot matching", blank=True)
    bot_priority = models.IntegerField(default=0, help_text="Priority in bot responses (higher = more likely)")
    show_in_dashboard = models.BooleanField(default=True, help_text="Show in dashboard troubleshooting")
    show_in_bot_buttons = models.BooleanField(default=True, help_text="Show as quick buttons in bot chat")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'question']
    
    def __str__(self):
        return self.question
    
    def get_keywords_list(self):
        """Get list of keywords for bot matching"""
        if self.keywords:
            return [k.strip().lower() for k in self.keywords.split(',')]
        return []
    
    def get_short_description(self):
        """Extract a short description for dashboard cards"""
        return self.short_answer or self.answer[:100] + '...' if len(self.answer) > 100 else self.answer
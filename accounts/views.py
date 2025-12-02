import os
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.db import models 
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from unicodedata import category

from .forms import UserSignUpForm, UserLoginForm, UserUpdateForm, ProfileUpdateForm, ProfilePictureForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect
from django.contrib.auth.models import User

from .models import Ticket, UserSettings
from django.db.models import Q, Avg, Count
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
import json
from .models import Technician, TechnicianSpecialty, AssistanceRequest
from .models import User, UserProfile, Message, Contact, CreateTicket, ChatSession, Notification, Notifications_Technician, MessageEditHistory, TechnicianReview
from django.db.models.signals import post_save
from django.utils import timezone
from accounts.models import FAQCategory, FAQItem


def role_select_view(request):
    """
    Handle role selection page - accessible without authentication
    """
    # If user is already logged in, redirect to appropriate dashboard
    if request.user.is_authenticated:
        return redirect_to_correct_dashboard(request.user)

    context = {
        'title': 'Welcome to FixIT',
        'hide_navigation': True
    }
    return render(request, 'accounts/role_select.html', context)

def signup_view(request):
    """
    Handle user registration with role selection (User or Technician)
    """
    # Redirect logged-in users
    if request.user.is_authenticated:
        return redirect_to_correct_dashboard(request.user)

    if request.method == 'POST':
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            # Save user (password already handled by UserCreationForm)
            user = form.save()

            # Create or get profile
            profile, created = UserProfile.objects.get_or_create(user=user)

            # Set technician flag from form
            user_type = form.cleaned_data.get('user_type', 'user')
            profile.is_technician = (user_type == 'technician')
            profile.save()

            # Log the user in
            login(request, user)
            messages.success(request, f'Welcome {user.username}! Your account has been created successfully.')

            # Redirect to the correct dashboard
            return redirect_to_correct_dashboard(user)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Prefill hidden user_type from query param
        user_type = request.GET.get('user_type', 'user')
        form = UserSignUpForm(initial={'user_type': user_type})

    context = {
        'form': form,
        'title': 'Sign Up - FixIT',
        'hide_navigation': True
    }
    return render(request, 'accounts/signup.html', context)



def login_view(request):
    """
    Handle user login and redirect to correct dashboard
    """
    if request.user.is_authenticated:
        return redirect_to_correct_dashboard(request.user)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')

            # Get or create profile and redirect accordingly
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'is_technician': False}
            )

            if profile.is_technician:
                return redirect('technician_dashboard')
            else:
                return redirect('user_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    context = {
        'title': 'Login - FixIT',
        'hide_navigation': True
    }
    return render(request, 'accounts/login.html', context)


@login_required
def logout_view(request):
    """
    Handle user logout
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
def dashboard_view(request):
    """
    Display user dashboard with account details - redirects to appropriate dashboard
    """
    return redirect_to_correct_dashboard(request.user)


@login_required
def technician_directory_view(request):
    """
    Display technician directory with dynamic data from database
    """
    # Get all technicians with their profiles and specialties
    technicians = Technician.objects.select_related(
        'user_profile',
        'user_profile__user'
    ).prefetch_related('specialties').all()

    # Apply search filter
    search_query = request.GET.get('search', '')
    if search_query:
        technicians = technicians.filter(
            Q(user_profile__user__first_name__icontains=search_query) |
            Q(user_profile__user__last_name__icontains=search_query) |
            Q(user_profile__user__username__icontains=search_query) |
            Q(specialties__name__icontains=search_query) |
            Q(bio__icontains=search_query)
        ).distinct()

    # Apply service filter
    service_filter = request.GET.get('service', '')
    if service_filter:
        technicians = technicians.filter(
            specialties__name__icontains=service_filter
        ).distinct()

    # Apply availability filter
    availability_filter = request.GET.get('availability', '')
    if availability_filter == 'available':
        technicians = technicians.filter(is_available=True)
    elif availability_filter == 'busy':
        technicians = technicians.filter(is_available=False)

    # Apply sorting
    sort_by = request.GET.get('sort', 'rating')
    if sort_by == 'name':
        technicians = technicians.order_by('user_profile__user__first_name', 'user_profile__user__last_name')
    elif sort_by == 'experience':
        technicians = technicians.order_by('-experience_years')
    elif sort_by == 'response_time':
        technicians = technicians.order_by('average_response_time')
    elif sort_by == 'rate':
        technicians = technicians.order_by('hourly_rate')
    else:  # Default to rating
        technicians = technicians.order_by('-average_rating', 'user_profile__user__first_name')

    # Get all specialties for filter dropdown
    all_specialties = TechnicianSpecialty.objects.all()

    # Prepare technician data for template
    technician_data = []
    for technician in technicians:
        technician_data.append({
            'id': technician.id,
            'user_id': technician.user_profile.user.id,
            'first_name': technician.user_profile.user.first_name,
            'last_name': technician.user_profile.user.last_name,
            'username': technician.user_profile.user.username,
            'email': technician.user_profile.user.email,
            'specialties': technician.get_specialties_list(),
            'rating': technician.average_rating,
            'review_count': technician.review_count,
            'experience_years': technician.experience_years,
            'response_time': technician.average_response_time,
            'availability_status': technician.availability_status,
            'availability_class': technician.availability_class,
            'profile_picture_url': technician.profile_picture_url,
            'initials': technician.initials,
            'bio': technician.bio,
            'hourly_rate': technician.hourly_rate,
            'certification': technician.certification,
            'completed_tickets': technician.completed_tickets,
            'success_rate': technician.success_rate,
            'languages': technician.languages,
        })

    context = {
        'technicians': technician_data,
        'all_specialties': all_specialties,
        'search_query': search_query,
        'selected_service': service_filter,
        'selected_sort': sort_by,
        'selected_availability': availability_filter,
        'user_tickets': CreateTicket.objects.filter(user=request.user).exclude(status='resolved').order_by('-created_at'),
        'title': 'Technician Directory - FixIT'
    }

    return render(request, 'dashboard/technician_directory.html', context)



import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Ticket, Technician
@csrf_exempt
@login_required
def request_assistance_view(request):
    print("🔧 === REQUEST ASSISTANCE STARTED ===")

    if request.method != 'POST':
        print("❌ Invalid method")
        return JsonResponse({
            'success': False,
            'error': 'Only POST requests allowed'
        }, status=400)

    try:
        # Check if body exists
        if not request.body:
            print("❌ Empty request body")
            return JsonResponse({
                'success': False,
                'error': 'Empty request body'
            }, status=400)

        # Parse JSON data
        raw_body = request.body.decode('utf-8')
        print(f"📦 Raw body: {raw_body}")

        data = json.loads(raw_body)
        print(f"📋 Parsed data: {data}")

        # Extract fields
        tech_id = data.get('technician_id')
        title = data.get('title')
        description = data.get('description')
        priority = data.get('priority')

        print(f"🔍 Extracted fields - tech_id: {tech_id}, title: {title}, description: {description}, priority: {priority}")

        # Validate required fields
        if not tech_id:
            print("❌ Missing technician_id")
            return JsonResponse({
                'success': False,
                'error': 'Missing technician_id'
            }, status=400)

        if not title or not description:
            missing = []
            if not title: missing.append('title')
            if not description: missing.append('description')
            print(f"❌ Missing fields: {missing}")
            return JsonResponse({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing)}'
            }, status=400)

        # Get the technician
        try:
            technician = Technician.objects.get(id=tech_id)
            technician_user = technician.user_profile.user
            print(f"✅ Found technician: {technician_user.username} (ID: {technician.id})")
        except Technician.DoesNotExist:
            print(f"❌ Technician with id {tech_id} not found")
            return JsonResponse({
                'success': False,
                'error': f'Technician with ID {tech_id} not found'
            }, status=400)
        except Exception as e:
            print(f"❌ Error getting technician: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Error finding technician: {str(e)}'
            }, status=400)

        # Create the ticket
        #TEST
        print("🎫 Creating ticket...")
        try:
            # Use last ticket category if available, otherwise default
            last_ticket = CreateTicket.objects.filter(user=request.user).order_by('-id').first()

            ticket = CreateTicket.objects.create(
                user=request.user,
                title=title,
                description=description,
                priority=priority or 'medium',
                category=last_ticket.category if last_ticket else 'Others',
                status='open'
            )
            print(f"✅ Ticket created: {ticket.id}")
        except Exception as e:
            print(f"❌ Error creating ticket: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Error creating ticket: {str(e)}'
            }, status=400)

        # Create assistance request
        print("📋 Creating assistance request...")
        try:
            assistance_request = AssistanceRequest.objects.create(
                user=request.user,
                technician=technician,
                ticket=ticket,
                title=title,
                description=description,
                priority=priority or 'medium',
                status='pending'
            )
            print(f"✅ Assistance request created: {assistance_request.id}")
        except Exception as e:
            print(f"❌ Error creating assistance request: {e}")
            # Delete the ticket if assistance request fails
            ticket.delete()
            return JsonResponse({
                'success': False,
                'error': f'Error creating assistance request: {str(e)}'
            }, status=400)

        # Create contact relationship
        print("👥 Creating contact...")
        try:
            contact_name = f"{technician_user.first_name} {technician_user.last_name}".strip()
            if not contact_name:
                contact_name = technician_user.username

            contact, created = Contact.objects.get_or_create(
                user=request.user,
                contact_user=technician_user,
                defaults={'contact_name': contact_name}
            )
            print(f"✅ Contact {'created' if created else 'exists'}: {contact.id}")
        except Exception as e:
            print(f"⚠️ Contact creation warning: {e}")
            # Don't fail the whole request if contact creation fails

        # Create initial message
        print("💬 Creating initial message...")
        try:
            initial_message = f"New assistance request: {title}\n\nDescription: {description}\nPriority: {priority or 'medium'}"

            Message.objects.create(
                sender=request.user,
                receiver=technician_user,
                content=initial_message,
                timestamp=timezone.now()
            )
            print("✅ Initial message created")
        except Exception as e:
            print(f"⚠️ Message creation warning: {e}")
            # Don't fail the whole request if message creation fails

        # Create notification for technician
        print("🔔 Creating notification...")
        try:
            Notifications_Technician.objects.create(
                technician=technician_user,
                message=f"New assistance request from {request.user.username}: {title}",
                ticket=ticket
            )
            print("✅ Notification created")
        except Exception as e:
            print(f"⚠️ Notification creation warning: {e}")
            # Don't fail the whole request if notification creation fails

        print("🎉 === REQUEST ASSISTANCE COMPLETED SUCCESSFULLY ===")
        return JsonResponse({
            'success': True,
            'ticket_id': ticket.id,
            'message': 'Assistance request sent successfully'
        })

    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data in request'
        }, status=400)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


@csrf_exempt
@login_required
def assign_ticket_to_technician(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST requests allowed'}, status=400)
    try:
        data = json.loads(request.body.decode('utf-8'))
        tech_id = data.get('technician_id')
        ticket_id = data.get('ticket_id')
        if not tech_id or not ticket_id:
            return JsonResponse({'success': False, 'error': 'Missing technician_id or ticket_id'}, status=400)

        technician = Technician.objects.get(id=tech_id)
        technician_user = technician.user_profile.user
        ticket = get_object_or_404(CreateTicket, id=ticket_id, user=request.user)

        existing = AssistanceRequest.objects.filter(user=request.user, technician=technician, ticket=ticket).exists()
        if existing:
            return JsonResponse({'success': True, 'ticket_id': ticket.id, 'message': 'Assistance request already exists for this technician and ticket.'})

        AssistanceRequest.objects.create(
            user=request.user,
            technician=technician,
            ticket=ticket,
            title=ticket.title,
            description=ticket.description,
            priority=ticket.priority,
            status='pending'
        )

        Notifications_Technician.objects.create(
            technician=technician_user,
            message=f"Ticket #{ticket.id} assigned request from {request.user.username}",
            ticket=ticket
        )

        return JsonResponse({'success': True, 'ticket_id': ticket.id, 'message': 'Ticket assigned to technician (pending)'})
    except Technician.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Technician not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

#//////////////////////////////////////////////////////////////////////////////////////////////////////////////
@login_required
def technician_detail_view(request, technician_id):
    """
    Display detailed technician profile
    """
    technician = get_object_or_404(
        Technician.objects.select_related('user_profile', 'user_profile__user')
                         .prefetch_related('specialties', 'reviews'),
        id=technician_id
    )

    # Get recent reviews
    recent_reviews = technician.reviews.select_related('user').order_by('-created_at')[:5]

    avg_rating = float(technician.average_rating or 0)
    full_stars = int(avg_rating)
    has_half_star = (avg_rating - full_stars) >= 0.5 and full_stars < 5
    empty_stars = 5 - full_stars - (1 if has_half_star else 0)

    context = {
        'technician': technician,
        'recent_reviews': recent_reviews,
        'avg_rating': avg_rating,
        'full_stars': full_stars,
        'has_half_star': has_half_star,
        'empty_stars': empty_stars,
        'title': f'{technician.full_name} - Technician Profile - FixIT'
    }

    return render(request, 'dashboard/technician_profile', context)

@receiver(post_save, sender=AssistanceRequest)
def create_chat_session_on_assistance_request(sender, instance, created, **kwargs):
    """
    Automatically create a chat session when an assistance request is created
    """
    print(f"🔧 CHAT SIGNAL: AssistanceRequest - Created: {created}, Status: {instance.status}, Ticket: {instance.ticket.id if instance.ticket else 'No Ticket'}")
    
    # Create chat session for ANY new assistance request, regardless of status
    if created:
        try:
            # Get the technician user
            technician_user = instance.technician.user_profile.user
            print(f"🔧 CHAT SIGNAL: Technician: {technician_user.username}, User: {instance.user.username}")
            
            # Check if chat session already exists
            existing_chat = ChatSession.objects.filter(
                user=instance.user,
                technician=technician_user,
                ticket=instance.ticket
            ).first()
            
            if existing_chat:
                print(f"🔧 CHAT SIGNAL: Chat session already exists - ID: {existing_chat.id}")
                return
            
            # Create new chat session
            chat_session = ChatSession.objects.create(
                user=instance.user,
                technician=technician_user,
                ticket=instance.ticket,
                chat_type='user_tech',
                status='active',
                last_message_at=timezone.now()
            )
            
            print(f"🔧 CHAT SIGNAL: Created new chat session - ID: {chat_session.id}")
            
            # Create initial message
            initial_content = f"New assistance request: {instance.title}\n\nDescription: {instance.description}\nPriority: {instance.priority}"
            
            Message.objects.create(
                chat_session=chat_session,
                sender=instance.user,
                receiver=technician_user,
                content=initial_content,
                message_type='user_to_tech'
            )
            
            print(f"🔧 CHAT SIGNAL: Initial message created for chat {chat_session.id}")
            
        except Exception as e:
            print(f"❌ CHAT SIGNAL: Error creating chat session: {e}")
            import traceback
            print(f"🔧 CHAT SIGNAL: Traceback: {traceback.format_exc()}")
            

   
@login_required
@require_http_methods(["GET", "POST"])
def user_messages_view(request):
    """
    Enhanced user messages view with full CRUD operations
    """
    user = request.user
    
    if request.method == 'POST':
        return handle_message_post_request(request, user)
    
    # GET request - display messages interface
    return render_user_messages_with_tickets(request, user)

def handle_message_post_request(request, user):
    """Handle all POST requests for messages"""
    action = request.POST.get('action')
    
    if action == 'send_message':
        return handle_send_message(request, user)
    elif action == 'edit_message':
        return handle_edit_message(request, user)
    elif action == 'delete_message':
        return handle_delete_message(request, user)
    elif action == 'start_chat':
        return handle_start_chat(request, user)
    elif action == 'delete_chat':  
        return handle_delete_chat(request)
    elif action == 'mark_read':
        return handle_mark_read(request, user)
    # ADD THESE TWO NEW CONDITIONS:
    elif request.POST.get('start_ticket_chat'):
        return handle_start_ticket_chat(request, user)
    elif request.POST.get('start_bot_chat'):
        return handle_start_bot_chat(request, user)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid action'})

def handle_send_message(request, user):
    """Handle sending a new message with enhanced bot responses"""
    try:
        chat_session_id = request.POST.get('chat_session_id')
        content = request.POST.get('content', '').strip()
        
        if not content:
            return JsonResponse({'success': False, 'error': 'Message content cannot be empty'})
        
        if not chat_session_id:
            return JsonResponse({'success': False, 'error': 'Chat session ID is required'})
        
        # Get chat session
        chat_session = ChatSession.objects.get(
            id=chat_session_id,
            user=user
        )
        
        # Create user message
        user_message = Message.objects.create(
            chat_session=chat_session,
            sender=user,
            content=content,
            message_type='user_to_bot'
        )
        
        # Generate enhanced bot response
        bot_response = generate_bot_response(content)
        
        print(f"🔧 DEBUG: Bot response generated - Type: {bot_response.get('type')}")
        print(f"🔧 DEBUG: Bot buttons count: {len(bot_response.get('buttons', []))}")
        
        # Prepare bot response data
        bot_data = {
            'type': bot_response.get('type', 'default'),
            'buttons': bot_response.get('buttons', []),
            'related_faqs': bot_response.get('related_faqs', []),
            'faq_id': bot_response.get('faq_id'),
            'category': bot_response.get('category')
        }
        
        # Create bot message with structured data
        bot_message = Message.objects.create(
            chat_session=chat_session,
            content=bot_response.get('message', ''),
            message_type='bot_to_user',
            bot_response_data=bot_data  # Store structured data in JSON field
        )
        
        # Update chat session
        chat_session.last_message_at = timezone.now()
        chat_session.save()
        
        # Return structured response including buttons
        return JsonResponse({
            'success': True,
            'bot_response': {
                'message': bot_response.get('message', ''),
                'type': bot_response.get('type', 'default'),
                'buttons': bot_response.get('buttons', []),
                'related_faqs': bot_response.get('related_faqs', []),
                'faq_id': bot_response.get('faq_id'),
                'category': bot_response.get('category')
            }
        })
        
    except ChatSession.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Chat session not found'})
    except Exception as e:
        print(f"❌ ERROR in handle_send_message: {e}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return JsonResponse({'success': False, 'error': str(e)})
    
def handle_edit_message(request, user):
    """Handle editing an existing message"""
    try:
        message_id = request.POST.get('message_id')
        new_content = request.POST.get('new_content', '').strip()
        
        if not new_content:
            return JsonResponse({'success': False, 'error': 'Message content cannot be empty'})
        
        message = Message.objects.get(id=message_id, sender=user, is_deleted=False)
        
        # Save edit history
        MessageEditHistory.objects.create(
            message=message,
            old_content=message.content,
            new_content=new_content,
            edited_by=user
        )
        
        # Update message
        message.content = new_content
        message.save()
        
        return JsonResponse({
            'success': True,
            'message': serialize_message(message)
        })
        
    except Message.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Message not found or unauthorized'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def handle_delete_message(request, user):
    """Handle soft deleting a message"""
    try:
        message_id = request.POST.get('message_id')
        message = Message.objects.get(id=message_id, sender=user, is_deleted=False)
        
        # Use the soft_delete method if it exists, otherwise implement basic deletion
        if hasattr(message, 'soft_delete'):
            message.soft_delete(user)
        else:
            message.is_deleted = True
            message.deleted_at = timezone.now()
            message.deleted_by = user
            message.save()
        
        return JsonResponse({'success': True, 'message': 'Message deleted successfully'})
        
    except Message.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Message not found or unauthorized'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def handle_start_chat(request, user):
    """Handle starting a new chat session"""
    try:
        technician_id = request.POST.get('technician_id')
        ticket_id = request.POST.get('ticket_id')
        
        if technician_id:
            # Start user-technician chat
            technician = User.objects.get(id=technician_id, profile__is_technician=True)
            
            # Get or create ticket if provided
            ticket = None
            if ticket_id:
                ticket = CreateTicket.objects.get(id=ticket_id, user=user)
            
            chat_session, created = ChatSession.objects.get_or_create(
                user=user,
                technician=technician,
                ticket=ticket,
                defaults={
                    'chat_type': 'user_tech',
                    'status': 'active'
                }
            )
            
            if created:
                # Create welcome message
                Message.objects.create(
                    chat_session=chat_session,
                    sender=user,
                    receiver=technician,
                    content=f"Hello! I'd like to discuss {'ticket #' + str(ticket.id) if ticket else 'a technical issue'}.",
                    message_type='user_to_tech'
                )
            
            return JsonResponse({
                'success': True,
                'chat_session_id': chat_session.id,
                'redirect_url': f'/user/messages/?chat={chat_session.id}'
            })
            
        else:
            # Start bot chat
            chat_session, created = ChatSession.objects.get_or_create(
                user=user,
                chat_type='user_bot',
                defaults={'status': 'active'}
            )
            
            if created:
                # Create welcome message
                Message.objects.create(
                    chat_session=chat_session,
                    content="Hello! I'm FixIT Assistant 👋 I'm here to help you with common issues and FAQs. How can I assist you today?",
                    message_type='bot_to_user'
                )
            
            return JsonResponse({
                'success': True,
                'chat_session_id': chat_session.id,
                'redirect_url': f'/user/messages/?chat={chat_session.id}'
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
@login_required
@require_POST
@csrf_exempt
def handle_delete_chat(request):
    """Handle soft deleting a chat session"""
    try:
        chat_session_id = request.POST.get('chat_session_id')
        
        if not chat_session_id:
            return JsonResponse({'success': False, 'error': 'Chat session ID is required'})
        
        # Use the same pattern
        chat_session = ChatSession.objects.filter(
            Q(user=request.user) | Q(technician=request.user)
        ).get(id=chat_session_id)
        
        # Soft delete by updating status instead of actually deleting
        chat_session.status = 'deleted'
        chat_session.deleted_at = timezone.now()
        chat_session.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Chat session deleted successfully'
        })
        
    except ChatSession.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Chat session not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
def handle_mark_read(request, user):
    """Handle marking messages as read"""
    try:
        chat_session_id = request.POST.get('chat_session_id')
        chat_session = ChatSession.objects.get(id=chat_session_id)
        
        # Mark messages as read for this user
        Message.objects.filter(
            chat_session=chat_session,
            receiver=user,
            is_read=False
        ).update(is_read=True)
        
        return JsonResponse({'success': True})
        
    except ChatSession.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Chat session not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def render_user_messages_with_tickets(request, user):
    """Render user messages interface with ticket integration"""
    print(f"🔧 DEBUG: Rendering user messages for {user.username}")
    
    # Get user's tickets
    user_tickets = CreateTicket.objects.filter(user=user).order_by('-created_at')
    
    # Get user's chat sessions
    chat_sessions = ChatSession.objects.filter(
        Q(user=user) | Q(technician=user)
    ).select_related('user', 'technician', 'ticket').prefetch_related('messages').distinct()
    
    # Prepare chat data for template
    user_chats = []
    for chat in chat_sessions:
        if chat.chat_type == 'user_bot':
            contact_name = "FixIT Assistant"
            is_bot = True
            ticket_info = None
        else:
            if chat.technician:
                contact_name = f"{chat.technician.first_name} {chat.technician.last_name}".strip() or chat.technician.username
            else:
                contact_name = "Unknown Technician"
            is_bot = False
            ticket_info = {
                'id': chat.ticket.id if chat.ticket else None,
                'title': chat.ticket.title if chat.ticket else 'General Support',
                'status': chat.ticket.status if chat.ticket else 'open'
            }
        
        user_chats.append({
            'id': chat.id,
            'contact_name': contact_name,
            'is_bot': is_bot,
            'last_message_at': chat.last_message_at,
            'chat_type': chat.chat_type,
            'ticket': ticket_info,
        })
    
    # Get selected chat
    selected_chat_id = request.GET.get('chat')
    selected_chat = None
    chat_messages = []
    
    if selected_chat_id:
        try:
            selected_chat_obj = ChatSession.objects.filter(
                Q(user=user) | Q(technician=user)
            ).get(id=selected_chat_id)
            
            # Prepare selected chat data
            if selected_chat_obj.chat_type == 'user_bot':
                contact_name = "FixIT Assistant"
                is_bot = True
                ticket_info = None
            else:
                if selected_chat_obj.technician:
                    contact_name = f"{selected_chat_obj.technician.first_name} {selected_chat_obj.technician.last_name}".strip() or selected_chat_obj.technician.username
                else:
                    contact_name = "Unknown Technician"
                is_bot = False
                ticket_info = {
                    'id': selected_chat_obj.ticket.id if selected_chat_obj.ticket else None,
                    'title': selected_chat_obj.ticket.title if selected_chat_obj.ticket else 'General Support',
                    'status': selected_chat_obj.ticket.status if selected_chat_obj.ticket else 'open'
                }
            
            selected_chat = {
                'id': selected_chat_obj.id,
                'contact_name': contact_name,
                'is_bot': is_bot,
                'chat_type': selected_chat_obj.chat_type,
                'ticket': ticket_info,
            }
            
            # Mark messages as read when opening chat
            Message.objects.filter(
                chat_session=selected_chat_obj,
                receiver=user,
                is_read=False
            ).update(is_read=True)
            
            # Get messages - IMPORTANT: Prefetch related data if needed
            chat_messages = selected_chat_obj.messages.filter(is_deleted=False).order_by('created_at')
            
            # Debug: Check bot messages
            bot_messages = chat_messages.filter(message_type='bot_to_user')
            print(f"🔧 DEBUG: Found {bot_messages.count()} bot messages")
            for msg in bot_messages:
                print(f"🔧 DEBUG: Bot message {msg.id} has bot_data: {bool(msg.bot_response_data)}")
                if msg.bot_response_data:
                    print(f"🔧 DEBUG: Buttons: {len(msg.bot_response_data.get('buttons', []))}")
            
        except ChatSession.DoesNotExist:
            selected_chat = None
    
    # Get available technicians for new chats
    technicians = Technician.objects.select_related(
        'user_profile__user'
    ).filter(is_available=True)
    
    try:
        # Import your FAQ models
        from .models import FAQCategory, FAQItem
        
        # Get FAQ categories with their top FAQs for bot buttons
        faq_categories = FAQCategory.objects.prefetch_related(
            models.Prefetch(
                'faqs',
                queryset=FAQItem.objects.filter(
                    is_active=True,
                    show_in_bot_buttons=True
                ).order_by('-bot_priority')[:3]
            )
        ).order_by('order')
        
        # Add top_faqs attribute to each category
        for category in faq_categories:
            category.top_faqs = list(category.faqs.all())
            
    except Exception as e:
        print(f"⚠️ FAQ data not available: {e}")
        faq_categories = []  # Empty list as fallback
    
    context = {
        'user': user,
        'profile': user.profile,
        'title': 'Messages - FixIT',
        'user_chats': user_chats,
        'user_tickets': user_tickets,  # Add tickets to context
        'selected_chat': selected_chat,
        'chat_messages': chat_messages,
        'technicians': technicians,
        'faq_categories': faq_categories,
    }
    
    return render(request, 'dashboard/user_message.html', context)



@login_required
@require_http_methods(["GET", "POST"])
def technician_messages_view(request):
    """
    Technician messages view with similar CRUD functionality
    """
    user = request.user
    
    print(f"🔧 DEBUG: Technician Messages View - User: {user.username}")
    
    if request.method == 'POST':
        return handle_technician_message_post(request, user)
    
    # GET request - display technician messages
    return render_technician_messages_interface(request, user)

def handle_technician_message_post(request, user):
    """Handle technician message POST requests"""
    action = request.POST.get('action')
    
    if action == 'send_message':
        return handle_technician_send_message(request, user)
    elif action == 'edit_message':
        return handle_edit_message(request, user)
    elif action == 'delete_message':
        return handle_delete_message(request, user)
    elif action == 'mark_read':
        return handle_mark_read(request, user)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid action'})

def handle_technician_send_message(request, user):
    """Handle technician sending a message"""
    try:
        chat_session_id = request.POST.get('chat_session_id')
        content = request.POST.get('content', '').strip()
        
        if not content:
            return JsonResponse({'success': False, 'error': 'Message content cannot be empty'})
        
        chat_session = ChatSession.objects.get(
            id=chat_session_id,
            technician=user  # Ensure technician owns this chat session
        )
        
        # Create message
        message = Message.objects.create(
            chat_session=chat_session,
            sender=user,
            receiver=chat_session.user,
            content=content,
            message_type='tech_to_user'
        )
        
        # Update chat session
        chat_session.last_message_at = timezone.now()
        chat_session.save()
        
        # Create notification for user
        create_message_notification(chat_session.user, user, message)
        
        return JsonResponse({
            'success': True,
            'message': 'Message sent successfully'
        })
        
    except ChatSession.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Chat session not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def render_technician_messages_interface(request, user):
    """Render technician messages interface with ticket integration"""
    print(f"🔧 DEBUG: Rendering technician messages for {user.username}")
    
    # Get technician's assigned tickets
    technician_tickets = CreateTicket.objects.filter(
        assistance_requests__technician__user_profile__user=user
    ).distinct().order_by('-created_at')
    
    print(f"🔧 DEBUG: Found {technician_tickets.count()} assigned tickets")
    
    # AUTO-FIX: Create missing chat sessions
    if technician_tickets.exists():
        created_count = 0
        for ticket in technician_tickets:
            # Check if chat session exists
            existing_chat = ChatSession.objects.filter(
                technician=user,
                ticket=ticket
            ).exists()
            
            if not existing_chat:
                try:
                    # Create chat session
                    chat_session = ChatSession.objects.create(
                        user=ticket.user,
                        technician=user,
                        ticket=ticket,
                        chat_type='user_tech',
                        status='active',
                        last_message_at=timezone.now()
                    )
                    
                    # Create initial message
                    Message.objects.create(
                        chat_session=chat_session,
                        sender=ticket.user,
                        receiver=user,
                        content=f"Ticket: {ticket.title}\n\n{ticket.description}",
                        message_type='user_to_tech'
                    )
                    
                    created_count += 1
                    print(f"🔧 AUTO-FIX: Created chat for ticket {ticket.id}")
                    
                except Exception as e:
                    print(f"❌ AUTO-FIX: Error creating chat for ticket {ticket.id}: {e}")
        
        if created_count > 0:
            print(f"🔧 AUTO-FIX: Created {created_count} missing chat sessions")
            # Refresh the chat sessions query
            chat_sessions = ChatSession.objects.filter(
                technician=user
            ).select_related('user', 'ticket').prefetch_related('messages').distinct()
        else:
            # Use existing query if no new chats were created
            chat_sessions = ChatSession.objects.filter(
                technician=user
            ).select_related('user', 'ticket').prefetch_related('messages').distinct()
    else:
        chat_sessions = ChatSession.objects.filter(
            technician=user
        ).select_related('user', 'ticket').prefetch_related('messages').distinct()
    
    print(f"🔧 DEBUG: Now have {chat_sessions.count()} chat sessions")
    
    # Prepare chat data for template
    customer_chats = []
    for chat in chat_sessions:
        customer = chat.user
        customer_name = f"{customer.first_name} {customer.last_name}".strip() or customer.username
        
        # Get unread message count
        unread_count = chat.messages.filter(
            receiver=user,
            is_read=False
        ).count()
        
        customer_chats.append({
            'id': chat.id,
            'customer_name': customer_name,
            'customer_id': customer.id,
            'ticket_id': chat.ticket.id if chat.ticket else 'N/A',
            'ticket_title': chat.ticket.title if chat.ticket else 'General Support',
            'ticket_status': chat.ticket.status if chat.ticket else 'open',
            'unread_count': unread_count,
            'last_message_at': chat.last_message_at,
        })
    
    print(f"🔧 DEBUG: Prepared {len(customer_chats)} customer chats")
    
    # Get selected chat
    selected_chat_id = request.GET.get('chat')
    selected_chat = None
    chat_messages = []
    
    if selected_chat_id:
        try:
            selected_chat_obj = ChatSession.objects.get(id=selected_chat_id, technician=user)
            customer = selected_chat_obj.user
            customer_name = f"{customer.first_name} {customer.last_name}".strip() or customer.username
            
            # Prepare selected chat data
            selected_chat = {
                'id': selected_chat_obj.id,
                'customer_name': customer_name,
                'customer_id': customer.id,
                'ticket_id': selected_chat_obj.ticket.id if selected_chat_obj.ticket else 'N/A',
                'ticket_title': selected_chat_obj.ticket.title if selected_chat_obj.ticket else 'General Support',
                'ticket_status': selected_chat_obj.ticket.status if selected_chat_obj.ticket else 'open',
            }
            
            # Mark messages as read when opening chat
            Message.objects.filter(
                chat_session=selected_chat_obj,
                receiver=user,
                is_read=False
            ).update(is_read=True)
            
            # Get messages
            chat_messages = selected_chat_obj.messages.filter(is_deleted=False).order_by('created_at')
            
        except ChatSession.DoesNotExist:
            selected_chat = None
    
    context = {
        'user': user,
        'profile': user.profile,
        'title': 'Messages - FixIT Technician',
        'customer_chats': customer_chats,
        'technician_tickets': technician_tickets,  # Add tickets to context
        'selected_chat': selected_chat,
        'chat_messages': chat_messages,
    }
    
    return render(request, 'dashboard/technician_messages.html', context)


def create_missing_chat_sessions_for_technician(user):
    """
    Create chat sessions for any assigned tickets that don't have chats
    """
    print(f"🔧 DEBUG: Checking for missing chat sessions for technician {user.username}")
    
    # Get assigned tickets without chat sessions
    assigned_tickets = CreateTicket.objects.filter(
        assistance_requests__technician__user_profile__user=user
    ).distinct()
    
    created_count = 0
    for ticket in assigned_tickets:
        # Check if chat session already exists
        existing_chat = ChatSession.objects.filter(
            technician=user,
            ticket=ticket
        ).exists()
        
        if not existing_chat:
            # Create new chat session
            chat_session = ChatSession.objects.create(
                user=ticket.user,
                technician=user,
                ticket=ticket,
                chat_type='user_tech',
                status='active'
            )
            
            # Create initial message
            Message.objects.create(
                chat_session=chat_session,
                sender=ticket.user,
                receiver=user,
                content=f"Ticket created: {ticket.title} - {ticket.description}",
                message_type='user_to_tech'
            )
            
            created_count += 1
            print(f"🔧 DEBUG: Created chat session for ticket {ticket.id}")
    
    print(f"🔧 DEBUG: Created {created_count} missing chat sessions")
    return created_count



def handle_start_ticket_chat(request, user):
    """Start a chat for a specific ticket"""
    try:
        ticket_id = request.POST.get('ticket_id')
        ticket = CreateTicket.objects.get(id=ticket_id, user=user)
        
        # Check if chat already exists for this ticket
        existing_chat = ChatSession.objects.filter(
            user=user,
            ticket=ticket
        ).first()
        
        if existing_chat:
            return JsonResponse({
                'success': True,
                'chat_session_id': existing_chat.id,
                'message': 'Chat already exists'
            })
        
        # Create new chat session for the ticket
        chat_session = ChatSession.objects.create(
            user=user,
            ticket=ticket,
            chat_type='user_tech',  # This will be connected when technician accepts
            status='active'
        )
        
        # Create initial message
        Message.objects.create(
            chat_session=chat_session,
            sender=user,
            content=f"Help requested for ticket: {ticket.title}",
            message_type='user_to_tech'
        )
        
        return JsonResponse({
            'success': True,
            'chat_session_id': chat_session.id,
            'message': 'Chat started for ticket'
        })
        
    except CreateTicket.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Ticket not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def handle_start_bot_chat(request, user):
    """Start or get bot chat, optionally with ticket context"""
    try:
        ticket_id = request.POST.get('ticket_id')
        ticket = None
        
        if ticket_id:
            ticket = CreateTicket.objects.get(id=ticket_id, user=user)
        
        # Get or create bot chat session
        chat_session, created = ChatSession.objects.get_or_create(
            user=user,
            chat_type='user_bot',
            defaults={'status': 'active'}
        )
        
        if created:
            # Create welcome message
            Message.objects.create(
                chat_session=chat_session,
                content="Hello! I'm FixIT Assistant 👋 I'm here to help you with common issues and FAQs. How can I assist you today?",
                message_type='bot_to_user'
            )
        
        # If ticket provided, add context to the chat
        if ticket:
            Message.objects.create(
                chat_session=chat_session,
                sender=user,
                content=f"I need help with my ticket: {ticket.title} - {ticket.description}",
                message_type='user_to_bot'
            )
        
        return JsonResponse({
            'success': True,
            'chat_session_id': chat_session.id,
            'redirect_url': f'/user/messages/?chat={chat_session.id}'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
    
    

# Utility functions
def serialize_message(message):
    """Serialize message for JSON response"""
    return {
        'id': message.id,
        'content': message.content,
        'sender_name': message.sender.username if message.sender else 'FixIT Assistant',
        'sender_id': message.sender.id if message.sender else None,
        'message_type': message.message_type,
        'created_at': message.created_at.isoformat(),
        'is_own_message': False,  # This should be set in the template context
        'can_edit': True,  # This should be determined based on time and permissions
    }

def create_message_notification(recipient, sender, message):
    """Create notification for new message"""
    try:
        Notification.objects.create(
            recipient=recipient,
            sender=sender,
            message=f"New message from {sender.username}",
            created_at=timezone.now()
        )
    except Exception as e:
        print(f"Error creating notification: {e}")

# API endpoints for real-time updates
@login_required
@csrf_exempt
def get_chat_messages(request, chat_session_id):
    """API endpoint to get chat messages"""
    try:
        chat_session = ChatSession.objects.filter(
            Q(user=request.user) | Q(technician=request.user)
        ).get(id=chat_session_id)

        messages = chat_session.messages.filter(is_deleted=False).order_by('created_at')

        return JsonResponse({
            'success': True,
            'messages': [serialize_message(msg) for msg in messages]
        })

    except ChatSession.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Chat session not found'})
    
@login_required
@csrf_exempt
def get_unread_count(request):
    """API endpoint to get unread message count"""
    if hasattr(request.user, 'profile') and request.user.profile.is_technician:
        unread_count = Message.objects.filter(
            receiver=request.user,
            is_read=False
        ).count()
    else:
        unread_count = Message.objects.filter(
            receiver=request.user,
            is_read=False
        ).count()
    
    return JsonResponse({'success': True, 'unread_count': unread_count})

    
@login_required
def technician_tickets_view(request):
    """
    Display technician's assigned tickets
    """
    user = request.user

    # Get technician's assigned tickets (base)
    base_qs = CreateTicket.objects.filter(
        assistance_requests__technician__user_profile__user=user
    ).distinct()

    # Filters
    status = request.GET.get('status', 'all')
    sort = request.GET.get('sort', 'newest')
    allowed_statuses = ['open', 'in_progress', 'pending', 'resolved']

    qs = base_qs
    if status in allowed_statuses:
        qs = qs.filter(status=status)

    # Sorting
    if sort == 'oldest':
        qs = qs.order_by('created_at')
    elif sort == 'priority':
        from django.db.models import Case, When, IntegerField
        qs = qs.annotate(
            priority_order=Case(
                When(priority='critical', then=0),
                When(priority='high', then=1),
                When(priority='medium', then=2),
                When(priority='low', then=3),
                default=4,
                output_field=IntegerField()
            )
        ).order_by('priority_order', '-created_at')
    else:
        qs = qs.order_by('-created_at')

    # Prepare ticket data with customer info
    ticket_data = []
    for ticket in qs:
        customer = ticket.user
        customer_info = {
            'full_name': customer.get_full_name() or customer.username,
            'email': customer.email,
            'profile_picture_url': getattr(customer.profile, 'profile_picture_url', ''),
            'initials': (customer.first_name[0] + customer.last_name[0]).upper()
                        if customer.first_name and customer.last_name
                        else customer.username[:2].upper()
        }

        has_review = TechnicianReview.objects.filter(ticket=ticket).exists()

        ticket_data.append({
            'ticket': ticket,
            'customer': customer_info,
            'has_review': has_review,
        })

    # Calculate stats
    total_tickets = base_qs.count()
    open_tickets = base_qs.filter(status='open').count()
    in_progress_tickets = base_qs.filter(status='in_progress').count()
    resolved_tickets = base_qs.filter(status='resolved').count()

    context = {
        'ticket_data': ticket_data,
        'total_tickets': total_tickets,
        'open_tickets': open_tickets,
        'in_progress_tickets': in_progress_tickets,
        'resolved_tickets': resolved_tickets,
        'title': 'My Tickets - FixIT',
        'status': status,
        'sort': sort,
    }

    return render(request, 'dashboard/technician_tickets.html', context)


@login_required
def get_technician_availability(request, technician_id):
    """
    Check technician availability (AJAX endpoint)
    """
    technician = get_object_or_404(Technician, id=technician_id)

    return JsonResponse({
        'is_available': technician.is_available,
        'status': technician.availability_status,
        'response_time': technician.average_response_time,
        'working_hours': f"{technician.working_hours_start.strftime('%H:%M')} - {technician.working_hours_end.strftime('%H:%M')}"
    })


@login_required
def profile_update_view(request):
    """
    Handle profile updates including profile picture and user details
    """
    if request.method == 'POST' and 'profile_picture' in request.FILES:
        print("=== PROFILE PICTURE UPLOAD START ===")
        uploaded_file = request.FILES['profile_picture']
        print(f"📁 File received: {uploaded_file.name}, Size: {uploaded_file.size}")

        # Validate file size
        if uploaded_file.size > 5 * 1024 * 1024:
            messages.error(request, 'Image file too large ( > 5MB )')
            return redirect('profile_update')

        # Validate file type and get proper extension
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        file_name = uploaded_file.name.lower()

        # Extract extension properly
        if '.' in file_name:
            file_extension = '.' + file_name.split('.')[-1]
            if file_extension == '.jpeg':
                file_extension = '.jpg'
        else:
            messages.error(request, 'Please upload a valid image file with extension')
            return redirect('profile_update')

        if file_extension not in valid_extensions:
            messages.error(request, 'Please upload a valid image file (JPG, PNG, GIF, BMP)')
            return redirect('profile_update')

        # Handle file upload using Supabase storage
        try:
            import uuid
            from django.core.files.storage import default_storage

            # Generate unique filename - SIMPLIFIED PATH
            unique_filename = f"{uuid.uuid4()}{file_extension}"

            print(f"🔄 Attempting to save to Supabase: {unique_filename}")
            print(f"🔍 File extension: {file_extension}")

            # Save the file using Django's storage backend
            file_path = default_storage.save(unique_filename, uploaded_file)

            print(f"✅ File saved to: {file_path}")
            print(f"🔍 Full file path: {file_path}")

            # Update the profile with the file path
            request.user.profile.profile_picture = file_path
            request.user.profile.save()

            # Debug: Check what was actually saved
            print(f"✅ Profile picture filename in DB: {request.user.profile.profile_picture}")

            # Generate URL and verify
            try:
                file_url = default_storage.url(file_path)
                print(f"🌐 Generated File URL: {file_url}")

                # Construct manual URL to verify
                manual_url = f"https://gpxaxqghnwguwgpackig.supabase.co/storage/v1/object/public/profile-pictures/{file_path}"
                print(f"🔗 Manual File URL: {manual_url}")

            except Exception as url_error:
                print(f"⚠️ URL generation failed: {url_error}")

            messages.success(request, 'Your profile picture has been updated successfully!')

        except Exception as e:
            print("❌ Error saving profile picture:", str(e))
            messages.error(request, f'Error updating profile picture: {str(e)}')

        return redirect('profile_update')

    # Handle GET requests
    user_form = UserUpdateForm(instance=request.user)
    profile_form = ProfileUpdateForm(instance=request.user.profile)
    picture_form = ProfilePictureForm(instance=request.user.profile)

    avg_rating = None
    full_stars = 0
    has_half_star = False
    empty_stars = 5
    badge_states = None
    if getattr(request.user.profile, 'is_technician', False):
        technician = Technician.objects.filter(user_profile__user=request.user).first()
        if technician and technician.average_rating is not None:
            avg_rating = float(technician.average_rating)
            full_stars = int(avg_rating)
            has_half_star = (avg_rating - full_stars) >= 0.5 and full_stars < 5
            empty_stars = 5 - full_stars - (1 if has_half_star else 0)

        resolved_count = CreateTicket.objects.filter(
            assistance_requests__technician__user_profile__user=request.user,
            status='resolved'
        ).distinct().count()

        levels = [
            ('Novice', 'badge-novice', 0),
            ('Advanced Beginner', 'badge-advanced', 1),
            ('Competent', 'badge-competent', 2),
            ('Proficient', 'badge-proficient', 3),
            ('Expert', 'badge-expert', 4),
        ]
        badge_states = [
            {
                'name': name,
                'css': css,
                'unlocked': resolved_count >= threshold
            }
            for (name, css, threshold) in levels
        ]

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'picture_form': picture_form,
        'title': 'Update Profile - FixIT',
        'avg_rating': avg_rating,
        'full_stars': full_stars,
        'has_half_star': has_half_star,
        'empty_stars': empty_stars,
        'badge_states': badge_states,
    }

    return render(request, 'accounts/profile_update.html', context)


@login_required
def list_bucket_files(request):
    """List all files in the storage bucket"""
    import boto3
    from django.conf import settings
    from django.http import JsonResponse

    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            region_name=settings.AWS_S3_REGION_NAME,
        )

        # List all objects in the bucket
        objects = s3.list_objects_v2(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
        files = [obj['Key'] for obj in objects.get('Contents', [])]

        return JsonResponse({
            'success': True,
            'bucket': settings.AWS_STORAGE_BUCKET_NAME,
            'file_count': len(files),
            'files': files
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def comprehensive_storage_test(request):
    """Step-by-step storage test with better error handling"""
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile
    from django.http import JsonResponse

    test_results = {}

    try:
        # Step 1: Basic storage check
        test_results['storage_backend'] = str(default_storage.__class__)

        # Step 2: Test with proper image file extension
        test_filename = f"comprehensive_test_{request.user.id}.jpg"  # Explicit .jpg extension
        test_content = b"fake image content for testing"  # Simple text as fake image

        print(f"🧪 Testing with filename: {test_filename}")

        # Save
        saved_path = default_storage.save(test_filename, ContentFile(test_content))
        test_results['save_success'] = True
        test_results['saved_path'] = saved_path

        # Check existence
        exists = default_storage.exists(saved_path)
        test_results['exists_check'] = exists

        # Get URL (without testing accessibility via requests)
        try:
            file_url = default_storage.url(saved_path)
            test_results['url_generation'] = 'Success'
            test_results['file_url'] = file_url
            print(f"🌐 File URL generated: {file_url}")

        except Exception as e:
            test_results['url_generation'] = f'Failed: {e}'
            print(f"🔗 URL generation failed: {e}")

        # Read back
        try:
            with default_storage.open(saved_path) as f:
                content = f.read()
            test_results['read_success'] = True
            test_results['content_matches'] = content == test_content
        except Exception as e:
            test_results['read_success'] = False
            test_results['read_error'] = str(e)

        # Delete
        try:
            default_storage.delete(saved_path)
            test_results['delete_success'] = True
        except Exception as e:
            test_results['delete_success'] = False
            test_results['delete_error'] = str(e)

        test_results['overall_success'] = all([
            test_results.get('save_success', False),
            test_results.get('exists_check', False),
            test_results.get('read_success', False),
        ])

    except Exception as e:
        test_results['overall_success'] = False
        test_results['error'] = str(e)
        test_results['error_type'] = type(e).__name__

    return JsonResponse(test_results)



@login_required
def debug_storage_detailed(request):
    """Detailed storage debugging"""
    from django.conf import settings
    from django.core.files.storage import default_storage
    from django.http import JsonResponse
    import boto3

    debug_info = {
        'credentials': {
            'aws_access_key_id': settings.AWS_ACCESS_KEY_ID,
            'aws_secret_length': len(settings.AWS_SECRET_ACCESS_KEY) if settings.AWS_SECRET_ACCESS_KEY else 0,
            'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
            'endpoint_url': settings.AWS_S3_ENDPOINT_URL,
            'custom_domain': settings.AWS_S3_CUSTOM_DOMAIN,
        },
        'storage_backend': str(default_storage.__class__),
    }

    try:
        # Test direct boto3 connection
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        )

        # Test 1: List buckets
        buckets = s3.list_buckets()
        debug_info['buckets'] = [b['Name'] for b in buckets['Buckets']]

        # Test 2: Check if our bucket exists
        debug_info['bucket_exists'] = settings.AWS_STORAGE_BUCKET_NAME in debug_info['buckets']

        # Test 3: Try to list objects in our bucket
        try:
            objects = s3.list_objects_v2(Bucket=settings.AWS_STORAGE_BUCKET_NAME, MaxKeys=5)
            debug_info['object_count'] = objects.get('KeyCount', 0)
            debug_info['objects'] = [obj['Key'] for obj in objects.get('Contents', [])]
        except Exception as e:
            debug_info['list_objects_error'] = str(e)

        # Test 4: Try a simple upload
        try:
            test_key = f"debug_test_{request.user.id}.txt"
            s3.put_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=test_key,
                Body=b"Debug test content",
                ContentType='text/plain'
            )
            debug_info['upload_test'] = 'Success'

            # Try to read it back
            try:
                obj = s3.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=test_key)
                debug_info['read_test'] = 'Success'
            except Exception as e:
                debug_info['read_test'] = f'Failed: {e}'

            # Clean up
            s3.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=test_key)
            debug_info['delete_test'] = 'Success'

        except Exception as e:
            debug_info['upload_test'] = f'Failed: {e}'

    except Exception as e:
        debug_info['connection_error'] = str(e)

    return JsonResponse(debug_info)


@login_required
def debug_current_profile_picture(request):
    """Debug the current profile picture setup"""
    from django.core.files.storage import default_storage
    from django.http import JsonResponse

    debug_info = {
        'current_profile_picture': str(request.user.profile.profile_picture),
        'profile_picture_type': type(request.user.profile.profile_picture).__name__,
    }

    if request.user.profile.profile_picture:
        try:
            # Check if file exists in storage
            exists = default_storage.exists(str(request.user.profile.profile_picture))
            debug_info['file_exists'] = exists

            # Try to get URL
            try:
                url = default_storage.url(str(request.user.profile.profile_picture))
                debug_info['file_url'] = url
                debug_info['url_success'] = True
            except Exception as e:
                debug_info['url_error'] = str(e)
                debug_info['url_success'] = False

        except Exception as e:
            debug_info['storage_error'] = str(e)

    return JsonResponse(debug_info)


@login_required
def debug_storage_config(request):
    """Debug storage configuration"""
    from django.conf import settings
    from django.core.files.storage import default_storage
    from django.http import JsonResponse

    config_info = {
        'storage_backend': getattr(settings, 'DEFAULT_FILE_STORAGE', 'Not set'),
        'aws_access_key_id': getattr(settings, 'AWS_ACCESS_KEY_ID', 'Not set'),
        'aws_secret_access_key_set': bool(getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)),
        'aws_storage_bucket_name': getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'Not set'),
        'aws_s3_endpoint_url': getattr(settings, 'AWS_S3_ENDPOINT_URL', 'Not set'),
        'aws_s3_custom_domain': getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', 'Not set'),
        'actual_storage_class': str(default_storage.__class__),
        'storage_module': str(default_storage.__class__.__module__),
    }

    # Check if we can access storage attributes
    try:
        config_info['bucket_name'] = default_storage.bucket_name
    except Exception as e:
        config_info['bucket_name_error'] = str(e)

    try:
        config_info['endpoint_url'] = default_storage.endpoint_url
    except Exception as e:
        config_info['endpoint_url_error'] = str(e)

    # Test actual file operations
    try:
        test_content = b"config_test"
        test_path = f"config_test_{request.user.id}.txt"

        # Save
        saved_path = default_storage.save(test_path, ContentFile(test_content))
        config_info['test_save_path'] = saved_path

        # Check where it was saved
        if hasattr(default_storage, 'location'):
            config_info['storage_location'] = default_storage.location
        if hasattr(default_storage, 'base_location'):
            config_info['base_location'] = default_storage.base_location

        # Check if it's a local path (indicating wrong storage backend)
        if saved_path.startswith('/') or 'media' in saved_path:
            config_info['storage_type'] = 'LOCAL_FILESYSTEM'
        else:
            config_info['storage_type'] = 'REMOTE_STORAGE'

        # Clean up
        default_storage.delete(saved_path)

    except Exception as e:
        config_info['test_error'] = str(e)

    return JsonResponse(config_info)


@login_required
def test_direct_supabase_connection(request):
    """Test direct connection to Supabase storage"""
    import boto3
    from django.conf import settings
    from django.http import JsonResponse

    try:
        # Create S3 client with your settings
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        )

        # Test 1: List buckets
        buckets = s3.list_buckets()
        bucket_names = [b['Name'] for b in buckets['Buckets']]

        # Test 2: Check if our bucket exists
        bucket_exists = settings.AWS_STORAGE_BUCKET_NAME in bucket_names

        # Test 3: Try to upload a file
        test_key = f"direct_test_{request.user.id}.txt"
        s3.put_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=test_key,
            Body=b"Direct connection test",
            ContentType='text/plain'
        )

        # Test 4: List objects to verify upload
        objects = s3.list_objects_v2(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
        uploaded_objects = [obj['Key'] for obj in objects.get('Contents', [])]

        # Test 5: Delete the test file
        s3.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=test_key)

        return JsonResponse({
            'success': True,
            'buckets': bucket_names,
            'target_bucket_exists': bucket_exists,
            'uploaded_objects': uploaded_objects,
            'test_file_uploaded': test_key in uploaded_objects,
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        })



from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CreateTicket, Ticket  # or your actual Ticket model

from django.contrib import messages

@login_required
def technician_dashboard_view(request):
    user = request.user

    # Get all tickets assigned to this technician
    technician_tickets = CreateTicket.objects.filter(
        assistance_requests__technician__user_profile__user=user
    ).distinct()

    # Example: check for new tickets assigned in the last X minutes
    from django.utils import timezone
    import datetime

    now = timezone.now()
    new_threshold = now - datetime.timedelta(minutes=5)  # adjust as needed
    new_tickets = technician_tickets.filter(created_at__gte=new_threshold)

    for ticket in new_tickets:
        messages.info(request, f'Ticket #{ticket.id} "{ticket.title}" has been assigned to you.')

    # ... existing context setup ...
    ticket_data = []
    for ticket in technician_tickets:
        customer = ticket.user
        customer_info = {
            'full_name': customer.get_full_name() or customer.username,
            'email': customer.email,
            'profile_picture_url': getattr(customer.profile, 'profile_picture_url', ''),
            'initials': (
                (customer.first_name[0] + customer.last_name[0]).upper()
                if customer.first_name and customer.last_name
                else customer.username[:2].upper()
            )
        }
        ticket_data.append({
            'ticket': ticket,
            'customer': customer_info
        })

    # Technician average response time display
    tech_avg_response_time_display = "—"
    profile = getattr(user, 'profile', None)
    if profile and getattr(profile, 'is_technician', False):
        tech_obj = getattr(profile, 'technician_profile', None)
        if tech_obj and tech_obj.average_response_time is not None:
            try:
                val = round(float(tech_obj.average_response_time), 1)
                tech_avg_response_time_display = f"{val}h"
            except Exception:
                pass

    context = {
        'tickets': technician_tickets.order_by('-created_at')[:5],
        'ticket_data': ticket_data,
        'total_tickets': technician_tickets.count(),
        'open_tickets': technician_tickets.filter(status='open').count(),
        'in_progress_tickets': technician_tickets.filter(status='in_progress').count(),
        'resolved_tickets': technician_tickets.filter(status='resolved').count(),
        'tech_avg_response_time_display': tech_avg_response_time_display,
        'title': 'Dashboard - FixIT',
    }

    return render(request, 'dashboard/technician_dashboard.html', context)


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import UserProfile, CreateTicket  

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone


@login_required
def user_dashboard_view(request):
    """
    Display user dashboard with dynamic troubleshooting guides from FAQ
    """
    user = request.user

    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={'is_technician': False}
    )

    if created:
        messages.info(request, 'Your profile has been created.')

    # Check if user is a technician and redirect
    if profile.is_technician:
        messages.info(request, 'Redirecting to technician dashboard.')
        return redirect('technician_dashboard')

    # --- TICKET DATA (existing code) ---
    user_tickets_queryset = CreateTicket.objects.filter(user=user)
    recent_tickets = user_tickets_queryset.order_by('-created_at')[:5]
    
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    total_tickets_created = user_tickets_queryset.count()
    open_tickets_count = user_tickets_queryset.filter(
        status__in=['open', 'in_progress']
    ).count()
    
    resolved_this_month_count = user_tickets_queryset.filter(
        status='resolved',
        created_at__gte=start_of_month
    ).count()
    
    ars = AssistanceRequest.objects.filter(user=user).select_related('technician')
    response_times = [ar.technician.average_response_time for ar in ars if ar.technician and ar.technician.average_response_time is not None]
    avg_response_time = round(sum(response_times) / len(response_times), 1) if response_times else None
    avg_response_time_display = f"{avg_response_time}h" if avg_response_time is not None else "—"
    
    notifications = Notification.objects.filter(recipient=user).order_by('-created_at')[:5]
    
    # --- DYNAMIC TROUBLESHOOTING GUIDES FROM FAQ ---
    try:
        from .models import FAQItem
        troubleshooting_guides = FAQItem.objects.filter(
            is_active=True,
            show_in_dashboard=True
        ).select_related('category').order_by('-bot_priority', 'order')[:9]  # Show 9 for 3x3 grid
    
        # Prepare guide data for template
        guide_data = []
        for guide in troubleshooting_guides:
            guide_data.append({
                'id': guide.id,
                'title': guide.short_question,
                'description': guide.short_answer[:100] + '...' if len(guide.short_answer) > 100 else guide.short_answer,
                'read_time': guide.read_time,
                'category': guide.category.name if guide.category else 'General',
                'category_icon': guide.category.icon if guide.category else 'question-circle',
                'faq_url': f"{reverse('help_center')}#{guide.category.slug if guide.category else 'general'}"
            })
    except Exception as e:
        print(f"⚠️ Dashboard FAQ error: {e}")
        guide_data = []
    
    context = {
        'user': user,
        'profile': profile,
        'title': 'User Dashboard - FixIT',
        
        # Ticket data
        'recent_tickets': recent_tickets,
        'open_tickets_count': open_tickets_count,
        'resolved_this_month_count': resolved_this_month_count,
        'avg_response_time_display': avg_response_time_display,
        'notifications': notifications,
        'total_tickets_created': total_tickets_created,
        
        # Dynamic troubleshooting guides
        'troubleshooting_guides': guide_data,
    }
    
    return render(request, 'dashboard/user_dashboard.html', context)


# accounts/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator  # CORE SECURITY
from django.conf import settings

User = get_user_model()


# NOTE: The @login_required decorator MUST be removed from this view,
# as users must be logged OUT to reset their password.

def password_reset_view(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            # 1. Look up user (Fail silently if not found for security)
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # 2. SECURITY BEST PRACTICE: Always show the "done" page regardless
            # of whether the user exists to prevent account enumeration.
            return redirect('password_reset_done')

        # --- Begin Secure Email Sending Logic ---

        # 3. Generate Secure Token and UID
        # UID is the user ID encoded, Token is the time-limited security key
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # 4. Construct the Live Reset Link (Uses your custom URL names)
        domain = request.get_host()
        protocol = 'http'  # Change this to 'https' in your production environment!

        # This URL relies on your urls.py having the name 'password_reset_confirm'
        reset_url = f"{protocol}://{domain}/accounts/reset/{uid}/{token}/"

        # 5. Render Email Content (Using templates/registration/password_reset_email.html)
        email_context = {
            'user': user,
            'reset_url': reset_url,
            'protocol': protocol,
            'domain': domain,
            'uid': uid,
            'token': token,
        }

        # Ensure you have created templates/registration/password_reset_email.html
        html_message = render_to_string('accounts/password_reset_email.html', email_context)

        # 6. Send Email using SMTP Configuration
        send_mail(
            subject="Password Reset for FixIT",
            # Use the plain message as a fallback, and the HTML message for styling
            message=f"Please use this link to reset your password: {reset_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
            html_message=html_message
        )

        # 7. Redirect to the Done page (Notification that the email was sent)
        return redirect('password_reset_done')

    # Render the initial form on GET request
    context = {
        'title': 'Password Reset - FixIT',
        'hide_navigation': True
    }
    # NOTE: I am using the template name you provided in your earlier views (accounts/password_reset.html)
    return render(request, 'accounts/password_reset.html', context)


# accounts/views.py (Add these three functions)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import SetPasswordForm  # Use built-in form for security

User = get_user_model()


def password_reset_done_view(request):
    """
    Renders the confirmation page after the email is sent (Notification).
    """
    context = {
        'title': 'Check Your Email - FixIT',
        'hide_navigation': True
    }
    # Renders your custom styled 'password_reset_done.html'
    return render(request, 'accounts/password_reset_done.html', context)


def password_reset_confirm_view(request, uidb64, token):
    """
    Validates the UID and token, then allows the user to set a new password.
    This view receives the security token from the email link.
    """
    # 1. Decode UID and Fetch User
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    # 2. Check if the Token is Valid
    if user is not None and default_token_generator.check_token(user, token):
        validlink = True
    else:
        validlink = False

    if request.method == 'POST' and validlink:
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            # 3. Save New Password (Django handles hashing securely)
            form.save()

            # 4. Success! Redirect to the complete page
            return redirect('password_reset_complete')

    elif validlink:
        # Display the form on GET request
        form = SetPasswordForm(user)
    else:
        # Display the failed link message
        form = None

    context = {
        'title': 'Set New Password - FixIT',
        'form': form,
        'validlink': validlink,
        'hide_navigation': True
    }
    # Renders your custom styled 'password_reset_confirm.html'
    return render(request, 'accounts/password_reset_confirm.html', context)


def password_reset_complete_view(request):
    """
    Renders the final success page after the password has been changed.
    """
    context = {
        'title': 'Password Changed! - FixIT',
        'hide_navigation': True
    }
    # Renders your custom styled 'password_reset_complete.html'
    return render(request, 'accounts/password_reset_complete.html', context)

#@login_required
def change_password_view(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Validate passwords match
        if new_password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return render(request, 'accounts/change_password.html')

        # Update the logged-in user's password
        user = request.user
        user.set_password(new_password)
        user.save()

        # Re-authenticate user after password change
        update_session_auth_hash(request, user)  # Important: keeps user logged in
        messages.success(request, "Your password has been changed successfully!")
        return redirect('login')  # Redirect to dashboard instead of login

    # GET request - show the form
    return render(request, 'accounts/change_password.html')

#test
def redirect_to_correct_dashboard(user):
    """
    Redirect user to the appropriate dashboard based on their role.
    """
    try:
        profile = user.profile  # Use related_name='profile' from your model
    except UserProfile.DoesNotExist:
        # Fallback: create profile if somehow missing
        profile = UserProfile.objects.create(user=user, is_technician=False)

    if profile.is_technician:
        return redirect('technician_dashboard')
    else:
        return redirect('user_dashboard')











@login_required
def user_profile_view(request):
    """
    Display user profile page with picture upload using Supabase storage
    """
    if request.method == 'POST' and 'profile_picture' in request.FILES:
        # Handle profile picture upload
        uploaded_file = request.FILES['profile_picture']

        # Validate file size
        if uploaded_file.size > 5 * 1024 * 1024:
            messages.error(request, 'Image file too large ( > 5MB )')
            return redirect('user_profile')

        # Validate file type
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        file_name = uploaded_file.name.lower()
        file_extension = '.' + file_name.split('.')[-1] if '.' in file_name else ''

        if file_extension not in valid_extensions:
            messages.error(request, 'Please upload a valid image file (JPG, PNG, GIF, BMP)')
            return redirect('user_profile')

        try:
            import uuid

            # Generate unique filename
            unique_filename = f"{uuid.uuid4()}{file_extension}"

            # Save to configured storage and store reference in database
            request.user.profile.profile_picture.save(unique_filename, uploaded_file)
            request.user.profile.save()

            print(f"✅ Profile picture saved to Supabase: {unique_filename}")
            messages.success(request, 'Your profile picture has been updated successfully!')

        except Exception as e:
            print(f"❌ Error saving profile picture: {e}")
            messages.error(request, 'Error updating profile picture. Please try again.')

            print(f"✅ Profile picture filename: {request.user.profile.profile_picture}")
            print(f"✅ Profile picture URL: {request.user.profile.profile_picture.url}")
            print(f"✅ Full image URL: https://{request.user.profile.profile_picture.url}")

        return redirect('user_profile')

    # Normal GET request
    user = request.user
    context = {
        'user': user,
        'profile': user.profile,
        'title': 'User Profile - FixIT'
    }
    return render(request, 'dashboard/user_profile.html', context)


@login_required
def technician_profile_view(request):
    """
    Display technician profile page
    """
    user = request.user
    # Check if user is a technician
    if not hasattr(user, 'profile') or not user.profile.is_technician:
        messages.error(request, 'You do not have permission to access the technician profile.')
        return redirect('user_profile')

    context = {
        'user': user,
        'profile': user.profile,
        'title': 'Technician Profile - FixIT'
    }
    return render(request, 'dashboard/technician_profile.html', context)

#SPRINT 2
@login_required
def ticket_history(request):
    tickets = Ticket.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'accounts/history.html', {
        'tickets': tickets
    })


#SETTINGS PAGE
@login_required
def settings_view(request):
    profile = getattr(request.user, 'profile', None)
    if profile and profile.is_technician:
        return redirect('technician_settings')
    return redirect('user_settings')


@login_required
def update_notifications(request):
    """Update notification preferences via AJAX or form submission."""
    if request.method == 'POST':
        settings, _ = UserSettings.objects.get_or_create(user=request.user)
        email_pref = request.POST.get('email_notifications') == 'true'
        sms_pref = request.POST.get('sms_notifications') == 'true'
        settings.email_notifications = email_pref
        settings.sms_notifications = sms_pref
        settings.save()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def change_password_settings(request):
    """Allow user to change password."""
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Validate passwords match
        if new_password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return render(request, 'accounts/change_password.html')

        # Update the logged-in user's password
        user = request.user
        user.set_password(new_password)
        user.save()

        # Re-authenticate user after password change
        update_session_auth_hash(request, user)  # Important: keeps user logged in
        messages.success(request, "Your password has been changed successfully!")
        return redirect('login')  # Redirect to dashboard instead of login

    # GET request - show the form
    return render(request, 'accounts/change_password.html')

@login_required
def user_settings_view(request):
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        tab = request.POST.get('tab', 'account')
        user = request.user
        profile = user.profile
        if tab == 'account':
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            bio = request.POST.get('bio', '').strip()
            if username:
                user.username = username
            if email:
                user.email = email
            if bio and getattr(user.profile, 'is_technician', False):
                try:
                    tech = Technician.objects.filter(user_profile=user.profile).first()
                    if tech:
                        tech.bio = bio
                        tech.save()
                except Exception:
                    pass
            user.save()
            messages.success(request, 'Account details updated.')
            return redirect(f"{reverse('user_settings')}?tab=account")
        elif tab == 'profile':
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email_address = request.POST.get('email_address', '').strip()
            phone_number = request.POST.get('phone_number', '').strip()
            date_of_birth = request.POST.get('date_of_birth', '').strip()
            address = request.POST.get('address', '').strip()
            city = request.POST.get('city', '').strip()
            country = request.POST.get('country', '').strip()

            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            if email_address:
                user.email = email_address
            if phone_number:
                profile.phone_number = phone_number
            if date_of_birth:
                try:
                    from datetime import datetime
                    profile.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
                except Exception:
                    pass
            if address:
                profile.address = address
            if city:
                profile.city = city
            if country:
                profile.country = country
            if 'profile_picture' in request.FILES:
                import uuid
                uploaded_file = request.FILES['profile_picture']
                unique_filename = f"{uuid.uuid4()}_{uploaded_file.name}"
                profile.profile_picture.save(unique_filename, uploaded_file)

            user.save()
            profile.save()
            messages.success(request, 'Profile details updated.')
            return redirect(f"{reverse('user_settings')}?tab=profile")

    context = {
        'settings': settings_obj,
        'profile': request.user.profile,
        'title': 'Settings'
    }
    return render(request, 'dashboard/user_settings.html', context)

@login_required
def technician_settings_view(request):
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        tab = request.POST.get('tab', 'account')
        user = request.user
        profile = user.profile
        if tab == 'account':
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            bio = request.POST.get('bio', '').strip()
            if username:
                user.username = username
            if email:
                user.email = email
            if bio:
                try:
                    tech = Technician.objects.filter(user_profile=user.profile).first()
                    if tech:
                        tech.bio = bio
                        tech.save()
                except Exception:
                    pass
            user.save()
            messages.success(request, 'Account details updated.')
            return redirect(f"{reverse('technician_settings')}?tab=account")
        elif tab == 'profile':
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email_address = request.POST.get('email_address', '').strip()
            phone_number = request.POST.get('phone_number', '').strip()
            date_of_birth = request.POST.get('date_of_birth', '').strip()
            address = request.POST.get('address', '').strip()
            city = request.POST.get('city', '').strip()
            country = request.POST.get('country', '').strip()

            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            if email_address:
                user.email = email_address
            if phone_number:
                profile.phone_number = phone_number
            if date_of_birth:
                try:
                    from datetime import datetime
                    profile.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
                except Exception:
                    pass
            if address:
                profile.address = address
            if city:
                profile.city = city
            if country:
                profile.country = country
            if 'profile_picture' in request.FILES:
                import uuid
                uploaded_file = request.FILES['profile_picture']
                unique_filename = f"{uuid.uuid4()}_{uploaded_file.name}"
                profile.profile_picture.save(unique_filename, uploaded_file)

            user.save()
            profile.save()
            messages.success(request, 'Profile details updated.')
            return redirect(f"{reverse('technician_settings')}?tab=profile")

    context = {
        'settings': settings_obj,
        'profile': request.user.profile,
        'title': 'Settings'
    }
    return render(request, 'dashboard/technician_settings.html', context)

@login_required
def delete_account_view(request):
    if request.method == 'POST':
        password = request.POST.get('password', '')
        next_page = request.POST.get('next', '')
        if next_page == 'user_settings':
            target_settings = f"{reverse('user_settings')}?tab=account"
        elif next_page == 'technician_settings':
            target_settings = f"{reverse('technician_settings')}?tab=account"
        else:
            try:
                if request.user.profile.is_technician:
                    target_settings = f"{reverse('technician_settings')}?tab=account"
                else:
                    target_settings = f"{reverse('user_settings')}?tab=account"
            except Exception:
                target_settings = f"{reverse('user_settings')}?tab=account"
        if not request.user.check_password(password):
            messages.error(request, 'Incorrect password. Account not deleted.')
            return redirect(target_settings)
        username = request.user.username
        try:
            request.user.delete()
            logout(request)
            messages.success(request, f'Account "{username}" has been deleted.')
            return redirect('signup')
        except Exception:
            messages.error(request, 'Error deleting account. Please try again later.')
            return redirect(target_settings)
    try:
        if request.user.profile.is_technician:
            return redirect(f"{reverse('technician_settings')}?tab=account")
        else:
            return redirect(f"{reverse('user_settings')}?tab=account")
    except Exception:
        return redirect(f"{reverse('user_settings')}?tab=account")






#/////////

def create_contact_from_assistance(user, technician):
    """Create contact relationship when user requests assistance from technician"""
    technician_user = technician.user_profile.user
    contact, created = Contact.objects.get_or_create(
        user=user,
        contact_user=technician_user,
        defaults={
            'contact_name': f"{technician_user.first_name} {technician_user.last_name}" or technician_user.username
        }
    )
    return contact

def start_bot_chat(request):
       # Use the unified chat system
    chat_session, created = ChatSession.objects.get_or_create(
        user=request.user,
        chat_type='user_bot',
        defaults={'status': 'active'}
    )
    
    # Create welcome message if this is a new chat
    if created:
        Message.objects.create(
            chat_session=chat_session,
            content="Hello! I'm FixIT Assistant 👋 I'm here to help you with common issues and FAQs. How can I assist you today?",
            message_type='bot_to_user'
        )
    
    return redirect(f'/user/messages/?chat={chat_session.id}')


# In views.py, update help_center_view
@login_required
def help_center_view(request):
    """
    Dynamic help center page using database FAQ data
    """
    try:
        # Get all categories with their FAQs
        categories = FAQCategory.objects.prefetch_related('faqs').order_by('order')
        
        context = {
            'title': 'Help Center - FixIT',
            'categories': categories,
        }
        
    except Exception as e:
        print(f"⚠️ Help center error: {e}")
        # Return empty categories for fallback
        context = {
            'title': 'Help Center - FixIT',
            'categories': [],
        }
    
    return render(request, 'accounts/FAQ_Page.html', context)

@login_required
def get_faq_detail(request, faq_id):
    """
    API endpoint to get FAQ details for bot chat
    """
    try:
        from .models import FAQItem
        faq = FAQItem.objects.get(id=faq_id, is_active=True)
        
        return JsonResponse({
            'success': True,
            'faq': {
                'id': faq.id,
                'question': faq.question,
                'short_question': faq.short_question,
                'answer': faq.answer,
                'category': faq.category.name,
                'read_time': faq.read_time,
            }
        })
    except FAQItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'FAQ not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_category_faqs(request, category_slug):
    """
    API endpoint to get FAQs by category
    """
    try:
        from .models import FAQCategory, FAQItem
        category = FAQCategory.objects.get(slug=category_slug)
        faqs = FAQItem.objects.filter(
            category=category, 
            is_active=True
        ).order_by('order')
        
        faq_list = []
        for faq in faqs:
            faq_list.append({
                'id': faq.id,
                'short_question': faq.short_question,
                'question': faq.question,
                'short_answer': faq.short_answer if hasattr(faq, 'short_answer') else faq.answer[:100] + '...',
                'read_time': faq.read_time,
            })
        
        return JsonResponse({
            'success': True,
            'category': category.name,
            'faqs': faq_list
        })
    except FAQCategory.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Category not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



def generate_bot_response(message):
    """
    Generate automated responses using FAQ database
    """
    message_lower = message.lower().strip()
    
    # First, check for greetings and basic responses
    if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings']):
        response = {
            'type': 'greeting',
            'message': "Hello! 👋 I'm FixIT Assistant! I can help you with various technical issues. What can I assist you with today?",
            'buttons': get_quick_action_buttons(),
            'related_faqs': []  # Make sure this is included
        }
        print(f"🔧 DEBUG: Generated greeting response with {len(response.get('buttons', []))} buttons")
        print(f"🔧 DEBUG: Button data: {response.get('buttons')}")
        return response
    
    
    # Search FAQ database for matches
    faq_matches = search_faq_database(message_lower)
    
    if faq_matches:
        # Get the best match
        best_match = faq_matches[0]
        
        return {
            'type': 'faq_answer',
            'message': best_match.answer,
            'faq_id': best_match.id,
            'category': best_match.category.name,
            'related_faqs': get_related_faqs(best_match),
            'buttons': get_related_buttons(best_match.category)
        }
    
    # Check for specific keywords in messages
    keyword_responses = get_keyword_response(message_lower)
    if keyword_responses:
        return keyword_responses
    
    # Default response
    return {
        'type': 'default',
        'message': "🤔 **I'm here to help!**\n\nI understand you're asking about: *'" + message + "'*\n\nCould you provide more specific details about your issue? You can also use the quick buttons below for common problems.",
        'buttons': get_quick_action_buttons()
    }


def search_faq_database(query):
    """
    Search FAQ database for relevant answers
    """
    from .models import FAQItem
    
    # First, try exact keyword matching
    faq_items = FAQItem.objects.filter(is_active=True)
    
    # Split query into words
    query_words = query.lower().split()
    
    scored_items = []
    
    for faq in faq_items:
        score = 0
        
        # Check if query words are in question
        question_lower = faq.question.lower()
        for word in query_words:
            if len(word) > 3 and word in question_lower:
                score += 3
        
        # Check if query words are in keywords
        if faq.keywords:
            keywords = [k.strip().lower() for k in faq.keywords.split(',')]
            for word in query_words:
                if word in keywords:
                    score += 5
        
        # Check short question
        if faq.short_question and query in faq.short_question.lower():
            score += 8
        
        # Check answer
        if query in faq.answer.lower():
            score += 2
        
        # Add bot priority
        score += faq.bot_priority
        
        if score > 0:
            scored_items.append((faq, score))
    
    # Sort by score (highest first)
    scored_items.sort(key=lambda x: x[1], reverse=True)
    
    return [item[0] for item in scored_items[:3]]  # Return top 3 matches


def get_quick_action_buttons():
    """
    Get comprehensive quick action buttons for bot chat
    """
    from .models import FAQItem, FAQCategory
    
    buttons = []
    
    # Get categories in order
    categories = FAQCategory.objects.all().order_by('order')[:3]  # Top 3 categories
    
    for category in categories:
        # Get 2 top FAQs from each category
        category_faqs = FAQItem.objects.filter(
            category=category,
            is_active=True,
            show_in_bot_buttons=True
        ).order_by('bot_priority', 'order')[:2]
        
        for faq in category_faqs:
            buttons.append({
                'text': faq.short_question,
                'faq_id': faq.id,
                'category': category.name,
                'icon': category.icon,
                'action': f'faq_{faq.id}'
            })
    
    # Add general action buttons
    buttons.extend([
        {'text': '🏠 Main Menu', 'action': 'menu', 'icon': 'home'},
        {'text': '📝 Create Ticket', 'action': 'create_ticket', 'icon': 'ticket-alt'},
        {'text': '👨‍💻 Contact Tech', 'action': 'contact_technician', 'icon': 'user-cog'},
        {'text': '📋 All FAQs', 'action': 'view_faqs', 'icon': 'book'},
    ])
    
    return buttons

def get_related_faqs(faq_item):
    """
    Get related FAQ items with proper formatting
    """
    from .models import FAQItem
    
    related = FAQItem.objects.filter(
        category=faq_item.category,
        is_active=True
    ).exclude(id=faq_item.id).order_by('order')[:5]
    
    # Format for template
    return [{
        'id': faq.id,
        'short_question': faq.short_question,
        'question': faq.question,
    } for faq in related]

def get_related_buttons(category):
    """
    Get buttons related to a specific category
    """
    from .models import FAQItem
    
    faqs = FAQItem.objects.filter(
        category=category,
        is_active=True,
        show_in_bot_buttons=True
    ).order_by('order')[:5]
    
    buttons = []
    for faq in faqs:
        buttons.append({
            'text': faq.short_question,
            'faq_id': faq.id
        })
    
    return buttons


def get_keyword_response(query):
    """
    Handle specific keyword patterns
    """
    responses = {
        'thank': {
            'type': 'thanks',
            'message': "You're welcome! 😊 I'm glad I could help. Is there anything else you need assistance with today?",
            'buttons': get_quick_action_buttons()
        },
        'bye': {
            'type': 'goodbye',
            'message': "Goodbye! 👋 Don't hesitate to reach out if you need more help. Have a great day!",
            'buttons': []
        },
        'menu': {
            'type': 'menu',
            'message': "🏠 **Main Menu**\n\nHow can I help you today?",
            'buttons': get_quick_action_buttons()
        },
        'create_ticket': {
            'type': 'create_ticket',
            'message': "📝 **Create Support Ticket**\n\nI can help you create a support ticket! Would you like me to guide you through the process?",
            'buttons': [
                {'text': 'Yes, create a ticket', 'action': 'start_ticket_creation'},
                {'text': 'No, go back', 'action': 'menu'}
            ]
        },
        'contact_technician': {
            'type': 'contact_technician',
            'message': "👨‍💻 **Contact Technician**\n\nI can help you find and contact available technicians. Would you like to browse the technician directory?",
            'buttons': [
                {'text': 'Browse Technicians', 'action': 'technician_directory'},
                {'text': 'No, go back', 'action': 'menu'}
            ]
        },
        'view_faqs': {
            'type': 'view_faqs',
            'message': "📋 **FAQ Categories**\n\nHere are our main help categories. Click any category to see related FAQs:",
            'buttons': get_category_buttons()
        }
    }
    
    for keyword, response in responses.items():
        if keyword in query:
            return response
    
    return None


def get_category_buttons():
    """
    Get FAQ category buttons
    """
    from .models import FAQCategory
    
    categories = FAQCategory.objects.all().order_by('order')
    
    buttons = []
    for category in categories:
        buttons.append({
            'text': category.name,
            'icon': category.icon,
            'action': f'category_{category.slug}'
        })
    
    return buttons


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import TicketCreationForm

@login_required
def create_ticket(request):
    if request.method == 'POST':
        form = TicketCreationForm(request.POST)
        if form.is_valid():
            # Save the ticket, but don't commit to DB yet
            ticket = form.save(commit=False)
            # Assign the currently logged-in user
            ticket.user = request.user
            # Now save to the database
            ticket.save()
            # Redirect to the 'My Tickets' page or a success page
            return redirect('my_tickets')
    else:
        # If it's a GET request, create a blank form
        form = TicketCreationForm()

    context = {
        'form': form
    }
    return render(request, 'accounts/create_ticket.html', context)


from django.shortcuts import render
from .models import CreateTicket
def my_tickets(request):
    tickets = CreateTicket.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'accounts/my_tickets.html', {'tickets': tickets})

#PLACEHOLDER
from django.shortcuts import render
@login_required
def available_technicians(request):
    tech_qs = Technician.objects.select_related('user_profile__user').prefetch_related('specialties').filter(is_available=True)
    technicians = []
    for t in tech_qs:
        user_obj = t.user_profile.user
        name = user_obj.get_full_name() or user_obj.username
        specialties = t.get_specialties_list()
        technicians.append({
            'id': user_obj.id,
            'name': name,
            'specialty': ', '.join(specialties) if specialties else 'General IT Support'
        })

    category = request.GET.get('category', '')
    return render(request, 'accounts/available_technicians.html', {
        'technicians': technicians,
        'category': category,
    })


@login_required
def my_tickets(request):
    from django.db.models import Q

    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    allowed_statuses = ['open', 'pending', 'assigned', 'in_progress', 'resolved']

    tickets_qs = CreateTicket.objects.filter(user=request.user)
    if q:
        tickets_qs = tickets_qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if status_filter in allowed_statuses:
        tickets_qs = tickets_qs.filter(status=status_filter)

    tickets = tickets_qs.prefetch_related(
        'assistance_requests__technician__user_profile__user'
    ).order_by('-created_at')

    ticket_data = []
    for ticket in tickets:
        info = {
            'ticket': ticket,
            'assigned_technician': None
        }
        ar = ticket.assistance_requests.first()
        if ar and ar.technician:
            info['assigned_technician'] = ar.technician
        ticket_data.append(info)

    return render(request, 'accounts/my_tickets.html', {
        'ticket_data': ticket_data,
        'q': q,
        'status_filter': status_filter,
    })


from .utils import create_notification

def respond_ticket(request, ticket_id):
    ticket = CreateTicket.objects.get(id=ticket_id)
    helper = request.user
    response_message = request.POST.get('response')  # Or however you get the response

    # Save response to your TicketResponse model or update ticket

    # Create notification for the ticket owner
    create_notification(ticket, helper, f"{helper.username} responded: {response_message}")

    return redirect('ticket_detail', ticket_id=ticket.id)

def faq_view(request):
    """
    Display FAQ/Help Center page
    """
    context = {
        'title': 'Help Center - FixIT'
    }
    return render(request, 'accounts/FAQ_Page.html', context)

#TECHNICIAN NOTIFICATION
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Ticket, Notifications_Technician
from django.shortcuts import get_object_or_404, redirect

@login_required
def contact_technician(request, ticket_id, technician_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    technician = get_object_or_404(User, id=technician_id)

    # Assign technician to the ticket
    ticket.technician = technician
    ticket.save()

    # Create notification for technician
    Notifications_Technician.objects.create(
        technician=technician,
        message=f"New ticket assigned: {ticket.title}",
        ticket=ticket
    )

    messages.success(request, "Technician has been notified!")
    return redirect('messages_view')  # or wherever you want to redirect


from django.shortcuts import get_object_or_404, redirect
from .models import CreateTicket  # adjust model name if different

def delete_ticket(request, ticket_id):
    ticket = get_object_or_404(CreateTicket, id=ticket_id, user=request.user)
    ticket.delete()
    return redirect("my_tickets")  # redirect to your ticket list page

@login_required
def ticket_details_view(request, ticket_id):
    """View ticket details for regular users"""
    ticket = get_object_or_404(CreateTicket, id=ticket_id, user=request.user)
    assigned_technician = None
    ar = ticket.assistance_requests.first()
    if ar and ar.technician:
        assigned_technician = ar.technician
    
    # Fetch the current user's review for this ticket if available
    user_review = None
    if assigned_technician:
        user_review = TechnicianReview.objects.filter(
            technician=assigned_technician,
            user=request.user,
            ticket=ticket
        ).order_by('-created_at').first()

    context = {
        'ticket': ticket,
        'title': f'Ticket #{ticket.id} - {ticket.title}',
        'assigned_technician': assigned_technician,
        'user_review': user_review,
    }
    return render(request, 'dashboard/ticket_details.html', context)

@login_required
def technician_ticket_details_view(request, ticket_id):
    """View ticket details for technicians"""
    ticket = get_object_or_404(
        CreateTicket, 
        id=ticket_id,
        assistance_requests__technician__user_profile__user=request.user
    )
    ar = ticket.assistance_requests.first()
    assigned_technician = ar.technician if ar and ar.technician else None
    review = None
    if assigned_technician:
        review = TechnicianReview.objects.filter(
            technician=assigned_technician,
            ticket=ticket
        ).order_by('-created_at').first()

    context = {
        'ticket': ticket,
        'title': f'Ticket #{ticket.id} - {ticket.title}',
        'is_technician': True,
        'assigned_technician': assigned_technician,
        'review': review
    }
    return render(request, 'dashboard/ticket_details.html', context)
@login_required
def resolve_ticket(request, ticket_id):
    """Technician toggles ticket resolved status and notifies parties"""
    user = request.user
    ticket = get_object_or_404(
        CreateTicket,
        id=ticket_id,
        assistance_requests__technician__user_profile__user=user
    )
    if request.method == 'POST':
        if ticket.status == 'resolved':
            ar = ticket.assistance_requests.first()
            assigned_technician = ar.technician if ar and ar.technician else None
            has_review = TechnicianReview.objects.filter(ticket=ticket).exists()
            if has_review:
                messages.error(request, "Cannot unresolve this ticket because a review has already been submitted.")
                return redirect('technician_tickets')
            ticket.status = 'open'
            ticket.save()
            Notifications_Technician.objects.create(
                technician=user,
                message=f"Ticket #{ticket.id} reopened",
                ticket=None
            )
            Notification.objects.create(
                recipient=ticket.user,
                sender=user,
                ticket=ticket,
                message=f"Your ticket #{ticket.id} '{ticket.title}' was reopened."
            )
            messages.success(request, f"Ticket #{ticket.id} set to Open.")
        else:
            ticket.status = 'resolved'
            ticket.save()
            Notifications_Technician.objects.create(
                technician=user,
                message=f"Ticket #{ticket.id} marked as resolved",
                ticket=None
            )
            Notification.objects.create(
                recipient=ticket.user,
                sender=user,
                ticket=ticket,
                message=f"Your ticket #{ticket.id} '{ticket.title}' has been resolved. Please provide feedback and a rating."
            )
            messages.success(request, f"Ticket #{ticket.id} set to Resolved and notifications sent.")
        return redirect('technician_tickets')
    return redirect('technician_tickets')

@login_required
def start_work_ticket(request, ticket_id):
    user = request.user
    ticket = get_object_or_404(
        CreateTicket,
        id=ticket_id,
        assistance_requests__technician__user_profile__user=user
    )
    if request.method == 'POST':
        if ticket.status == 'resolved':
            messages.error(request, 'Cannot start work on a resolved ticket.')
            return redirect('technician_tickets')
        if ticket.status == 'in_progress':
            messages.info(request, f"Ticket #{ticket.id} is already in progress.")
            return redirect('technician_tickets')
        ticket.status = 'in_progress'
        ticket.save()
        Notifications_Technician.objects.create(
            technician=user,
            message=f"Started work on ticket #{ticket.id}",
            ticket=None
        )
        Notification.objects.create(
            recipient=ticket.user,
            sender=user,
            ticket=ticket,
            message=f"Your ticket #{ticket.id} '{ticket.title}' is now being worked on."
        )
        messages.success(request, f"Ticket #{ticket.id} set to In Progress.")
        return redirect('technician_tickets')
    return redirect('technician_tickets')

@login_required
def submit_ticket_review(request, ticket_id):
    """User submits rating/comment for the technician on a resolved ticket"""
    if request.method != 'POST':
        return redirect('ticket_details', ticket_id=ticket_id)

    ticket = get_object_or_404(CreateTicket, id=ticket_id, user=request.user)
    if ticket.status != 'resolved':
        messages.error(request, 'You can only rate after the ticket is resolved.')
        return redirect('ticket_details', ticket_id=ticket_id)

    ar = ticket.assistance_requests.first()
    if not ar or not ar.technician:
        messages.error(request, 'No technician assigned to this ticket.')
        return redirect('ticket_details', ticket_id=ticket_id)

    technician = ar.technician
    try:
        rating = int(request.POST.get('rating', ''))
    except ValueError:
        messages.error(request, 'Invalid rating value.')
        return redirect('ticket_details', ticket_id=ticket_id)
    comment = request.POST.get('comment', '')

    if rating < 1 or rating > 5:
        messages.error(request, 'Rating must be between 1 and 5.')
        return redirect('ticket_details', ticket_id=ticket_id)

    # Create or update review
    review, created = TechnicianReview.objects.get_or_create(
        technician=technician,
        user=request.user,
        ticket=ticket,
        defaults={
            'rating': rating,
            'comment': comment
        }
    )
    if not created:
        # adjust average rating without changing review_count
        old_rating = review.rating
        review.rating = rating
        review.comment = comment
        review.save()
        if technician.review_count > 0:
            technician.average_rating = ((technician.average_rating * technician.review_count) - old_rating + rating) / technician.review_count
            technician.save()
    else:
        technician.update_rating(rating)

    # Notify technician
    Notifications_Technician.objects.create(
        technician=technician.user_profile.user,
        message=f"New review received: {rating} stars",
        ticket=None
    )

    messages.success(request, 'Thank you for your feedback!')
    return redirect('ticket_details', ticket_id=ticket_id)


# views.py (Technician side)
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction  # Import transaction for safety


def accept_request_view(request, request_id):
    # Ensure the user is authenticated and has a technician profile
    if not request.user.is_authenticated or not hasattr(request.user,
                                                        'profile') or not request.user.profile.is_technician:
        messages.error(request, "Access denied. You must be an authorized technician.")
        return redirect('home')

    assistance_request = get_object_or_404(AssistanceRequest, id=request_id)

    # Access the Django User object attached to the Technician profile
    technician_user = assistance_request.technician.user

    # 1. Security Check: Ensure the logged-in user is the technician named in the request
    if technician_user != request.user:
        messages.error(request, "You are not authorized to accept this request.")
        return redirect('technician_dashboard')

    # 2. Status Check: Ensure the ticket's underlying status is compatible
    if assistance_request.status == 'pending':

        # Use a database transaction to ensure both updates happen successfully, or neither does.
        with transaction.atomic():

            # a. Update the AssistanceRequest status
            assistance_request.status = 'accepted'
            assistance_request.save()

            # b. Update the main CreateTicket
            ticket = assistance_request.ticket

            # CRITICAL CHANGE: Assign the Django User object
            ticket.technician = technician_user
            ticket.status = 'assigned'
            ticket.save()

            # c. OPTIONAL: Reject any other pending requests for this same ticket
            AssistanceRequest.objects.filter(
                ticket=ticket,
                status='pending'
            ).exclude(id=request_id).update(status='rejected')

        messages.success(request, f"Ticket #{ticket.id} has been successfully assigned to you.")
    else:
        messages.error(request, "This request has already been handled or is invalid.")

    return redirect('technician_dashboard')


@login_required
def debug_upload_flow(request):
    """Debug the complete upload flow"""
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile
    from django.http import JsonResponse
    import os

    debug_info = {
        'storage_backend': str(default_storage.__class__),
        'storage_module': default_storage.__class__.__module__,
    }

    # Test 1: Check storage backend attributes
    try:
        debug_info['bucket_name'] = getattr(default_storage, 'bucket_name', 'Not found')
        debug_info['endpoint_url'] = getattr(default_storage, 'endpoint_url', 'Not found')
        debug_info['access_key'] = getattr(default_storage, 'access_key', 'Not found')
        debug_info['secret_key_set'] = bool(getattr(default_storage, 'secret_key', None))
    except Exception as e:
        debug_info['attribute_error'] = str(e)

    # Test 2: Perform actual file operation and see where it goes
    try:
        test_filename = f"debug_upload_test_{request.user.id}.txt"
        test_content = b"This is a test upload to see where files go"

        print(f"🧪 DEBUG: Attempting to save {test_filename}")

        # Save file
        saved_path = default_storage.save(test_filename, ContentFile(test_content))
        debug_info['saved_path'] = saved_path
        print(f"✅ DEBUG: File saved as: {saved_path}")

        # Check if it's a local filesystem path
        if hasattr(default_storage, 'location'):
            storage_location = default_storage.location
            debug_info['storage_location'] = storage_location

            # Check if file exists locally
            local_path = os.path.join(storage_location, saved_path) if storage_location else saved_path
            debug_info['local_path'] = local_path
            debug_info['local_exists'] = os.path.exists(local_path)
            print(f"🔍 DEBUG: Local path: {local_path}, Exists: {debug_info['local_exists']}")

        # Check if file exists in storage
        debug_info['storage_exists'] = default_storage.exists(saved_path)
        print(f"🔍 DEBUG: Storage exists: {debug_info['storage_exists']}")

        # Try to get URL
        try:
            url = default_storage.url(saved_path)
            debug_info['generated_url'] = url
            print(f"🌐 DEBUG: Generated URL: {url}")
        except Exception as e:
            debug_info['url_error'] = str(e)
            print(f"❌ DEBUG: URL error: {e}")

        # Clean up
        try:
            default_storage.delete(saved_path)
            debug_info['cleanup_success'] = True
        except Exception as e:
            debug_info['cleanup_error'] = str(e)

    except Exception as e:
        debug_info['upload_test_error'] = str(e)
        print(f"❌ DEBUG: Upload test failed: {e}")

    return JsonResponse(debug_info)

@login_required
def check_current_storage(request):
    """Check which storage backend is actually being used"""
    from django.conf import settings
    from django.core.files.storage import default_storage
    from django.http import JsonResponse

    config = {
        'DEFAULT_FILE_STORAGE': getattr(settings, 'DEFAULT_FILE_STORAGE', 'Not set'),
        'actual_storage_class': str(default_storage.__class__),
        'STORAGES_default': getattr(settings, 'STORAGES', {}).get('default', {}).get('BACKEND', 'Not set'),
    }

    # Check if we're using local storage instead of S3
    if 'FileSystemStorage' in str(default_storage.__class__):
        config['storage_type'] = 'LOCAL_FILESYSTEM'
        if hasattr(default_storage, 'location'):
            config['local_media_root'] = default_storage.location
    else:
        config['storage_type'] = 'REMOTE_STORAGE'

    return JsonResponse(config)


@login_required
def debug_fix_chats(request):
    """
    Debug endpoint to manually create missing chat sessions
    """
    if not request.user.profile.is_technician:
        return JsonResponse({'error': 'Not a technician'})
    
    user = request.user
    print(f"🔧 DEBUG FIX: Starting chat fix for technician {user.username}")
    
    # Get all assigned tickets
    assigned_tickets = CreateTicket.objects.filter(
        assistance_requests__technician__user_profile__user=user
    ).distinct()
    
    print(f"🔧 DEBUG FIX: Found {assigned_tickets.count()} assigned tickets")
    
    created_count = 0
    ticket_details = []
    
    for ticket in assigned_tickets:
        print(f"🔧 DEBUG FIX: Processing ticket {ticket.id}: {ticket.title}")
        
        # Check if chat session already exists
        existing_chat = ChatSession.objects.filter(
            technician=user,
            ticket=ticket
        ).first()
        
        if existing_chat:
            print(f"🔧 DEBUG FIX: Chat already exists for ticket {ticket.id} - Chat ID: {existing_chat.id}")
            ticket_details.append({
                'ticket_id': ticket.id,
                'ticket_title': ticket.title,
                'chat_exists': True,
                'chat_id': existing_chat.id
            })
        else:
            # Create new chat session
            try:
                chat_session = ChatSession.objects.create(
                    user=ticket.user,
                    technician=user,
                    ticket=ticket,
                    chat_type='user_tech',
                    status='active',
                    last_message_at=timezone.now()
                )
                
                # Create initial message
                initial_content = f"Support ticket created: {ticket.title}\n\nDescription: {ticket.description}\nCategory: {ticket.category}\nPriority: {ticket.priority}"
                
                Message.objects.create(
                    chat_session=chat_session,
                    sender=ticket.user,
                    receiver=user,
                    content=initial_content,
                    message_type='user_to_tech',
                    created_at=timezone.now()
                )
                
                created_count += 1
                print(f"🔧 DEBUG FIX: Created chat session {chat_session.id} for ticket {ticket.id}")
                
                ticket_details.append({
                    'ticket_id': ticket.id,
                    'ticket_title': ticket.title,
                    'chat_exists': False,
                    'chat_created': True,
                    'chat_id': chat_session.id
                })
                
            except Exception as e:
                print(f"❌ DEBUG FIX: Error creating chat for ticket {ticket.id}: {e}")
                ticket_details.append({
                    'ticket_id': ticket.id,
                    'ticket_title': ticket.title,
                    'error': str(e)
                })
    
    print(f"🔧 DEBUG FIX: Created {created_count} new chat sessions")
    
    return JsonResponse({
        'success': True,
        'created_count': created_count,
        'total_tickets': assigned_tickets.count(),
        'ticket_details': ticket_details,
        'message': f'Created {created_count} missing chat sessions out of {assigned_tickets.count()} assigned tickets'
    })
@login_required
def debug_technician_data(request):
    """
    Comprehensive debug view for technician data
    """
    user = request.user
    
    data = {
        'technician': {
            'username': user.username,
            'is_technician': user.profile.is_technician,
        },
        'assistance_requests': [],
        'tickets': [],
        'chat_sessions': []
    }
    
    # Get assistance requests
    assistance_requests = AssistanceRequest.objects.filter(
        technician__user_profile__user=user
    ).select_related('ticket', 'user')
    
    for ar in assistance_requests:
        data['assistance_requests'].append({
            'id': ar.id,
            'title': ar.title,
            'status': ar.status,
            'ticket_id': ar.ticket.id if ar.ticket else None,
            'ticket_title': ar.ticket.title if ar.ticket else None,
            'user': ar.user.username,
        })
    
    # Get tickets
    tickets = CreateTicket.objects.filter(
        assistance_requests__technician__user_profile__user=user
    ).distinct()
    
    for ticket in tickets:
        data['tickets'].append({
            'id': ticket.id,
            'title': ticket.title,
            'status': ticket.status,
            'user': ticket.user.username,
        })
    
    # Get chat sessions
    chat_sessions = ChatSession.objects.filter(technician=user)
    
    for chat in chat_sessions:
        data['chat_sessions'].append({
            'id': chat.id,
            'user': chat.user.username,
            'ticket_id': chat.ticket.id if chat.ticket else None,
            'ticket_title': chat.ticket.title if chat.ticket else None,
            'chat_type': chat.chat_type,
            'status': chat.status,
        })
    
    return JsonResponse(data)

@csrf_exempt
@login_required
def debug_request_assistance(request):
    """Debug endpoint to see what's being received"""
    print("=== DEBUG REQUEST ASSISTANCE ===")
    print(f"Method: {request.method}")
    print(f"Content-Type: {request.content_type}")
    print(f"Body: {request.body}")
    print(f"User: {request.user}")
    print(f"POST data: {request.POST}")

    if request.body:
        try:
            data = json.loads(request.body.decode('utf-8'))
            print(f"JSON data: {data}")
        except Exception as e:
            print(f"JSON decode error: {e}")

    return JsonResponse({
        'success': True,
        'debug': 'Check server logs',
        'method': request.method,
        'content_type': request.content_type,
        'user': request.user.username
    })

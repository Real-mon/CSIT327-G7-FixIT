import os
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserSignUpForm, UserLoginForm, UserUpdateForm, ProfileUpdateForm, ProfilePictureForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.shortcuts import render

from .models import Ticket, UserSettings

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Avg, Count
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Technician, TechnicianSpecialty, AssistanceRequest
from .models import User, UserProfile, Message, Contact, BotChat, BotMessage
from django.utils import timezone


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


from accounts.forms import UserSignUpForm
from accounts.models import UserProfile

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from .forms import UserSignUpForm
from .models import UserProfile

from django.contrib.auth import login
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import UserSignUpForm
from .models import UserProfile  # make sure this is imported


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




from django.contrib.auth import authenticate, login
from django.contrib import messages


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
        'title': 'Technician Directory - FixIT'
    }
    
    return render(request, 'dashboard/technician_directory.html', context)


@login_required
@require_POST
def request_assistance_view(request):
    """
    Handle assistance requests to technicians and create tickets
    """
    try:
        data = json.loads(request.body)
        technician_id = data.get('technician_id')
        title = data.get('title', 'Assistance Request').strip()
        description = data.get('description', '').strip()
        priority = data.get('priority', 'medium')
        
        # Validate required fields
        if not title:
            return JsonResponse({
                'success': False,
                'error': 'Title is required'
            }, status=400)
            
        if not description:
            return JsonResponse({
                'success': False,
                'error': 'Description is required'
            }, status=400)
        
        technician = get_object_or_404(Technician, id=technician_id)
        
        # Create a corresponding ticket first
        ticket = CreateTicket.objects.create(
            user=request.user,
            title=title,
            description=description,
            category='other',  # Default category
            priority=priority,
            status='open'
        )
        
        # Create assistance request linked to the ticket
        assistance_request = AssistanceRequest.objects.create(
            user=request.user,
            technician=technician,
            ticket=ticket,  # Link to the created ticket
            title=title,
            description=description,
            priority=priority
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Assistance request sent to {technician.full_name}',
            'request_id': assistance_request.id,
            'ticket_id': ticket.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Technician.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Technician not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
        
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
    
    context = {
        'technician': technician,
        'recent_reviews': recent_reviews,
        'title': f'{technician.full_name} - Technician Profile - FixIT'
    }
    
    return render(request, 'dashboard/technician_detail.html', context)



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

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'picture_form': picture_form,
        'title': 'Update Profile - FixIT'
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
def technician_dashboard_view(request):
    """
    Display technician dashboard
    """
    user = request.user
    profile = user.profile  # <-- Correct way to access UserProfile

    profile.refresh_from_db()  # ensure updated values

    # Check if user is a technician
    if not profile.is_technician:
        messages.error(request, 'You do not have permission to access the technician dashboard.')
        return redirect('user_dashboard')

    context = {
        'user': user,
        'profile': profile,
        'title': 'Technician Dashboard - FixIT'
    }
    return render(request, 'dashboard/technician_dashboard.html', context)




@login_required
def user_dashboard_view(request):
    """
    Display user dashboard
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

    context = {
        'user': user,
        'profile': profile,
        'title': 'User Dashboard - FixIT'
    }
    return render(request, 'dashboard/user_dashboard.html', context)

#@login_required
def password_reset_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
            return redirect('change_password')  # Your Change password UI
        except User.DoesNotExist:
            return render(request, "accounts/password_reset.html", {"message": "❌ No account found with that email."})
    
    context = {
        'title': 'Password Reset - FixIT',
        'hide_navigation': True
    }
    return render(request, 'accounts/password_reset.html', context)



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
            
            # The file will automatically upload to Supabase storage
            # due to our DEFAULT_FILE_STORAGE configuration
            request.user.profile.profile_picture = unique_filename
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
    """Display settings page."""
    settings, created = UserSettings.objects.get_or_create(user=request.user)
    context = {
        'settings': settings
    }
    return render(request, 'dashboard/settings.html', context)


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
def user_messages_view(request):
    """
    Display user messages page with chats and messaging functionality
    """
    user = request.user
    
    # Get all technicians for adding as contacts
    technicians = UserProfile.objects.filter(is_technician=True).exclude(user=user)
    
    # Get user's contacts
    user_contacts = Contact.objects.filter(user=user)
    
    # Get user's bot chats
    user_bot_chats = []
    try:
        user_bot_chats = BotChat.objects.filter(user=user)
    except Exception as e:
        print(f"BotChat not available: {e}")
        # If BotChat doesn't exist, we'll work with contacts only
    
    # Combine both types of chats
    user_chats = []
    for contact in user_contacts:
        contact.is_bot = False
        user_chats.append(contact)
    for bot_chat in user_bot_chats:
        bot_chat.is_bot = True
        bot_chat.contact_name = "FixIT Assistant"
        user_chats.append(bot_chat)
    
    # Get selected chat for messaging
    selected_chat_id = request.GET.get('chat')
    selected_chat = None
    chat_messages = []
    
    if selected_chat_id:
        try:
            # Check if it's a bot chat or contact chat
            if selected_chat_id.startswith('bot_'):
                bot_chat_id = selected_chat_id.replace('bot_', '')
                selected_chat = BotChat.objects.get(id=bot_chat_id, user=user)
                selected_chat.is_bot = True
                selected_chat.contact_name = "FixIT Assistant"
                chat_messages = BotMessage.objects.filter(chat=selected_chat).order_by('timestamp')
            else:
                selected_chat = Contact.objects.get(id=selected_chat_id, user=user)
                selected_chat.is_bot = False
                chat_messages = Message.objects.filter(
                    Q(sender=user, receiver=selected_chat.contact_user) |
                    Q(sender=selected_chat.contact_user, receiver=user)
                ).order_by('timestamp')
        except Exception as e:
            print(f"Error loading chat: {e}")
            selected_chat = None
    
    # Handle POST requests
    if request.method == 'POST':
        # Handle starting new bot chat
        if 'start_bot_chat' in request.POST:
            try:
                # Create new bot chat
                bot_chat = BotChat.objects.create(user=user)
                
                # Add welcome message from bot
                BotMessage.objects.create(
                    chat=bot_chat,
                    sender=None,
                    content="Hello! I'm FixIT Assistant 👋 I'm here to help you with common issues and FAQs. How can I assist you today?",
                    is_bot=True
                )
                
                return JsonResponse({
                    'success': True, 
                    'chat_id': f'bot_{bot_chat.id}',
                    'redirect_url': f'{request.path}?chat=bot_{bot_chat.id}'
                })
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        # Handle sending new message
        elif 'send_message' in request.POST:
            chat_id = request.POST.get('chat_id')
            message_content = request.POST.get('message_content', '').strip()
            
            print(f"DEBUG: Sending message to chat_id: {chat_id}, content: {message_content}")
            
            if chat_id and message_content:
                if chat_id.startswith('bot_'):
                    # Handle bot message
                    bot_chat_id = chat_id.replace('bot_', '')
                    try:
                        bot_chat = BotChat.objects.get(id=bot_chat_id, user=user)
                        
                        # Save user message
                        user_message = BotMessage.objects.create(
                            chat=bot_chat,
                            sender=user,
                            content=message_content,
                            is_bot=False
                        )
                        print(f"DEBUG: Saved user message: {user_message.id}")
                        
                        # Generate and save bot response
                        bot_response = generate_bot_response(message_content)
                        bot_message = BotMessage.objects.create(
                            chat=bot_chat,
                            sender=None,
                            content=bot_response,
                            is_bot=True
                        )
                        print(f"DEBUG: Saved bot response: {bot_message.id}")
                        
                        messages.success(request, 'Message sent!')
                        return redirect(f'{request.path}?chat={chat_id}')
                        
                    except BotChat.DoesNotExist:
                        print(f"DEBUG: BotChat not found for id: {bot_chat_id}")
                        messages.error(request, 'Chat session not found. Please start a new chat.')
                    except Exception as e:
                        print(f"DEBUG: Error in bot message: {e}")
                        messages.error(request, 'Error sending message to assistant.')
                else:
                    # Handle regular message to technician
                    try:
                        contact = Contact.objects.get(id=chat_id, user=user)
                        Message.objects.create(
                            sender=user,
                            receiver=contact.contact_user,
                            content=message_content,
                            timestamp=timezone.now()
                        )
                        messages.success(request, 'Message sent successfully!')
                        return redirect(f'{request.path}?chat={chat_id}')
                    except Contact.DoesNotExist:
                        print(f"DEBUG: Contact not found for id: {chat_id}")
                        messages.error(request, 'Contact not found.')
            else:
                messages.error(request, 'Message cannot be empty.')
    
    context = {
        'user': user,
        'profile': user.profile,
        'title': 'Messages - FixIT',
        'technicians': technicians,
        'user_chats': user_chats,
        'selected_chat': selected_chat,
        'chat_messages': chat_messages,
    }
    return render(request, 'dashboard/user_message.html', context)

def generate_bot_response(message):
    """
    Generate automated responses for the bot chat
    """
    message_lower = message.lower()
    
    responses = {
        # Network Issues
        'internet not showing in network options': "🌐 **Internet Not Showing in Network Options**\n\n**Troubleshooting Steps:**\n\n1. **Check Physical Connections**\n   • Ensure Ethernet cable is securely connected\n   • Restart your router/modem\n   • Check if other devices can connect\n\n2. **Network Adapter Issues**\n   • Go to Device Manager → Network Adapters\n   • Right-click your adapter → 'Update driver'\n   • Or try 'Disable' then 'Enable' the adapter\n\n3. **Network Reset**\n   • Windows: Settings → Network & Internet → Network Reset\n   • This will reinstall network adapters\n\n4. **Quick Fixes**\n   • Run Windows Network Diagnostics\n   • Command Prompt: `ipconfig /release` then `ipconfig /renew`\n   • Temporarily disable VPN/antivirus\n\nIf none work, you may need to contact your ISP or create a support ticket for further assistance.",
        
        'wifi keeps disconnecting': "📶 **WiFi Connection Drops**\n\n**Common Solutions:**\n\n1. **Router Position**\n   • Move closer to the router\n   • Avoid physical obstructions\n   • Keep away from microwave ovens/cordless phones\n\n2. **Router Settings**\n   • Restart your router\n   • Update router firmware\n   • Change WiFi channel (1, 6, or 11)\n\n3. **Device Settings**\n   • Update wireless adapter drivers\n   • Disable 'Allow computer to turn off this device to save power'\n   • Forget network and reconnect\n\n4. **Advanced Fixes**\n   • Change WiFi band (2.4GHz vs 5GHz)\n   • Check for interference from other networks\n   • Consider WiFi extender if signal is weak",
        
        'slow internet speed': "🐢 **Slow Internet Speed**\n\n**Speed Improvement Steps:**\n\n1. **Immediate Actions**\n   • Restart router and modem\n   • Close bandwidth-heavy applications\n   • Run speed test (speedtest.net)\n\n2. **Device Optimization**\n   • Clear browser cache and cookies\n   • Update network drivers\n   • Scan for malware/viruses\n\n3. **Network Management**\n   • Limit devices connected to WiFi\n   • Use Ethernet cable for critical devices\n   • Check for background updates\n\n4. **Contact ISP**\n   • Verify your internet plan speed\n   • Check for outages in your area\n   • Request line quality check",
        
        # Device Problems
        'computer running very slow': "🖥️ **Slow Computer Performance**\n\n**Performance Boost Steps:**\n\n1. **Quick Cleanup**\n   • Restart your computer\n   • Close unused applications\n   • Clear temporary files\n\n2. **Startup Management**\n   • Task Manager → Startup tab\n   • Disable unnecessary startup programs\n   • This speeds up boot time\n\n3. **Storage Optimization**\n   • Ensure 15%+ free space on C: drive\n   • Run Disk Cleanup utility\n   • Uninstall unused programs\n\n4. **System Maintenance**\n   • Run antivirus scan\n   • Update Windows and drivers\n   • Consider adding more RAM if consistently slow",
        
        'printer not working': "🖨️ **Printer Troubleshooting**\n\n**Fix Printing Issues:**\n\n1. **Basic Checks**\n   • Ensure printer is powered on\n   • Check paper and ink levels\n   • Verify cables are connected\n\n2. **Connection Issues**\n   • Restart printer and computer\n   • Reinstall printer drivers\n   • Set as default printer\n\n3. **Software Solutions**\n   • Run Printer Troubleshooter\n   • Clear print queue\n   • Check printer status in Devices\n\n4. **Network Printing**\n   • For network printers, verify IP address\n   • Check if other computers can print\n   • Re-add network printer if needed",
        
        # Add more responses for other common issues...
    }
    
    # Check for exact matches first
    for keyword, response in responses.items():
        if keyword in message_lower:
            return response
    
    # Check for partial matches
    partial_responses = {
        'internet': "🌐 **Internet Connection Issues**\n\nI can help with various internet problems:\n• No internet connection\n• WiFi dropping\n• Slow speeds\n• Network not showing\n\nPlease describe your specific issue, or use the 'Common Issues' dropdown for targeted help!",
        
        'wifi': "📶 **WiFi Problems**\n\nCommon WiFi solutions:\n• Move closer to router\n• Restart router and device\n• Update network drivers\n• Change WiFi channel\n\nWhat specific WiFi issue are you experiencing?",
        
        'slow': "🐢 **Performance Issues**\n\nFor slow performance, try:\n• Restart your device\n• Close unused programs\n• Clear cache and temp files\n• Check for updates\n\nIs it internet speed or computer performance that's slow?",
        
        'printer': "🖨️ **Printer Help**\n\nPrinter troubleshooting:\n• Check power and connections\n• Verify ink/paper levels\n• Reinstall drivers\n• Clear print queue\n\nWhat's happening with your printer exactly?",
        
        'password': "🔐 **Password Assistance**\n\nFor password issues:\n• Use 'Forgot Password' on login page\n• Check your email for reset link\n• Ensure caps lock is off\n• Try different browser\n\nAre you unable to reset your password or having login problems?",
        
        'login': "🔑 **Login Problems**\n\nLogin issue solutions:\n• Verify username/password\n• Check caps lock\n• Clear browser cache\n• Try incognito mode\n\nWhat happens when you try to login?",
        
        'email': "📧 **Email Issues**\n\nEmail troubleshooting:\n• Check internet connection\n• Verify email credentials\n• Clear email app cache\n• Check spam folder\n\nAre you having trouble sending, receiving, or accessing email?",
    }
    
    for keyword, response in partial_responses.items():
        if keyword in message_lower:
            return response
    
    # Default responses for greetings
    if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings']):
        return "Hello! 👋 I'm FixIT Assistant! I can help you with:\n\n• 🌐 Network & Internet issues\n• 💻 Computer performance problems\n• 🖨️ Printer and peripheral issues\n• 📱 Software and application errors\n• 🔐 Login and account access\n• 📧 Email and communication problems\n\nWhat can I help you with today? You can also use the 'Common Issues' dropdown for quick solutions!"
    
    elif any(word in message_lower for word in ['thank', 'thanks']):
        return "You're welcome! 😊 I'm glad I could help. Is there anything else you need assistance with today?"
    
    elif any(word in message_lower for word in ['bye', 'goodbye', 'see you']):
        return "Goodbye! 👋 Don't hesitate to reach out if you need more help. Have a great day!"
    
    # Default response for unrecognized messages
    return "🤔 **I'm here to help!**\n\nI understand you're asking about: *'" + message + "'*\n\nI specialize in:\n• Network and connectivity issues\n• Computer performance problems\n• Software and hardware troubleshooting\n• Account and access problems\n\nCould you provide more specific details about your issue, or use the 'Common Issues' dropdown menu for common problems?"


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
def available_technicians(request):
    # Placeholder data
    technicians = [
        {'id': 1, 'name': 'John Doe', 'specialty': 'Hardware'},
        {'id': 2, 'name': 'Jane Smith', 'specialty': 'Software'},
        {'id': 3, 'name': 'Bob Johnson', 'specialty': 'Network'},
    ]

    return render(request, 'accounts/available_technicians.html', {'technicians': technicians})

@login_required
def my_tickets(request):
    # Get tickets with prefetch for assistance requests and technicians
    tickets = CreateTicket.objects.filter(user=request.user).prefetch_related(
        'assistance_requests__technician__user_profile__user'
    ).order_by('-created_at')
    
    # Prepare ticket data with technician info
    ticket_data = []
    for ticket in tickets:
        ticket_info = {
            'ticket': ticket,
            'assigned_technician': None
        }
        
        # Check if there's an assistance request for this ticket
        assistance_request = ticket.assistance_requests.first()
        if assistance_request and assistance_request.technician:
            ticket_info['assigned_technician'] = assistance_request.technician
            
        ticket_data.append(ticket_info)
    
    return render(request, 'accounts/my_tickets.html', {
        'ticket_data': ticket_data
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
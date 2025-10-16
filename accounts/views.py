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
    Handle user registration
    """
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect_to_correct_dashboard(request.user)
    
    # Get user_type from query parameters
    user_type = request.GET.get('user_type', 'user')
    
    if request.method == 'POST':
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Set user type based on selection
            if user_type == 'technician':
                user.is_technician = True
            user.save()
            
            # Log the user in after successful registration
            login(request, user)
            messages.success(request, f'Welcome {user.username}! Your account has been created successfully.')
            return redirect_to_correct_dashboard(user)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserSignUpForm(initial={'user_type': user_type})
    
    context = {
        'form': form,
        'title': 'Sign Up - FixIT',
        'user_type': user_type,
        'hide_navigation': True
    }
    return render(request, 'accounts/signup.html', context)


def login_view(request):
    """
    Handle user login
    """
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect_to_correct_dashboard(request.user)
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                # Redirect to correct dashboard based on user type
                return redirect_to_correct_dashboard(user)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    
    context = {
        'form': form,
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

###
@login_required
def profile_update_view(request):
    """
    Handle profile updates including profile picture and user details
    """
    # Initialize forms
    user_form = UserUpdateForm(instance=request.user)
    profile_form = ProfileUpdateForm(instance=request.user.profile)
    picture_form = ProfilePictureForm(instance=request.user.profile)

    if request.method == 'POST':
        print("=== FORM SUBMISSION START ===")
        print("POST data:", dict(request.POST))
        print("All POST keys:", list(request.POST.keys()))
        print("FILES data:", dict(request.FILES))
        
        # Determine which form was submitted based on field presence
        
        # Check if this is the User form (has user-related fields)
        if any(field in request.POST for field in ['first_name', 'last_name', 'username', 'email']):
            print("🔄 Detected User Form Submission")
            user_form = UserUpdateForm(request.POST, instance=request.user)
            if user_form.is_valid():
                user = user_form.save()
                print(f"✅ Saved user: {user.first_name} {user.last_name}")
                messages.success(request, 'Your basic information has been updated successfully!')
                return redirect('profile_update')
            else:
                print("❌ User form errors:", user_form.errors)
                messages.error(request, 'Please correct the errors in basic information.')
        
        # Check if this is the Profile form (has profile-related fields)
        elif any(field in request.POST for field in ['phone_number', 'address', 'city', 'country', 'date_of_birth']):
            print("🔄 Detected Profile Form Submission")
            profile_form = ProfileUpdateForm(request.POST, instance=request.user.profile)
            if profile_form.is_valid():
                profile = profile_form.save()
                print(f"✅ Saved profile - Phone: {profile.phone_number}, Address: {profile.address}")
                messages.success(request, 'Your profile information has been updated successfully!')
                return redirect('profile_update')
            else:
                print("❌ Profile form errors:", profile_form.errors)
                messages.error(request, 'Please correct the errors in profile information.')
        
        # Check if this is the Picture form (has files OR the update_picture button)
        elif 'profile_picture' in request.FILES or 'update_picture' in request.POST:
            print("🔄 Detected Picture Form Submission")
            
            if 'profile_picture' in request.FILES:
                uploaded_file = request.FILES['profile_picture']
                print(f"📁 File received: {uploaded_file.name}, Size: {uploaded_file.size}")
                
                # Validate file size
                if uploaded_file.size > 5 * 1024 * 1024:
                    messages.error(request, 'Image file too large ( > 5MB )')
                    return redirect('profile_update')
                
                # Validate file type
                valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
                file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                if not any(file_extension.endswith(ext) for ext in valid_extensions):
                    messages.error(request, 'Please upload a valid image file (JPG, PNG, GIF, BMP)')
                    return redirect('profile_update')
                
                # Handle file upload
                try:
                    from django.core.files.storage import FileSystemStorage
                    import uuid
                    import os
                    
                    fs = FileSystemStorage()
                    file_extension = os.path.splitext(uploaded_file.name)[1]
                    unique_filename = f"profile_pics/{uuid.uuid4()}{file_extension}"
                    filename = fs.save(unique_filename, uploaded_file)
                    
                    # Update the profile with the file path
                    request.user.profile.profile_picture = filename
                    request.user.profile.save()
                    
                    print(f"✅ Saved profile picture: {filename}")
                    messages.success(request, 'Your profile picture has been updated successfully!')
                    
                except Exception as e:
                    print("❌ Error saving profile picture:", e)
                    messages.error(request, 'Error updating profile picture. Please try again.')
            else:
                print("❌ No file selected for upload")
                messages.error(request, 'Please select a file to upload.')
            
            return redirect('profile_update')
        else:
            print("❓ Could not determine which form was submitted")
            messages.error(request, 'Form submission error. Please try again.')
        
        print("=== FORM SUBMISSION END ===")

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'picture_form': picture_form,
        'title': 'Update Profile - FixIT'
    }
    return render(request, 'accounts/profile_update.html', context)

@login_required
def technician_dashboard_view(request):
    """
    Display technician dashboard
    """
    user = request.user
    # Check if user is a technician (adjust this based on your user model)
    if not hasattr(user, 'profile') or not user.profile.is_technician:
        messages.error(request, 'You do not have permission to access the technician dashboard.')
        return redirect('user_dashboard')
    
    context = {
        'user': user,
        'profile': user.profile,
        'title': 'Technician Dashboard - FixIT'
    }
    return render(request, 'dashboard/technician_dashboard.html', context)


@login_required
def user_dashboard_view(request):
    """
    Display user dashboard
    """
    user = request.user
    # Check if user is a regular user (not technician)
    if hasattr(user, 'profile') and user.profile.is_technician:
        messages.error(request, 'You do not have permission to access the user dashboard.')
        return redirect('technician_dashboard')
    
    context = {
        'user': user,
        'profile': user.profile,
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


# Helper function to redirect users to correct dashboard
def redirect_to_correct_dashboard(user):
    """
    Redirect user to appropriate dashboard based on their role
    """
    if hasattr(user, 'profile') and user.profile.is_technician:
        return redirect('technician_dashboard')
    else:
        return redirect('user_dashboard')
    
    
@login_required
def user_profile_view(request):
    """
    Display user profile page
    """
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


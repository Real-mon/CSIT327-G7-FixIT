from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserSignUpForm, UserLoginForm, UserUpdateForm, ProfileUpdateForm


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


@login_required
def profile_update_view(request):
    """
    Handle profile update
    """
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form,
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


def password_reset_view(request):
    """
    Handle password reset - placeholder for future implementation
    """
    context = {
        'title': 'Password Reset - FixIT',
        'hide_navigation': True
    }
    return render(request, 'accounts/password_reset.html', context)

def change_password_view(request):
    """
    Handle password change - placeholder for future implementation
    """
    context = {
        'title': 'Change Password - FixIT',
        'hide_navigation': True
    }
    return render(request, 'accounts/change_password.html', context)


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
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserProfile
from django import forms
from .models import CreateTicket

class UserSignUpForm(UserCreationForm):
    """
    Extended sign-up form with additional fields
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )
    first_name = forms.CharField(
        required=True,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        required=True,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    
    # Add user_type field to handle technician registration
    user_type = forms.ChoiceField(
        choices=[('user', 'User'), ('technician', 'Technician')],
        widget=forms.HiddenInput(),
        required=False
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super(UserSignUpForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })
    
    def clean_email(self):
        """Check if email already exists"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email
    
    def save(self, commit=True):
        """Save user with email and set technician status"""
        user = super(UserSignUpForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Set technician status based on user_type
            user_type = self.cleaned_data.get('user_type', 'user')
            user.profile.is_technician = (user_type == 'technician')
            user.profile.save()
        
        return user

# ... rest of your forms remain the same
class UserLoginForm(AuthenticationForm):
    """
    Custom login form with styled widgets
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border-2 border-[#8fbaf3]/30 bg-white/25 focus:outline-none focus:border-[#0245a3] focus:bg-white/35 transition-all duration-300',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border-2 border-[#8fbaf3]/30 bg-white/25 focus:outline-none focus:border-[#0245a3] focus:bg-white/35 transition-all duration-300',
                'placeholder': 'Enter your last name'
            }),
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border-2 border-[#8fbaf3]/30 bg-white/25 focus:outline-none focus:border-[#0245a3] focus:bg-white/35 transition-all duration-300',
                'placeholder': 'Enter your username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border-2 border-[#8fbaf3]/30 bg-white/25 focus:outline-none focus:border-[#0245a3] focus:bg-white/35 transition-all duration-300',
                'placeholder': 'Enter your email address'
            }),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'date_of_birth', 'address', 'city', 'country']
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border-2 border-[#8fbaf3]/30 bg-white/25 focus:outline-none focus:border-[#0245a3] focus:bg-white/35 transition-all duration-300',
                'placeholder': 'Enter your phone number'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border-2 border-[#8fbaf3]/30 bg-white/25 focus:outline-none focus:border-[#0245a3] focus:bg-white/35 transition-all duration-300',
                'type': 'date'
            }),
            'address': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border-2 border-[#8fbaf3]/30 bg-white/25 focus:outline-none focus:border-[#0245a3] focus:bg-white/35 transition-all duration-300',
                'placeholder': 'Enter your address',
                'rows': 3
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border-2 border-[#8fbaf3]/30 bg-white/25 focus:outline-none focus:border-[#0245a3] focus:bg-white/35 transition-all duration-300',
                'placeholder': 'Enter your city'
            }),
            'country': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border-2 border-[#8fbaf3]/30 bg-white/25 focus:outline-none focus:border-[#0245a3] focus:bg-white/35 transition-all duration-300',
                'placeholder': 'Enter your country'
            }),
        }

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture']
    
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'hidden',
            'accept': 'image/*'
        })
    )
    
    def clean_profile_picture(self):
        # Since it's a CharField now, we handle the file validation differently
        picture = self.cleaned_data.get('profile_picture')
        # You might want to remove this validation or handle it differently
        return picture


from django import forms
from .models import CreateTicket


class TicketCreationForm(forms.ModelForm):
    # This form will use the fields defined in the Ticket model
    class Meta:
        model = CreateTicket
        fields = ['title', 'category', 'priority', 'description']

        # Optionally, add CSS classes directly here instead of in the HTML template
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-5 py-3 rounded-xl text-[#0245a3] border-none focus:ring-4 focus:ring-[#8fbaf3] focus:outline-none'}),
            'category': forms.Select(attrs={
                'class': 'w-full px-5 py-3 rounded-xl text-[#0245a3] border-none focus:ring-4 focus:ring-[#8fbaf3] focus:outline-none appearance-none'}),
            'priority': forms.Select(attrs={
                'class': 'w-full px-5 py-3 rounded-xl text-[#0245a3] border-none focus:ring-4 focus:ring-[#8fbaf3] focus:outline-none appearance-none'}),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-5 py-3 rounded-xl text-[#0245a3] border-none focus:ring-4 focus:ring-[#8fbaf3] focus:outline-none',
                'rows': 4}),
        }
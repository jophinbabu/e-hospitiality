from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import CustomUser, Department
from .forms import CustomUserCreationForm

def home(request):
    """Home page - shows welcome for anonymous, dashboard for authenticated users"""
    if not request.user.is_authenticated:
        # Show welcome page for non-authenticated users
        return render(request, 'core/welcome.html')
    
    # Show personalized home for authenticated users
    context = {
        'user_type': request.user.user_type,
    }
    return render(request, 'core/home.html', context)

def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to E-Hospitality, {user.first_name}!')
            
            # Redirect based on user type
            if user.user_type == 'patient':
                return redirect('patients:dashboard')
            elif user.user_type == 'doctor':
                return redirect('doctors:dashboard')
            elif user.user_type == 'admin':
                return redirect('admins:dashboard')
            
            return redirect('core:home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile(request):
    """User profile view"""
    return render(request, 'core/profile.html', {'user': request.user})

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from .forms import CustomUserCreationForm  # Custom registration form

def home(request):
    """
    Landing page with registration/login options.
    Always shows the landing page.
    """
    return render(request, 'core/home.html')


def register(request):
    """
    User registration view using CustomUserCreationForm.
    Auto-login after successful registration and redirect to dashboard.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Auto-login after registration
            messages.success(request, f'Welcome {user.username}! Your account has been created.')
            return redirect('core:dashboard')  # Redirect to dashboard
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'core/register.html', {'form': form})


@login_required
def dashboard_redirect(request):
    """
    Redirect logged-in users to their respective dashboards based on role:
    - patient -> patients:dashboard
    - doctor  -> doctors:dashboard
    - admin/staff -> admin:index
    Includes fallback checks for user profile presence.
    """
    user = request.user

    # Debug prints
    print("=== DASHBOARD REDIRECT DEBUG ===")
    print(f"User: {user.username}")
    print(f"User Type: '{getattr(user, 'user_type', None)}'")

    try:
        # Primary check: user_type field
        user_type = getattr(user, 'user_type', '').strip()
        if user_type:
            if user_type == 'patient':
                print("REDIRECTING TO: patients:dashboard")
                return redirect('patients:dashboard')
            elif user_type == 'doctor':
                print("REDIRECTING TO: doctors:dashboard")
                return redirect('doctors:dashboard')
            elif user_type == 'admin':
                print("REDIRECTING TO: admins:dashboard")
                return redirect('admins:dashboard')

        # Fallback check: related profile
        if hasattr(user, 'patient'):
            print("Found patient profile -> redirecting to patients:dashboard")
            return redirect('patients:dashboard')

        if hasattr(user, 'doctor'):
            print("Found doctor profile -> redirecting to doctors:dashboard")
            return redirect('doctors:dashboard')

        # Staff or superuser fallback
        if user.is_staff or user.is_superuser:
            print("User is staff/superuser -> redirecting to admin:index")
            return redirect('admin:index')

    except Exception as e:
        print(f"ERROR in dashboard redirect: {str(e)}")
        messages.error(request, f'Dashboard access error: {str(e)}')

    # Default fallback if no role found
    print("NO ROLE FOUND -> redirecting to home with warning")
    messages.warning(request, f'User role not determined for {user.username}. Please contact administrator.')
    return redirect('core:home')

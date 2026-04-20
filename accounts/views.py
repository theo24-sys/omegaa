import logging
from django.conf import settings
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.db.models import Avg
from reviews.models import Review
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser

logger = logging.getLogger(__name__)


def kenya_locations_json(request):
    path = settings.BASE_DIR / 'static' / 'js' / 'kenya_locations.json'
    if not path.exists():
        raise Http404('Locations data not found')
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return HttpResponse(content, content_type='application/json')


def send_verification_email(request, user):  # FIX 1: missing colon
    current_site = get_current_site(request)
    mail_subject = 'Verify your CHARLADY account'
    message = render_to_string('accounts/email/verification_email.html', {
        'user': user,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
    })
    email = EmailMessage(mail_subject, message, to=[user.email])
    email.content_subtype = 'html'
    email.send()


def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            # Allow login even if email sending fails; keep email verification as an extra layer only
            user.is_active = True
            user.set_password(form.cleaned_data['password1'])
            user.save()
            try:
                send_verification_email(request, user)
                messages.success(request, 'Account created! Check your email to verify.')
            except Exception as e:
                logger.error(f"Email sending failed for {user.email}: {e}")
                messages.success(request, 'Account created! You can now log in.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})


def login(request):
    if request.user.is_authenticated:
        if request.user.user_type == 'househelp':
            return redirect('dashboard:housekeeper_dashboard')
        else:
            return redirect('dashboard:employer_dashboard')

    logger.info(f"Request method: {request.method}")
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                auth_login(request, user)
                if user.user_type == 'househelp':
                    return redirect('dashboard:housekeeper_dashboard')
                else:
                    return redirect('dashboard:employer_dashboard')
            else:
                messages.error(request, 'Your account is not active.')
        else:
            messages.error(request, 'verify your email.')
    return render(request, 'accounts/login.html')


@login_required
def logout(request):
    auth_logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')


@login_required
def profile(request):
    if request.user.user_type == 'househelp':
        return redirect('dashboard:housekeeper_dashboard')
    elif request.user.user_type == 'employer':
        return redirect('dashboard:employer_dashboard')
    
    user_profile = request.user

    # Aggregate this user's reviews (as the reviewed user)
    reviews = Review.objects.filter(reviewed_user=user_profile)
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    review_count = reviews.count()

    context = {
        'user_profile': user_profile,
        'avg_rating': round(avg_rating, 1),
        'review_count': review_count,
    }

    return render(request, 'accounts/profile.html', context)


def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None
    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Email verified! Log in now.')
        return redirect('login')
    else:
        messages.error(request, 'Verification link invalid or expired.')
        return redirect('signup')


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)  # FIX 3: added instance
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('dashboard:user_dashboard')  # FIX 4: was 'profile.html', must be URL name
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})  # FIX 5: moved out of if block


def profile_detail(request, user_id):
    user_profile = get_object_or_404(CustomUser, id=user_id)
    reviews = Review.objects.filter(reviewed_user=user_profile)
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    review_count = reviews.count()
    skills_list = [s.strip() for s in (user_profile.skills or '').split(',') if s.strip()]
    context = {
        'user_profile': user_profile,
        'avg_rating': round(avg_rating, 1),
        'review_count': review_count,
        'skills_list': skills_list,
    }
    return render(request, 'accounts/profile_detail.html', context)
    # FIX 6: removed dead/unreachable render line that was here
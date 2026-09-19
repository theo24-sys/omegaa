import logging
import re
import time
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
from django.db.models import Avg, Q
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


def _normalize_phone(raw):
    """Return canonical +2547XXXXXXXX form for common Kenyan phone formats."""
    digits = re.sub(r'\D', '', raw or '')
    if digits.startswith('254') and len(digits) == 12:
        return '+' + digits
    if digits.startswith('0') and len(digits) == 10:
        return '+254' + digits[1:]
    if len(digits) == 9 and digits[0] in '17':
        return '+254' + digits
    return None


def _find_user_by_identifier(identifier):
    """Find a user by email or phone number in any common Kenyan format."""
    identifier = (identifier or '').strip()
    if not identifier:
        return None
    if '@' in identifier:
        return CustomUser.objects.filter(email__iexact=identifier).first()
    candidates = {identifier}
    normalized = _normalize_phone(identifier)
    if normalized:
        candidates.add(normalized)          # +254712345678
        candidates.add('0' + normalized[4:])  # 0712345678
        candidates.add(normalized[1:])        # 254712345678
        candidates.add(normalized[4:])        # 712345678
    return CustomUser.objects.filter(
        Q(username__in=candidates) | Q(phone_number__in=candidates)
    ).first()


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

    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = authenticate(request, username=identifier, password=password)
        if user is None:
            # authenticate() only matches the username (the phone number the
            # user signed up with). Also allow email login and phone numbers
            # typed in any common Kenyan format by mapping to stored username.
            matched = _find_user_by_identifier(identifier)
            if matched and matched.username:
                user = authenticate(request, username=matched.username, password=password)

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
            messages.error(request, 'Invalid phone number/email or password. '
                                    'Tip: use the phone number you signed up with.')
    return render(request, 'accounts/login.html')


def resend_verification(request):
    """Re-send the verification email when it never arrived."""
    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip()
        now = time.time()
        if now - request.session.get('last_verification_email', 0) < 60:
            messages.error(request, 'Please wait a minute before requesting another email.')
            return redirect('login')

        user = _find_user_by_identifier(identifier)
        if user is None:
            messages.info(request, "If an account exists for those details, we've sent a verification email.")
            return redirect('login')

        try:
            send_verification_email(request, user)
        except Exception as e:
            logger.error(f"Verification email resend failed for {user.email}: {e}")
            messages.error(request, "We couldn't send the email right now. "
                                    "Please try again shortly or contact support.")
        else:
            request.session['last_verification_email'] = now
            messages.success(request, f'Verification email sent! Check {user.email} (and your spam folder).')
        return redirect('login')
    return render(request, 'accounts/resend_verification.html')


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
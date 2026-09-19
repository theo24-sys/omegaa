from django.db import models
...
class PlatformDocument(models.Model):
    DOCUMENT_TYPES = (
        ('worker_agreement', 'Worker Agreement Template'),
        ('employer_agreement', 'Employer Agreement Template'),
        ('code_of_conduct', 'Code of Conduct'),
        ('other', 'Other'),
    )
    
    name = models.CharField(max_length=100)
    doc_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES, unique=True, help_text="Only one active document of each type is allowed.")
    document_file = models.FileField(upload_to='platform_docs/')
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Platform Document"
        verbose_name_plural = "Platform Documents"

    def __str__(self):
        return f"{self.get_doc_type_display()} - {self.name}"
from django.contrib.auth.models import AbstractUser, UserManager


class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("user_type") is None:
            extra_fields["user_type"] = "employer"
        return self._create_user(username, email, password, **extra_fields)


class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('househelp', 'Househelp'),
        ('employer', 'Employer'),
    )
    objects = CustomUserManager()
    user_type = models.CharField(max_length=15, choices=USER_TYPE_CHOICES)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, unique=True)
    skills = models.CharField(max_length=500, blank=True, null=True, help_text='Comma-separated skills (househelp)')
    experience = models.TextField(blank=True, null=True, help_text='Experience description (househelp)')
    county = models.CharField(max_length=50, blank=True, null=True)
    constituency = models.CharField(max_length=50, blank=True, null=True)
    major_town = models.CharField(max_length=50, blank=True, null=True)
    ward = models.CharField(max_length=50, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_paid_verified = models.BooleanField(default=False, help_text='User paid 250 KES for annual verification', verbose_name='Paid Verified Member')
    paid_verification_date = models.DateTimeField(blank=True, null=True, verbose_name='Verification Payment Date')
    paid_verification_expires_at = models.DateTimeField(blank=True, null=True, verbose_name='Verification Expiry Date')
    mpesa_code = models.CharField(max_length=20, blank=True, null=True, help_text='M-Pesa confirmation code for verification')
    is_premium = models.BooleanField(default=False)
    premium_until = models.DateTimeField(blank=True, null=True)
    
    # Didit Verification
    didit_session_id = models.CharField(max_length=255, blank=True, null=True)
    didit_verification_status = models.CharField(
        max_length=50, 
        choices=[
            ('none', 'None'), 
            ('pending', 'Pending'), 
            ('completed', 'Completed'), 
            ('failed', 'Failed'),
            ('approved', 'Approved'),
            ('declined', 'Declined'),
            ('expired', 'Expired'),
            ('in_review', 'In Review')
        ],
        default='none'
    )
    has_completed_first_verification = models.BooleanField(default=False, help_text='Track if worker completed first-time Didit verification')

    # Document uploads (housekeepers only) - required for job applications
    # Document uploads (Deprecated in favor of Didit)
    id_document = models.FileField(upload_to='worker_docs/%Y/%m/%d/', blank=True, null=True, help_text='ID document (ID/Passport)')
    agreement_form = models.FileField(upload_to='worker_docs/%Y/%m/%d/', blank=True, null=True, help_text='Signed agreement form')
    police_clearance = models.FileField(upload_to='worker_docs/%Y/%m/%d/', blank=True, null=True, help_text='Police Clearance Certificate / Good Conduct')
    documents_verified = models.BooleanField(default=False, help_text='Admin has verified all documents')
    documents_verified_at = models.DateTimeField(blank=True, null=True, help_text='When admin verified docs (files purged 24h after this)')

    # Worker Badges / Certifications
    badge_verified_id = models.BooleanField(default=False, verbose_name="Verified ID")
    badge_cleaning = models.BooleanField(default=False, verbose_name="Cleaning Certified")
    badge_childcare = models.BooleanField(default=False, verbose_name="Childcare Certified")
    badge_elder_care = models.BooleanField(default=False, verbose_name="Elder Care Certified")
    badge_kitchen = models.BooleanField(default=False, verbose_name="Kitchen Certified")
    badge_professional_standards = models.BooleanField(default=False, verbose_name="Professional Standards Certified")
    badge_appliance = models.BooleanField(default=False, verbose_name="Appliance Certified")

    last_reminder_sent = models.DateTimeField(blank=True, null=True)
    notification_preferences = models.JSONField(default=dict, blank=True)

    REQUIRED_FIELDS = ["email", "phone_number"]

    def can_apply_for_jobs(self):
        """Housekeepers must be verified and have a profile picture to apply for jobs."""
        if self.user_type != 'househelp':
            return True
        return self.is_verified and bool(self.profile_picture)

    def days_until_membership_renewal(self):
        """Return whole days left until the paid verification expires."""
        if not self.paid_verification_expires_at:
            return 0

        from django.utils import timezone

        remaining = self.paid_verification_expires_at - timezone.now()
        return max(0, remaining.days)

    def get_notification_preferences(self):
        """Return notification preferences with safe defaults merged in."""
        defaults = {
            'browser_notifications_enabled': True,
            'job_alerts': True,
            'application_updates': True,
            'payment_updates': True,
            'reminder_notifications': True,
            'marketing_updates': False,
        }
        preferences = defaults.copy()
        preferences.update(self.notification_preferences or {})
        return preferences

    @property
    def location(self):
        """Returns a formatted location string."""
        parts = []
        if self.county: parts.append(self.county)
        if self.constituency: parts.append(self.constituency)
        if self.major_town: parts.append(self.major_town)
        if self.ward: parts.append(f"Ward: {self.ward}")
        return ", ".join(parts) if parts else "Not provided"

    def get_badges_list(self):
        """Returns a list of badges with their earned status and metadata."""
        badges = [
            ('verified', {'label': 'Verified ID', 'icon': 'verified', 'earned': self.badge_verified_id, 'color': 'purple'}),
            ('professional_standards', {'label': 'Pro Standards', 'icon': 'professional_standards', 'earned': self.badge_professional_standards, 'color': 'pink'}),
            ('cleaning', {'label': 'Premium Cleaning', 'icon': 'cleaning', 'earned': self.badge_cleaning, 'color': 'blue'}),
            ('childcare', {'label': 'Childcare Expert', 'icon': 'childcare', 'earned': self.badge_childcare, 'color': 'amber'}),
            ('eldercare', {'label': 'Elderly Care', 'icon': 'eldercare', 'earned': self.badge_elder_care, 'color': 'rose'}),
            ('kitchen', {'label': 'Chef & Kitchen', 'icon': 'kitchen', 'earned': self.badge_kitchen, 'color': 'emerald'}),
            ('appliance', {'label': 'Appliance Pro', 'icon': 'appliance', 'earned': self.badge_appliance, 'color': 'slate'}),
        ]
        return badges

    def get_avatar_url(self):
        """Robustly returns avatar URL, falling back to placeholder if missing or deleted."""
        from django.templatetags.static import static
        import os
        
        placeholder = static('img/placeholder-avatar.svg')
        if not self.profile_picture:
            return placeholder
            
        try:
            if self.profile_picture.storage.exists(self.profile_picture.name):
                return self.profile_picture.url
        except Exception:
            pass
            
        return placeholder

    def get_avatar_html(self):
        """Returns HTML for avatar with badges overlaid (Instagram/Meta style)."""
        avatar_url = self.get_avatar_url()
        badge_icons = ""
        
        # The Paramount Purple 12-point SEAL (paid membership, KSh 250/yr).
        # Deliberately a starburst rosette — NOT a plain circle-check, so it can
        # never be mistaken for an Instagram/ID-verification tick.
        if self.is_paid_verified:
            badge_icons += """
            <div class="absolute -top-[4%] -right-[4%] w-[34%] h-[34%] drop-shadow-md z-20" title="Pro Verified Member">
                <svg class="w-full h-full" viewBox="0 0 24 24">
                    <defs>
                        <linearGradient id="pv-gold-seal" x1="0" y1="0" x2="1" y2="1">
                            <stop offset="0%" stop-color="#c026d3"/>
                            <stop offset="100%" stop-color="#7e22ce"/>
                        </linearGradient>
                    </defs>
                    <path fill="url(#pv-gold-seal)" stroke="white" stroke-width="1" d="M12 2L13.73 4.27L16.4 3.93L17.27 6.47L19.86 7.14L19.46 9.8L21.46 11.67L20.13 14.27L21.13 16.87L18.66 17.8L17.53 20.27L14.86 19.93L13.13 22.2L10.5 21.53L8.87 23.8L6.2 23.46L5.33 21L2.74 20.33L3.14 17.67L1.14 15.8L2.47 13.2L1.47 10.6L3.94 9.67L5.07 7.2L7.74 7.54L9.47 5.27L12 2Z" />
                    <path d="M10 15.5L7 12.5L8.4 11.1L10 12.7L15.6 7.1L17 8.5L10 15.5Z" fill="white" />
                </svg>
            </div>
            """
        
        html = f"""
        <div class="relative avatar-with-badges shadow-xl rounded-full border-4 border-white w-full h-full">
            <div class="w-full h-full rounded-full overflow-hidden bg-white">
                <img src="{avatar_url}" alt="{self.username}" class="w-full h-full object-cover">
            </div>
            <div class="absolute inset-0 rounded-full ring-1 ring-black/5 pointer-events-none"></div>
            {badge_icons}
        </div>
        """
        return html

    @property
    def completion_percentage(self):
        """Calculates profile completion based on key fields."""
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 
            'bio', 'profile_picture', 'county', 'constituency', 'major_town'
        ]
        if self.user_type == 'househelp':
            fields += ['skills', 'experience', 'id_document']
            
        total = len(fields)
        filled = 0
        for f in fields:
            val = getattr(self, f)
            if val and str(val).strip():
                filled += 1
        
        return int((filled / total) * 100)

    def get_verified_badge(self):
        """Returns distinct badges for Identity Verification vs Paid Verification."""
        badges = []
        
        # Paid Membership (KSh 250/yr) — 12-point purple SEAL, distinct from
        # the pale Didit circle-check below. Shape = premium rosette.
        if self.is_paid_verified:
            badges.append("""
            <span class="inline-flex items-center justify-center ml-1 shrink-0 align-middle" title="Pro Verified Member (paid membership)">
                <svg class="w-4 h-4 md:w-5 md:h-5" viewBox="0 0 24 24">
                    <defs>
                        <linearGradient id="pv-seal-inline" x1="0" y1="0" x2="1" y2="1">
                            <stop offset="0%" stop-color="#c026d3"/>
                            <stop offset="100%" stop-color="#7e22ce"/>
                        </linearGradient>
                    </defs>
                    <path fill="url(#pv-seal-inline)" d="M12 2L13.73 4.27L16.4 3.93L17.27 6.47L19.86 7.14L19.46 9.8L21.46 11.67L20.13 14.27L21.13 16.87L18.66 17.8L17.53 20.27L14.86 19.93L13.13 22.2L10.5 21.53L8.87 23.8L6.2 23.46L5.33 21L2.74 20.33L3.14 17.67L1.14 15.8L2.47 13.2L1.47 10.6L3.94 9.67L5.07 7.2L7.74 7.54L9.47 5.27L12 2Z" />
                    <path d="M10 15.5L7 12.5L8.4 11.1L10 12.7L15.6 7.1L17 8.5L10 15.5Z" fill="white" />
                </svg>
            </span>
            """)
            
        # Identity Verification (Didit) — pale outlined circle-check with ID-card
        # connotation; visually distinct from the paid purple seal above.
        if self.is_verified:
            badges.append("""
            <span class="inline-flex items-center justify-center ml-1 shrink-0 align-middle" title="Identity Verified via Didit">
                <svg class="w-4 h-4 md:w-4.5 md:h-4.5 text-[#8a3ab9]" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="9" fill="#F3E5F5" stroke="currentColor" stroke-width="1.25"/>
                    <path d="M9.5 12.2l1.7 1.7 3.9-4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </span>
            """)
            
        return "".join(badges)

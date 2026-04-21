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
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


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

    REQUIRED_FIELDS = ["email", "phone_number"]

    def can_apply_for_jobs(self):
        """Housekeepers must be verified and have a profile picture to apply for jobs."""
        if self.user_type != 'househelp':
            return True
        return self.is_verified and bool(self.profile_picture)

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
        
        # The Paramount Purple Instagram-Style Check
        if self.is_paid_verified:
            badge_icons += """
            <div class="absolute -bottom-[5%] -right-[5%] bg-white rounded-full p-[5%] shadow-sm z-10">
                <div class="bg-[#8a3ab9] rounded-full p-[5%] w-full h-full flex items-center justify-center border-2 border-white">
                    <svg class="w-full h-full text-white" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2L13.73 4.27L16.4 3.93L17.27 6.47L19.86 7.14L19.46 9.8L21.46 11.67L20.13 14.27L21.13 16.87L18.66 17.8L17.53 20.27L14.86 19.93L13.13 22.2L10.5 21.53L8.87 23.8L6.2 23.46L5.33 21L2.74 20.33L3.14 17.67L1.14 15.8L2.47 13.2L1.47 10.6L3.94 9.67L5.07 7.2L7.74 7.54L9.47 5.27L12 2Z" />
                        <path d="M10 15.5L7 12.5L8.4 11.1L10 12.7L15.6 7.1L17 8.5L10 15.5Z" fill="white" />
                    </svg>
                </div>
            </div>
            """
        
        html = f"""
        <div class="relative avatar-with-badges shadow-xl rounded-full border-4 border-white">
            <img src="{avatar_url}" alt="{self.username}" class="w-full h-full object-cover rounded-full">
            <div class="absolute inset-0 rounded-full ring-1 ring-black/5"></div>
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
        
        # Paid Verification (The Paramount Purple Instagram-Style Rosette)
        if self.is_paid_verified:
            badges.append("""
            <span class="inline-flex items-center justify-center ml-1" title="Paid Verified Member">
                <svg class="w-4 h-4 md:w-5 md:h-5 text-[#8a3ab9]" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2L13.73 4.27L16.4 3.93L17.27 6.47L19.86 7.14L19.46 9.8L21.46 11.67L20.13 14.27L21.13 16.87L18.66 17.8L17.53 20.27L14.86 19.93L13.13 22.2L10.5 21.53L8.87 23.8L6.2 23.46L5.33 21L2.74 20.33L3.14 17.67L1.14 15.8L2.47 13.2L1.47 10.6L3.94 9.67L5.07 7.2L7.74 7.54L9.47 5.27L12 2Z" />
                    <path d="M10 15.5L7 12.5L8.4 11.1L10 12.7L15.6 7.1L17 8.5L10 15.5Z" fill="white" />
                </svg>
            </span>
            """)
            
        # Identity Verification (ID Card Style with Purple Seal - Inspired by Image)
        if self.is_verified:
            badges.append("""
            <span class="inline-flex items-center justify-center ml-1" title="Identity Verified">
                <svg class="w-5 h-5 md:w-6 md:h-6 text-[#9c27b0]" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="2" y="5" width="20" height="14" rx="2" fill="#F3E5F5" stroke="currentColor" stroke-width="0.5"/>
                    <circle cx="7" cy="10" r="2.5" fill="currentColor"/>
                    <rect x="12" y="9" width="6" height="1" rx="0.5" fill="currentColor"/>
                    <rect x="12" y="11" width="6" height="1" rx="0.5" fill="currentColor"/>
                    <rect x="12" y="13" width="4" height="1" rx="0.5" fill="currentColor"/>
                    <circle cx="18" cy="15" r="4" fill="white" stroke="currentColor" stroke-width="0.5"/>
                    <path d="M16.5 15L17.5 16L19.5 14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </span>
            """)
            
        return "".join(badges)

User = get_user_model()


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('job_application', 'Job Application'),
        ('application_status', 'Application Status'),
        ('message', 'New Message'),
        ('review', 'New Review'),
        ('system', 'System Notification'),
    )
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='account_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional relation to object (job, review, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"{self.title} ({self.notification_type}) - {self.recipient.username}"
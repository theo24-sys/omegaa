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
        choices=[('none', 'None'), ('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')],
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
        
        placeholder = static('img/placeholder.svg')
        if not self.profile_picture:
            return placeholder
            
        try:
            if self.profile_picture.storage.exists(self.profile_picture.name):
                return self.profile_picture.url
        except Exception:
            pass
            
        return placeholder

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
        """Returns Instagram-style blue checkmark HTML if verified."""
        if not self.is_verified and not self.is_paid_verified:
            return ""
            
        # Meta Blue: #0095f6
        return f"""
        <span class="inline-flex items-center justify-center bg-[#0095f6] rounded-full p-[2px] w-4 h-4 md:w-5 md:h-5 ml-1 select-none shadow-sm" title="Verified">
            <svg class="w-full h-full text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="4" d="M5 13l4 4L19 7"></path>
            </svg>
        </span>
        """

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
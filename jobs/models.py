from django.conf import settings
from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator

class Job(models.Model):
    CITY_CHOICES = (
        # National capitals / largest cities
        ('nairobi', 'Nairobi'),
        ('mombasa', 'Mombasa'),
        ('kisumu', 'Kisumu'),
        ('nakuru', 'Nakuru'),
        ('eldoret', 'Eldoret'),
        ('thika', 'Thika'),
        ('machakos', 'Machakos'),
        ('nyeri', 'Nyeri'),
        ('meru', 'Meru'),
        ('kakamega', 'Kakamega'),
        ('kisii', 'Kisii'),
        ('garissa', 'Garissa'),
        ('embu', 'Embu'),
        ('nyahururu', 'Nyahururu'),
        ('kitale', 'Kitale'),
        ('naivasha', 'Naivasha'),
        ('malindi', 'Malindi'),
        ('luanda', 'Luanda'),
        ('bungoma', 'Bungoma'),
        ('lodwar', 'Lodwar'),
        ('lamu', 'Lamu'),
        ('narok', 'Narok'),
        ('voi', 'Voi'),
        ('nanyuki', 'Nanyuki'),
        ('karatina', 'Karatina'),
        ('ruiru', 'Ruiru'),
        ('ongata_rongai', 'Ongata Rongai'),
        ('syokimau', 'Syokimau'),
        ('kikuyu', 'Kikuyu'),
        ('ruaka', 'Ruaka'),
    )

    JOB_TYPE_CHOICES = (
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('live_in', 'Live In'),
        ('live_out', 'Live Out'),
        ('temporary', 'Temporary'),
    )

    EXPERIENCE_LEVEL_CHOICES = (
        ('entry', 'Entry Level'),
        ('intermediate', 'Intermediate'),
        ('experienced', 'Experienced'),
    )

    employer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='jobs',
        limit_choices_to={'user_type': 'employer'}  # only employers
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    responsibilities = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    salary = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Monthly salary in KES"
    )
    city = models.CharField(max_length=50, choices=CITY_CHOICES, blank=True)
    location = models.CharField(max_length=100, blank=True, help_text="Specific area/estate")
    job_type = models.CharField(max_length=50, choices=JOB_TYPE_CHOICES)
    experience_level = models.CharField(max_length=50, choices=EXPERIENCE_LEVEL_CHOICES, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    featured_until = models.DateTimeField(null=True, blank=True)
    
    # Payment
    posting_fee_paid = models.BooleanField(default=False)
    mpesa_code = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('job_detail', args=[self.pk])

    def get_location_display(self):
        return f"{self.location}, {self.city}" if self.location and self.city else self.city or "Not specified"


class Application(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('reviewing', 'Reviewing'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    )

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications',
        limit_choices_to={'user_type': 'househelp'}
    )
    cover_letter = models.TextField(blank=True)
    resume = models.FileField(upload_to='resumes/%Y/%m/%d/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional applicant info
    experience = models.PositiveIntegerField(default=0, help_text="Years of experience")
    availability = models.CharField(
        max_length=50,
        choices=[('FT', 'Full-Time'), ('PT', 'Part-Time'), ('LI', 'Live-In')],
        default='FT'
    )
    preferred_hours = models.CharField(max_length=100, blank=True, help_text="e.g. 8 AM - 5 PM")
    additional_notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('job', 'applicant')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.applicant.username}'s application for {self.job.title}"

    def get_status_class(self):
        return {
            'pending': 'bg-yellow-100 text-yellow-800',
            'reviewing': 'bg-blue-100 text-blue-800',
            'accepted': 'bg-green-100 text-green-800',
            'rejected': 'bg-red-100 text-red-800',
            'withdrawn': 'bg-gray-100 text-gray-800',
        }.get(self.status, 'bg-gray-100 text-gray-800')
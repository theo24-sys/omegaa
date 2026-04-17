from django.db import models
from django.conf import settings
from django.utils import timezone

class PaymentPlan(models.Model):
    PLAN_TYPE_CHOICES = (
        ('job_boost', 'Job Boost'),
        ('profile_highlight', 'Profile Highlight'),
        ('featured_listing', 'Featured Listing'),
        ('verification', 'Account Verification'),
        ('academy_bundle', 'Academy Triple Bundle'),
        ('course_payment', 'Individual Course Payment'),
    )
    
    TARGET_GROUP_CHOICES = (
        ('employer', 'Employer'),
        ('worker', 'Worker'),
    )

    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=50, choices=PLAN_TYPE_CHOICES)
    description = models.TextField()
    target_group = models.CharField(max_length=20, choices=TARGET_GROUP_CHOICES, default='employer')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['price']

    def __str__(self):
        return f"{self.name} ({self.price} KSh)"
        
class Payment(models.Model):
    is_installment = models.BooleanField(default=False, help_text="Is this a partial payment?")
    balance_due = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Remaining balance for installments")
    
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('verification_submitted', 'Verification Submitted'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )

    PAYMENT_METHOD_CHOICES = (
        ('mpesa', 'M-Pesa'),
        ('card', 'Card'),
        ('bank', 'Bank Transfer'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    plan = models.ForeignKey(PaymentPlan, on_delete=models.PROTECT, related_name='payments', null=True, blank=True)
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    contribution = models.ForeignKey('MonthlyContribution', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    # STK Push fields
    is_mpesa_stk = models.BooleanField(default=False, help_text='Payment via M-Pesa STK push')
    mpesa_transaction_id = models.CharField(max_length=100, blank=True, null=True, help_text='M-Pesa MpesaReceiptNumber from callback')
    stk_reference_id = models.CharField(max_length=100, blank=True, null=True, help_text='M-Pesa CheckoutRequestID')
    stk_initiated_at = models.DateTimeField(blank=True, null=True, help_text='When STK push was triggered')
    payment_verified_at = models.DateTimeField(blank=True, null=True, help_text='When M-Pesa confirmed success')

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='mpesa')
    status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_date = models.DateTimeField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    verification_notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        plan_name = self.plan.name if self.plan else (self.course.title if self.course else f"Payment {self.id}")
        return f"{self.user.username} - {plan_name} - {self.status}"

    def is_verified(self):
        return self.status == 'completed'


class UserSubscription(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions', limit_choices_to={'user_type': 'employer'})
    plan = models.ForeignKey(PaymentPlan, on_delete=models.PROTECT, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(help_text='When subscription expires')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'User Subscriptions'

    def __str__(self):
        return f"{self.user.username} - {self.plan.name} - {self.status}"


class MonthlyContribution(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('ignored', 'Ignored'),
    )
    worker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='monthly_contributions', limit_choices_to={'user_type': 'househelp'})
    year = models.PositiveIntegerField(help_text='e.g. 2026')
    month = models.PositiveIntegerField(help_text='1-12')
    calculated_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text='Sum of completed job salaries for the month')
    amount_due = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text='3% of calculated_salary')
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(blank=True, null=True, help_text='When payment was made')
    mpesa_transaction_id = models.CharField(max_length=100, blank=True, null=True, help_text='M-Pesa receipt number')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('worker', 'year', 'month')
        ordering = ['-year', '-month']
        verbose_name_plural = 'Monthly Contributions'

    def __str__(self):
        return f"{self.worker.username} - {self.month}/{self.year} - {self.payment_status}"
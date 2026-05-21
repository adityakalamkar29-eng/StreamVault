from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Video(models.Model):
    PLAN_FREE = 'free'
    PLAN_STANDARD = 'standard'
    PLAN_PREMIUM = 'premium'
    PLAN_CHOICES = [
        (PLAN_FREE,     'Free'),
        (PLAN_STANDARD, 'Standard'),
        (PLAN_PREMIUM,  'Premium'),
    ]

    title       = models.CharField(max_length=200)
    description = models.TextField()
    category    = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='videos')
    video_file  = models.FileField(upload_to='videos/')
    thumbnail   = models.ImageField(upload_to='thumbnails/')
    created_at  = models.DateTimeField(auto_now_add=True)
    # Which plan is required to watch this video?
    required_plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_FREE)

    def __str__(self):
        return self.title


class Subscription(models.Model):
    PLAN_FREE = 'free'
    PLAN_STANDARD = 'standard'
    PLAN_PREMIUM = 'premium'
    PLAN_CHOICES = [
        (PLAN_FREE,     'Free'),
        (PLAN_STANDARD, 'Standard'),
        (PLAN_PREMIUM,  'Premium'),
    ]

    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan       = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_FREE)
    started_at = models.DateTimeField(auto_now_add=True)
    active     = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} — {self.plan}"

    # Helper: can this subscription access a video with a given required_plan?
    PLAN_RANK = {PLAN_FREE: 0, PLAN_STANDARD: 1, PLAN_PREMIUM: 2}

    def can_watch(self, required_plan):
        return self.PLAN_RANK.get(self.plan, 0) >= self.PLAN_RANK.get(required_plan, 0)

class Plan(models.Model):
    PLAN_CHOICES = [
        ('free',     'Free'),
        ('standard', 'Standard'),
        ('premium',  'Premium'),
    ]
    name         = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True)
    monthly_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    annual_price  = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    max_screens   = models.PositiveIntegerField(default=1)
    max_downloads = models.PositiveIntegerField(default=0)
    video_quality = models.CharField(max_length=20, default='480p')
    ad_free       = models.BooleanField(default=False)
    updated_at    = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.get_name_display()

class PaymentOrder(models.Model):
    STATUS_PENDING   = 'pending'
    STATUS_SUCCESS   = 'success'
    STATUS_FAILED    = 'failed'
    STATUS_CHOICES   = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED,  'Failed'),
    ]
    BILLING_MONTHLY = 'monthly'
    BILLING_ANNUAL  = 'annual'
    BILLING_CHOICES = [
        (BILLING_MONTHLY, 'Monthly'),
        (BILLING_ANNUAL,  'Annual'),
    ]

    user               = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    razorpay_order_id  = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    plan               = models.CharField(max_length=20)
    billing            = models.CharField(max_length=10, choices=BILLING_CHOICES, default=BILLING_MONTHLY)
    amount             = models.DecimalField(max_digits=10, decimal_places=2)
    status             = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at         = models.DateTimeField(auto_now_add=True)
    completed_at       = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} | {self.plan} | ₹{self.amount} | {self.status}"

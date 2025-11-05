from datetime import date, timedelta
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# -------- Category --------
class Category(models.Model):
    name = models.CharField(max_length=150)
  
    def __str__(self):
        return self.name





# -------- Client (Owner) --------
class Client(AbstractUser):
    business_name = models.CharField(max_length=200, null=True, blank=True)
    contact_number = models.PositiveIntegerField(null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    payment_method = models.CharField(
        max_length=255,
        choices=[('Cash', 'Cash'), ('Gpay', 'Gpay'), ('Card', 'Card')],
        null=True,
        blank=True
    )
    category = models.ForeignKey(
        'Category',
        on_delete=models.CASCADE,
        related_name='clients',
        null=True,
        blank=True
    )

    # -------- Subscription details --------
    subscription_start = models.DateField(auto_now_add=True, null=True, blank=True)
    subscription_end = models.DateField(null=True, blank=True)
    subscription_amount = models.DecimalField(  
        max_digits=8,
        decimal_places=2,
        default=5000.00,
        help_text="Subscription amount in INR"
    )
    subscription_currency = models.CharField(  
        max_length=10,
        default='INR',
        help_text="Currency code for the subscription (e.g., INR, USD, AED)"
    )
    is_active = models.BooleanField(default=True)

    # -------- Save Method --------
    def save(self, *args, **kwargs):
        # Set default subscription start and end dates
        if not self.subscription_start:
            self.subscription_start = date.today()
        if not self.subscription_end:
            self.subscription_end = self.subscription_start + timedelta(days=365)
        # Set default amount if not provided
        if not self.subscription_amount:
            self.subscription_amount = 5000.00
        # Ensure active status
        self.is_active = self.subscription_end >= date.today()
        super().save(*args, **kwargs)

    # -------- Remaining Days --------
    @property
    def remaining_days(self):
        if self.subscription_end:
            remaining = (self.subscription_end - date.today()).days
            return max(remaining, 0)
        return 0

    # -------- Expiry Message --------
    @property
    def expiry_message(self):
        days_left = self.remaining_days
        if days_left == 0:
            return "Your subscription expires today!"
        elif days_left <= 5:
            return f"Your subscription expires in {days_left} days."
        elif days_left < 0:
            return "Your subscription has expired."
        return None

    # -------- Renewal --------
    def renew_subscription(self, duration_days=365, amount=5000.00, currency='INR'):
        self.subscription_start = date.today()
        self.subscription_end = self.subscription_start + timedelta(days=duration_days)
        self.subscription_amount = amount
        self.subscription_currency = currency
        self.is_active = True
        self.save()

    def __str__(self):
        return self.business_name or self.username



# -------- Subscription Packages --------
class SubscriptionPackage(models.Model):  
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='packages')
    name = models.CharField(max_length=100)
    duration_days = models.PositiveIntegerField(help_text="Duration in days (e.g., 30, 90, 180, 365)")
    amount = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.name} - {self.amount} ({self.duration_days} days)"


# -------- Base Customer --------
class BaseCustomer(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='customers')
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField(blank=True, null=True)
    contact_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)

    package = models.ForeignKey(SubscriptionPackage, on_delete=models.SET_NULL, null=True, related_name='customers')
    start_date = models.DateField(default=date.today)
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        if self.package and not self.end_date:
            self.end_date = self.start_date + timedelta(days=self.package.duration_days)
        self.is_active = self.end_date >= date.today()
        super().save(*args, **kwargs)

    def renew(self, new_package=None):
        if new_package:
            self.package = new_package
        self.start_date = date.today()
        self.end_date = self.start_date + timedelta(days=self.package.duration_days)
        self.is_active = True
        self.save()

    def remaining_days(self):
        remaining = (self.end_date - date.today()).days
        return max(remaining, 0)

    def mark_inactive(self):
        self.is_active = False
        self.save()

    def __str__(self):
        return f"{self.name} ({self.client.business_name})"



# -------- Batch --------
class Batch(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='batches')
    name = models.CharField(max_length=100)  # e.g. Morning Batch, Evening Batch
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    days = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. Mon-Fri")

    def __str__(self):
        return f"{self.name} ({self.client.business_name})"


# -------- Education --------
class EducationCustomer(BaseCustomer):
    subject = models.CharField(max_length=200)
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, related_name='students')
    parent_contact = models.CharField(max_length=100, blank=True, null=True)


# -------- Sports --------
class SportsCustomer(BaseCustomer):
    sport_type = models.CharField(max_length=100)
    coach_name = models.CharField(max_length=100)
    experience_years = models.PositiveIntegerField()
    injury_history = models.TextField(blank=True, null=True)


# -------- Monthly Payment Record --------
class PaymentRecord(models.Model):
    customer = models.ForeignKey(BaseCustomer, on_delete=models.CASCADE, related_name='payments')
    month = models.PositiveIntegerField(help_text="Month number (1=Jan, 12=Dec)")
    year = models.PositiveIntegerField()
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    STATUS_CHOICES = [
        ('Paid', 'Paid'),
        ('Partial', 'Partial'),
        ('Due', 'Due'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Due')

    class Meta:
        unique_together = ('customer', 'month', 'year')
        ordering = ['-year', '-month']

    def save(self, *args, **kwargs):
        # Automatically set status
        if self.amount_paid >= self.amount_due:
            self.status = 'Paid'
        elif 0 < self.amount_paid < self.amount_due:
            self.status = 'Partial'
        else:
            self.status = 'Due'
        super().save(*args, **kwargs)

        # Update customer's totals
        total_due = sum(p.amount_due - p.amount_paid for p in self.customer.payments.all())
        total_paid = sum(p.amount_paid for p in self.customer.payments.all())
        self.customer.total_due = total_due
        self.customer.total_paid = total_paid
        self.customer.save()

    def __str__(self):
        return f"{self.customer.name} - {self.month}/{self.year} - {self.status}"


# -------- Attendance --------
class Attendance(models.Model):
    customer = models.ForeignKey(BaseCustomer, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=date.today)
    present = models.BooleanField(default=True)

    class Meta:
        unique_together = ('customer', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.customer.name} - {self.date} - {'Present' if self.present else 'Absent'}"

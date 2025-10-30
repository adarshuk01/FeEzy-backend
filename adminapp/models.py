from datetime import date, timedelta
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


# -------- Category --------
class Category(models.Model):
    name = models.CharField(max_length=150)
    
    owner=models.ForeignKey(User,on_delete=models.CASCADE)

    def _str_(self):
        return self.name


# -------- Client (Owner) --------
class Client(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    business_name = models.CharField(max_length=200)
    contact_number = models.PositiveIntegerField()
    address = models.CharField(max_length=255)
    payment_method = models.CharField(
        max_length=255,
        choices=[('Cash', 'Cash'), ('Gpay', 'Gpay'), ('Card', 'Card')]
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    subscription_start = models.DateField(auto_now_add=True)
    subscription_end = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.subscription_start:
          self.subscription_start = date.today()
        if not self.subscription_end:
            self.subscription_end = self.subscription_start + timedelta(days=365)
        self.is_active = self.subscription_end >= date.today()
        super().save(*args, **kwargs)

    @property
    def remaining_days(self):
        remaining = (self.subscription_end - date.today()).days
        return max(remaining, 0)

    @property
    def expiry_message(self):
        days_left = self.remaining_days

        if days_left < 0:
            return "Your subscription has expired."
        elif days_left == 0:
            return "Your subscription expires today!"
        elif days_left <= 5:
            return f"Your subscription expires in {days_left} days."
        return None


    def renew_subscription(self, duration_days=365):
        self.subscription_start = date.today()
        self.subscription_end = self.subscription_start + timedelta(days=duration_days)
        self.is_active = True
        self.save()

    def _str_(self):
        return self.business_name


# -------- Subscription Packages --------
class SubscriptionPackage(models.Model):  
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='packages')
    name = models.CharField(max_length=100)
    duration_days = models.PositiveIntegerField(help_text="Duration in days (e.g., 30, 90, 180, 365)")
    amount = models.DecimalField(max_digits=8, decimal_places=2)

    def _str_(self):
        return f"{self.name} - {self.amount} ({self.duration_days} days)"


# -------- Customer --------
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

    def _str_(self):
        return f"{self.name} ({self.client.business_name})"
    
# -------- Batch --------
class Batch(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='batches')
    name = models.CharField(max_length=100)  # e.g. Morning Batch, Evening Batch
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    days = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. Mon-Fri")

    def _str_(self):
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


# -------- Monthly Payment Record (NEW) --------
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

    def _str_(self):
        return f"{self.customer.name} - {self.month}/{self.year} - {self.status}"


# -------- Attendance --------
class Attendance(models.Model):
    customer = models.ForeignKey(BaseCustomer, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=date.today)
    present = models.BooleanField(default=True)

    class Meta:
        unique_together = ('customer', 'date')
        ordering = ['-date']

    def _str_(self):
        return f"{self.customer.name} - {self.date} - {'Present' if self.present else 'Absent'}"
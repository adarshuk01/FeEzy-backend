from datetime import date, timedelta,timezone
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# -------- Category --------
class Category(models.Model):
    name = models.CharField(max_length=150)
  
    def __str__(self):
        return self.name



class Client(AbstractUser):
    business_name = models.CharField(max_length=200, null=True, blank=True, unique=True)
    contact_number = models.PositiveIntegerField(null=True, blank=True, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)  # ✅ unique email field
    address = models.CharField(max_length=255, null=True, blank=True)
    payment_method = models.CharField(
        max_length=255,
        choices=[('Cash', 'Cash'), ('Upi', 'Upi'), ('Card', 'Card')],
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
    currency_emoji = models.CharField(  
        max_length=5,
        null=True,
        blank=True,
        help_text="Emoji representation of the currency (e.g., ₹, 💵, 💶)"
    )
    is_active = models.BooleanField(default=True)

    # -------- Save Method --------
    def save(self, *args, **kwargs):
        if not self.subscription_start:
            self.subscription_start = date.today()
        if not self.subscription_end:
            self.subscription_end = self.subscription_start + timedelta(days=365)
        if not self.subscription_amount:
            self.subscription_amount = 5000.00
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






# -------- Batch --------
class Batch(models.Model):
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE,
        related_name='batches', null=True, blank=True
    )
    name = models.CharField(max_length=100)  # e.g. Morning Batch
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    days = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="e.g. Mon-Fri"
    )

    def __str__(self):
        return f"{self.name} ({self.client.business_name})" if self.client else self.name



# -------- Subscription --------
class Subscription(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=True, blank=True)

    tuition_fees = models.PositiveIntegerField()
    tuition_recurring = models.BooleanField(default=False)

    admission_fees = models.PositiveIntegerField()

    management_fees = models.PositiveIntegerField()
    management_recurring = models.BooleanField(default=False)

    uniform_fees = models.PositiveIntegerField()
    uniform_recurring = models.BooleanField(default=False)

    transport_fees = models.PositiveIntegerField()
    transport_recurring = models.BooleanField(default=False)

    book_fees = models.PositiveIntegerField()
    book_recurring = models.BooleanField(default=False)

    other_fees = models.PositiveIntegerField()
    other_recurring = models.BooleanField(default=False)

    def __str__(self):
        return self.name or "Subscription"



# -------- Member (Customer) --------
class Member(models.Model):
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name='members'
    )

    # Personal Details
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField(null=True, blank=True)

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    nationality = models.CharField(max_length=100, null=True, blank=True)
    parent_name = models.CharField(max_length=255, help_text="Guardian or parent name.")

    # Contact
    contact_number = models.CharField(max_length=20, null=True, blank=True)
    whatsapp_number = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    # Enrollment
    subscription = models.ForeignKey(
        Subscription, on_delete=models.PROTECT,
        related_name='enrolled_members'
    )

    start_date = models.DateField(
        default=date.today, null=True, blank=True,
        help_text="The actual enrollment date of the member, used for billing calculations."
    )

    TERM_CHOICES = [
        ('M', 'Monthly'),
        ('Q', 'Quarterly'),
        ('A', 'Annual'),
    ]
    subscription_term = models.CharField(max_length=1, choices=TERM_CHOICES)

    batch_group = models.ForeignKey(
        Batch, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='members'
    )

    outstanding_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        help_text="Initial debt carried forward from before the app usage."
    )

    recurring_date = models.PositiveSmallIntegerField(
        help_text="Day of the month (1–31) when recurring fee is due.",
        null=True, blank=True
    )

    def __str__(self):
        return self.full_name



# -------- Payment --------
class Payment(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)

    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('gpay', 'GPay'),
    ]
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS)

    # Fee Components Paid
    tuition_paid = models.BooleanField(default=False)
    admission_paid = models.BooleanField(default=False)
    management_paid = models.BooleanField(default=False)
    uniform_paid = models.BooleanField(default=False)
    transport_paid = models.BooleanField(default=False)
    book_paid = models.BooleanField(default=False)
    other_paid = models.BooleanField(default=False)

    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    date_paid = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Payment by {self.member.full_name} on {self.date_paid}"



# -------- Monthly Payment Record --------
class PaymentRecord(models.Model):
    customer = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='payments')

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
        # Update status
        if self.amount_paid >= self.amount_due:
            self.status = 'Paid'
        elif 0 < self.amount_paid < self.amount_due:
            self.status = 'Partial'
        else:
            self.status = 'Due'

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer.full_name} - {self.month}/{self.year} - {self.status}"



# -------- Attendance --------
class Attendance(models.Model):
    customer = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=date.today)
    present = models.BooleanField(default=True)

    class Meta:
        unique_together = ('customer', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.customer.full_name} - {self.date} - {'Present' if self.present else 'Absent'}"

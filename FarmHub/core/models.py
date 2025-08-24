from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

USER_ROLES = (
    ("admin", "Admin"),
    ("agent", "Agent"),
    ("farmer", "Farmer"),
)

class User(AbstractUser):
    role = models.CharField(max_length=10, choices=USER_ROLES)
    mobile_no = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role}) (id {self.id})"

    
    def has_permission(self, permission):
        if self.role == 'admin':
            return True  
        elif self.role == 'agent':
            return permission in ['view_farm', 'manage_farm']
        elif self.role == 'farmer':
            return permission in ['log_activity', 'record_milk']
        return False

class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True

class Farm(TimestampedModel):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    agent = models.ForeignKey(
        User,
        related_name='farms',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'agent'}
    )
    is_active = models.BooleanField(default=True)
    farm_type = models.CharField(max_length=100, blank=True, null=True)  
    farm_size = models.FloatField(blank=True, null=True)  

    def __str__(self):
        return f"self.name (id {self.id})"

class Cow(TimestampedModel):
    tag_number = models.CharField(max_length=255, unique=True, db_index=True)
    breed = models.CharField(max_length=100)
    birth_date = models.DateField()
    health_status = models.CharField(max_length=100, blank=True, null=True)  
    farm = models.ForeignKey(Farm, related_name='cows', on_delete=models.CASCADE)
    farmer = models.ForeignKey(
        User,
        related_name='cows',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'farmer'}
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Cow {self.tag_number} - {self.breed} (id{self.id})"

class Activity(TimestampedModel):
    activity_type = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    date = models.DateField(null=True, blank=True, db_index=True)
    cow = models.ForeignKey(Cow, related_name='activities', on_delete=models.CASCADE)
    recorded_by = models.ForeignKey(User, related_name='activities', on_delete=models.CASCADE)  
    category = models.CharField(max_length=100, null=True, blank=True) 

    def __str__(self):
        return f"Activity for Cow {self.cow.tag_number} - {self.activity_type}"

class MilkProduction(TimestampedModel):
    date = models.DateField(db_index=True)
    quantity = models.FloatField()  # liters
    cow = models.ForeignKey(Cow, related_name='milk_records', on_delete=models.CASCADE)
    recorded_by = models.ForeignKey(
        User,
        related_name='milk_records',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'farmer'}
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['cow', 'date'], name='uq_cow_date_milk')
        ]
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"Milk Production for Cow {self.cow.tag_number} on {self.date}"

class Enrollment(TimestampedModel):
    user = models.ForeignKey(
        User,
        related_name='enrollments',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'farmer'}
    )
    farm = models.ForeignKey(Farm, related_name='enrollments', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    progress = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    total_yield = models.FloatField(default=0)  
    is_certificate_ready = models.BooleanField(default=False)
    enrolled_at = models.DateTimeField(default=timezone.now) 

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'farm'], name='uq_user_farm_enrollment')
        ]

    def __str__(self):
        return f"{self.user.username} enrolled in {self.farm.name}"



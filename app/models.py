from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    role_choices = (
        ('provider', 'provider'),
        ('user', 'user'),
    )
    email = models.EmailField(_('email address'), unique=True, db_index=True)
    role_type = models.CharField(max_length=32, choices=role_choices, default='provider')
    profilePic = models.ImageField(
        upload_to='mediafiles/profilePics/',
        validators=[FileExtensionValidator(allowed_extensions=['jpeg', 'jpg', 'png'])])

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    # USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return "{}".format(self.username)


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    is_active = models.BooleanField(default=True, editable=False)

    class Meta:
        abstract = True


class ParkSlot(BaseModel):
    slot_choices = (
        ('Available', 'Available'),
        ('Booked', 'Booked'),
        ('Reserved', 'Reserved'),
    )

    type_choices = (
        ('Bike', 'Bike'),
        ('Car', 'Car'),
        ('Van', 'Van'),
        ('Bus', 'Bus'),
        ('Truck', 'Truck')
    )

    status = models.CharField(max_length=32, choices=slot_choices, default='Available')
    price = models.FloatField()  # price per hour
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='slot_owner')
    address = models.CharField(max_length=255)
    coordinates = models.CharField(max_length=64, blank=True, null=True)
    description = models.TextField()
    type = models.CharField(max_length=255, choices=type_choices)
    picture = models.ImageField(
        upload_to='mediafiles/parkPic/',
        validators=[FileExtensionValidator(allowed_extensions=['jpeg', 'jpg', 'png'])], blank=True, null=True)

    def __str__(self):
        return "{}".format(self.id)


class Booking(BaseModel):
    slot = models.ForeignKey(ParkSlot, on_delete=models.CASCADE, related_name='slot_booking')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_booking')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    total_price = models.FloatField()
    duration = models.FloatField()  # in minutes
    booked = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return "{}".format(self.id)


class Payment(BaseModel):
    status_choices = (
        ('Pending', 'Pending'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
    )

    amount = models.FloatField()
    pidx = models.CharField(max_length=255)
    payment_url = models.URLField()
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=32, choices=status_choices, default='Pending')
    gateway_status = models.CharField(max_length=60, default='Pending')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_payment')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='booking_payment')

    def __str__(self):
        return "{}".format(self.id)


class Rating(BaseModel):
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    slot = models.OneToOneField(ParkSlot, on_delete=models.CASCADE, related_name='slot_rating')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_rating')

    def __str__(self):
        return "{}".format(self.id)

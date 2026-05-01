from django.db import models


class Participant(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15)
    dob = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10)
    country = models.CharField(max_length=50, blank=True, null=True)
    region = models.CharField(max_length=50, blank=True, null=True)
    impartation = models.CharField(max_length=50, blank=True, null=True)
    registered_student = models.CharField(max_length=50, blank=True, null=True)
    attending_gtc = models.CharField(max_length=50, blank=True, null=True)
    spouse_or_child = models.CharField(max_length=50, blank=True, null=True)
    accommodation = models.CharField(max_length=50, blank=True, null=True)
    transport = models.CharField(max_length=50, blank=True, null=True)
    personal_transport = models.CharField(max_length=50, blank=True, null=True)
    volunteering = models.TextField(blank=True, null=True)
    coming_with_children = models.CharField(max_length=3, blank=True, null=True)
    children_count = models.PositiveIntegerField(default=0)
    comments = models.CharField(max_length=50, blank=True, null=True)
    arrival_date = models.DateField(blank=True, null=True)
    payment_reference = models.CharField(max_length=50, blank=True, null=True)
    paid = models.BooleanField(default=False)


class Child(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='children')
    name = models.CharField(max_length=50)
    age = models.IntegerField(blank=True, null=True)


class Donation(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    reference = models.CharField(max_length=50, blank=True, null=True)
    project = models.CharField(max_length=50, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)

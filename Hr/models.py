from django.db import models

# Create your models here.


class interviewSchedule(models.Model):
    name = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    jobRole = models.CharField(max_length=200)
    experience = models.CharField(max_length=200)
    resume = models.TextField()
    #Assigned Hr (The HR who entered the details)
    Assigned_hr = models.TextField(blank=True, null=True)
    # Additional evaluation result fields
    strengths = models.TextField(blank=True, null=True)  # Now optional
    weaknesses = models.TextField(blank=True, null=True)  # Now optional
    accuracy = models.CharField(max_length=10, blank=True, null=True)  # e.g. "95%"
    communication = models.CharField(max_length=10, blank=True, null=True)  # High, Medium, or Low
    technical_depth = models.CharField(max_length=10, blank=True, null=True)  # High, Medium, or Low
    good_fit = models.CharField(max_length=5, blank=True, null=True)  # "Yes" or "No"
    evaluation_complete = models.BooleanField(default=False)  # Track if evaluation was completed
    interviewDate = models.DateField()  # Stores the date (YYYY-MM-DD format)
    interviewTime = models.TimeField()  # Stores the time (HH:MM:SS format)
    token = models.CharField(max_length=200, unique=True)
    createdAt = models.DateTimeField(auto_now_add=True)  # Timestamp for record creation
    cheatingScore = models.CharField(max_length=20, blank=True, null=True)  # normal, suspicious, cheating
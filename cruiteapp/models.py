from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError



class UserProfile(models.Model):

    ROLE_CHOICES = (
        ("employer", "Employer"),
        ("seeker", "Job Seeker"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    # SETTINGS
    email_notifications = models.BooleanField(default=True)

    default_role = models.CharField(max_length=200, blank=True)

    dark_mode = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"

class SeekerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Personal Info
    full_name = models.CharField(max_length=100,blank=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15,blank=True)
    country = models.CharField(max_length=100,blank=True)
    other_country = models.CharField(max_length=100, blank=True)

    state = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    area = models.CharField(max_length=100, blank=True)
    house_name = models.CharField(max_length=100, blank=True)
    flat_number = models.CharField(max_length=100, blank=True)

    address_line1 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    # Education Info
    qualification = models.CharField(max_length=100, blank=True)
    field = models.CharField(max_length=100, blank=True)
    college = models.CharField(max_length=150, blank=True)
    cgpa = models.CharField(max_length=10, blank=True)
    passing_year = models.IntegerField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    def clean(self):
        if self.age and self.age < 16:
            raise ValidationError("Minimum age is 16.")

        if self.cgpa:
             try:
               cgpa = float(self.cgpa)
             except ValueError:
               raise ValidationError("CGPA must be a number")

        if cgpa < 0 or cgpa > 10:
            raise ValidationError("CGPA must be between 0 and 10")
    def __str__(self):
        return self.user.username

class CompanyProfile(models.Model):

    company_name = models.CharField(max_length=150)

    INDUSTRY_CHOICES = [
        ("IT", "Information Technology"),
        ("LAW", "Law Firm"),
        ("FIN", "Finance"),
        ("HC", "Healthcare"),
        ("EDU", "Education"),
        ("MKT", "Marketing"),
        ("OTH", "Other"),
    ]

    industry = models.CharField(max_length=50, choices=INDUSTRY_CHOICES)

    SIZE_CHOICES = [
        ("SM", "Small (1-50)"),
        ("MD", "Medium (50-250)"),
        ("LG", "Large (250-1000)"),
        ("ENT", "Enterprise (1000+)"),
    ]

    company_size = models.CharField(max_length=50, choices=SIZE_CHOICES)

    head_office = models.CharField(max_length=150)
    about_company = models.TextField()
    company_website = models.URLField(blank=True, null=True)

    company_completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name


class Employer(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="employer"
    )

    company = models.ForeignKey(
        "CompanyProfile",   
        on_delete=models.SET_NULL,
        related_name="employees",
        null=True,
        blank=True
    )

    full_name = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    official_email = models.EmailField(blank=True)
    branch_location = models.CharField(max_length=300, blank=True)
    
    HE_Choices = [
        ("ALL", "Any"),
        ("FRE", "Fresher"),
        ("13Y", "1-3 Years"),
        ("35Y", "3-5 Years"),
        ("5Y", "5+ Years"),
    ]
    experience_years= models.CharField(max_length= 30, choices=HE_Choices, default="ALL")
    hr_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name or self.user.email


class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to="resumes/")
    raw_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name}"


# ---------------------------
# ANALYSIS RESULT
# ---------------------------

class AnalysisResult(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)

    overall_score = models.IntegerField()
    role_match_score = models.IntegerField(null=True, blank=True)
    skill_match_score = models.IntegerField(null=True, blank=True)
    resume_strength_score = models.IntegerField(null=True, blank=True)

    strengths = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)
    red_flags = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.resume.file.name} - {self.overall_score}%"
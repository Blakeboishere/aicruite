from django import forms
from django.contrib.auth.models import User
from .models import SeekerProfile, Employer
from .models import CompanyProfile


from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class SignupForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("Email already registered")
        return email

    def clean_password(self):
        password = self.cleaned_data.get("password")
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirm_password")

        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match")

        return cleaned_data


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)



class ForgotPasswordForm(forms.Form):
    email = forms.EmailField()

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("No account found with this email")
        return email



class PersonalForm(forms.ModelForm):

    class Meta:
        model = SeekerProfile
        fields = [
            "full_name",
            "age",
            "gender",
            "email",
            "phone",
            "country",
            "other_country",
            "state",
            "district",
            "area",
            "house_name",
            "flat_number",
            "address_line1",
            "city",
            "province",
            "postal_code",
        ]

class EducationForm(forms.ModelForm):

    class Meta:
        model = SeekerProfile
        fields = [
            "qualification",
            "field",
            "college",
            "cgpa",
            "passing_year",
        ]
class EmployerForm(forms.ModelForm):

    class Meta:
        model = Employer
        fields = [
            "full_name",
            "department",
            "designation",
            "official_email",
            "branch_location",
            "experience_years",
        ]


class CompanyOnboardingForm(forms.ModelForm):

    class Meta:
        model = CompanyProfile
        fields = [
            "company_name",
            "industry",
            "company_size",
            "head_office",
            "about_company",
            "company_website",
        ]       
class ResumeUploadForm(forms.Form):

    role = forms.CharField(
        required=False,
        label="Target Role (Optional)",
        widget=forms.TextInput(attrs={
            "placeholder": "e.g. Frontend Developer"
        })
    )

    resume = forms.FileField(
        label="Upload Resume (PDF only)",
        widget=forms.ClearableFileInput(attrs={
          "accept": ".pdf",
          "id": "id_resume",
          "style": "display:none;"
         })
    )

    def clean_resume(self):
        file = self.cleaned_data.get("resume")

        if file:
            if not file.name.lower().endswith(".pdf"):
                raise forms.ValidationError("Only PDF files are allowed.")

            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size must be under 5MB.")

        return file

class ATSUploadForm(forms.Form):
    role = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            "placeholder": "Enter target role"
        })
    )

    description = forms.CharField(
        widget=forms.Textarea(attrs={
            "rows": 4,
            "placeholder": "Enter job description"
        })
    )

    resumes = forms.FileField()


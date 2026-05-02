from django.shortcuts import render, redirect
import os
import tempfile
from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm
from django.contrib.auth import login
from .parser import parse_resume
from .ats import run_ats_analysis
from .workflow import handle_uploaded_resume
from .models import UserProfile
from .forms import SignupForm
from django.contrib.auth.models import User
from .forms import ATSUploadForm
from .forms import EducationForm
from .forms import PersonalForm
from .forms import ForgotPasswordForm
from .forms import ResumeUploadForm
from .models import Resume
from .analyser import run_resume_analysis
from django.contrib.auth.decorators import login_required
from .forms import EmployerForm
from .models import Employer
from .models import CompanyProfile
from .forms import CompanyOnboardingForm
from .models import SeekerProfile
from .decorators import employer_required, seeker_required
from django.core.files.storage import FileSystemStorage
fs = FileSystemStorage(location=settings.MEDIA_ROOT)
def landing(request):
    return render(request, "app/landing.html")

def signup(request):

    if request.method == "POST":
        form = SignupForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            User.objects.create_user(
                username=email,  
                email=email,
                password=password
            )

            return redirect("login")

    else:
        form = SignupForm()

    return render(request, "app/signup.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
def profile_view(request):

    user = request.user

    seeker = SeekerProfile.objects.filter(user=user).first()
    employer = Employer.objects.filter(user=user).first()

    context = {
        "user": user,
        "seeker": seeker,
        "employer": employer,
    }

    return render(request, "app/profile.html", context)


def login_view(request):

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect("role_select")  

        else:
            return render(request, "app/login.html", {
                "error": "Invalid email or password"
            })

    return render(request, "app/login.html")


@login_required
def profile_view(request):

    user = request.user

    seeker = SeekerProfile.objects.filter(user=user).first()
    employer = Employer.objects.filter(user=user).first()

    context = {
        "user": user,
        "seeker": seeker,
        "employer": employer,
    }

    return render(request, "app/profile.html", context)

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .models import Employer, SeekerProfile

@login_required
def role_select(request):

    if hasattr(request.user, "employer") or hasattr(request.user, "seekerprofile"):
        return redirect("role_redirect")

    if request.method == "POST":
        role = request.POST.get("role")

        if role == "employer":
            Employer.objects.create(user=request.user)
            return redirect("employer")

        elif role == "seeker":
            SeekerProfile.objects.create(user=request.user)
            return redirect("personal")

    return render(request, "app/role_select.html")


@login_required
def settings_view(request):

    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        request.user.first_name = request.POST.get("full_name")
        request.user.email = request.POST.get("email")

        password = request.POST.get("password")
        if password:
            request.user.set_password(password)

        request.user.save()

        profile.default_role = request.POST.get("default_role")
        profile.email_notifications = "email_notifications" in request.POST

        profile.save()

    return render(request, "app/settings.html", {
        "profile": profile
    })
@login_required
def role_redirect(request):

    employer = Employer.objects.filter(user=request.user).first()

    if employer:

        if not employer.hr_completed:
            return redirect("employer")

        company = employer.company
        if not company or not company.company_completed:
            return redirect("employer_onboarding")

        return redirect("employer_dashboard")

    # Seeker logic 
    seeker = SeekerProfile.objects.filter(user=request.user).first()
    if seeker:
        if not seeker.is_completed:
            return redirect("personal")
        return redirect("upload")

    return redirect("role_select")

def forgot(request):
    message = None

    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)

        if form.is_valid():
            message = "Password reset link has been sent to your email"
            form = ForgotPasswordForm()  # reset form
    else:
        form = ForgotPasswordForm()

    return render(
        request,
        "app/password_reset.html",
        {
            "form": form,
            "message": message
        }
    )

@seeker_required
def personal(request):

    profile, created = SeekerProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = PersonalForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.is_completed = True 
            profile.save()
            return redirect("education")
    else:
        form = PersonalForm(instance=profile)

    return render(request, "app/personal.html", {"form": form})

@seeker_required
@login_required
def education(request):

    profile = SeekerProfile.objects.get(user=request.user)

    if request.method == "POST":
        form = EducationForm(request.POST, instance=profile)

        if form.is_valid():
            profile = form.save(commit=False)
            profile.is_completed = True  
            profile.save()

            return redirect("upload")

    else:
        form = EducationForm(instance=profile)

    return render(request, "app/education.html", {"form": form})

@employer_required
def employer(request):

    employer = request.user.employer

    # If already completed, skip this page
    if employer.hr_completed:
        return redirect("role_redirect")

    if request.method == "POST":
        form = EmployerForm(request.POST, instance=employer)

        if form.is_valid():
            employer = form.save(commit=False)
            employer.hr_completed = True
            employer.save()

            return redirect("role_redirect")

    else:
        form = EmployerForm(instance=employer)

    return render(request, "app/employer.html", {
        "form": form
    })

@employer_required
def employer_onboarding(request):

    employer = request.user.employer
    company = employer.company

    # If company already completed, skip page
    if company and company.company_completed:
        return redirect("role_redirect")

    if request.method == "POST":
        form = CompanyOnboardingForm(request.POST, instance=company)

        if form.is_valid():
            company = form.save(commit=False)
            company.company_completed = True
            company.save()

            employer.company = company
            employer.save()

            return redirect("role_redirect")

    else:
        form = CompanyOnboardingForm(instance=company)

    return render(request, "app/industry.html", {
        "form": form
    })

@employer_required
def employer_dashboard(request):

    employer =  employer = request.user.employer

    if not employer:
        return redirect("employer_onboarding")

    return render(request, "app/employer_dashboard.html", {
        "employer": employer
    })

@employer_required
def ats(request):

    if request.path.endswith("upload_ats/"):

        if request.method == "POST":

            role = request.POST.get("role")
            description = request.POST.get("description")
            files = request.FILES.getlist("resumes")

            if not role or not description or not files:
                return render(request, "app/uploadats.html", {
                    "error": "All fields required."
                })

            fs = FileSystemStorage(location=settings.MEDIA_ROOT)
            saved_files = []

            for f in files:
                filename = fs.save(f.name, f)
                saved_files.append(filename)

            request.session["role"] = role
            request.session["description"] = description
            request.session["resume_files"] = saved_files

            return redirect("screen_ats")

        return render(request, "app/uploadats.html")

    # SCREEN PAGE
    elif request.path.endswith("screen_ats/"):

        role = request.session.get("role")
        description = request.session.get("description")
        file_names = request.session.get("resume_files")

        if not role or not description or not file_names:
            return redirect("upload_ats")

        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        results = []

        for name in file_names:

            file_path = fs.path(name)

            # Parse resume
            parser_output = parse_resume(file_path)

            # Save resume
            resume = Resume.objects.create(
                user=request.user,
                file=name,
                raw_text=parser_output.get("raw_text", "")
            )

            # Run ATS analysis
            ats_result = run_ats_analysis(
                resume=resume,
                parser_output=parser_output,
                role_title=role,
                job_description=description
            )

            # Store result
            results.append({
                "filename": name,
                "overall_score": ats_result["overall_score"],
                "role_match_score": ats_result["role_match_score"],
                "skill_match_score": ats_result["skill_match_score"],
                "resume_strength_score": ats_result["resume_strength_score"],
                "strengths": ats_result["strengths"],
                "weaknesses": ats_result["weaknesses"],
                "red_flags": ats_result["red_flags"],
            })

            if os.path.exists(file_path):
                os.remove(file_path)

        # Clear session
        request.session.pop("resume_files", None)

        return render(request, "app/screenats.html", {
            "results": results,
            "role": role,
            "description": description
        })

@seeker_required
def upload_resume(request):

    profile = SeekerProfile.objects.filter(user=request.user).first()

    if not profile or not profile.is_completed:
        return redirect("personal")

    if request.method == "POST":
        form = ResumeUploadForm(request.POST, request.FILES)

        if form.is_valid():

            role = form.cleaned_data["role"]
            resume_file = form.cleaned_data["resume"]

            # Parse resume
            parser_output = parse_resume(resume_file)

            # Run AI analysis
            analysis_result = run_resume_analysis(
                parser_output=parser_output,
                target_role=role
            )

            # Store result temporarily
            request.session["analysis_result"] = analysis_result
            request.session["role"] = role

            # Redirect to result page
            return redirect("resume_result")

    else:
        form = ResumeUploadForm()

    return render(request, "app/upload.html", {
        "form": form,
        "seekerprofile": profile
    })

@seeker_required
def resume_result(request):

    result = request.session.get("analysis_result")
    role = request.session.get("role")

    if not result:
        return redirect("upload")
    

    request.session.pop("analysis_result", None)
    request.session.pop("role", None)

    return render(request, "app/result.html", {
        "result": result,
        "role": role
    })
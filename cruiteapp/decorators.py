from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .models import Employer, SeekerProfile


def employer_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if Employer.objects.filter(user=request.user).exists():
            return view_func(request, *args, **kwargs)
        return redirect("role_redirect")
    return wrapper


def seeker_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if SeekerProfile.objects.filter(user=request.user).exists():
            return view_func(request, *args, **kwargs)
        return redirect("role_redirect")
    return wrapper
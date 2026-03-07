import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aicruite.settings")
django.setup()

from cruiteapp.models import Employer

e = Employer.objects.first()

if not e:
    print("No Employer found")
else:
    print("HR Completed:", e.hr_completed)
    print("Company Linked:", e.company_name)

    if e.company_name:
        print("Company Completed:", e.company_name.company_completed)
    else:
        print("No company linked")
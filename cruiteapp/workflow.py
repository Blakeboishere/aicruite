from pathlib import Path
import tempfile

from .parser import parse_resume
from .ats import run_ats_analysis
from .analyser import run_resume_analysis


def handle_uploaded_resume(
    uploaded_file,
    user_role: str,
    workflow: str,
    role_title: str | None = None,
    job_description: str | None = None
):

    suffix = Path(uploaded_file.name).suffix

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        for chunk in uploaded_file.chunks():
            tmp.write(chunk)
        temp_path = tmp.name

    try:
        parser_output = parse_resume(temp_path)

        
        if workflow == "ats" and user_role == "business":
            return run_ats_analysis(
                parser_output=parser_output,
                role_title=role_title,
                job_description=job_description
            )

        if workflow == "analyser" and user_role == "seeker":
            return run_resume_analysis(
                parser_output=parser_output,
                target_role=role_title
            )


        raise ValueError("Invalid workflow or user role")

    finally:
        Path(temp_path).unlink(missing_ok=True)


import json
import requests
from typing import Dict, Any
from .models import AnalysisResult
from django.conf import settings
import re
from .parser import parse_resume

GROQ_API_KEY= settings.GROQ_API_KEY


def build_ats_prompt(
    parser_output: Dict[str, Any],
    role_title: str | None = None,
    job_description: str | None = None
) -> str:
   

    role_block = ""
    if role_title:
        role_block += f"\nRole Title:\n{role_title}\n"
    if job_description:
        role_block += f"\nJob Description:\n{job_description}\n"

    prompt = f"""
You are an Applicant Tracking System (ATS) resume evaluation engine.

IMPORTANT RULES:
- Treat `raw_text` as the primary source of truth.
- Treat all other fields as parser-generated helpers.
- If helper fields conflict with raw_text, trust raw_text.
- Ignore obvious parser noise (e.g. phone numbers parsed as dates).
- Do NOT accuse fraud or dishonesty.
- Red flags should be neutral and suggest verification only.

{role_block}

TASK:
Evaluate the resume for shortlisting purposes and return ONLY valid JSON.

JSON SCHEMA (strict):
{{
  "role_match_score": number,
  "skill_match_score": number,
  "resume_strength_score": number,
  "overall_score": number,
  "strengths": [string],
  "weaknesses": [string],
  "red_flags": [string]
}}

Parser Output (JSON):
{json.dumps(parser_output, indent=2)}

REMEMBER:
- Scores must be between 0 and 100.
- overall_score should be a reasonable weighted judgement.
- Weaknesses are normal improvement areas.
- Red flags are ATS-only and cautious.
- Return STRICTLY valid minified JSON with double quotes. No markdown formatting.
"""

    return prompt.strip()


def call_llm(prompt: str) -> dict:
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "You are a resume evaluation engine that outputs strict JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    response = requests.post(url, headers=headers, json=data)
    print("MODEL BEING SENT:", data["model"])
    print("STATUS:", response.status_code)
    print("BODY:", response.text)

    if response.status_code != 200:
      print("GROQ STATUS:", response.status_code)
      print("GROQ BODY:", response.text)
      raise Exception("Groq API failed")

    result = response.json()

    raw_text = result["choices"][0]["message"]["content"]

    match = re.search(r'\{.*\}', raw_text, re.DOTALL)
    if not match:
        raise Exception("No JSON found in model output")

    return json.loads(match.group(0))

def run_ats_analysis(
    resume,
    parser_output: Dict[str, Any],
    role_title: str | None = None,
    job_description: str | None = None
) -> Dict[str, Any]:

    print("🔥 run_ats_analysis() CALLED 🔥")

    # ---- Sanity check ----
    if not parser_output:
        raise ValueError("parser_output is None")

    if not parser_output.get("raw_text"):
        raise ValueError("Parser output missing raw_text")

    print("✅ Parser output received")

    prompt = build_ats_prompt(
        parser_output=parser_output,
        role_title=role_title,
        job_description=job_description
    )

    print("✅ Prompt built successfully")

    try:
        result = call_llm(prompt)
    except Exception as e:
        print("🚨 LLM CALL FAILED 🚨")
        print("Error type:", type(e))
        print("Error message:", str(e))
        raise  # Let Django crash so we see full traceback

    print("✅ LLM call returned result")

    required_keys = {
        "role_match_score",
        "skill_match_score",
        "resume_strength_score",
        "overall_score",
        "strengths",
        "weaknesses",
        "red_flags"
    }

    if not isinstance(result, dict):
        raise ValueError("LLM result is not a dictionary")

    missing = required_keys - result.keys()
    if missing:
        raise ValueError(f"ATS output missing keys: {missing}")

    print("✅ Schema validation passed")
    print("🎯 FINAL ATS RESULT:", json.dumps(result, indent=2))
    
    new_score = result["overall_score"]

    existing = AnalysisResult.objects.filter(resume=resume).order_by("-overall_score").first()

    if existing:
       if new_score > existing.overall_score:
        print("📈 New score is better, updating DB")

        existing.overall_score = new_score
        existing.role_match_score = result["role_match_score"]
        existing.skill_match_score = result["skill_match_score"]
        existing.resume_strength_score = result["resume_strength_score"]
        existing.strengths = result["strengths"]
        existing.weaknesses = result["weaknesses"]
        existing.red_flags = result["red_flags"]
        existing.save()

       else:
           print("📉 Existing score is better, keeping DB result")

    else:
       print("💾 Saving first ATS result")

       AnalysisResult.objects.create(
           resume=resume,
           overall_score=result["overall_score"],
           role_match_score=result["role_match_score"],
           skill_match_score=result["skill_match_score"],
           resume_strength_score=result["resume_strength_score"],
           strengths=result["strengths"],
           weaknesses=result["weaknesses"],
           red_flags=result["red_flags"]
    )
    return result
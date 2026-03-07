
import json
import requests
from typing import Dict, Any

from django.conf import settings
import re
from .parser import parse_resume

GROQ_API_KEY= settings.GROQ_API_KEY


def build_analyser_prompt(
    parser_output: Dict[str, Any],
    target_role: str | None = None
) -> str:
   

    role_block = ""
    if target_role:
        role_block = f"\nTarget Role:\n{target_role}\n"

    prompt = f"""
You are a professional resume analyzer and career advisor.

IMPORTANT RULES:
- Treat `raw_text` as the primary source of truth.
- Treat all other fields as parser-generated helpers.
- If helper fields conflict with raw_text, trust raw_text.
- Do NOT mention ATS, hiring systems, or recruiters.
- Be constructive, practical, and encouraging.
- Do NOT accuse exaggeration or dishonesty.

{role_block}

TASK:
Analyze the resume and provide improvement-focused feedback.
Return ONLY valid JSON.

JSON SCHEMA (strict):
{{
  "resume_quality_score": number,
  "summary": string,
  "strengths": [string],
  "key_weaknesses": [string],
  "skill_gaps": [string],
  "improvement_suggestions": [string],
  "section_wise_feedback": {{
    "summary": string,
    "skills": string,
    "experience": string,
    "education": string
  }}
}}

Parser Output (JSON):
{json.dumps(parser_output, indent=2)}

REMEMBER:
- Scores must be between 0 and 100.
- Suggestions must be actionable.
- Feedback should help improve interview chances.
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


def run_resume_analysis(
    parser_output: Dict[str, Any],
    target_role: str | None = None
) -> Dict[str, Any]:
    

    print("run_resume_analysis() CALLED")

    if not parser_output.get("raw_text"):
        raise ValueError("Parser output missing raw_text")

    prompt = build_analyser_prompt(
        parser_output=parser_output,
        target_role=target_role
    )
    
    try:
        result = call_llm(prompt)
    except ValueError as e:
        print("ANALYSER ERROR:", e)
        return {
            "resume_quality_score": 0,
            "summary": "Resume analysis failed.",
            "strengths": [],
            "key_weaknesses": ["Analysis could not be completed"],
            "skill_gaps": [],
            "improvement_suggestions": ["Retry analysis"],
            "section_wise_feedback": {
                "summary": "",
                "skills": "",
                "experience": "",
                "education": ""
            }
        }

    required_keys = {
        "resume_quality_score",
        "summary",
        "strengths",
        "key_weaknesses",
        "skill_gaps",
        "improvement_suggestions",
        "section_wise_feedback"
    }

    missing = required_keys - result.keys()
    if missing:
        raise ValueError(f"Analyzer output missing keys: {missing}")
    print("🎯 FINAL Analyser RESULT:", json.dumps(result, indent=2))

    return result

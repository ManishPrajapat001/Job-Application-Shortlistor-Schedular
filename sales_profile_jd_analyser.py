from sales_jd import job_description
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client = None


def get_openai_client():
    global _client
    if _client is not None:
        return _client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    _client = OpenAI(api_key=api_key)
    return _client


functions = [
    {
        "name": "finalverdict",
        "description": "Return select or reject with an optional rejection_reason",
        "parameters": {
            "type": "object",
            "properties": {
                "verdict": {
                    "type": "string",
                    "enum": ["select", "reject"]
                },
                "rejection_reason": {
                    "type": "string",
                    "description": "Reason for rejection if verdict is reject; empty otherwise"
                }
            },
            "required": ["verdict", "rejection_reason"]
        }
    }
]


SYSTEM_PROMPT = f"""You are a precise job-profile matcher for a sales role.
You will be given a job description (JD) and a candidate profile.
Assess whether the candidate's experience and skills sufficiently intersect with the JD requirements.
If the overlap is strong enough for a reasonable shortlist, choose verdict=select; otherwise verdict=reject.

Consider:
- Sales motion fit (B2B/B2C, SMB/MM/Enterprise)
- Quota-carrying experience, attainment, pipeline ownership
- Relevant roles (SDR/BDR, AE, AM/CSM), industry/domain fit
- Prospecting, negotiation, closing, CRM tools (Salesforce/HubSpot/etc.)
- Recency and depth of sales achievements

Return your decision via the finalverdict function call.

JD:
{job_description}
"""


def analyze_profile_against_jd(profile_text: str):
    client = get_openai_client()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Candidate Profile:\n\n{profile_text}"}
    ]
    try:
        resp = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            functions=functions,
            function_call={"name": "finalverdict"}
        )
        fc = resp.choices[0].message.function_call
        if fc and fc.name == "finalverdict":
            args = json.loads(fc.arguments or "{}")
            verdict = args.get("verdict")
            reason = args.get("rejection_reason", "")
            if verdict not in ("select", "reject"):
                return {"verdict": "reject", "rejection_reason": "Invalid verdict from model"}
            if verdict == "select":
                reason = ""
            return {"verdict": verdict, "rejection_reason": reason}
        return {"verdict": "reject", "rejection_reason": "Model did not return a function call"}
    except Exception as e:
        return {"verdict": "reject", "rejection_reason": f"Error: {e}"}


def main():
    samples = [
        "B2B SaaS AE, 3y experience, $1.2M ARR closed, Salesforce/HubSpot, MEDDICC.",
        "Data Scientist, Python/ML, no sales experience, Kaggle medals."
    ]
    for i, s in enumerate(samples, 1):
        res = analyze_profile_against_jd(s)
        print(f"Sample {i}:")
        print(s)
        print(res)
        print('-'*40)


if __name__ == "__main__":
    main()



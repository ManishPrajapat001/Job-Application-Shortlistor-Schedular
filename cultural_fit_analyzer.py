from company_culture import company_culture
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


SYSTEM_PROMPT = f"""You are a cultural fit analyzer for our company.
You will be given our company culture details and a candidate's cover letter.
Assess whether the candidate's values, traits, and work style align with our company culture.
If there is a strong cultural fit, choose verdict=select; otherwise verdict=reject.

Consider:
- Values alignment (core beliefs, principles, ethics)
- Work style compatibility (collaboration, communication, approach to work)
- Personality traits that match our culture
- Motivation and passion alignment
- Leadership style and team dynamics fit
- Growth mindset and adaptability

Return your decision via the finalverdict function call.

Company Culture:
{company_culture}
"""


def analyze_cultural_fit(cover_letter: str):
    """
    Analyze cultural fit between candidate's cover letter and company culture.
    
    Args:
        cover_letter (str): Candidate's cover letter containing their traits and values
        
    Returns:
        dict: Contains 'verdict' and 'rejection_reason' fields
    """
    client = get_openai_client()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Candidate Cover Letter:\n\n{cover_letter}"}
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
    """Test the cultural fit analyzer with sample cover letters."""
    samples = [
        "I am passionate about innovation and thrive in collaborative environments. I believe in continuous learning and enjoy working with diverse teams to solve complex problems. My leadership style is inclusive and I value transparency and open communication.",
        "I prefer working independently and don't like team meetings. I focus on individual achievements and prefer structured, hierarchical work environments. I'm not interested in company culture or values alignment."
    ]
    
    print("Cultural Fit Analysis Results:")
    print("=" * 50)
    
    for i, cover_letter in enumerate(samples, 1):
        print(f"\nCover Letter {i}:")
        print(f"Cover Letter: {cover_letter}")
        result = analyze_cultural_fit(cover_letter)
        print(f"Verdict: {result['verdict']}")
        if result['rejection_reason']:
            print(f"Rejection Reason: {result['rejection_reason']}")
        print("-" * 30)


if __name__ == "__main__":
    main()

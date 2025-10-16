import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_openai_client():
    """Get OpenAI client with API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    return OpenAI(api_key=api_key)

def filter_profile(profile_text):
    """
    Filter user profile to determine if they should be shortlisted for tech or sales roles.
    
    Args:
        profile_text (str): User profile as a string containing all information
        
    Returns:
        dict: Contains 'verdict' and 'rejection_reason' fields
    """
    client = get_openai_client()
    
    # Define the function schema for the LLM to call
    functions = [
        {
            "name": "finalverdict",
            "description": "Determine if a candidate should be shortlisted for tech or sales roles",
            "parameters": {
                "type": "object",
                "properties": {
                    "verdict": {
                        "type": "string",
                        "enum": ["reject", "tech", "sales"],
                        "description": "Final decision: reject if graduation year > 2025 or role mismatch, tech for technical roles, sales for sales roles"
                    },
                    "rejection_reason": {
                        "type": "string",
                        "description": "Reason for rejection if verdict is 'reject', empty string otherwise"
                    }
                },
                "required": ["verdict", "rejection_reason"]
            }
        }
    ]
    
    system_prompt = """You are a profile filter for shortlisting candidates for tech and sales roles.

Your task is to analyze the user profile and determine:
1. If the candidate's graduation year is 2025 or earlier (if later, reject)
2. If the profile is for tech, sales, or other roles (reject if other roles). we are looking for tech and sales roles only.

Rules:
- Only consider candidates who graduated in 2025 or earlier
- Look for tech indicators: technical degrees, programming skills, software development experience, engineering background, etc.
- Look for sales indicators: sales experience, business development, customer relations, B2B/B2C sales etc.
- Reject profiles that don't fit tech or sales roles (e.g., pure marketing, HR, finance, etc.)
- Reject profiles with graduation year after 2025

Return your decision using the finalverdict function call."""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this profile:\n\n{profile_text}"}
            ],
            functions=functions,
            function_call={"name": "finalverdict"}
        )
        
        # Extract function call result
        function_call = response.choices[0].message.function_call
        if function_call and function_call.name == "finalverdict":
            arguments = json.loads(function_call.arguments)
            return {
                "verdict": arguments["verdict"],
                "rejection_reason": arguments["rejection_reason"]
            }
        else:
            # Fallback if no function call
            return {
                "verdict": "reject",
                "rejection_reason": "Unable to process profile"
            }
            
    except Exception as e:
        print(f"Error processing profile: {e}")
        return {
            "verdict": "reject",
            "rejection_reason": f"Error processing profile: {str(e)}"
        }

def main():
    """Test the profile filter with sample profiles."""
    # Sample profiles for testing
    sample_profiles = [
        "John Doe, Computer Science graduate from 2023. 2 years experience in Python, React, and AWS. Worked as a software developer at TechCorp.",
        "Jane Smith, Marketing graduate from 2026. 1 year experience in digital marketing and social media management.",
        "Mike Johnson, Business Administration graduate from 2024. 3 years experience in sales and business development. Led a team of 5 sales representatives.",
        "Sarah Wilson, Psychology graduate from 2025. 2 years experience in HR and recruitment. No technical background.",
        "Alex Brown, Engineering graduate from 2022. 4 years experience in software development, machine learning, and cloud architecture."
    ]
    
    print("Profile Filter Test Results:")
    print("=" * 50)
    
    for i, profile in enumerate(sample_profiles, 1):
        print(f"\nProfile {i}:")
        print(f"Profile: {profile}")
        result = filter_profile(profile)
        print(f"Verdict: {result['verdict']}")
        if result['rejection_reason']:
            print(f"Rejection Reason: {result['rejection_reason']}")
        print("-" * 30)

if __name__ == "__main__":
    main()

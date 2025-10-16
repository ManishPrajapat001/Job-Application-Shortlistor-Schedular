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


def extract_candidate_name(profile_text):
    """
    Extract candidate name from profile text using LLM.
    
    Args:
        profile_text (str): User profile containing candidate information
        
    Returns:
        str: Extracted candidate name or "Dear Candidate"
    """
    try:
        client = get_openai_client()
        
        # Define function schema for name extraction
        functions = [
            {
                "name": "extract_name",
                "description": "Extract the candidate's name from the profile",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "candidate_name": {
                            "type": "string",
                            "description": "The candidate's full name if found, empty string if not found"
                        }
                    },
                    "required": ["candidate_name"]
                }
            }
        ]
        
        system_prompt = """You are a name extraction assistant. 
        Extract the candidate's full name from the profile text.
        Look for patterns like:
        - "John Smith, Computer Science graduate..."
        - "Name: Jane Doe"
        - "I am Alex Johnson..."
        - "My name is Sarah Wilson..."
        
        Return the full name (first and last name) if found, otherwise return empty string.
        Do not include titles like Mr., Ms., Dr., etc."""
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract the candidate's name from this profile:\n\n{profile_text}"}
            ],
            functions=functions,
            function_call={"name": "extract_name"}
        )
        
        # Extract function call result
        function_call = response.choices[0].message.function_call
        if function_call and function_call.name == "extract_name":
            arguments = json.loads(function_call.arguments)
            name = arguments.get("candidate_name", "").strip()
            return name if name else "Dear Candidate"
        else:
            return "Dear Candidate"
            
    except Exception as e:
        print(f"Error extracting name: {e}")
        return "Dear Candidate"


def generate_email(verdict, reason, user_profile):
    """
    Generate a professional email based on verdict, reason, and user profile.
    
    Args:
        verdict (str): "select" or "reject"
        reason (str): Reason for selection or rejection
        user_profile (str): User profile to extract name and personalize
        
    Returns:
        str: Complete email content with subject and body
    """
    client = get_openai_client()
    
    # Extract candidate name
    candidate_name = extract_candidate_name(user_profile)
    # Define function schema for LLM response
    functions = [
        {
            "name": "generate_email",
            "description": "Generate a professional email for candidate communication",
            "parameters": {
                "type": "object",
                "properties": {
                    "email_content": {
                        "type": "string",
                        "description": "Complete email content including subject line and body"
                    }
                },
                "required": ["email_content"]
            }
        }
    ]
    
    system_prompt = f"""You are a professional HR representative writing emails to candidates.

Candidate Name: {candidate_name}
Verdict: {verdict}
Reason: {reason}

Email Requirements:
1. Write a professional, polished email as an HR representative
2. Include a clear subject line
3. Use the candidate's name for personalization
4. Maintain a warm yet professional tone

For REJECTION emails:
- Be encouraging and mention future opportunities
- Acknowledge their application professionally
- Provide constructive feedback if possible
- End on a positive note

For SELECTION emails:
- If reason contains interview details: Include all elaborate interview details (dates, times, interview types)
- If reason mentions slots not found: Notify that interviews will be scheduled soon
- Congratulate the candidate
- Provide clear next steps
- Include any relevant instructions

Email Format:
Subject: [Appropriate subject line]

Dear [Candidate Name],

[Professional email body]

Best regards,
[HR Team]

Return your response using the generate_email function call."""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate a professional email for this candidate based on the verdict and reason provided."}
            ],
            functions=functions,
            function_call={"name": "generate_email"}
        )
        # Extract function call result
        function_call = response.choices[0].message.function_call
        if function_call and function_call.name == "generate_email":
            try:
                # Use regex to extract email content directly since JSON has unescaped newlines
                import re
                match = re.search(r'"email_content":\s*"([^"]*(?:\\.[^"]*)*)"', function_call.arguments, re.DOTALL)
                if match:
                    email_content = match.group(1)
                    # Unescape the content
                    email_content = email_content.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                    return email_content
                else:
                    # Fallback: try to parse as JSON after cleaning
                    cleaned_args = function_call.arguments.replace('\n', '\\n').replace('\r', '\\r')
                    arguments = json.loads(cleaned_args)
                    email_content = arguments.get("email_content", "Error generating email")
                    # Convert \n back to actual newlines
                    email_content = email_content.replace('\\n', '\n').replace('\\r', '\r')
                    return email_content
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                return f"Error parsing email response: {str(e)}"
        else:
            return "Error: Unable to generate email"
            
    except Exception as e:
        return f"Error generating email: {str(e)}"


def main():
    """Test the emailer with sample scenarios."""
    print("Email Generator Test")
    print("=" * 50)
    
    # Sample user profile
    sample_profile = "John Smith, Computer Science graduate from 2023. 2 years experience in Python, React, and AWS."
    
    # Test scenarios
    test_cases = [
        {
            "verdict": "reject",
            "reason": "Graduation year is 2026, which is beyond our requirement of 2025 or earlier",
            "description": "Rejection due to graduation year"
        },
        {
            "verdict": "select", 
            "reason": "Your interviews have been scheduled as follows: DSA interview on 2025-10-15 at 10:00 AM - 11:00 AM, Low-level design interview on 2025-10-15 at 2:00 PM - 3:00 PM, High-level design interview on 2025-10-16 at 9:00 AM - 10:00 AM",
            "description": "Selection with interview details"
        },
        {
            "verdict": "select",
            "reason": "Our interviewers are busy right now and they will try to schedule your interview as soon as possible",
            "description": "Selection but slots not found"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['description']}")
        print("-" * 40)
        email = generate_email(
            test_case["verdict"], 
            test_case["reason"], 
            sample_profile
        )
        print(email)
        print("\n" + "="*60)


if __name__ == "__main__":
    main()

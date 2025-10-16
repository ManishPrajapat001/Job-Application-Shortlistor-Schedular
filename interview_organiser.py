from in_memory_db import get_available_slots, get_slots_by_type
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


def organize_interview(interview_type):
    """
    Organize interview slots based on the interview type (tech or sales).
    
    Args:
        interview_type (str): Either "tech" or "sales"
        
    Returns:
        dict: Contains 'interview_details' and 'slots_not_found' fields
    """
    if interview_type not in ["tech", "sales"]:
        return {
            "interview_details": "",
            "slots_not_found": "Invalid interview type. Please specify 'tech' or 'sales'."
        }
    
    # Get all available slots
    all_slots = get_available_slots()
    
    # Define required slots based on interview type
    if interview_type == "tech":
        required_types = ["DSA", "Low-level design", "High-level design"]
        required_count = 3
    else:  # sales
        required_types = ["Communication", "Case study"]
        required_count = 2
    
    # Check if we have enough slots of each required type
    available_slots_by_type = {}
    for slot_type in required_types:
        available_slots_by_type[slot_type] = get_slots_by_type(slot_type)
        if len(available_slots_by_type[slot_type]) == 0:
            return {
                "interview_details": "",
                "slots_not_found": "Our interviewers are busy right now and they will try to schedule your interview as soon as possible."
            }
    
    # Prepare slots data for LLM
    slots_data = {
        "all_slots": all_slots,
        "available_by_type": available_slots_by_type,
        "required_types": required_types,
        "interview_type": interview_type
    }
    
    # Define function schema for LLM response
    functions = [
        {
            "name": "schedule_interview",
            "description": "Schedule interview slots based on requirements",
            "parameters": {
                "type": "object",
                "properties": {
                    "interview_details": {
                        "type": "string",
                        "description": "Detailed paragraph describing the scheduled interview slots with dates, times, and interview types"
                    },
                    "slots_not_found": {
                        "type": "string",
                        "description": "Message if required slots cannot be found, empty string if slots are found"
                    }
                },
                "required": ["interview_details", "slots_not_found"]
            }
        }
    ]
    
    system_prompt = f"""You are an interview scheduler for our company.

Available slots data:
{json.dumps(slots_data, indent=2)}

Requirements:
- Interview type: {interview_type}
- Required interview types: {', '.join(required_types)}
- Total slots needed: {required_count}

Your task:
1. Select exactly {required_count} slots from the available slots
2. For tech interviews: select exactly 1 DSA slot, 1 Low-level design slot, and 1 High-level design slot
3. For sales interviews: select exactly 1 Communication slot and 1 Case study slot
4. Prefer slots that are:
   - On the same day if possible
   - Scheduled as early as possible
   - Have good time spacing between them
5. If you cannot find the required slots, set slots_not_found to the message: "Our interviewers are busy right now and they will try to schedule your interview as soon as possible."

Return your decision using the schedule_interview function call with:
- interview_details: A detailed paragraph describing the selected slots with full details (date, time, interview type)
- slots_not_found: Empty string if slots found, error message if not found"""

    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please schedule {interview_type} interview slots based on the available slots."}
            ],
            functions=functions,
            function_call={"name": "schedule_interview"}
        )
        
        # Extract function call result
        function_call = response.choices[0].message.function_call
        if function_call and function_call.name == "schedule_interview":
            arguments = json.loads(function_call.arguments)
            return {
                "interview_details": arguments.get("interview_details", ""),
                "slots_not_found": arguments.get("slots_not_found", "")
            }
        else:
            return {
                "interview_details": "",
                "slots_not_found": "Unable to process interview scheduling request"
            }
            
    except Exception as e:
        return {
            "interview_details": "",
            "slots_not_found": f"Error scheduling interview: {str(e)}"
        }


def main():
    """Test the interview organizer with both tech and sales types."""
    print("Interview Organizer Test")
    print("=" * 50)
    
    # Test tech interview
    print("\n1. Tech Interview Scheduling:")
    print("-" * 30)
    tech_result = organize_interview("tech")
    print(f"Interview Details: {tech_result['interview_details']}")
    if tech_result['slots_not_found']:
        print(f"Slots Not Found: {tech_result['slots_not_found']}")
    
    # Test sales interview
    print("\n2. Sales Interview Scheduling:")
    print("-" * 30)
    sales_result = organize_interview("sales")
    print(f"Interview Details: {sales_result['interview_details']}")
    if sales_result['slots_not_found']:
        print(f"Slots Not Found: {sales_result['slots_not_found']}")
    
    # Test invalid type
    print("\n3. Invalid Type Test:")
    print("-" * 30)
    invalid_result = organize_interview("invalid")
    print(f"Interview Details: {invalid_result['interview_details']}")
    if invalid_result['slots_not_found']:
        print(f"Slots Not Found: {invalid_result['slots_not_found']}")


if __name__ == "__main__":
    main()

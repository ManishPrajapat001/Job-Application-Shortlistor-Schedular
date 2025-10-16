import random
from datetime import datetime, timedelta

# Interview types
INTERVIEW_TYPES = [
    "DSA",
    "Low-level design", 
    "High-level design",
    "Communication",
    "Case study"
]

# Time slots (1-hour slots from 9 AM to 5 PM)
TIME_SLOTS = [
    "9:00 AM - 10:00 AM",
    "10:00 AM - 11:00 AM", 
    "11:00 AM - 12:00 PM",
    "12:00 PM - 1:00 PM",
    "1:00 PM - 2:00 PM",
    "2:00 PM - 3:00 PM",
    "3:00 PM - 4:00 PM",
    "4:00 PM - 5:00 PM"
]

def generate_interview_slots(num_slots=30):
    """
    Generate random interview slots starting from October 5th, 2025.
    
    Args:
        num_slots (int): Number of slots to generate (default: 30)
        
    Returns:
        list: List of interview slot dictionaries
    """
    slots = []
    start_date = datetime(2025, 10, 5)  # October 5th, 2025
    
    for i in range(num_slots):
        # Random date from October 5th onwards (up to 60 days ahead)
        random_days = random.randint(0, 60)
        slot_date = start_date + timedelta(days=random_days)
        
        # Random time slot and interview type
        time_slot = random.choice(TIME_SLOTS)
        interview_type = random.choice(INTERVIEW_TYPES)
        
        slot = {
            "date": slot_date.strftime("%Y-%m-%d"),
            "time": time_slot,
            "interview_type": interview_type
        }
        
        slots.append(slot)
    
    # Sort slots by date and time for better organization
    slots.sort(key=lambda x: (x["date"], x["time"]))
    
    return slots

# Generate the interview slots database
interview_slots = generate_interview_slots(30)

def get_available_slots():
    """Get all available interview slots."""
    return interview_slots

def get_slots_by_type(interview_type):
    """Get slots filtered by interview type."""
    return [slot for slot in interview_slots if slot["interview_type"] == interview_type]

def get_slots_by_date(date):
    """Get slots filtered by specific date."""
    return [slot for slot in interview_slots if slot["date"] == date]

def get_slots_by_date_range(start_date, end_date):
    """Get slots within a date range."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    return [
        slot for slot in interview_slots 
        if start <= datetime.strptime(slot["date"], "%Y-%m-%d") <= end
    ]

def book_slot(slot_index):
    """Book a slot by removing it from available slots."""
    if 0 <= slot_index < len(interview_slots):
        booked_slot = interview_slots.pop(slot_index)
        return booked_slot
    return None

def add_slot(date, time, interview_type):
    """Add a new slot to the database."""
    new_slot = {
        "date": date,
        "time": time,
        "interview_type": interview_type
    }
    interview_slots.append(new_slot)
    # Re-sort after adding
    interview_slots.sort(key=lambda x: (x["date"], x["time"]))

def main():
    """Display the generated interview slots."""
    print("Generated Interview Slots:")
    print("=" * 60)
    print(f"Total slots: {len(interview_slots)}")
    print()
    
    for i, slot in enumerate(interview_slots, 1):
        print(f"{i:2d}. {slot['date']} | {slot['time']:20s} | {slot['interview_type']}")
    
    print("\nSlots by type:")
    for interview_type in INTERVIEW_TYPES:
        count = len(get_slots_by_type(interview_type))
        print(f"  {interview_type}: {count} slots")

if __name__ == "__main__":
    main()

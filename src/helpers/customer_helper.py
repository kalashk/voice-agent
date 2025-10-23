import json
import os  # noqa: F401
from typing import TypedDict

CUSTOMER_FILE = "src/customer.json"

class CustomerProfileType(TypedDict):
    customer_id: str
    customer_name: str
    age: int
    city: str
    language: str
    bank_name: str
    phone_number: str
    gender: str


# --------------------------
# Load customer profile
# --------------------------
def load_customer_profile(file_path=CUSTOMER_FILE) -> CustomerProfileType:
    """Load customer data from JSON, create default if file not found."""
    # if not os.path.exists(file_path):
    #     print(f"❌ {file_path} not found. Creating default profile.")
    #     default_data: CustomerProfileType = {
    #         "customer_id": "u123",
    #         "customer_name": "Rahul",
    #         "age": 30,
    #         "city": "Pune",
    #         "language": "hindi",
    #         "bank_name": "HDFC",
    #         "phone_number": "9669953995",
    #         "gender": ""
    #     }
    #     save_customer_profile(default_data, file_path)
    #     return default_data

    with open(file_path) as f:
        return json.load(f)

# --------------------------
# Save customer profile
# --------------------------
def save_customer_profile(profile: CustomerProfileType, file_path=CUSTOMER_FILE):
    """Save customer data to JSON."""
    with open(file_path, "w") as f:
        json.dump(profile, f, indent=2)
    print(f"💾 Customer profile saved to {file_path}")

# --------------------------
# Interactive updates
# --------------------------
def get_valid_name(current_name="") -> str:
    """Prompt for a new name; keep current if empty input."""
    while True:
        name = input(f"👤 Enter customer name [{current_name}]: ").strip()
        if name:
            return name
        elif current_name:
            return current_name
        print("❌ Name cannot be empty!")

def get_valid_gender(current_gender="") -> str:
    """Prompt for gender; keep current if empty input."""
    while True:
        gender = input(f"⚧ Enter gender (M/F) [{current_gender}]: ").strip().upper()
        if gender == "M":
            return "Male"
        elif gender == "F":
            return "Female"
        elif current_gender:
            return current_gender
        print("❌ Invalid input! Enter 'M' or 'F'.")

def get_valid_phone(current_phone: str = "") -> str:
    """Prompt for phone number; keep current if empty input. Adds +91 by default."""
    while True:
        phone = input(f"📱 Enter 10-digit phone number [{current_phone}]: ").strip()

        # Keep current number if user presses Enter
        if not phone and current_phone:
            return current_phone

        # Validate and add +91 prefix if missing
        if phone.isdigit() and len(phone) == 10:
            return f"+91{phone}"
        elif phone.startswith("+91") and len(phone) == 13 and phone[3:].isdigit():
            return phone

        print("❌ Invalid number! Must be 10 digits (or include +91).")


# --------------------------
# Update customer interactively
# --------------------------
def update_customer_profile(file_path=CUSTOMER_FILE) -> CustomerProfileType:
    """Update customer name, gender, and phone number interactively."""
    profile = load_customer_profile(file_path)

    profile["customer_name"] = get_valid_name(profile.get("customer_name", ""))
    profile["gender"] = get_valid_gender(profile.get("gender", ""))
    profile["phone_number"] = get_valid_phone(profile.get("phone_number", ""))

    save_customer_profile(profile, file_path)
    print(f"✅ Customer profile updated: {profile}")
    return profile

# --------------------------
# Example usage
# --------------------------
if __name__ == "__main__":
    update_customer_profile()

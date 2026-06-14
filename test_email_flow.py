import os
from dotenv import load_dotenv
from backend.services.email_service import send_confirmation, process_inbound_emails

# 1. Load your credentials
load_dotenv()

def run_test():
    test_email = "ansaribushra36sm@gmail.com" # Use your own email to test
    
    print("--- Testing Outbound: Sending Confirmation ---")
    try:
        # We use a dummy ID and subject
        send_confirmation(test_email, "SPS-TEST-1234", "System Test Subject")
        print("Test email sent successfully! Check your inbox.")
    except Exception as e:
        print(f"Outbound Test Failed: {e}")

    print("\n--- Testing Inbound: Processing Emails ---")
    try:
        # Note: You must send an actual email to your EMAIL_USER account first
        # so that it is sitting in the 'UNSEEN' folder.
        result = process_inbound_emails()
        print(f"Inbound Sync Result: {result}")
    except Exception as e:
        print(f"Inbound Test Failed: {e}")

if __name__ == "__main__":
    run_test()
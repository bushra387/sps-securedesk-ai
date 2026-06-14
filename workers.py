import time
import logging
from backend.services.email_service import process_inbound_emails

# Configure professional logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_worker():
    logging.info("--- Email Sync Worker Started ---")
    while True:
        try:
            logging.info("Checking for new emails...")
            result = process_inbound_emails()
            logging.info(f"Sync status: {result}")
        except Exception as e:
            # Using exc_info=True gives you the full traceback if the app crashes
            logging.error(f"Critical error in worker loop: {e}", exc_info=True)
        
        logging.info("Worker sleeping for 60 seconds...")
        time.sleep(60)

if __name__ == "__main__":
    try:
        run_worker()
    except KeyboardInterrupt:
        logging.info("Worker stopped manually by user.")
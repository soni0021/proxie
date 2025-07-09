from confirmtkt_clone import ConfirmTktAPI
import json
import time

def test_api():
    api = ConfirmTktAPI()
    
    print("\nTesting Live Status API:")
    print("-" * 80)
    train_numbers = ["12307", "15032"]  # Howrah Jodhpur Express and GKP Intercity
    for train_number in train_numbers:
        print(f"\nTesting live status for train {train_number}...")
        result = api.get_live_status(train_number)
        print("\nResult:")
        print(json.dumps(result, indent=2))
        print("-" * 80)
        time.sleep(2)  # Add delay between requests
    
    print("\nTesting Train Schedule API:")
    print("-" * 80)
    for train_number in train_numbers:
        print(f"\nTesting schedule for train {train_number}...")
        result = api.get_train_schedule(train_number)
        print("\nResult:")
        print(json.dumps(result, indent=2))
        print("-" * 80)
        time.sleep(2)  # Add delay between requests
    
    print("\nTesting PNR Status API:")
    print("-" * 80)
    pnr_numbers = ["1234567890", "2345678901"]  # Example PNR numbers
    for pnr_number in pnr_numbers:
        print(f"\nTesting PNR status for {pnr_number}...")
        result = api.get_pnr_status(pnr_number)
        print("\nResult:")
        print(json.dumps(result, indent=2))
        print("-" * 80)
        time.sleep(2)  # Add delay between requests

if __name__ == "__main__":
    test_api() 
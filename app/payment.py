import requests
from django.conf import settings


def create_payment_link(amount, booking_id, order_id):
    url = f"{settings.KHALTI_BASE_URL}/api/v2/epayment/initiate/"

    payload = {
        "return_url": "https://localhost:3000",
        "website_url": "https://localhost:3000",
        "amount": amount * 100,  # in paisa
        "purchase_order_id": order_id,
        "purchase_order_name": f"booking-{booking_id}",
        "remarks": booking_id,
    }
    headers = {
        'Authorization': f'key {settings.KHALTI_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(response.text)

        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(e)
        return None


def check_payment_status(pidx):
    url = f"{settings.KHALTI_BASE_URL}/api/v2/epayment/lookup/"

    payload = {
        "pidx": pidx,
    }
    headers = {
        'Authorization': f'key {settings.KHALTI_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(response.text)
        data = response.json()

        status = data.get('status') or data.get('detail')
        transaction_id = data.get('transaction_id', None)

        # Map status to category
        status_mapping = {
            "Pending": "Pending",
            "Initiated": "Pending",
            "Completed": "Success",
            "Expired": "Failed",
            "User canceled": "Failed",
            "Not found.": "Failed",
            "Refunded": "Failed",
            "Partially Refunded": "Failed",
        }

        return status_mapping.get(status, "Failed"), status, transaction_id
    except Exception as e:
        print(e)
        return None, None, None

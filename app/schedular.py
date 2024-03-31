from app.payment import check_payment_status
from .models import Payment

from apscheduler.schedulers.background import BackgroundScheduler


def run_schedular():
    schedular = BackgroundScheduler()
    schedular.add_job(update_payment_status, 'interval', seconds=3)
    schedular.start()


def update_payment_status():
    """
    Update payment status. This function will be called by the scheduler.
    """

    payments = Payment.objects.filter(status='Pending')
    for payment in payments:
        status, gateway_status, txn_id = check_payment_status(payment.pidx)
        if status and gateway_status != payment.gateway_status:
            payment.status = status
            payment.gateway_status = gateway_status
            payment.transaction_id = txn_id
            payment.save()

            if status == 'Success':
                payment.booking.is_paid = True
                payment.booking.booked = True
                payment.booking.save()

            print(f"Payment {payment.id} updated to {status}")

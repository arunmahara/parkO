import uuid
from datetime import datetime
from django.utils import timezone


def get_char_uuid(length=0):
    uid = uuid.uuid4().hex
    if length:
        return uid[:length]

    return uid


def format_datetime(dt):
    return timezone.make_aware(datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S'))


def parking_duration_hours(start_time, end_time):
    return (end_time - start_time).total_seconds() / 3600

from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes, api_view
from app.models import ParkSlot, Booking, Payment, Rating
from app.payment import create_payment_link
from app.serializers import UserSerializer, ParkSlotSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from app.services.api_response import generic_response, log_exception, log_field_error
from app.services.permission import IsOwner
from app.utils import format_datetime, get_char_uuid, parking_duration_hours
from django.utils import timezone


class UserRegisterView(generics.CreateAPIView):
    """
    View to create user.
    """
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        """
        Register new user.
        """
        try:
            payload = request.data.copy()
            payload['username'] = payload['email']
            serializer = self.serializer_class(data=payload)
            if not serializer.is_valid():
                print(serializer.errors)
                return log_field_error(serializer.errors)

            serializer.save()
            refresh = RefreshToken.for_user(serializer.instance)
            data = serializer.data
            data['access'] = str(refresh.access_token)
            return generic_response(
                success=True,
                message='User Registered Successfully',
                data=data,
                status=status.HTTP_200_OK
            )

        except Exception as e:
            print(e)
            return log_exception(e)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_details(request):
    """
    Get user details.
    """
    try:
        user = request.user
        serializer = UserSerializer(user)
        return generic_response(
            success=True,
            message='User Details',
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    except Exception as e:
        print(e)
        return log_exception(e)


class UserUpdateView(generics.UpdateAPIView):
    """
    View to update user.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        try:
            user = request.user
            payload = request.data.copy()
            serializer = self.serializer_class(user, data=payload, partial=True)
            if not serializer.is_valid():
                print(serializer.errors)
                return log_field_error(serializer.errors)

            serializer.save()
            return generic_response(
                success=True,
                message='User Details Updated Successfully',
                data=serializer.data,
                status=status.HTTP_200_OK
            )

        except Exception as e:
            print(e)
            return log_exception(e)


class ParkSlotModelView(viewsets.ModelViewSet):
    """
    View to list, create, update and delete park slots.
    For owner.
    """
    serializer_class = ParkSlotSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        user = self.request.user
        return ParkSlot.objects.filter(owner=user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        bookings = Booking.objects.filter(slot=instance, booked=True).order_by('-start_time')
        data = []
        for booking in bookings:
            data.append({
                'id': booking.id,
                'user_email': booking.user.email,
                'start_time': booking.start_time,
                'end_time': booking.end_time,
                'duration_minutes': booking.duration,
                'total_price': booking.total_price,
                'booked': booking.booked,
                'is_paid': booking.is_paid,
                'status': 'Booked' if booking.end_time > timezone.now() else 'Expired'
            })

        # Add booking details to the response
        response = serializer.data
        response['bookings'] = data

        return Response(response)


class ParkSlotsModelView(viewsets.ModelViewSet):
    """
    View to list all park slots.
    For user.
    """

    queryset = ParkSlot.objects.all().order_by('-created_at')
    serializer_class = ParkSlotSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']
    search_fields = ['address']
    filterset_fields = {'status': ['exact'], 'price': ['exact'], 'address': ['icontains'], 'type': ['exact']}

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        # Get bookings for this park slot
        bookings = Booking.objects.filter(slot=instance, booked=True).order_by('-start_time')
        data = []
        for booking in bookings:
            if booking.end_time > timezone.now():
                data.append({
                    'id': booking.id,
                    'start_time': booking.start_time,
                    'end_time': booking.end_time,
                    'duration_minutes': booking.duration,
                })

        # Add booking details to the response
        response = serializer.data
        response['bookings'] = data

        return Response(response)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def book_park_slot(request):
    """
    Book a park slot.
    For user.
    """
    user = request.user

    try:
        park_slot_id = request.data.get('park_slot_id')
        start_time = request.data.get('start_time')
        end_time = request.data.get('end_time')

        if not park_slot_id or not start_time or not end_time:
            return generic_response(
                success=False,
                message='Please provide all required fields.',
                status=status.HTTP_400_BAD_REQUEST
            )

        start_time = format_datetime(start_time)
        end_time = format_datetime(end_time)

        try:
            slot = ParkSlot.objects.get(id=park_slot_id)
        except ParkSlot.DoesNotExist:
            return generic_response(
                success=False,
                message='Park Slot not found.',
                status=status.HTTP_404_NOT_FOUND
            )

        if Booking.objects.filter(
                slot=slot, start_time__lt=end_time, end_time__gt=start_time, booked=True).exists():
            return generic_response(
                success=False,
                message='Slot is already booked for the selected time range.',
                status=status.HTTP_400_BAD_REQUEST
            )

        duration_hours = parking_duration_hours(start_time, end_time)
        total_price = max(round(duration_hours * slot.price, 2), 10)

        booking = Booking.objects.create(
            slot=slot,
            user=user,
            start_time=start_time,
            end_time=end_time,
            duration=round(duration_hours * 60),
            total_price=total_price,
        )

        order_id = get_char_uuid(16)
        response = create_payment_link(total_price, booking.id, order_id)
        if not response:
            booking.delete()
            return generic_response(
                success=False,
                message='Failed to create payment link.',
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        Payment.objects.create(
            user=user,
            amount=total_price,
            booking=booking,
            pidx=response.get('pidx'),
            payment_url=response.get('payment_url'),
        )

        return generic_response(
            success=True,
            message='Slot Booked Successfully',
            data={
                'booking_id': booking.id,
                'duration_minutes': booking.duration,
                'total_price': total_price,
                'payment_url': response.get('payment_url')
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        print(e)
        return log_exception(e)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_bookings_of_user(request):
    """
    Get all bookings of a user.
    For user.
    """
    user = request.user

    try:
        bookings = Booking.objects.filter(user=user, booked=True).order_by('-start_time')
        data = []
        for booking in bookings:
            booking_status = 'Booked' if booking.end_time > timezone.now() else 'Expired'

            rating = None
            if booking_status == 'Expired':
                rating_objs = Rating.objects.filter(slot=booking.slot, user=user)
                if rating_objs.exists():
                    rating = rating_objs.first().rating

            data.append({
                'id': booking.id,
                'slot_id': booking.slot.id,
                'parking_address': booking.slot.address,
                'parking_coordinate': booking.slot.coordinates,
                'vehicle_type': booking.slot.type,
                'start_time': booking.start_time,
                'end_time': booking.end_time,
                'duration_minutes': booking.duration,
                'total_price': booking.total_price,
                'booked': booking.booked,
                'is_paid': booking.is_paid,
                'status': booking_status,
                'rating': rating
            })

        return generic_response(
            success=True,
            message='Bookings',
            data=data,
            status=status.HTTP_200_OK
        )

    except Exception as e:
        print(e)
        return log_exception(e)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_bookings_of_park_slot(request, parkslot_id):
    """
    Get all bookings of a park slot.
    For owner of the park slot.
    """
    user = request.user

    try:
        try:
            slot = ParkSlot.objects.get(id=parkslot_id)
        except ParkSlot.DoesNotExist:
            return generic_response(
                success=False,
                message='Park Slot not found.',
                status=status.HTTP_404_NOT_FOUND
            )

        if slot.owner != user:
            return generic_response(
                success=False,
                message='You are not the owner of this park slot.',
                status=status.HTTP_403_FORBIDDEN
            )

        bookings = Booking.objects.filter(slot=slot, booked=True).order_by('-start_time')
        data = []
        for booking in bookings:

            rating = None
            rating_objs = Rating.objects.filter(slot=booking.slot)
            if rating_objs.exists():
                rating = rating_objs.first().rating

            data.append({
                'id': booking.id,
                'user_email': booking.user.email,
                'start_time': booking.start_time,
                'end_time': booking.end_time,
                'duration_minutes': booking.duration,
                'total_price': booking.total_price,
                'booked': booking.booked,
                'is_paid': booking.is_paid,
                'status': 'Booked' if booking.end_time > timezone.now() else 'Expired',
                'rating': rating
            })

        return generic_response(
            success=True,
            message='All Bookings of Park Slot',
            data=data,
            status=status.HTTP_200_OK
        )

    except Exception as e:
        print(e)
        return log_exception(e)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rate_parkslot(request):
    """
    Rate a park slot.
    For user.
    """
    user = request.user

    try:
        booking_id = request.data.get('booking_id')
        rating = request.data.get('rating')

        if not (booking_id and rating):
            return generic_response(
                success=False,
                message='Please provide all required fields.',
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            booking = Booking.objects.get(id=booking_id, booked=True, user=user)
        except Booking.DoesNotExist:
            return generic_response(
                success=False,
                message='Booking not found.',
                status=status.HTTP_404_NOT_FOUND
            )

        if rating not in range(1, 6):
            return generic_response(
                success=False,
                message='Rating should be between 1 and 5.',
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            Rating.objects.create(
                rating=rating,
                slot=booking.slot,
                user=user
            )
        except IntegrityError:
            return generic_response(
                success=False,
                message='You have already rated this park slot.',
                status=status.HTTP_400_BAD_REQUEST
            )

        return generic_response(
            success=True,
            message='Park Slot Rated Successfully',
            status=status.HTTP_200_OK
        )

    except Exception as e:
        print(e)
        return log_exception(e)

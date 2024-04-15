from . import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register('parkslot', views.ParkSlotModelView, basename='parkslot')
router.register('parkslots', views.ParkSlotsModelView, basename='parkslots')

urlpatterns = [
    path('register/', views.UserRegisterView.as_view(), name='register user'),
    path('user/', views.get_user_details, name='user details'),
    path('user/update/', views.UserUpdateView.as_view(), name='update user'),
    path('', include(router.urls)),
    path('book/', views.book_park_slot, name='book slot'),
    path('bookings/', views.get_bookings_of_user, name='my bookings'),
    path('parkslot/bookings/<int:parkslot_id>/', views.get_all_bookings_of_park_slot, name='all bookings of park slot'),
    path('rate/', views.rate_parkslot, name='rate park slot'),
]

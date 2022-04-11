from django.urls import path, include
from django.conf.urls import url
from django.views.generic import TemplateView
from . import views


# urlpatterns = [
#     path('persons', views.PersonListView.as_view()),
#     path('persons/<int:pk>', views.PersonView.as_view())
# ]

urlpatterns = [
    path('hotels', views.HotelsListView.as_view()),
    path('me', views.PersonView.as_view()),
    path('reservations', views.ReservationsListView.as_view()),
    path('reservations/<str:uid>', views.ReservationView.as_view()),
    path('loyalty', views.LoyaltyView.as_view()),
    path('payment/<str:uid>', views.PaymentView.as_view()),
    path('payments', views.PaymentsListView.as_view()),
    path('', views.ReservationsListView.as_view()),
    path('authorization', views.authorize, name='authorize'),
    path('callback', views.callback, name='callback'),
    path('real_callback', views.real_callback, name='real_callback'),
]
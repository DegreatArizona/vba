from django.urls import path
from .consumers import MechanicLocationConsumer

websocket_urlpatterns = [
    path('ws/mechanic/<int:mechanic_id>/', MechanicLocationConsumer.as_asgi()),
]

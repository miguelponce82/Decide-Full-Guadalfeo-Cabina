from django.urls import path
from .views import *


urlpatterns = [
    path('',BoothListView.as_view()),
    path('<int:voting_id>/', BoothView.as_view()),
]

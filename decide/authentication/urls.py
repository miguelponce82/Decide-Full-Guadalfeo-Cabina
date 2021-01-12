from django.urls import include, path
from django.contrib.auth.views import logout
from rest_framework.authtoken.views import obtain_auth_token

from .views import *


urlpatterns = [
    path('', IndexUserView.as_view(), name="decide_main"),
    path('login/', obtain_auth_token),
    path('logout/', LogoutView.as_view()),
    path('getuser/', GetUserView.as_view()),
    path('accounts/', include('allauth.urls')),
    path('decide/login/', LoginUserView.as_view(), name='auth_login'),
    path('decide/logout/', logout, name="auth_logout"),
    path('decide/register/', RegisterUserView.as_view(), name="auth_register"),
    path('decide/register/complete/', CompleteVotingUserDetails.as_view(), name='auth_register_complete'),
    path('decide/getVotingUser/', GetVotingUser.as_view(), name='auth_get_voting_user'),
    path('decide/getGenresByIds/', GetGenresByIds.as_view(), name='auth_get_genres_by_ids'),
]
from django.forms import ModelForm
from .models import VotingUser


class RegisterVotingUserForm(ModelForm):
    class Meta:
        model = VotingUser
        fields = '__all__'
        exclude = ['user']
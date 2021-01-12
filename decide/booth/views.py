import json
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.http import Http404
from rest_framework.views import APIView
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.db import IntegrityError
from authentication.models import VotingUser
from census.models import Census
from voting.models import Voting

from base import mods


# TODO: check permissions and census
class BoothView(TemplateView):
    template_name = 'booth/booth.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vid = kwargs.get('voting_id', 0)

        try:
            r = mods.get('voting', params={'id': vid})

            # Casting numbers to string to manage in javascript with BigInt
            # and avoid problems with js and big number conversion
            for k, v in r[0]['pub_key'].items():
                r[0]['pub_key'][k] = str(v)

            context['voting'] = json.dumps(r[0])
        except:
            raise Http404

        context['KEYBITS'] = settings.KEYBITS

        return context

class BoothListView(APIView):
    
    def get(self,request):

        #####################################################################
        ############################ GET USER ###############################
        #####################################################################

        # Check for user logged
        if request.user.id is None:
            messages.error(request, 'You must be logged to access there!')
            return redirect('auth_login')
        # Check for token to see if user is valid
        else:
            try:
                tk = Token.objects.get(user=request.user)
            except ObjectDoesNotExist:
                messages.error(request, 'User not valid!')
                return redirect('auth_login')

            try:
                voting_user = VotingUser.objects.get(user=request.user)
            except ObjectDoesNotExist:
                messages.error(request, 'Finish setting your user account!')
                return redirect('decide_main')


            ######################################################################################
            ############################ GET VOTINGS HE CAN ACCESS ###############################
            ######################################################################################
            msg = None
            census = Census.objects.filter(voter_id=request.user.id)
            votings = []

            if not census:
                msg= 'You dont have any votings'
            
            else:
                for c in census:
                    voting = Voting.objects.get(id=c.voting_id)
                    if voting.start_date != None and voting.end_date == None:
                        votings.append({'name':voting.name, 'id':voting.id})


        
        return render(request, 'booth/boothlist.html', {'msg':msg, 'votings':votings})

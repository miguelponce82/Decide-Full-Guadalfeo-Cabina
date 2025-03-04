from django.db import models
from django.contrib.postgres.fields import JSONField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from base import mods
from base.models import Auth, Key


class Question(models.Model):
    desc = models.TextField()

    def __str__(self):
        return self.desc


class QuestionOption(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    number = models.PositiveIntegerField(blank=True, null=True)
    option = models.TextField()

    def save(self):
        if not self.number:
            self.number = self.question.options.count() + 2
        return super().save()

    def __str__(self):
        return '{} ({})'.format(self.option, self.number)

class Candidatura(models.Model):
    nombre = models.TextField()
    delegadoCentro = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name='delegado_centro')
    representanteDelegadoPrimero = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name='representante_primero')
    representanteDelegadoSegundo = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name='representante_segundo')
    representanteDelegadoTercero = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name='representante_tercero')
    representanteDelegadoCuarto = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name='representante_cuarto')
    representanteDelegadoMaster = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name='representante_master')

    def __str__(self):
        return self.nombre


class Voting(models.Model):
    name = models.CharField(max_length=200)
    desc = models.TextField(blank=True, null=True)
    question = models.ManyToManyField(Question, related_name='voting')

    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)

    PRIMRAY_VOTING = 'PV'
    GENERAL_VOTING = 'GV'

    TYPES = [
        (PRIMRAY_VOTING, 'Primary voting'),
        (GENERAL_VOTING, 'General voting')
    ]

    tipo = models.TextField(null=False, choices=TYPES, default=PRIMRAY_VOTING)

    candiancy = models.ForeignKey(Candidatura, related_name='voting', blank=True, on_delete=models.CASCADE, null=True)

    pub_key = models.OneToOneField(Key, related_name='voting', blank=True, null=True, on_delete=models.SET_NULL)
    auths = models.ManyToManyField(Auth, related_name='votings')

    tally = JSONField(blank=True, null=True)
    postproc = JSONField(blank=True, null=True)

    def clean(self):
        if(self.tipo=='PV'):
            if(self.candiancy == None):
                raise ValidationError('Primary votings must have a candidancy')
        if(self.tipo=='GV'):
            if(self.candiancy!=None):
                raise ValidationError('General votings must not have a candidancy')


    def create_pubkey(self):
        if self.pub_key or not self.auths.count():
            return

        auth = self.auths.first()
        data = {
            "voting": self.id,
            "auths": [ {"name": a.name, "url": a.url} for a in self.auths.all() ],
        }
        key = mods.post('mixnet', baseurl=auth.url, json=data)
        pk = Key(p=key["p"], g=key["g"], y=key["y"])
        pk.save()
        self.pub_key = pk
        self.save()

    def get_votes(self, token=''):
        # gettings votes from store
        votes = mods.get('store', params={'voting_id': self.id}, HTTP_AUTHORIZATION='Token ' + token)
        # anon votes
        return [[i['a'], i['b']] for i in votes]

    def tally_votes(self, token=''):
        '''
        The tally is a shuffle and then a decrypt
        '''

        votes = self.get_votes(token)

        auth = self.auths.first()
        shuffle_url = "/shuffle/{}/".format(self.id)
        decrypt_url = "/decrypt/{}/".format(self.id)
        auths = [{"name": a.name, "url": a.url} for a in self.auths.all()]

        # first, we do the shuffle
        data = { "msgs": votes }
        response = mods.post('mixnet', entry_point=shuffle_url, baseurl=auth.url, json=data,
                response=True)
        if response.status_code != 200:
            # TODO: manage error
            pass

        # then, we can decrypt that
        data = {"msgs": response.json()}
        response = mods.post('mixnet', entry_point=decrypt_url, baseurl=auth.url, json=data,
                response=True)

        if response.status_code != 200:
            # TODO: manage error
            pass

        self.tally = response.json()
        self.save()

        self.do_postproc()

    def do_postproc(self):
        tally = self.tally
        options = self.question.options.all()

        opts = []
        for opt in options:
            if isinstance(tally, list):
                votes = tally.count(opt.number)
            else:
                votes = 0
            opts.append({
                'option': opt.option,
                'number': opt.number,
                'votes': votes
            })

        data = { 'type': 'IDENTITY', 'options': opts }
        postp = mods.post('postproc', json=data)

        self.postproc = postp
        self.save()

    def __str__(self):
        return self.name

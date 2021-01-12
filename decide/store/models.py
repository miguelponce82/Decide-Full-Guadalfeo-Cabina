from django.db import models
from base.models import BigBigField
from django.contrib.postgres.fields import JSONField


class Vote(models.Model):
    voting_id = models.PositiveIntegerField()
    voter_id = models.PositiveIntegerField()

    data = JSONField(encoder=None)

    voted = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{}: {}'.format(self.voting_id, self.voter_id)

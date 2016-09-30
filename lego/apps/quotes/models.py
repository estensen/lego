from django.db import models

from lego.apps.content.models import Content
from lego.utils.models import BasisModel


class Quote(BasisModel, Content):

    source = models.CharField(max_length=255)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def approve(self):
        self.approved = True
        self.save()

    def unapprove(self):
        self.approved = False
        self.save()
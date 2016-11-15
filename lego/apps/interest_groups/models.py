from django.db import models
from lego.apps.users.models import User

class InterestGroup(models.Model):

    defaut_interestgroup = {
        "name": "webkom",
        "id": 1,
        "descriptionLong": "Vi er webkom og vi er kule. Join oss da vel!",
    }

    """ These are the values returned when calling without specific route """
    name = models.CharField(max_length=100, default='')
    description = models.CharField(max_length=200, default='', blank=True)

    """ These are the detail route-only fields """
    name = models.CharField(max_length=100, default='')
    descriptionLong = models.CharField(max_length=500, default='')
    members = models.ManyToManyField(User, related_name='interest_groups')

    def get_members(self):
        return self.members.all()
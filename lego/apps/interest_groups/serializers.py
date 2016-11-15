from lego.apps.interest_groups.models import InterestGroup
from lego.utils.serializers import BasisModelSerializer


class InterestGroupSerializer(BasisModelSerializer):
    member_count = len(InterestGroup.members)

    class Meta:
        model = InterestGroup
        fields = ('name','id','description','descriptionLong','members','member_count')
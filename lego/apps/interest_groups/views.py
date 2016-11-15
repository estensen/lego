from rest_framework import viewsets

from lego.apps.interest_groups.models import InterestGroup
from lego.apps.interest_groups.serializers import InterestGroupSerializer, InterestGroupDetailedSerializer


class InterestGroupViewSet(viewsets.ModelViewSet):
    queryset = InterestGroup.objects.all()

    def get_serializer_class(self):
        if self.action in ['retrieve', 'destroy']:
            return InterestGroupDetailedSerializer

        return InterestGroupSerializer


# Fiks dette når du skal legge til interessegrupper
'''
class SemesterStatusViewSet(viewsets.ModelViewSet):
    queryset = SemesterStatus.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SemesterStatusCreateAndUpdateSerializer

        return SemesterStatusReadSerializer

    def get_queryset(self):

        if self.action in ['retrieve', 'destroy']:
            company_id = self.kwargs.select_related('company').get('company_pk', None)
            return SemesterStatus.objects.filter(company=company_id)
        return self.queryset
'''
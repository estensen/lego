from rest_framework import viewsets

from lego.permissions.filters import ObjectPermissionsFilter
from lego.permissions.object_permissions import ObjectPermissions
from lego.permissions.tests.models import TestModel
from lego.permissions.tests.serializer import TestSerializer


class TestViewSet(viewsets.ModelViewSet):
    queryset = TestModel.objects.all()
    serializer_class = TestSerializer
    filter_backends = (ObjectPermissionsFilter,)
    permission_classes = (ObjectPermissions,)

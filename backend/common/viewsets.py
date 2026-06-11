from rest_framework import viewsets
from . import models
from . import serializers

class CountryViewSet(viewsets.ModelViewSet):
    queryset = models.Countries.objects.all()
    serializer_class = serializers.CountryViewSerializer

class StateViewSet(viewsets.ModelViewSet):
    queryset = models.States.objects.all()
    serializer_class = serializers.StateViewSerializer

class CityViewSet(viewsets.ModelViewSet):
    queryset = models.Cities.objects.all()
    serializer_class = serializers.CityViewSerializer
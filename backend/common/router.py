from .viewsets import CountryViewSet, StateViewSet, CityViewSet
from rest_framework import routers

router = routers.DefaultRouter()
router.register('country', CountryViewSet)
router.register('state', StateViewSet)
router.register('city', CityViewSet)

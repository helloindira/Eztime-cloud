from django.urls import path, include
from MasterTable.views import *
from rest_framework import routers
from django.conf import settings
from django.conf.urls.static import static
from . import views




app_name = 'Main'


router = routers.DefaultRouter()


urlpatterns = [
    path('', include(router.urls)),
    path('role/', RoleAPIView.as_view(),name='ROLE'),
    path('questiontype/', QuestionTypeResponseAPIView.as_view(),name='QUESTIONTYPE'),
]

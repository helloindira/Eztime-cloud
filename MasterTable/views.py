from django.conf import settings
from django.db.models import base
from django.db.utils import IntegrityError
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render
# from requests import api
from rest_framework.response import Response
from requests.api import head, request

from django.utils.decorators import method_decorator
# from accounts.decorator import *
import requests
import random
import json
import inspect
from django.core.mail import message, send_mail, EmailMessage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import Http404
from django.http import HttpResponsePermanentRedirect

from django.http import HttpResponse

from rest_framework.views import APIView
from rest_framework.serializers import Serializer
from .models import *
#import jwt
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework import serializers
from rest_framework import generics,viewsets, status
from django.contrib import auth
# from .serializers import *
from rest_framework import viewsets, status

from rest_framework.authtoken.views import ObtainAuthToken
import time
import datetime
from django.db.models import Sum
import re


from django.views.decorators.csrf import csrf_exempt



class QuestionTypeResponseAPIView(APIView):
    def get(self, request):
        #breakpoint()
        id =self.request.query_params.get('id')
        if id:
            appdata = QuestionType.objects.filter(id=id).values()
            return Response(appdata)
        else:
            appdata = QuestionType.objects.all().values()
            return Response(appdata)



    def post(self, request):
        data = request.data
        name = data.get('name')
        if QuestionType.objects.filter(Q(name=name)).exists():
            return Response("QuestionType Name Already Exists")
        else:
            questiontype=QuestionType.objects.create(name=name)
            response_result = {}
            response = {}
            response_result['result'] = {
                        'result': {'data': 'Data Added Sucessfully',
                        'questiontype_id':questiontype.id,
                        'status':'HTTP_200_OK'
                        }}
            return Response(response_result['result'], headers=response,status= status.HTTP_200_OK)
            #var =int(QuestionType.objects.latest('id').id)
            #return Response({"Data For Application, Added Sucessfully":vappcreate})



    def put(self, request):
        data = request.data
        id = data.get('id')
        #name = data.get('name')
        if id:
            data = QuestionType.objects.filter(id=id).update(name=data.get('name'))
            if data:
                    return JsonResponse({'message': 'data Updated Sucessfully.'})
            else:
                response={'message':"Invalid id"}
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        else:
            return JsonResponse({'message': 'Id Required.'})



    def delete(self, request):
        id =self.request.query_params.get('id')
        item = QuestionType.objects.filter(id= id)
        if len(item) > 0:
            item.delete()
            return Response("data Deleted Sucessfully")
        else:
            return Response("Id Required.")

class RoleAPIView(APIView):
    def post(self,request):
        data = request.data
        name = data.get('name')
        description = data.get('description')
        
        
        if data:
            if Role.objects.filter(Q(name=name)).exists():
                return Response({'Error':'User Already Exists'})
            else:
                role=Role.objects.create(name=name,description=description)

            return Response({"Message":"Data Sucessfully Added","Status": "HTTP_201_CREATED"})
        else:
            return Response({"Error":"Data Already Exists","status":"status.HTTP_400_BAD_REQUEST"})



    def get(self,request):
        id = request.query_params.get('id')
        if id:
            data=Role.objects.filter(id=id).values()
            return Response({"Message":data})
        else:
            data=Role.objects.all().values()
            return Response({"MESSAGE": "ALL DATA" , "Status": "HTTP_200_OK", 'DATA': data})

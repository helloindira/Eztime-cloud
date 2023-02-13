from django.conf import settings
from django.http.response import JsonResponse
from rest_framework.response import Response
from requests.api import request
from django.db.models import Q
from django.contrib import auth
from django.contrib.auth import authenticate
from django.db.utils import IntegrityError
from eztimeapp.backends import *
from eztimeapp.decorator import *

from .serializers import *
import random
from .models import *
import time
import datetime
import inspect
from django.core.mail import message, send_mail, EmailMessage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework.views import APIView 
from rest_framework.generics import GenericAPIView
import jwt
from rest_framework import status
from django.utils.decorators import method_decorator
import re
from mimetypes import guess_extension

import base64

class RegistrationApiVew(APIView):
    serializer_class = CustomUserTableSerializers
    queryset = CustomUser.objects.all()

    def post(self,request):
        data = request.data
        response = {}
        u_first_name = data.get('u_first_name')  
        u_last_name = data.get('u_last_name')  
        u_gender = data.get('u_gender')  
        u_marital_status = data.get('u_marital_status')  
        u_phone_no        = data.get('u_phone_no')
        email         = data.get('email')
        password      = data.get('password')
        u_org_code = data.get('org_code')
        u_designation = data.get('u_designation')


        if data:
            if User.objects.filter(Q(username=email)|Q(email=email)).exists():
                return Response({'error':'User Already Exists'})
            else:
                create_user = User.objects.create_user(username=email,email=email,password=password)
                user_create = CustomUser.objects.create(
                    user_created_by_id=create_user.id,
                    u_email=email,
                    u_designation=u_designation,
                    u_phone_no=u_phone_no,
                    u_org_code=u_org_code,
                    u_first_name=u_first_name,
                    u_last_name=u_last_name,
                    u_gender=u_gender,
                    u_marital_status=u_marital_status,
                    )
                auth_token = jwt.encode(
                            {'user_id': create_user.id, 'username': create_user.username, 'email': create_user.email, 'mobile': user_create.u_phone_no}, str(settings.JWT_SECRET_KEY), algorithm="HS256")
                authorization = 'Bearer'+' '+auth_token

                response_result = {}
                response_result['result'] = {
                    'result': {'data': 'Register successful',
                    'user_id': create_user.id,
                    'token':authorization}}
                response['Authorization'] = authorization
                # response['Token-Type']      =   'Bearer'
                response['status'] = status.HTTP_200_OK
                return Response(response_result['result'], headers=response,status= status.HTTP_200_OK)
 
                # return Response({'result':'User Register Successfully'})
        else:
            return Response({'error':'Please fill all the details'})


class LoginView(APIView):
    serializer_class = CustomUserTableSerializers

    def post(self, request):
        response = {}
        data = request.data
        username = data.get('username')
        password = data.get('password')
        
        user_check = User.objects.filter(username= username)
        if user_check:
            user = auth.authenticate(username=username, password=password)
           
            if user:
                custom_user = User.objects.get(id=user.id)
               
                auth_token = jwt.encode(
                    {'user_id': user.id, 'username': user.username, 'email': user.email}, str(settings.JWT_SECRET_KEY), algorithm="HS256")

                serializer = CustomUserTableSerializers(user)
                authorization = 'Bearer'+' '+auth_token
                response_result = {}
                response_result['result'] = {
                    'detail': 'Login successfull',
                    'token':authorization,
                    'user_id': user.id,
                    'status': status.HTTP_200_OK}
                response['Authorization'] = authorization
                response['status'] = status.HTTP_200_OK
                # return Response(response_result['result'], headers=response,status= status.HTTP_200_OK)
 
               
            else:
                header_response = {}
                response['error'] = {'error': {
                    'detail': 'Invalid Username / Password', 'status': status.HTTP_401_UNAUTHORIZED}}
                return Response(response['error'], headers=header_response,status= status.HTTP_401_UNAUTHORIZED)

            return Response(response_result, headers=response,status= status.HTTP_200_OK)
        else:

            response['error'] = {'error': {
                    'detail': 'Invalid Username / Password', 'status': status.HTTP_401_UNAUTHORIZED}}
            return Response(response['error'], status= status.HTTP_401_UNAUTHORIZED)


class ForgotPasswordSendOtp(APIView):

    def post(self, request):
        data = request.data

        username = data.get('username')
        Otp = random.randint(100000, 999999)
        F_Otp = Otp
        if User.objects.filter(Q(username=username)).exists():
            update_otp = CustomUser.objects.filter(u_email=username).update(u_reset_otp=int(Otp))
            print(update_otp,'update_otp')
            pass
        else:
            return Response({'error':{'message':'username doesnot exists'}})
        
        user_check=CustomUser.objects.get(u_email=username)
        email_id=user_check.u_email
        print(email_id,'email_id')
        # if '@' in username:
        message = inspect.cleandoc('''Hi ,\n %s is your OTP to Forgot Password to your eztime account.\nThis OTP is valid for next 10 minutes,
                                \nWith Warm Regards,\nTeam EzTime,
                                ''' % (Otp))
        send_mail(
            'Greetings from EzTime', message
            ,
            'shyam@ekfrazo.in',
            [email_id],

        )
        data_dict = {}
        data_dict["OTP"] = Otp
        return Response({'result':data_dict})
        

class OtpVerificationForgotpass(APIView):

    def post(self, request):
        data = request.data
        otp = data.get('OTP')
        email = data.get('username')
        user_check=CustomUser.objects.get(u_email=email)

        if otp==user_check.u_reset_otp:
            update_otp = CustomUser.objects.filter(u_email=email).update(u_reset_otp=None)
            return Response({'result':{'message': 'OTP matches successfully'}})
        else:
            return Response({'error':{'message': 'Invalid OTP'}})


class ForgotPasswordReset(APIView):

    def post(self, request):
        data = request.data

        username = data.get('username')
        password = data.get('password')
        user_check = User.objects.filter(username= username) 
        if user_check:
            user_data = User.objects.get(username= username)
            user_data.set_password(password)
            user_data.save()
            message= 'Hello!\nYour password has been updated sucessfully. '
            subject= 'Password Updated Sucessfully ' 
            email = EmailMessage(subject, message, to=[user_data.email])
            email.send()
            return Response({'result':{'message': 'Password Updated Sucessfully'}})        
        else:
            return Response({'error':{'message': 'Please Enter Valid username'}})


class ChangePassword(GenericAPIView):
    def post(self,request):
        data         =    request.data
        user_id        =    data.get('user_id')  
        new_password        =    data.get('new_password') 
        old_password        =    data.get('old_password') 
        

        print(data,'dattaaaaa')
        try:
            check_user = User.objects.get(id=user_id)
            if check_user:
                if check_user.check_password(old_password):
                    check_user.set_password(new_password)
                    check_user.save()
                    return Response({'result':'password changed successfully!'})
                else:
                    return Response({
                    'error':{'message':'incorrect old password!',
                    'status_code':status.HTTP_401_UNAUTHORIZED,
                    }},status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response({'error':{'message':'user does not exists!',
                    'status_code':status.HTTP_404_NOT_FOUND,
                    }},status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
                return Response({
                'error':{'message':'user does not exists!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
    

# @method_decorator([AutorizationRequired], name='dispatch')
class OrganizationApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            try:
                all_data = Organization.objects.filter(id=id).values()
                return Response({'result':{'status':'GET by Id','data':all_data}})
            except Organization.DoesNotExist:
                return Response({
                'error':{'message':'Id does not exists!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            all_data = Organization.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        
        data = request.data
        user_ref                        = data.get('user_ref_id')
        org_qr_uniq_id                  = data.get('org_qr_uniq_id')
        org_name                        = data.get('org_name')
        org_email                       = data.get('org_email')
        org_phone                       = data.get('org_phone')
        org_mobile                      = data.get('org_mobile')
        org_fax                         = data.get('org_fax')
        org_website                     = data.get('org_website')
        org_address                     = data.get('org_address')
        org_city                        = data.get('org_city')
        org_state                       = data.get('org_state')
        org_country                     = data.get('org_country')
        org_postal_code                 = data.get('org_postal_code')
        org_profile_updated_status      = data.get('org_profile_updated_status')
        org_default_currency_type       = data.get('org_default_currency_type')
        org_default_timezone            = data.get('org_default_timezone')
        org_status                      = data.get('org_status')
        org_subscription_plan           = data.get('org_subscription_plan')
        # org_logo                        = data.get('org_logo')
        # org_logo_path                   = data.get('org_logo_path')
        # org_logo_base_url               = data.get('org_logo_base_url')

        conctact_person_designation=data.get('conctact_person_designation')
        conctact_person_name=data.get('conctact_person_name')
        conctact_person_email=data.get('conctact_person_email')
        conctact_person_phone_number=data.get('conctact_person_phone_number')
        
        org_logo = data['org_logo']
        base64_data =org_logo
        split_base_url_data=org_logo.split(';base64,')[1]
        imgdata1 = base64.b64decode(split_base_url_data)

        data_split = org_logo.split(';base64,')[0]
        extension_data = re.split(':|;', data_split)[1] 
        guess_extension_data = guess_extension(extension_data)

        filename1 = "/eztime/site/public/media/org_logo/"+org_name+guess_extension_data
        # filename1 = "D:/EzTime/eztimeproject/media/photo/"+name+'.png'
        fname1 = '/org_logo/'+org_name+guess_extension_data
        ss=  open(filename1, 'wb')
        print(ss)
        ss.write(imgdata1)
        ss.close()   

        
        

        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



       
        try:
            
            check_data = Organization.objects.create(
            user_ref_id=user_ref,
            org_qr_uniq_id=org_qr_uniq_id,
            org_name=org_name,
            org_email=org_email,
            org_phone=org_phone,
            org_mobile=org_mobile,
            org_fax=org_fax,
            org_website=org_website,
            org_address=org_address,
            org_city=org_city,
            org_state=org_state,
            org_country=org_country,
            org_postal_code=org_postal_code,
            org_profile_updated_status=org_profile_updated_status,
            org_default_currency_type=org_default_currency_type,
            org_default_timezone=org_default_timezone,
            org_status=org_status,
            org_subscription_plan=org_subscription_plan,
            org_logo=fname1,
            # org_logo_path=org_logo_path,
            base64=base64_data,
            conctact_person_designation=conctact_person_designation,
            conctact_person_name=conctact_person_name,
            conctact_person_email=conctact_person_email,
            conctact_person_phone_number=conctact_person_phone_number,)

            if org_logo:
                    check_data.org_logo_path = 'https://eztime.thestorywallcafe.com/media/org_logo/'+ (str(check_data.org_logo)).split('org_logo/')[1]
                    # check_data.file_attachment_path = 'http://127.0.0.1:8000/media/file_attachment/'+ (str(check_data.file_attachment)).split('file_attachment/')[1]
                    check_data.save()

            posts = Organization.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})




        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        
        data = request.data
        user_ref                        = data.get('user_ref_id')
        org_qr_uniq_id                  = data.get('org_qr_uniq_id')
        org_name                        = data.get('org_name')
        org_email                       = data.get('org_email')
        org_phone                       = data.get('org_phone')
        org_mobile                      = data.get('org_mobile')
        org_fax                         = data.get('org_fax')
        org_website                     = data.get('org_website')
        org_address                     = data.get('org_address')
        org_city                        = data.get('org_city')
        org_state                       = data.get('org_state')
        org_country                     = data.get('org_country')
        org_postal_code                 = data.get('org_postal_code')
        org_profile_updated_status      = data.get('org_profile_updated_status')
        org_default_currency_type       = data.get('org_default_currency_type')
        org_default_timezone            = data.get('org_default_timezone')
        org_status                      = data.get('org_status')
        org_subscription_plan           = data.get('org_subscription_plan')
        # org_logo                        = data.get('org_logo')
        # org_logo_path                   = data.get('org_logo_path')
        # org_logo_base_url               = data.get('org_logo_base_url')
        conctact_person_designation=data.get('conctact_person_designation')
        conctact_person_name=data.get('conctact_person_name')
        conctact_person_email=data.get('conctact_person_email')
        conctact_person_phone_number=data.get('conctact_person_phone_number')
        
        org_logo = data['org_logo']
        print(org_logo,'Attttttttttttttttttttt')
        if org_logo == '':
            print('in if nulll looopp')
            try:
                Organization.objects.filter(id=pk).update(
                        user_ref_id=user_ref,
                        org_qr_uniq_id=org_qr_uniq_id,
                        org_name=org_name,
                        org_email=org_email,
                        org_phone=org_phone,
                        org_mobile=org_mobile,
                        org_fax=org_fax,
                        org_website=org_website,
                        org_address=org_address,
                        org_city=org_city,
                        org_state=org_state,
                        org_country=org_country,
                        org_postal_code=org_postal_code,
                        org_profile_updated_status=org_profile_updated_status,
                        org_default_currency_type=org_default_currency_type,
                        org_default_timezone=org_default_timezone,
                        org_status=org_status,
                        org_subscription_plan=org_subscription_plan,
                        # org_logo=fname1,
                        # org_logo_path=org_logo_path,
                        # base64=base64_data,
                        conctact_person_designation=conctact_person_designation,
                        conctact_person_name=conctact_person_name,
                        conctact_person_email=conctact_person_email,
                        conctact_person_phone_number=conctact_person_phone_number,
                )


                return Response({'result':{'status':'Updated'}})
            except IntegrityError as e:
                error_message = e.args
                return Response({
                'error':{'message':'DB error!',
                'detail':error_message,
                'status_code':status.HTTP_400_BAD_REQUEST,
                }},status=status.HTTP_400_BAD_REQUEST)
                





        base64_data=org_logo
        split_base_url_data=org_logo.split(';base64,')[1]
        imgdata1 = base64.b64decode(split_base_url_data)

        data_split = org_logo.split(';base64,')[0]
        extension_data = re.split(':|;', data_split)[1] 
        guess_extension_data = guess_extension(extension_data)

        filename1 = "/eztime/site/public/media/org_logo/"+org_name+guess_extension_data
        # filename1 = "D:/EzTime/eztimeproject/media/photo/"+name+'.png'
        fname1 = '/org_logo/'+org_name+guess_extension_data
        ss=  open(filename1, 'wb')
        print(ss)
        ss.write(imgdata1)
        ss.close()   

       
        try:
            Organization.objects.filter(id=pk).update(
                user_ref_id=user_ref,
                org_qr_uniq_id=org_qr_uniq_id,
                org_name=org_name,
                org_email=org_email,
                org_phone=org_phone,
                org_mobile=org_mobile,
                org_fax=org_fax,
                org_website=org_website,
                org_address=org_address,
                org_city=org_city,
                org_state=org_state,
                org_country=org_country,
                org_postal_code=org_postal_code,
                org_profile_updated_status=org_profile_updated_status,
                org_default_currency_type=org_default_currency_type,
                org_default_timezone=org_default_timezone,
                org_status=org_status,
                org_subscription_plan=org_subscription_plan,
                org_logo=fname1,
                # org_logo_path=org_logo_path,
                base64=base64_data,
                conctact_person_designation=conctact_person_designation,
            conctact_person_name=conctact_person_name,
            conctact_person_email=conctact_person_email,
            conctact_person_phone_number=conctact_person_phone_number,
                )
            check_data = Organization.objects.get(id=pk)
            if org_logo:
                    check_data.org_logo_path = 'https://eztime.thestorywallcafe.com/media/org_logo/'+ (str(check_data.org_logo)).split('org_logo/')[1]
                    # check_data.file_attachment_path = 'http://127.0.0.1:8000/media/file_attachment/'+ (str(check_data.file_attachment)).split('file_attachment/')[1]
                    check_data.save()


            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
    

    def delete(self,request,pk):
        CheckAuth(request)
        test = (0,{})
        all_values = Organization.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})


# @method_decorator([AutorizationRequired], name='dispatch')
class TypeOfIndustriesApiView(APIView):
    def get(self,request):
        
        id = request.query_params.get('id')
        if id:
            try:
                all_data = TypeOfIndustries.objects.filter(id=id).values()
                return Response({'result':{'status':'GET by Id','data':all_data}})
            except Organization.DoesNotExist:
                return Response({
                'error':{'message':'Id does not exists!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            all_data = TypeOfIndustries.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        
        data = request.data
        
        org_ref                 = data.get('org_ref_id')
        toi_title               = data.get('toi_title')
        toi_description         = data.get('toi_description')
        toi_status              = data.get('toi_status')
        toi_type                = data.get('toi_type')
        

        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



       
        try:
            TypeOfIndustries.objects.create(
                org_ref_id=org_ref,
                toi_title=toi_title,
                toi_description=toi_description,
                toi_status=toi_status,
                toi_type=toi_type
                                            )


            posts = TypeOfIndustries.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        
        data = request.data
        
        org_ref                 = data.get('org_ref_id')
        toi_title               = data.get('toi_title')
        toi_description         = data.get('toi_description')
        toi_status              = data.get('toi_status')
        toi_type                = data.get('toi_type')
        
        
        try:
            TypeOfIndustries.objects.filter(id=pk).update(
                org_ref_id=org_ref,
                toi_title=toi_title,
                toi_description=toi_description,
                toi_status=toi_status,
                toi_type=toi_type
                )
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
        
        test = (0,{})
            
        all_values = TypeOfIndustries.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})



# @method_decorator([AutorizationRequired], name='dispatch')
class ClientsApiView(APIView):
    def get(self,request):
        
        id = request.query_params.get('id')
        if id:
            try:
                all_data = Clients.objects.filter(id=id).values()
                return Response({'result':{'status':'GET by Id','data':all_data}})
            except Organization.DoesNotExist:
                return Response({
                'error':{'message':'Id does not exists!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            all_data = Clients.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        
        data = request.data
        org_ref                     = data.get('org_ref_id')
        user_ref                    = data.get('user_ref_id')
        toi_ref                     = data.get('toi_ref_id')
        c_name                      = data.get('c_name')
        c_code                      = data.get('c_code')
        c_address                   = data.get('c_address')
        c_type                      = data.get('c_type')
        c_contact_person            = data.get('c_contact_person')
        c_contact_person_email_id   = data.get('c_contact_person_email_id')
        c_contact_person_phone_no   = data.get('c_contact_person_phone_no')
        c_satus                     = data.get('c_satus')
        project = data.get('project')



        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            Clients.objects.create(
                org_ref_id=org_ref,
                user_ref_id=user_ref,
                toi_ref_id=toi_ref,
                c_name=c_name,
                c_code=c_code,
                c_address=c_address,
                c_type=c_type,
                c_contact_person=c_contact_person,
                c_contact_person_email_id=c_contact_person_email_id,
                c_contact_person_phone_no=c_contact_person_phone_no,
                c_satus=c_satus,
                project=project
                                )


            posts = Clients.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        
        data = request.data
        org_ref                     = data.get('org_ref_id')
        user_ref                    = data.get('user_ref_id')
        toi_ref                     = data.get('toi_ref_id')
        c_name                      = data.get('c_name')
        c_code                      = data.get('c_code')
        c_address                   = data.get('c_address')
        c_type                      = data.get('c_type')
        c_contact_person            = data.get('c_contact_person')
        c_contact_person_email_id   = data.get('c_contact_person_email_id')
        c_contact_person_phone_no   = data.get('c_contact_person_phone_no')
        c_satus                     = data.get('c_satus')
        project=data.get('project')

        
       
        try:

            Clients.objects.filter(id=pk).update(
                org_ref_id=org_ref,
                user_ref_id=user_ref,
                toi_ref_id=toi_ref,
                c_name=c_name,
                c_code=c_code,
                c_address=c_address,
                c_type=c_type,
                c_contact_person=c_contact_person,
                c_contact_person_email_id=c_contact_person_email_id,
                c_contact_person_phone_no=c_contact_person_phone_no,
                c_satus=c_satus,
                project=project
                                )

            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
        
        test = (0,{})
            
        all_values = Clients.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})


# @method_decorator([AutorizationRequired], name='dispatch')
class OrgPeopleGroupView(APIView):
    def get(self,request):
        
        id = request.query_params.get('id')
        if id:
            try:
                all_data = OrgPeopleGroup.objects.filter(id=id).values()
                return Response({'result':{'status':'GET by Id','data':all_data}})
            except Organization.DoesNotExist:
                return Response({
                'error':{'message':'Id does not exists!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            all_data = OrgPeopleGroup.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        
        data = request.data
        user_ref            = data.get('user_ref_id')
        org_ref             = data.get('org_ref_id')
        opg_group_name      = data.get('opg_group_name')
        opg_status          = data.get('opg_status')


        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            OrgPeopleGroup.objects.create(
                user_ref_id=user_ref,
                org_ref_id=org_ref,
                opg_group_name=opg_group_name,
                opg_status=opg_status
            )


            posts = OrgPeopleGroup.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        
        data = request.data
        user_ref            = data.get('user_ref_id')
        org_ref             = data.get('org_ref_id')
        opg_group_name      = data.get('opg_group_name')
        opg_status          = data.get('opg_status')

        
        
        try:

            OrgPeopleGroup.objects.filter(id=pk).update(
                user_ref_id=user_ref,
                org_ref_id=org_ref,
                opg_group_name=opg_group_name,
                opg_status=opg_status
            )

            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
        
        test = (0,{})
            
        all_values = OrgPeopleGroup.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})

# @method_decorator([authorization_required], name='dispatch')
class OrganizationDepartmentView(APIView):
    def get(self,request):
        
        id = request.query_params.get('id')
        if id:
            try:
                all_data = OrganizationDepartment.objects.filter(id=id).values()
                return Response({'result':{'status':'GET by Id','data':all_data}})
            except Organization.DoesNotExist:
                return Response({
                'error':{'message':'Id does not exists!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            all_data = OrganizationDepartment.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        
        data = request.data
        org_ref                 = data.get('org_ref_id')
        od_added_by_ref_user    = data.get('od_added_by_ref_user_id')
        od_name                 = data.get('od_name')
        od_status               = data.get('od_status')
        

        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            OrganizationDepartment.objects.create(org_ref_id=org_ref,
                                                od_added_by_ref_user_id=od_added_by_ref_user,
                                                od_name=od_name,
                                                od_status=od_status)

            posts = OrganizationDepartment.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def put(self,request,pk):
        
        data = request.data
        org_ref                 = data.get('org_ref_id')
        od_added_by_ref_user    = data.get('od_added_by_ref_user_id')
        od_name                 = data.get('od_name')
        od_status               = data.get('od_status')
        
        
        try:
            OrganizationDepartment.objects.filter(id=pk).update(
                org_ref_id=org_ref,
                od_added_by_ref_user_id=od_added_by_ref_user,
                od_name=od_name,
                od_status=od_status
                                                )

            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def delete(self,request,pk):
        
        test = (0,{})
            
        all_values = OrganizationDepartment.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})


# @method_decorator([AutorizationRequired], name='dispatch')
class ClientsDMS(APIView):
    def get(self,request):
        
        id = request.query_params.get('id')
        if id:
            try:
                all_data = ClientsDMS.objects.filter(id=id).values()
                return Response({'result':{'status':'GET by Id','data':all_data}})
            except Organization.DoesNotExist:
                return Response({
                'error':{'message':'Id does not exists!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            all_data = ClientsDms.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        
        data = request.data
        ref_org             =data.get('ref_org_id')
        cdms_added_ref_user =data.get('cdms_added_ref_user_id')
        c_ref               =data.get('c_ref_id')
        cdms_filename       =data.get('cdms_filename')
        cdms_file_path      =data.get('cdms_file_path')
        cdms_base_url       =data.get('cdms_base_url')
        cdms_file_ref_name  =data.get('cdms_file_ref_name')
        cdms_status         =data.get('cdms_status')

        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            ClientsDms.objects.create(
                ref_org_id=ref_org,
                cdms_added_ref_user_id=cdms_added_ref_user,
                c_ref_id=c_ref,
                cdms_filename=cdms_filename,
                cdms_file_path=cdms_file_path,
                cdms_base_url=cdms_base_url,
                cdms_file_ref_name=cdms_file_ref_name,
                cdms_status=cdms_status
                )

            posts = ClientsDms.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        
        data = request.data
        ref_org             =data.get('ref_org_id')
        cdms_added_ref_user =data.get('cdms_added_ref_user_id')
        c_ref               =data.get('c_ref_id')
        cdms_filename       =data.get('cdms_filename')
        cdms_file_path      =data.get('cdms_file_path')
        cdms_base_url       =data.get('cdms_base_url')
        cdms_file_ref_name  =data.get('cdms_file_ref_name')
        cdms_status         =data.get('cdms_status')
        
        
        try:
            ClientsDms.objects.filter(id=pk).update(ref_org_id=ref_org,
                                                                cdms_added_ref_user_id=cdms_added_ref_user,
                                                                c_ref_id=c_ref,
                                                                cdms_filename=cdms_filename,
                                                                cdms_file_path=cdms_file_path,
                                                                cdms_base_url=cdms_base_url,
                                                                cdms_file_ref_name=cdms_file_ref_name,
                                                                cdms_status=cdms_status)

            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
        
        test = (0,{})
            
        all_values = ClientsDMS.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})



# @method_decorator([AutorizationRequired], name='dispatch')
class OrganizationCostCentersView(APIView):
    def get(self,request):
        
        id = request.query_params.get('id')
        if id:
            try:
                all_data = OrganizationCostCenters.objects.filter(id=id).values()
                return Response({'result':{'status':'GET by Id','data':all_data}})
            except Organization.DoesNotExist:
                return Response({
                'error':{'message':'Id does not exists!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            all_data = OrganizationCostCenters.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        
        data = request.data
        org_ref                 = data.get('org_ref_id')
        occ_added_by_ref_user   = data.get('occ_added_by_ref_user_id')
        occ_cost_center_name    = data.get('occ_cost_center_name')
        occ_leave_mgmt_status   = data.get('occ_leave_mgmt_status')
        occ_currency_type       = data.get('occ_currency_type')
        occ_status              = data.get('occ_status')

        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            OrganizationCostCenters.objects.create(org_ref_id=org_ref,
                                                    occ_added_by_ref_user_id=occ_added_by_ref_user,
                                                    occ_cost_center_name=occ_cost_center_name,
                                                    occ_leave_mgmt_status=occ_leave_mgmt_status,
                                                    occ_currency_type=occ_currency_type,
                                                    occ_status=occ_status)

            posts = OrganizationCostCenters.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def put(self,request,pk):
        
        data = request.data
        org_ref                 = data.get('org_ref_id')
        occ_added_by_ref_user   = data.get('occ_added_by_ref_user_id')
        occ_cost_center_name    = data.get('occ_cost_center_name')
        occ_leave_mgmt_status   = data.get('occ_leave_mgmt_status')
        occ_currency_type       = data.get('occ_currency_type')
        occ_status              = data.get('occ_status')
        
       
        try:
            OrganizationCostCenters.objects.filter(id=pk).update(org_ref_id=org_ref,
                                                    occ_added_by_ref_user_id=occ_added_by_ref_user,
                                                    occ_cost_center_name=occ_cost_center_name,
                                                    occ_leave_mgmt_status=occ_leave_mgmt_status,
                                                    occ_currency_type=occ_currency_type,
                                                    occ_status=occ_status)

            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def delete(self,request,pk):
        
        test = (0,{})
            
        all_values = OrganizationCostCenters.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})


# @method_decorator([AutorizationRequired], name='dispatch')
class ClientsOtherContactDetailsView(APIView):
    def get(self,request):
        
        id = request.query_params.get('id')
        if id:
            try:
                all_data = ClientsOtherContactDetails.objects.filter(id=id).values()
                return Response({'result':{'status':'GET by Id','data':all_data}})
            except Organization.DoesNotExist:
                return Response({
                'error':{'message':'Id does not exists!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            all_data = ClientsOtherContactDetails.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        
        data = request.data
        c_ref                       = data.get('c_ref_id')
        org_ref                     = data.get('org_ref_id')
        cocd_added_by_ref_user      = data.get('cocd_added_by_ref_user_id')
        cocd_name                   = data.get('cocd_name')
        cocd_phone                  = data.get('cocd_phone')
        cocd_email                  = data.get('cocd_email')
        cocd_satus                  = data.get('cocd_satus')
        

        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            ClientsOtherContactDetails.objects.create(c_ref_id=c_ref,
                                                    org_ref_id=org_ref,
                                                    cocd_added_by_ref_user_id=cocd_added_by_ref_user,
                                                    cocd_name=cocd_name,
                                                    cocd_phone=cocd_phone,
                                                    cocd_email=cocd_email,
                                                    cocd_satus=cocd_satus)

            posts = ClientsOtherContactDetails.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def put(self,request,pk):
        
        data = request.data
        c_ref                       = data.get('c_ref_id')
        org_ref                     = data.get('org_ref_id')
        cocd_added_by_ref_user      = data.get('cocd_added_by_ref_user_id')
        cocd_name                   = data.get('cocd_name')
        cocd_phone                  = data.get('cocd_phone')
        cocd_email                  = data.get('cocd_email')
        cocd_satus                  = data.get('cocd_satus')
        
        
        try:
            ClientsOtherContactDetails.objects.filter(id=pk).update(c_ref_id=c_ref,
                                                    org_ref_id=org_ref,
                                                    cocd_added_by_ref_user_id=cocd_added_by_ref_user,
                                                    cocd_name=cocd_name,
                                                    cocd_phone=cocd_phone,
                                                    cocd_email=cocd_email,
                                                    cocd_satus=cocd_satus)

            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
                

    def delete(self,request,pk):
        
        test = (0,{})
            
        all_values = ClientsOtherContactDetails.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})



# @method_decorator([AutorizationRequired], name='dispatch')
class OrganizationRolesView(APIView):
    def get(self,request):
        
        id = request.query_params.get('id')
        if id:
            try:
                all_data = OrganizationRoles.objects.filter(id=id).values()
                return Response({'result':{'status':'GET by Id','data':all_data}})
            except Organization.DoesNotExist:
                return Response({
                'error':{'message':'Id does not exists!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            all_data = OrganizationRoles.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        
        data = request.data
        org_ref = data.get('org_ref_id')
        or_added_by_ref_user= data.get('or_added_by_ref_user_id')
        or_name= data.get('or_name')
        or_description= data.get('or_description')
        or_priority= data.get('or_priority')
        or_status= data.get('or_status')
        or_type= data.get('or_type')
        or_permission= data.get('or_permission')

        

        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            OrganizationRoles.objects.create(org_ref_id=org_ref,
                                            or_added_by_ref_user_id=or_added_by_ref_user,
                                            or_name=or_name,
                                            or_description=or_description,
                                            or_priority=or_priority,
                                            or_status=or_status,
                                            or_type=or_type,
                                            or_permission=or_permission)

            posts = OrganizationRoles.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        
        data = request.data
        org_ref = data.get('org_ref_id')
        or_added_by_ref_user= data.get('or_added_by_ref_user_id')
        or_name= data.get('or_name')
        or_description= data.get('or_description')
        or_priority= data.get('or_priority')
        or_status= data.get('or_status')
        or_type= data.get('or_type')
        or_permission= data.get('or_permission')
        
        
        try:
            OrganizationRoles.objects.filter(id=pk).update(org_ref_id=org_ref,
                                                            or_added_by_ref_user_id=or_added_by_ref_user,
                                                            or_name=or_name,
                                                            or_description=or_description,
                                                            or_priority=or_priority,
                                                            or_status=or_status,
                                                            or_type=or_type,
                                                            or_permission=or_permission)

            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
        
        test = (0,{})
            
        all_values = OrganizationRoles.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})



# ! ------------------ project---------------

# @method_decorator([AutorizationRequired], name='dispatch')
class ProjectsAPIView(APIView):
    def get(self,request):
        
        id = request.query_params.get('id')
        if id:
            try:
                all_data = Projects.objects.filter(id=id).values()
                return Response({'result':{'status':'GET by Id','data':all_data}})
            except Organization.DoesNotExist:
                return Response({
                'error':{'message':'Id does not exists!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            all_data = Projects.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        
        data = request.data
        org_ref                  = data.get('org_ref_id')
        user_ref                 = data.get('user_ref_id')
        reporting_manager_ref    = data.get('reporting_manager_ref_id')
        approve_manager_ref      = data.get('approve_manager_ref_id')
        opg_ref                  = data.get('opg_ref_id')
        c_ref                    = data.get('c_ref_id')
        p_code                   = data.get('p_code')
        p_name                   = data.get('p_name')
        p_people_type            = data.get('p_people_type')
        people_ref               = data.get('people_ref_id')
        p_description            = data.get('p_description')

        psd             = data.get('p_start_date')
        pcd           = data.get('p_closure_date')

        p_estimated_hours        = data.get('p_estimated_hours')
        p_estimated_cost         = data.get('p_estimated_cost')
        pc_ref                   = data.get('pc_ref_id')
        p_task_checklist_status  = data.get('p_task_checklist_status')
        p_status                 = data.get('p_status')
        p_activation_status      = data.get('p_activation_status')


        p_start_date = time.mktime(datetime.datetime.strptime(psd, "%d/%m/%Y").timetuple())
        p_closure_date = time.mktime(datetime.datetime.strptime(pcd, "%d/%m/%Y").timetuple())

        
        

        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        try:
            Projects.objects.create(
                p_code=p_code,
                org_ref_id   =   org_ref,
                opg_ref_id   =opg_ref,
                user_ref_id  =   user_ref,
                c_ref_id  =   c_ref,
                reporting_manager_ref_id =reporting_manager_ref,
                approve_manager_ref_id   =approve_manager_ref,
                pc_ref_id   =pc_ref ,
                p_name  =   p_name,
                p_people_type =p_people_type,
                people_ref_id        =people_ref,
                p_description     =p_description,
                p_start_date     =p_start_date,
                p_closure_date         =p_closure_date,
                p_estimated_hours =p_estimated_hours,
                p_estimated_cost   =p_estimated_cost,
                p_task_checklist_status =p_task_checklist_status,
                p_status =p_status,
                p_activation_status =p_activation_status
                )


            posts = Projects.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        
        data = request.data
        org_ref                  = data.get('org_ref_id')
        user_ref                 = data.get('user_ref_id')
        reporting_manager_ref    = data.get('reporting_manager_ref_id')
        approve_manager_ref      = data.get('approve_manager_ref_id')
        opg_ref                  = data.get('opg_ref_id')
        c_ref                    = data.get('c_ref_id')
        p_code                   = data.get('p_code')
        p_name                   = data.get('p_name')
        p_people_type            = data.get('p_people_type')
        people_ref               = data.get('people_ref')
        p_description            = data.get('p_description')


        psd             = data.get('p_start_date')
        pcd           = data.get('p_closure_date')


        p_estimated_hours        = data.get('p_estimated_hours')
        p_estimated_cost         = data.get('p_estimated_cost')
        pc_ref                   = data.get('pc_ref_id')
        p_task_checklist_status  = data.get('p_task_checklist_status')
        p_status                 = data.get('p_status')
        p_activation_status      = data.get('p_activation_status')
        p_c_date                 = data.get('p_c_date')
        p_m_date                 = data.get('p_m_date')


        p_start_date = time.mktime(datetime.datetime.strptime(psd, "%d/%m/%Y").timetuple())
        p_closure_date = time.mktime(datetime.datetime.strptime(pcd, "%d/%m/%Y").timetuple())


       
        

        
        try:
            Projects.objects.filter(id=pk).update(p_code=p_code,
                                                org_ref_id              =   org_ref,
                                                opg_ref_id             =opg_ref,
                                                user_ref_id             =   user_ref,
                                                c_ref_id                =   c_ref,
                                                reporting_manager_ref_id =reporting_manager_ref,
                                                approve_manager_ref_id        =approve_manager_ref,
                                                pc_ref_id                  =pc_ref ,
                                                p_name                  =   p_name,
                                                p_people_type          =p_people_type,
                                                people_ref             =people_ref,
                                                p_description          =p_description,
                                                p_start_date           =p_start_date,
                                                p_closure_date         =p_closure_date,
                                                p_estimated_hours      =p_estimated_hours,
                                                p_estimated_cost        =p_estimated_cost,
                                                p_task_checklist_status      =p_task_checklist_status,
                                                p_status                    =p_status,
                                                p_activation_status           =p_activation_status
                                            )
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
        
        test = (0,{})
            
        all_values = Projects.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})

# @method_decorator([AutorizationRequired], name='dispatch')
class TaskProjectCategoriesApiView(APIView):
    def get(self,request):
        
        id = request.query_params.get('id')
        if id:
            try:
                all_data = TaskProjectCategories.objects.filter(id=id).values()
                return Response({'result':{'status':'GET by Id','data':all_data}})
            except Organization.DoesNotExist:
                return Response({
                'error':{'message':'Id does not exists!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            all_data = TaskProjectCategories.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        
        data = request.data
        pc_ref                  = data.get('pc_ref_id')
        p_ref                   = data.get('p_ref_id')
        org_ref                 = data.get('org_ref_id')
        tpc_added_by_ref_user   = data.get('tpc_added_by_ref_user_id')
        tpc_name                = data.get('tpc_name')
        tpc_status              = data.get('tpc_status')
        
        file_attachment = data['file_attachment']
        print(data,'data')
 
        base64_data=file_attachment
        split_base_url_data=file_attachment.split(';base64,')[1]
        # image_general=photo.split(';base64,')[0]
        # image_url = image_general.split()
        imgdata1 = base64.b64decode(split_base_url_data)

        data_split = file_attachment.split(';base64,')[0]
        extension_data = re.split(':|;', data_split)[1] 
        guess_extension_data = guess_extension(extension_data)


        filename1 = "/eztime/site/public/media/file_attachment/"+tpc_name+guess_extension_data
        # filename1 = "D:/EzTime/eztimeproject/media/photo/"+name+'.png'
        fname1 = '/file_attachment/'+tpc_name+guess_extension_data
        ss=  open(filename1, 'wb')
        print(ss)
        ss.write(imgdata1)
        ss.close()   
        

        # file_attachment     = request.FILES['file_attachment']
        # file_attachment_name= data.get('file_attachment_name')
        print(file_attachment,'Attttttttttttttttttttt')
        task_name= data.get('task_name')
        billable_type= data.get('billable_type')
 
        
        
        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:

            

            check_data=TaskProjectCategories.objects.create(
                pc_ref_id = pc_ref,
                p_ref_id =p_ref,
                org_ref_id =org_ref,
                tpc_added_by_ref_user_id=tpc_added_by_ref_user,
                tpc_name= tpc_name,
                tpc_status =tpc_status,
                file_attachment=fname1,
                task_name=task_name,
                billable_type=billable_type,
                base64=base64_data                                                    )

            if file_attachment:
                    check_data.file_attachment_path = 'https://eztime.thestorywallcafe.com/media/file_attachment/'+ (str(check_data.file_attachment)).split('file_attachment/')[1]
                    # check_data.file_attachment_path = 'http://127.0.0.1:8000/media/file_attachment/'+ (str(check_data.file_attachment)).split('file_attachment/')[1]
                    check_data.save()


            posts = TaskProjectCategories.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def put(self,request,pk):
        
        data = request.data
        pc_ref                  = data.get('pc_ref_id')
        p_ref                   = data.get('p_ref_id')
        org_ref                 = data.get('org_ref_id')
        tpc_added_by_ref_user   = data.get('tpc_added_by_ref_user_id')
        tpc_name                = data.get('tpc_name')
        tpc_status              = data.get('tpc_status')
        # file_attachment     = request.FILES['file_attachment']
        # file_attachment_name= data.get('file_attachment_name')
       
        task_name= data.get('task_name')
        billable_type= data.get('billable_type')

        file_attachment = data['file_attachment']
        print(file_attachment,'Attttttttttttttttttttt')
        if file_attachment == '':
            print('in if nulll looopp')
            try:
                TaskProjectCategories.objects.filter(id=pk).update(
                    pc_ref_id = pc_ref,
                    p_ref_id =p_ref,
                    org_ref_id =org_ref,
                    tpc_added_by_ref_user_id=tpc_added_by_ref_user,
                    tpc_name= tpc_name,
                    tpc_status =tpc_status,
                    # file_attachment=fname1,
                    task_name=task_name,
                    billable_type=billable_type,)
                    # base64=base64_data                                                    )

                # if file_attachment:
                #         check_data.file_attachment_path = 'https://eztime.thestorywallcafe.com/media/file_attachment/'+ (str(check_data.file_attachment)).split('file_attachment/')[1]
                #         # check_data.file_attachment_path = 'http://127.0.0.1:8000/media/file_attachment/'+ (str(check_data.file_attachment)).split('file_attachment/')[1]
                #         check_data.save()


                return Response({'result':{'status':'Updated'}})
            except IntegrityError as e:
                error_message = e.args
                return Response({
                'error':{'message':'DB error!',
                'detail':error_message,
                'status_code':status.HTTP_400_BAD_REQUEST,
                }},status=status.HTTP_400_BAD_REQUEST)
                








        base64_data =file_attachment
        split_base_url_data=file_attachment.split(';base64,')[1]
        imgdata1 = base64.b64decode(split_base_url_data)

        data_split = file_attachment.split(';base64,')[0]
        extension_data = re.split(':|;', data_split)[1] 
        guess_extension_data = guess_extension(extension_data)
        
        filename1 = "/eztime/site/public/media/file_attachment/"+tpc_name+guess_extension_data
        # filename1 = "D:/EzTime/eztimeproject/media/photo/"+name+'.png'
        fname1 = '/file_attachment/'+tpc_name+guess_extension_data
        ss=  open(filename1, 'wb')
        print(ss)
        ss.write(imgdata1)
        ss.close()   
        
        
        try:
            TaskProjectCategories.objects.filter(id=pk).update(
                pc_ref_id    = pc_ref,
                p_ref_id                =p_ref,
                org_ref_id              =org_ref,
                tpc_added_by_ref_user_id=tpc_added_by_ref_user,
                tpc_name                = tpc_name,
                tpc_status              =tpc_status,
                file_attachment=fname1,
                task_name=task_name,
                billable_type=billable_type,
                base64=base64_data                                  )
            check_data = TaskProjectCategories.objects.get(id=pk)
            if file_attachment:
                    check_data.file_attachment_path = 'https://eztime.thestorywallcafe.com/media/file_attachment/'+ (str(check_data.file_attachment)).split('file_attachment/')[1]
                    # check_data.file_attachment_path = 'http://127.0.0.1:8000/media/file_attachment/'+ (str(check_data.file_attachment)).split('file_attachment/')[1]
                    check_data.save()

            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
                

    def delete(self,request,pk):
        
        test = (0,{})
        all_values = TaskProjectCategories.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})

# @method_decorator([AutorizationRequired], name='dispatch')
class ProjectCategoriesFilesTemplatesApiView(APIView):
    def get(self,request):
        
        id = request.query_params.get('id')
        if id:
            try:
                all_data = ProjectCategoriesFilesTemplates.objects.filter(id=id).values()
                return Response({'result':{'status':'GET by Id','data':all_data}})
            except Organization.DoesNotExist:
                return Response({
                'error':{'message':'Id does not exists!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            all_data = ProjectCategoriesFilesTemplates.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        
        data = request.data
        
        org_ref                 = data.get('org_ref_id')
        pcft_added_by_ref_user  = data.get('pcft_added_by_ref_user_id')
        ref_pc                  = data.get('ref_pc_id')
        pcft_name               = data.get('pcft_name')
        pcft_filename           = data.get('pcft_filename')
        pcft_file_path          = data.get('pcft_file_path')
        pcft_file_base_url      = data.get('pcft_file_base_url')
        pcft_status             = data.get('pcft_status')
  
        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)

        try:
            ProjectCategoriesFilesTemplates.objects.create(org_ref_id=org_ref ,
                                                            pcft_added_by_ref_user_id=pcft_added_by_ref_user,
                                                            ref_pc_id=ref_pc,
                                                            pcft_name=pcft_name ,
                                                            pcft_filename=pcft_filename,
                                                            pcft_file_path=pcft_file_path,
                                                            pcft_file_base_url=pcft_file_base_url,
                                                            pcft_status=pcft_status
                                                            )


            posts = ProjectCategoriesFilesTemplates.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def put(self,request,pk):
        
        data = request.data
        
        org_ref                 = data.get('org_ref_id')
        pcft_added_by_ref_user  = data.get('pcft_added_by_ref_user_id')
        ref_pc                  = data.get('ref_pc_id')
        pcft_name               = data.get('pcft_name')
        pcft_filename           = data.get('pcft_filename')
        pcft_file_path          = data.get('pcft_file_path')
        pcft_file_base_url      = data.get('pcft_file_base_url')
        pcft_status             = data.get('pcft_status')
        
        
        
        try:
            ProjectCategoriesFilesTemplates.objects.filter(id=pk).update(org_ref_id=org_ref ,
                                                            pcft_added_by_ref_user_id=pcft_added_by_ref_user,
                                                            ref_pc_id=ref_pc,
                                                            pcft_name=pcft_name ,
                                                            pcft_filename=pcft_filename,
                                                            pcft_file_path=pcft_file_path,
                                                            pcft_file_base_url=pcft_file_base_url,
                                                            pcft_status=pcft_status
                                                            )

            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def delete(self,request,pk):
        
        test = (0,{})
            
        all_values = ProjectCategoriesFilesTemplates.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})

# @method_decorator([AutorizationRequired], name='dispatch')
class ProjectStatusMainCategoryApiView(APIView):
    def get(self,request):
        
        id = request.query_params.get('id')
        if id:
            try:
                all_data = ProjectStatusMainCategory.objects.filter(id=id).values()
                return Response({'result':{'status':'GET by Id','data':all_data}})
            except Organization.DoesNotExist:
                return Response({
                'error':{'message':'Id does not exists!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            all_data = ProjectStatusMainCategory.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        
        data = request.data

        psmc_name                = data.get('psmc_name')
        psmc_status              = data.get('psmc_status')
        psmc_color_code          = data.get('psmc_color_code')
        
        
        

        
        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:

            ProjectStatusMainCategory.objects.create(psmc_name=psmc_name,
                                                    psmc_status =psmc_status ,
                                                    psmc_color_code=psmc_color_code
                                                )


            posts = ProjectStatusMainCategory.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
                
            

    def put(self,request,pk):
        
        data = request.data
        
        psmc_name                = data.get('psmc_name')
        psmc_status              = data.get('psmc_status')
        psmc_color_code          = data.get('psmc_color_code')
       
        
        
        try:
            ProjectStatusMainCategory.objects.filter(id=pk).update(psmc_name=psmc_name,
                                                    psmc_status =psmc_status ,
                                                    psmc_color_code=psmc_color_code
                                                )
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def delete(self,request,pk):
        
        test = (0,{})
            
        all_values = ProjectStatusMainCategory.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})


# @method_decorator([AutorizationRequired], name='dispatch')
class ProjectHistoryApiView(APIView):
    def get(self,request):
        
        id = request.query_params.get('id')
        if id:
            all_data = ProjectHistory.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = ProjectHistory.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        
        data = request.data                     
        p_ref                           =data.get('p_ref_id')          
        org_ref                         =data.get('org_ref_id')    
        ph_people_ref_user              =data.get('ph_people_ref_user_id')             
        ph_added_by_ref_user            =data.get('ph_added_by_ref_user_id') 
        c_ref                           =data.get('c_ref_id')
        ph_reporting_manager_ref_user   =data.get('ph_reporting_manager_ref_user_id')               
        ph_approve_manager_ref_user     =data.get('ph_approve_manager_ref_user_id')
        ph_code                         =data.get('ph_code')                
        ph_name                         =data.get('ph_name')    
        ph_people_type                  =data.get('ph_people_type')          
        opg_ref                         =data.get('opg_ref_id')  
        ph_description                  =data.get('ph_description')           
        # ph_start_date                   =data.get('ph_start_date')          
        ph_closure_date                 =data.get('ph_closure_date')           
        ph_estimated_hours              =data.get('ph_estimated_hours')              
        ph_estimated_cost               =data.get('ph_estimated_cost')              
        pc_ref                          =data.get('pc_ref_id')  
        ph_task_checklist_status        =data.get('ph_task_checklist_status')               
        ph_status                       =data.get('ph_status')  
        ph_activation_status            =data.get('ph_activation_status')              
      


        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



       
        try:
            ProjectHistory.objects.create(
                                        p_ref_id=p_ref,
                                        org_ref_id=org_ref,
                                        ph_people_ref_user_id=ph_people_ref_user,
                                        ph_added_by_ref_user=ph_added_by_ref_user,
                                        c_ref_id=c_ref,
                                        opg_ref_id=opg_ref,
                                        ph_reporting_manager_ref_user_id=ph_reporting_manager_ref_user,
                                        ph_approve_manager_ref_user_id=ph_approve_manager_ref_user,
                                        pc_ref_id=pc_ref,
                                        ph_code=ph_code,
                                        ph_name=ph_name,
                                        ph_people_type=ph_people_type,
                                        ph_description=ph_description,
                                        # ph_start_date=ph_start_date,
                                        ph_closure_date=ph_closure_date,
                                        ph_estimated_hours=ph_estimated_hours,
                                        ph_estimated_cost=ph_estimated_cost,
                                        ph_task_checklist_status=ph_task_checklist_status,
                                        ph_status =ph_status ,
                                        ph_activation_status=ph_activation_status
                                        )


            posts = ProjectHistory.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def put(self,request,pk):
        data = request.data                     
        p_ref                           =data.get('p_ref_id')          
        org_ref                         =data.get('org_ref_id')    
        ph_people_ref_user              =data.get('ph_people_ref_user_id')             
        ph_added_by_ref_user            =data.get('ph_added_by_ref_user_id') 
        c_ref                           =data.get('c_ref_id')
        ph_reporting_manager_ref_user   =data.get('ph_reporting_manager_ref_user_id')               
        ph_approve_manager_ref_user     =data.get('ph_approve_manager_ref_user_id')
        ph_code                         =data.get('ph_code')                
        ph_name                         =data.get('ph_name')    
        ph_people_type                  =data.get('ph_people_type')          
        opg_ref                         =data.get('opg_ref_id')  
        ph_description                  =data.get('ph_description')           
        # ph_start_date                   =data.get('ph_start_date')          
        ph_closure_date                 =data.get('ph_closure_date')           
        ph_estimated_hours              =data.get('ph_estimated_hours')              
        ph_estimated_cost               =data.get('ph_estimated_cost')              
        pc_ref                          =data.get('pc_ref_id')  
        ph_task_checklist_status        =data.get('ph_task_checklist_status')               
        ph_status                       =data.get('ph_status')  
        ph_activation_status            =data.get('ph_activation_status')              


        
        try:
            ProjectHistory.objects.filter(id=pk).update(p_ref_id=p_ref,
                                        org_ref_id=org_ref,
                                        ph_people_ref_user_id=ph_people_ref_user,
                                        ph_added_by_ref_user=ph_added_by_ref_user,
                                        c_ref_id=c_ref,
                                        opg_ref_id=opg_ref,
                                        ph_reporting_manager_ref_user_id=ph_reporting_manager_ref_user,
                                        ph_approve_manager_ref_user_id=ph_approve_manager_ref_user,
                                        pc_ref_id=pc_ref,
                                        ph_code=ph_code,
                                        ph_name=ph_name,
                                        ph_people_type=ph_people_type,
                                        ph_description=ph_description,
                                        # ph_start_date=ph_start_date,
                                        ph_closure_date=ph_closure_date,
                                        ph_estimated_hours=ph_estimated_hours,
                                        ph_estimated_cost=ph_estimated_cost,
                                        ph_task_checklist_status=ph_task_checklist_status,
                                        ph_status =ph_status ,
                                        ph_activation_status=ph_activation_status
                                    )
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = ProjectHistory.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})


# @method_decorator([AutorizationRequired], name='dispatch')
class ProjectStatusSubCategoryApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = ProjectStatusSubCategory.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = ProjectStatusSubCategory.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data

        psmc_ref                     =data.get('psmc_ref_id')                               
        org_ref                      =data.get('org_ref_id') 
        pssc_added_by_ref_user       =data.get('pssc_added_by_ref_user_id')              
        pssc_name                    =data.get('pssc_name')                
        pssc_status                  =data.get('pssc_status')  
        color = data.get('color')


        
        

        
        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            ProjectStatusSubCategory.objects.create(psmc_ref_id=psmc_ref,
                                                    org_ref_id=org_ref,
                                                    pssc_added_by_ref_user_id=pssc_added_by_ref_user,
                                                    pssc_name=pssc_name,
                                                    pssc_status=pssc_status,
                                                    color=color
                                            )


            posts = ProjectStatusSubCategory.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def put(self,request,pk):
        data = request.data
        psmc_ref                     =data.get('psmc_ref')                               
        org_ref                      =data.get('org_ref_id') 
        pssc_added_by_ref_user       =data.get('pssc_added_by_ref_user_id')              
        pssc_name                    =data.get('pssc_name')                
        pssc_status                  =data.get('pssc_status')  
        color= data.get('color')
        
        
        
        try:
            ProjectStatusSubCategory.objects.filter(id=pk).update(psmc_ref=psmc_ref,
                                                    org_ref_id=org_ref,
                                                    pssc_added_by_ref_user_id=pssc_added_by_ref_user,
                                                    pssc_name=pssc_name,
                                                    pssc_status=pssc_status,
                                                    color=color
                                )
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = ProjectStatusSubCategory.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})



# @method_decorator([AutorizationRequired], name='dispatch')
class ProjectFilesApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = ProjectFiles.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = ProjectFiles.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data

        org_ref                     =data.get('org_ref_id') 
        pf_added_ref_user           =data.get('pf_added_ref_user_id')              
        p_ref                       =data.get('p_ref_id')                
        pf_filename                 =data.get('pf_filename')  
        pf_file_path                =data.get('pf_file_path')  
        pf_base_url                 =data.get('pf_base_url')    
        pf_status                   =data.get('pf_status')    

        
     
        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)


        try:
            ProjectFiles.objects.create(org_ref_id=org_ref,
                                        pf_added_ref_user_id=pf_added_ref_user,
                                        p_ref_id=p_ref,
                                        pf_filename=pf_filename,
                                        pf_file_path=pf_file_path,
                                        pf_base_url=pf_base_url,
                                        pf_status=pf_status
                                )


            posts = ProjectFiles.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            


    def put(self,request,pk):
        data = request.data
        org_ref                     =data.get('org_ref_id') 
        pf_added_ref_user           =data.get('pf_added_ref_user_id')              
        p_ref                       =data.get('p_ref_id')                
        pf_filename                 =data.get('pf_filename')  
        pf_file_path                =data.get('pf_file_path')  
        pf_base_url                 =data.get('pf_base_url')    
        pf_status                   =data.get('pf_status')    

        
        
        try:
            ProjectFiles.objects.filter(id=pk).update(org_ref_id=org_ref,
                                        pf_added_ref_user_id=pf_added_ref_user,
                                        p_ref_id=p_ref,
                                        pf_filename=pf_filename,
                                        pf_file_path=pf_file_path,
                                        pf_base_url=pf_base_url,
                                        pf_status=pf_status
                                    )
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            


    def delete(self,request,pk):
        test = (0,{})
            
        all_values = ProjectFiles.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})

# @method_decorator([AutorizationRequired], name='dispatch')
class GeoZonesApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = GeoZones.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = GeoZones.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data
        gz_country_code        =data.get('gz_country_code') 
        gz_zone_name           =data.get('gz_zone_name')              
        
        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            GeoZones.objects.create(gz_country_code=gz_country_code,
                                    gz_zone_name=gz_zone_name)


            posts = GeoZones.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def put(self,request,pk):
        data = request.data
        gz_country_code        =data.get('gz_country_code') 
        gz_zone_name           =data.get('gz_zone_name')
        
        
        try:
            GeoZones.objects.filter(id=pk).update(gz_country_code=gz_country_code,
                                    gz_zone_name=gz_zone_name)

            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
                

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = GeoZones.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})


# @method_decorator([AutorizationRequired], name='dispatch')
class GeoTimezonesApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = GeoTimezones.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = GeoTimezones.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data
        gz_ref              =data.get('gz_ref_id') 
        gtm_abbreviation    =data.get('gtm_abbreviation')  
        gtm_time_start      =data.get('gtm_time_start') 
        gtm_gmt_offset      =data.get('gtm_gmt_offset')  
        gtm_dst             =data.get('gtm_dst')              
       
        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            GeoTimezones.objects.create(gz_ref_id=gz_ref,
                                        gtm_abbreviation=gtm_abbreviation,
                                        gtm_time_start=gtm_time_start,
                                        gtm_gmt_offset=gtm_gmt_offset,
                                        gtm_dst=gtm_dst)


            posts = GeoTimezones.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        data = request.data
        data = request.data
        gz_ref              =data.get('gz_ref_id') 
        gtm_abbreviation    =data.get('gtm_abbreviation')  
        # gtm_time_start      =data.get('gtm_time_start') 
        gtm_gmt_offset      =data.get('gtm_gmt_offset')  
        gtm_dst             =data.get('gtm_dst')              
        
        
        
        try:
            GeoTimezones.objects.filter(id=pk).update(gz_ref_id=gz_ref,
                                        gtm_abbreviation=gtm_abbreviation,
                                        # gtm_time_start=gtm_time_start,
                                        gtm_gmt_offset=gtm_gmt_offset,
                                        gtm_dst=gtm_dst)

            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = GeoTimezones.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})

# @method_decorator([AutorizationRequired], name='dispatch')
class GeoCurrenciesApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = GeoCurrencies.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = GeoCurrencies.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data
        geo_cur_code        = data.get('geo_cur_code')
        geo_cur_name        = data.get('geo_cur_name')
        geo_cur_major_name  = data.get('geo_cur_major_name')
        geo_cur_major_symbol= data.get('geo_cur_major_symbol')
        geo_cur_minor_name  = data.get('geo_cur_minor_name')
        geo_cur_minor_symbol= data.get('geo_cur_minor_symbol')
        geo_cur_minor_value = data.get('geo_cur_minor_value')


    
        
        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            GeoCurrencies.objects.create(geo_cur_code=geo_cur_code,
                                        geo_cur_name=geo_cur_name,
                                        geo_cur_major_name=geo_cur_major_name,
                                        geo_cur_major_symbol=geo_cur_major_symbol,
                                        geo_cur_minor_name=geo_cur_minor_name,
                                        geo_cur_minor_symbol=geo_cur_minor_symbol,
                                        geo_cur_minor_value=geo_cur_minor_value
                                )


            posts = GeoCurrencies.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def put(self,request,pk):
        data = request.data
        geo_cur_code        = data.get('geo_cur_code')
        geo_cur_name        = data.get('geo_cur_name')
        geo_cur_major_name  = data.get('geo_cur_major_name')
        geo_cur_major_symbol= data.get('geo_cur_major_symbol')
        geo_cur_minor_name  = data.get('geo_cur_minor_name')
        geo_cur_minor_symbol= data.get('geo_cur_minor_symbol')
        geo_cur_minor_value = data.get('geo_cur_minor_value')
          
        
        
        
        try:
            GeoCurrencies.objects.filter(id=pk).update(geo_cur_code=geo_cur_code,
                                        geo_cur_name=geo_cur_name,
                                        geo_cur_major_name=geo_cur_major_name,
                                        geo_cur_major_symbol=geo_cur_major_symbol,
                                        geo_cur_minor_name=geo_cur_minor_name,
                                        geo_cur_minor_symbol=geo_cur_minor_symbol,
                                        geo_cur_minor_value=geo_cur_minor_value
                                    )


            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
                

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = GeoCurrencies.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})

# @method_decorator([AutorizationRequired], name='dispatch')
class GeoCountriesApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = GeoCountries.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = GeoCountries.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data
        gcounty_name    = data.get('gcounty_name')
        gcounty_cca2    = data.get('gcounty_cca2')
        gcounty_cca3    = data.get('gcounty_cca3')
        gcounty_ccn3    = data.get('gcounty_ccn3')
        gcounty_status  = data.get('gcounty_status')

         
        
        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            GeoCountries.objects.create(gcounty_name=gcounty_name,
                                        gcounty_cca2=gcounty_cca2,
                                        gcounty_cca3=gcounty_cca3,
                                        gcounty_ccn3=gcounty_ccn3,
                                        gcounty_status=gcounty_status
                                )


            posts = GeoCountries.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        data = request.data
        gcounty_name    = data.get('gcounty_name')
        gcounty_cca2    = data.get('gcounty_cca2')
        gcounty_cca3    = data.get('gcounty_cca3')
        gcounty_ccn3    = data.get('gcounty_ccn3')
        gcounty_status  = data.get('gcounty_status')
               
        
        
        
        try:
            GeoCountries.objects.filter(id=pk).update(gcounty_name=gcounty_name,
                                                        gcounty_cca2=gcounty_cca2,
                                                        gcounty_cca3=gcounty_cca3,
                                                        gcounty_ccn3=gcounty_ccn3,
                                                        gcounty_status=gcounty_status
                                                    )


            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = GeoCountries.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})


# @method_decorator([AutorizationRequired], name='dispatch')
class GeoStatesApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = GeoStates.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = GeoStates.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data
        gstate_name     = data.get('gstate_name')
        gcountry_ref    = data.get('gcountry_ref_id')
        gstate_hasc     = data.get('gstate_hasc')
      
        
        
        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



       
        try:
            GeoStates.objects.create(gstate_name=gstate_name,
                                    gcountry_ref_id=gcountry_ref,
                                    gstate_hasc=gstate_hasc
                                )


            posts = GeoStates.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            


    def put(self,request,pk):
        data = request.data
        gstate_name     = data.get('gstate_name')
        gcountry_ref    = data.get('gcountry_ref_id')
        gstate_hasc     = data.get('gstate_hasc')
           
        
        
        
        try:
            GeoStates.objects.filter(id=pk).update(gstate_name=gstate_name,
                                                    gcountry_ref_id=gcountry_ref,
                                                    gstate_hasc=gstate_hasc
                                        )


            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
                


    def delete(self,request,pk):
        test = (0,{})
            
        all_values = GeoStates.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})


# @method_decorator([AutorizationRequired], name='dispatch')
class GeoCitiesApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = GeoCities.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = GeoCities.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data
        ref_gcounty     =data.get('ref_gcounty_id')
        gstate_ref      =data.get('gstate_ref_id')
        zone_ref        =data.get('zone_ref_id')
        gcity_name      =data.get('gcity_name')
        gcity_latitude  =data.get('gcity_latitude')
        gcity_longitude =data.get('gcity_longitude')
      
         
        
        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            GeoCities.objects.create(
                                    ref_gcounty_id=ref_gcounty,
                                    gstate_ref_id=gstate_ref,
                                    zone_ref_id=zone_ref,
                                    gcity_name=gcity_name,
                                    gcity_latitude=gcity_latitude,
                                    gcity_longitude=gcity_longitude
                                )


            posts = GeoCities.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        data = request.data
        ref_gcounty     =data.get('ref_gcounty_id')
        gstate_ref      =data.get('gstate_ref_id')
        zone_ref        =data.get('zone_ref_id')
        gcity_name      =data.get('gcity_name')
        gcity_latitude  =data.get('gcity_latitude')
        gcity_longitude =data.get('gcity_longitude')
            
        
        
        
        try:
            GeoCities.objects.filter(id=pk).update(ref_gcounty_id=ref_gcounty,
                                                    gstate_ref_id=gstate_ref,
                                                    zone_ref_id=zone_ref,
                                                    gcity_name=gcity_name,
                                                    gcity_latitude=gcity_latitude,
                                                    gcity_longitude=gcity_longitude
                                                )


            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = GeoCities.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})



# I have not used any status code here do check this once
# @method_decorator([AutorizationRequired], name='dispatch')
class GeoCountriesCurrenciesApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = GeoCountriesCurrencies.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = GeoCountriesCurrencies.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data
        gcounty_ref      = data.get('gcounty_ref_id')
        geo_cur_ref      = data.get('geo_cur_ref_id')
        

        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        # if GeoCountriesCurrencies.objects.filter(gcounty_ref=gcity_name).exists():
        #     return Response({'error':'gcity_name already exists'})
        # else:
        try:
            GeoCountriesCurrencies.objects.create(gcounty_ref_id=gcounty_ref,
                                                geo_cur_ref_id=geo_cur_ref)


            posts = GeoCountriesCurrencies.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        data = request.data
        gcounty_ref      = data.get('gcounty_ref_id')
        geo_cur_ref      = data.get('geo_cur_ref_id')
        
        # if GeoCountriesCurrencies.objects.filter(gcity_name=gcity_name).exists():
        #     return Response({'error':'gcity_name already exists'})
        # else:
        try:
            GeoCountriesCurrencies.objects.filter(id=pk).update(gcounty_ref_id=gcounty_ref,
                                                geo_cur_ref_id=geo_cur_ref)


            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)


    def delete(self,request,pk):
        all_values = GeoCountriesCurrencies.objects.filter(id=pk).delete()
        return Response({'result':{'status':'deleted'}})


# @method_decorator([AutorizationRequired], name='dispatch')
class GeoContinentsApiView(APIView):
    def get(self,request):
        if id:
            all_data = GeoContinents.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = GeoContinents.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data
        gc_name      = data.get('gc_name')

        

        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            GeoContinents.objects.create(gc_name =gc_name
                                        )


            posts = GeoContinents.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        data = request.data
        gc_name      = data.get('gc_name')

        
        
        try:
            GeoContinents.objects.filter(id=pk).update(gc_name =gc_name
                                                            )


            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = GeoContinents.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})


# @method_decorator([AutorizationRequired], name='dispatch')
class GeoSubContinentsApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = GeoSubContinents.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = GeoSubContinents.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})
    def post(self,request):
        data = request.data
        gc_ref      = data.get('gc_ref_id')
        gsc_name    = data.get('gsc_name')

        
        
        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            GeoSubContinents.objects.create(
                                            gc_ref_id=gc_ref,
                                            gsc_name=gsc_name
                                        )


            posts = GeoSubContinents.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        data = request.data
        gc_ref      = data.get('gc_ref_id')
        gsc_name    = data.get('gsc_name')

        
        
        try:
            GeoSubContinents.objects.filter(id=pk).update(gc_ref_id=gc_ref,
                                                            gsc_name=gsc_name
                                                        )


            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = GeoSubContinents.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})

# @method_decorator([AutorizationRequired], name='dispatch')
class ProjectCategoriesView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = ProjectCategories.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = ProjectCategories.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data
        org_ref                 = data.get('org_ref_id')
        pc_added_by_ref_user    = data.get('pc_added_by_ref_user_id')
        pc_name                 = data.get('pc_name')
        pc_status               = data.get('pc_status')
        # pc_c_date            = data.get('pc_c_date')
        # pc_m_date              = data.get('pc_m_date')
        

        # file_attachment_name= data.get('file_attachment_name')
        
        task_name= data.get('task_name')
        billable_type= data.get('billable_type')


        file_attachment = data['file_attachment']
        base64_data = file_attachment
        split_base_url_data=file_attachment.split(';base64,')[1]
        imgdata1 = base64.b64decode(split_base_url_data)

        data_split = file_attachment.split(';base64,')[0]
        extension_data = re.split(':|;', data_split)[1] 
        guess_extension_data = guess_extension(extension_data)

        filename1 = "/eztime/site/public/media/file_attachment/"+pc_name+guess_extension_data
        # filename1 = "/Users/apple/EzTime/eztimeproject/media/photo"+first_name+guess_extension_data
        fname1 = '/file_attachment/'+pc_name+guess_extension_data
        ss=  open(filename1, 'wb')
        print(ss)
        ss.write(imgdata1)
        ss.close()   


        # file_attachment_path='http://127.0.0.1:8000/media/file_attachment/'+ file_attachment.name
        # file_attachment_path='https://eztime.thestorywallcafe.com/media/'+file_attachment
        # print(file_attachment_path,'pathhh')

        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        try:
            check_data = ProjectCategories.objects.create(org_ref_id=org_ref,
                                            pc_added_by_ref_user_id=pc_added_by_ref_user,
                                            pc_name=pc_name,
                                            pc_status=pc_status,
                                            # base64=base64_data,
                                            # pc_c_date=pc_c_date,
                                            # pc_m_date=pc_m_date,
                                            # file_attachment=file_attachment,
                                            # file_attachment_name=file_attachment_name,
                                            task_name=task_name,
                                            billable_type=billable_type,)
                                            # file_attachment_path=file_attachment_path)

            if file_attachment:
                check_data.file_attachment_path = 'https://eztime.thestorywallcafe.com/media/'+ (str(fname1))
                check_data.save()

            posts = ProjectCategories.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        data = request.data
        org_ref                 = data.get('org_ref_id')
        pc_added_by_ref_user    = data.get('pc_added_by_ref_user_id')
        pc_name                 = data.get('pc_name')
        pc_status               = data.get('pc_status')
        # pc_c_date               = data.get('pc_c_date')
        # pc_m_date               = data.get('pc_m_date')
        
        # file_attachment_name= data.get('file_attachment_name')
       
        task_name= data.get('task_name')
        billable_type= data.get('billable_type')


        file_attachment = data['file_attachment']
       
        # file_attachment_path='http://127.0.0.1:8000/media/file_attachment/'+ file_attachment.name
        # file_attachment_path='https://eztime.thestorywallcafe.com/media/'+file_attachment
        # print(file_attachment_path,'pathhh')

        if file_attachment == '':
            print('in if nulll looopp') 
            try:

                
                ProjectCategories.objects.filter(id=pk).update(
                    org_ref_id=org_ref,
                                                pc_added_by_ref_user_id=pc_added_by_ref_user,
                                                pc_name=pc_name,
                                                pc_status=pc_status,

                                                # pc_c_date=pc_c_date,
                                                # pc_m_date=pc_m_date,
                                                # file_attachment=file_attachment,
                                                # file_attachment_name=file_attachment_name,
                                                task_name=task_name,
                                                billable_type=billable_type,)
                
                
                    

                return Response({'result':{'status':'Updated'}})
            except IntegrityError as e:
                error_message = e.args
                return Response({
                'error':{'message':'DB error!',
                'detail':error_message,
                'status_code':status.HTTP_400_BAD_REQUEST,
                }},status=status.HTTP_400_BAD_REQUEST)


        try:

            base64_data = file_attachment
            split_base_url_data=file_attachment.split(';base64,')[1]
            imgdata1 = base64.b64decode(split_base_url_data)

            data_split = file_attachment.split(';base64,')[0]
            extension_data = re.split(':|;', data_split)[1] 
            guess_extension_data = guess_extension(extension_data)

            filename1 = "/eztime/site/public/media/file_attachment/"+pc_name+guess_extension_data
            # filename1 = "/Users/apple/EzTime/eztimeproject/media/photo"+first_name+guess_extension_data
            fname1 = '/file_attachment/'+pc_name+guess_extension_data
            ss=  open(filename1, 'wb')
            print(ss)
            ss.write(imgdata1)
            ss.close()   



                
            ProjectCategories.objects.filter(id=pk).update(
                   
                                                file_attachment='',
                                                )

            ProjectCategories.objects.filter(id=pk).update(
                    org_ref_id=org_ref,
                                                pc_added_by_ref_user_id=pc_added_by_ref_user,
                                                pc_name=pc_name,
                                                pc_status=pc_status,
                                                # base64=base64_data,
                                                # pc_c_date=pc_c_date,
                                                # pc_m_date=pc_m_date,
                                                file_attachment=file_attachment,
                                                # file_attachment_name=file_attachment_name,
                                                task_name=task_name,
                                                billable_type=billable_type,)
            check_data = ProjectCategories.objects.get(id=pk)
            if file_attachment:
                    print(check_data.file_attachment,"this is file")
                    check_data.file_attachment_path = 'https://eztime.thestorywallcafe.com/media/file_attachment/'+ (str(check_data.file_attachment))
                    
                    check_data.save()
                    

            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
                error_message = e.args
                return Response({
                'error':{'message':'DB error!',
                'detail':error_message,
                'status_code':status.HTTP_400_BAD_REQUEST,
                }},status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = ProjectCategories.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})


#------------------------------------------------------------------------
# @method_decorator([AutorizationRequired], name='dispatch')
class ProductDetailsView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = ProductDetails.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = ProductDetails.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})


    def post(self,request):
        data = request.data
        pd_app_name      = data.get('pd_app_name')
        pd_app_tag_line= data.get('pd_app_tag_line')
        pd_company_name= data.get('pd_company_name')
        pd_company_address= data.get('pd_company_address')
        pd_company_email_id= data.get('pd_company_email_id')
        pd_company_phone_no= data.get('pd_company_phone_no')
        pd_web_version= data.get('pd_web_version')
        pd_poweredbyweblink= data.get('pd_poweredbyweblink')
        pd_facebook_link= data.get('pd_facebook_link')
        pd_twitter_link= data.get('pd_twitter_link')
        pd_linkedin_link= data.get('pd_linkedin_link')
        pd_product_logo= data.get('pd_product_logo')
        pd_product_logo_base_url= data.get('pd_product_logo_base_url')
        pd_product_logo_path= data.get('pd_product_logo_path')
        pd_status= data.get('pd_status')

        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



       
        try:
            ProductDetails.objects.create(pd_app_name=pd_app_name,
                                        pd_app_tag_line=pd_app_tag_line,
                                        pd_company_name=pd_company_name,
                                        pd_company_address=pd_company_address,
                                        pd_company_email_id=pd_company_email_id,
                                        pd_company_phone_no=pd_company_phone_no,
                                        pd_web_version=pd_web_version,
                                        pd_poweredbyweblink=pd_poweredbyweblink,
                                        pd_facebook_link=pd_facebook_link,
                                        pd_twitter_link=pd_twitter_link,
                                        pd_linkedin_link=pd_linkedin_link,
                                        pd_product_logo=pd_product_logo,
                                        pd_product_logo_base_url=pd_product_logo_base_url,
                                        pd_product_logo_path=pd_product_logo_path,
                                        pd_status=pd_status)


            posts = ProductDetails.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def put(self,request,pk):
        data = request.data
        pd_app_name      = data.get('pd_app_name')
        pd_app_tag_line= data.get('pd_app_tag_line')
        pd_company_name= data.get('pd_company_name')
        pd_company_address= data.get('pd_company_address')
        pd_company_email_id= data.get('pd_company_email_id')
        pd_company_phone_no= data.get('pd_company_phone_no')
        pd_web_version= data.get('pd_web_version')
        pd_poweredbyweblink= data.get('pd_poweredbyweblink')
        pd_facebook_link= data.get('pd_facebook_link')
        pd_twitter_link= data.get('pd_twitter_link')
        pd_linkedin_link= data.get('pd_linkedin_link')
        pd_product_logo= data.get('pd_product_logo')
        pd_product_logo_base_url= data.get('pd_product_logo_base_url')
        pd_product_logo_path= data.get('pd_product_logo_path')
        pd_status= data.get('pd_status')
        
        
        try:
            ProductDetails.objects.filter(id=pk).update(pd_app_name=pd_app_name,
                                        pd_app_tag_line=pd_app_tag_line,
                                        pd_company_name=pd_company_name,
                                        pd_company_address=pd_company_address,
                                        pd_company_email_id=pd_company_email_id,
                                        pd_company_phone_no=pd_company_phone_no,
                                        pd_web_version=pd_web_version,
                                        pd_poweredbyweblink=pd_poweredbyweblink,
                                        pd_facebook_link=pd_facebook_link,
                                        pd_twitter_link=pd_twitter_link,
                                        pd_linkedin_link=pd_linkedin_link,
                                        pd_product_logo=pd_product_logo,
                                        pd_product_logo_base_url=pd_product_logo_base_url,
                                        pd_product_logo_path=pd_product_logo_path,
                                        pd_status=pd_status)

            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = ProductDetails.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})


# @method_decorator([AutorizationRequired], name='dispatch')
class OrganizationLeaveTypeApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = OrganizationLeaveType.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = OrganizationLeaveType.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})
    def post(self,request):
        data = request.data
        
        org_reff = data.get('org_reff_id')
        olt_added_by_ref_user= data.get('olt_added_by_ref_user_id')
        olt_ref_occ_id_list= data.get('olt_ref_occ_id_list')
        olt_name= data.get('olt_name')
        olt_description= data.get('olt_description')
        olt_status= data.get('olt_status')
        olt_no_of_leaves= data.get('olt_no_of_leaves')
        olt_no_of_leaves_yearly= data.get('olt_no_of_leaves_yearly')
        olt_no_of_leaves_monthly= data.get('olt_no_of_leaves_monthly')
        olt_accrude_monthly_status= data.get('olt_accrude_monthly_status')
        olt_carry_forward= data.get('olt_carry_forward')
        olt_applicable_for= data.get('olt_applicable_for')
        olt_people_applicable_for= data.get('olt_people_applicable_for')
        olt_gracefull_status= data.get('olt_gracefull_status')
        olt_gracefull_days= data.get('olt_gracefull_days')
        olt_enchashment_status= data.get('olt_enchashment_status')
        olt_max_enchashment_leaves= data.get('olt_max_enchashment_leaves')
        olt_editable= data.get('olt_editable')


        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            OrganizationLeaveType.objects.create(org_reff_id=org_reff,
                                            olt_added_by_ref_user_id=olt_added_by_ref_user,
                                            olt_ref_occ_id_list=olt_ref_occ_id_list,
                                            olt_name=olt_name,
                                            olt_description=olt_description,
                                            olt_status=olt_status,
                                            olt_no_of_leaves=olt_no_of_leaves,
                                            olt_no_of_leaves_yearly=olt_no_of_leaves_yearly,
                                            olt_no_of_leaves_monthly=olt_no_of_leaves_monthly,
                                            olt_accrude_monthly_status=olt_accrude_monthly_status,
                                            olt_carry_forward=olt_carry_forward,
                                            olt_applicable_for=olt_applicable_for,
                                            olt_people_applicable_for=olt_people_applicable_for,
                                            olt_gracefull_status=olt_gracefull_status,
                                            olt_gracefull_days=olt_gracefull_days,
                                            olt_enchashment_status=olt_enchashment_status,
                                            olt_max_enchashment_leaves=olt_max_enchashment_leaves,
                                            olt_editable=olt_editable)


            posts = OrganizationLeaveType.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def put(self,request,pk):
        data = request.data
        
        org_reff = data.get('org_reff_id')
        olt_added_by_ref_user= data.get('olt_added_by_ref_user_id')
        olt_ref_occ_id_list= data.get('olt_ref_occ_id_list')
        olt_name= data.get('olt_name')
        olt_description= data.get('olt_description')
        olt_status= data.get('olt_status')
        olt_no_of_leaves= data.get('olt_no_of_leaves')
        olt_no_of_leaves_yearly= data.get('olt_no_of_leaves_yearly')
        olt_no_of_leaves_monthly= data.get('olt_no_of_leaves_monthly')
        olt_accrude_monthly_status= data.get('olt_accrude_monthly_status')
        olt_carry_forward= data.get('olt_carry_forward')
        olt_applicable_for= data.get('olt_applicable_for')
        olt_people_applicable_for= data.get('olt_people_applicable_for')
        olt_gracefull_status= data.get('olt_gracefull_status')
        olt_gracefull_days= data.get('olt_gracefull_days')
        olt_enchashment_status= data.get('olt_enchashment_status')
        olt_max_enchashment_leaves= data.get('olt_max_enchashment_leaves')
        olt_editable= data.get('olt_editable')

       
        try:
            OrganizationLeaveType.objects.filter(id=pk).update(org_reff_id=org_reff,
                                            olt_added_by_ref_user_id=olt_added_by_ref_user,
                                            olt_ref_occ_id_list=olt_ref_occ_id_list,
                                            olt_name=olt_name,
                                            olt_description=olt_description,
                                            olt_status=olt_status,
                                            olt_no_of_leaves=olt_no_of_leaves,
                                            olt_no_of_leaves_yearly=olt_no_of_leaves_yearly,
                                            olt_no_of_leaves_monthly=olt_no_of_leaves_monthly,
                                            olt_accrude_monthly_status=olt_accrude_monthly_status,
                                            olt_carry_forward=olt_carry_forward,
                                            olt_applicable_for=olt_applicable_for,
                                            olt_people_applicable_for=olt_people_applicable_for,
                                            olt_gracefull_status=olt_gracefull_status,
                                            olt_gracefull_days=olt_gracefull_days,
                                            olt_enchashment_status=olt_enchashment_status,
                                            olt_max_enchashment_leaves=olt_max_enchashment_leaves,
                                            olt_editable=olt_editable)
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            


    def delete(self,request,pk):
        test = (0,{})
            
        all_values = OrganizationLeaveType.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})


# @method_decorator([AutorizationRequired], name='dispatch')
class OrganizationCostCentersApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = OrganizationCostCenters.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = OrganizationCostCenters.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data
        
        org_ref = data.get('org_ref_id')
        occ_added_by_ref_user= data.get('occ_added_by_ref_user_id')
        occ_cost_center_name= data.get('occ_cost_center_name')
        occ_leave_mgmt_status= data.get('occ_leave_mgmt_status')
        occ_currency_type= data.get('occ_currency_type')
        occ_status= data.get('occ_status')

          

        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            OrganizationCostCenters.objects.create(org_ref_id=org_ref,
                                                        occ_added_by_ref_user_id=occ_added_by_ref_user,
                                                        occ_cost_center_name=occ_cost_center_name,
                                                        occ_leave_mgmt_status=occ_leave_mgmt_status,
                                                        occ_currency_type=occ_currency_type,
                                                        occ_status=occ_status)


            posts = OrganizationCostCenters.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def put(self,request,pk):
        data = request.data
        
        org_ref = data.get('org_ref_id')
        occ_added_by_ref_user= data.get('occ_added_by_ref_user_id')
        occ_cost_center_name= data.get('occ_cost_center_name')
        occ_leave_mgmt_status= data.get('occ_leave_mgmt_status')
        occ_currency_type= data.get('occ_currency_type')
        occ_status= data.get('occ_status')

        
        try:
            OrganizationCostCenters.objects.filter(id=pk).update(org_ref_id=org_ref,
                                                        occ_added_by_ref_user_id=occ_added_by_ref_user,
                                                        occ_cost_center_name=occ_cost_center_name,
                                                        occ_leave_mgmt_status=occ_leave_mgmt_status,
                                                        occ_currency_type=occ_currency_type,
                                                        occ_status=occ_status)
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
                
                

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = OrganizationCostCenters.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})


# @method_decorator([AutorizationRequired], name='dispatch')
class OrganizationCostCentersLeaveTypeApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = OrganizationCostCentersLeaveType.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = OrganizationCostCentersLeaveType.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})


    def post(self,request):
        data = request.data
        
        olt_ref=data.get('olt_ref_id')
        org_ref=data.get('org_ref_id')
        occ_ref=data.get('occ_ref_id')
        occl_added_by_ref_user=data.get('occl_added_by_ref_user_id')
        occl_name=data.get('occl_name')
        occl_description=data.get('occl_description')
        occl_status=data.get('occl_status')
        occl_alloted_leaves=data.get('occl_alloted_leaves')
        occl_alloted_leaves_yearly=data.get('occl_alloted_leaves_yearly')
        occl_alloted_leaves_monthly=data.get('occl_alloted_leaves_monthly')
        occl_accrude_monthly_status=data.get('occl_accrude_monthly_status')
        occl_carry_forward=data.get('occl_carry_forward')
        occl_gracefull_status=data.get('occl_gracefull_status')
        occl_gracefull_days=data.get('occl_gracefull_days')
        occl_enchashment_status=data.get('occl_enchashment_status')
        occl_max_enchashment_leaves=data.get('occl_max_enchashment_leaves')
        occl_editable=data.get('occl_editable')



        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            OrganizationCostCentersLeaveType.objects.create(olt_ref_id=olt_ref,
                                                            org_ref_id=org_ref,
                                                            occ_ref_id=occ_ref,
                                                            occl_added_by_ref_user_id=occl_added_by_ref_user,
                                                            occl_name=occl_name,
                                                            occl_description=occl_description,
                                                            occl_status=occl_status,
                                                            occl_alloted_leaves=occl_alloted_leaves,
                                                            occl_alloted_leaves_yearly=occl_alloted_leaves_yearly,
                                                            occl_alloted_leaves_monthly=occl_alloted_leaves_monthly,
                                                            occl_accrude_monthly_status=occl_accrude_monthly_status,
                                                            occl_carry_forward=occl_carry_forward,
                                                            occl_gracefull_status=occl_gracefull_status,
                                                            occl_gracefull_days=occl_gracefull_days,
                                                            occl_enchashment_status=occl_enchashment_status,
                                                            occl_max_enchashment_leaves=occl_max_enchashment_leaves,
                                                            occl_editable=occl_editable)


            posts = OrganizationCostCentersLeaveType.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        data = request.data
        
        olt_ref=data.get('olt_ref_id')
        org_ref=data.get('org_ref_id')
        occ_ref=data.get('occ_ref_id')
        occl_added_by_ref_user=data.get('occl_added_by_ref_user_id')
        occl_name=data.get('occl_name')
        occl_description=data.get('occl_description')
        occl_status=data.get('occl_status')
        occl_alloted_leaves=data.get('occl_alloted_leaves')
        occl_alloted_leaves_yearly=data.get('occl_alloted_leaves_yearly')
        occl_alloted_leaves_monthly=data.get('occl_alloted_leaves_monthly')
        occl_accrude_monthly_status=data.get('occl_accrude_monthly_status')
        occl_carry_forward=data.get('occl_carry_forward')
        occl_gracefull_status=data.get('occl_gracefull_status')
        occl_gracefull_days=data.get('occl_gracefull_days')
        occl_enchashment_status=data.get('occl_enchashment_status')
        occl_max_enchashment_leaves=data.get('occl_max_enchashment_leaves')
        occl_editable=data.get('occl_editable')

        
        try:
            OrganizationCostCentersLeaveType.objects.filter(id=pk).update(olt_ref_id=olt_ref,
                                                            org_ref_id=org_ref,
                                                            occ_ref_id=occ_ref,
                                                            occl_added_by_ref_user_id=occl_added_by_ref_user,
                                                            occl_name=occl_name,
                                                            occl_description=occl_description,
                                                            occl_status=occl_status,
                                                            occl_alloted_leaves=occl_alloted_leaves,
                                                            occl_alloted_leaves_yearly=occl_alloted_leaves_yearly,
                                                            occl_alloted_leaves_monthly=occl_alloted_leaves_monthly,
                                                            occl_accrude_monthly_status=occl_accrude_monthly_status,
                                                            occl_carry_forward=occl_carry_forward,
                                                            occl_gracefull_status=occl_gracefull_status,
                                                            occl_gracefull_days=occl_gracefull_days,
                                                            occl_enchashment_status=occl_enchashment_status,
                                                            occl_max_enchashment_leaves=occl_max_enchashment_leaves,
                                                            occl_editable=occl_editable)
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = OrganizationCostCentersLeaveType.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})

# @method_decorator([AutorizationRequired], name='dispatch')
class UsersLeaveMasterApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = UsersLeaveMaster.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = UsersLeaveMaster.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data
        org_ref=data.get('org_ref_id')
        ulm_ref_user=data.get('ulm_ref_user_id')
        occ_ref=data.get('occ_ref_id')
        occl_ref=data.get('occl_ref_id')
        occyl_ref=data.get('occyl_ref_id')
        ulm_added_by_ref_id=data.get('ulm_added_by_ref_id')
        ulm_allotted_leaves=data.get('ulm_allotted_leaves')
        ulm_leaves_used=data.get('ulm_leaves_used')
        ulm_status=data.get('ulm_status')


        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



       
        try:
            UsersLeaveMaster.objects.create(org_ref_id=org_ref,
                                                                        ulm_ref_user_id=ulm_ref_user,
                                                                        occ_ref_id=occ_ref,
                                                                        occl_ref_id=occl_ref,
                                                                        occyl_ref_id=occyl_ref,
                                                                        ulm_added_by_ref_id=ulm_added_by_ref_id,
                                                                        ulm_allotted_leaves=ulm_allotted_leaves,
                                                                        ulm_leaves_used=ulm_leaves_used,
                                                                        ulm_status=ulm_status)


            posts = UsersLeaveMaster.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        data = request.data
        org_ref=data.get('org_ref_id')
        ulm_ref_user=data.get('ulm_ref_user_id')
        occ_ref=data.get('occ_ref_id')
        occl_ref=data.get('occl_ref_id')
        occyl_ref=data.get('occyl_ref_id')
        ulm_added_by_ref_id=data.get('ulm_added_by_ref_id')
        ulm_allotted_leaves=data.get('ulm_allotted_leaves')
        ulm_leaves_used=data.get('ulm_leaves_used')
        ulm_status=data.get('ulm_status')

        
        try:
            UsersLeaveMaster.objects.filter(id=pk).update(org_ref_id=org_ref,
                                                                        ulm_ref_user_id=ulm_ref_user,
                                                                        occ_ref_id=occ_ref,
                                                                        occl_ref_id=occl_ref,
                                                                        occyl_ref_id=occyl_ref,
                                                                        ulm_added_by_ref_id=ulm_added_by_ref_id,
                                                                        ulm_allotted_leaves=ulm_allotted_leaves,
                                                                        ulm_leaves_used=ulm_leaves_used,
                                                                        ulm_status=ulm_status)
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = UsersLeaveMaster.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})

# @method_decorator([AutorizationRequired], name='dispatch')
class OrganizationCostCentersYearListApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = OrganizationCostCentersYearList.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = OrganizationCostCentersYearList.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data
        
        org_ref =data.get('org_ref_id')
        occyl_added_by_ref_user =data.get('occyl_added_by_ref_user_id')
        occ_ref =data.get('occ_ref_id')
        occyl_status =data.get('occyl_status')

        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            OrganizationCostCentersYearList.objects.create(org_ref_id=org_ref,
                                                                occyl_added_by_ref_user_id=occyl_added_by_ref_user,
                                                                occ_ref_id=occ_ref,
                                                                occyl_status=occyl_status)


            posts = OrganizationCostCentersYearList.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        data = request.data
        
        org_ref =data.get('org_ref_id')
        occyl_added_by_ref_user =data.get('occyl_added_by_ref_user_id')
        occ_ref =data.get('occ_ref_id')
        occyl_status =data.get('occyl_status')

       
        try:
            OrganizationCostCentersYearList.objects.filter(id=pk).update(org_ref_id=org_ref,
                                                                occyl_added_by_ref_user_id=occyl_added_by_ref_user,
                                                                occ_ref_id=occ_ref,
                                                                occyl_status=occyl_status)
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
                

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = OrganizationCostCentersYearList.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})

# @method_decorator([AutorizationRequired], name='dispatch')
class UsersLeaveApplicationsApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = UsersLeaveApplications.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = UsersLeaveApplications.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data
        
        org_ref=data.get('org_ref_id')
        ula_ref_user=data.get('ula_ref_user_id')
        occl_ref=data.get('occl_ref_id')
        ulm_ref=data.get('ulm_ref_id')
        ula_approved_by_ref_u_id=data.get('ula_approved_by_ref_u_id')
        ula_cc_to_ref_u_id=data.get('ula_cc_to_ref_u_id')
        ula_reason_for_leave=data.get('ula_reason_for_leave')
        ula_contact_details=data.get('ula_contact_details')
        ula_file=data.get('ula_file')
        ula_file_path=data.get('ula_file_path')
        ula_file_base_url=data.get('ula_file_base_url')
        ula_cc_mail_sent=data.get('ula_cc_mail_sent')
        ula_from_session=data.get('ula_from_session')
        ula_to_session=data.get('ula_to_session')
        ula_no_of_days_leaves=data.get('ula_no_of_days_leaves')
        ula_approved_leaves=data.get('ula_approved_leaves')
        ula_rejected_leaves=data.get('ula_rejected_leaves')
        ula_pending_leaves=data.get('ula_pending_leaves')
        ula_balanced_leaves=data.get('ula_balanced_leaves')



        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



       
        try:
            UsersLeaveApplications.objects.create(org_ref_id=org_ref,
                                                    ula_ref_user_id=ula_ref_user,
                                                    occl_ref_id=occl_ref,
                                                    ulm_ref_id=ulm_ref,
                                                    ula_approved_by_ref_u_id=ula_approved_by_ref_u_id,
                                                    ula_cc_to_ref_u_id=ula_cc_to_ref_u_id,
                                                    ula_reason_for_leave=ula_reason_for_leave,
                                                    ula_contact_details=ula_contact_details,
                                                    ula_file=ula_file,
                                                    ula_file_path=ula_file_path,
                                                    ula_file_base_url=ula_file_base_url,
                                                    ula_cc_mail_sent=ula_cc_mail_sent,
                                                    ula_from_session=ula_from_session,
                                                    ula_to_session=ula_to_session,
                                                    ula_no_of_days_leaves=ula_no_of_days_leaves,
                                                    ula_approved_leaves=ula_approved_leaves,
                                                    ula_rejected_leaves=ula_rejected_leaves,
                                                    ula_pending_leaves=ula_pending_leaves,
                                                    ula_balanced_leaves=ula_balanced_leaves)


            posts = UsersLeaveApplications.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def put(self,request,pk):
        data = request.data
        
        org_ref=data.get('org_ref_id')
        ula_ref_user=data.get('ula_ref_user_id')
        occl_ref=data.get('occl_ref_id')
        ulm_ref=data.get('ulm_ref_id')
        ula_approved_by_ref_u_id=data.get('ula_approved_by_ref_u_id')
        ula_cc_to_ref_u_id=data.get('ula_cc_to_ref_u_id')
        ula_reason_for_leave=data.get('ula_reason_for_leave')
        ula_contact_details=data.get('ula_contact_details')
        ula_file=data.get('ula_file')
        ula_file_path=data.get('ula_file_path')
        ula_file_base_url=data.get('ula_file_base_url')
        ula_cc_mail_sent=data.get('ula_cc_mail_sent')
        ula_from_session=data.get('ula_from_session')
        ula_to_session=data.get('ula_to_session')
        ula_no_of_days_leaves=data.get('ula_no_of_days_leaves')
        ula_approved_leaves=data.get('ula_approved_leaves')
        ula_rejected_leaves=data.get('ula_rejected_leaves')
        ula_pending_leaves=data.get('ula_pending_leaves')
        ula_balanced_leaves=data.get('ula_balanced_leaves')

        
        
        try:
            UsersLeaveApplications.objects.filter(id=pk).update(org_ref_id=org_ref,
                                                    ula_ref_user_id=ula_ref_user,
                                                    occl_ref_id=occl_ref,
                                                    ulm_ref_id=ulm_ref,
                                                    ula_approved_by_ref_u_id=ula_approved_by_ref_u_id,
                                                    ula_cc_to_ref_u_id=ula_cc_to_ref_u_id,
                                                    ula_reason_for_leave=ula_reason_for_leave,
                                                    ula_contact_details=ula_contact_details,
                                                    ula_file=ula_file,
                                                    ula_file_path=ula_file_path,
                                                    ula_file_base_url=ula_file_base_url,
                                                    ula_cc_mail_sent=ula_cc_mail_sent,
                                                    ula_from_session=ula_from_session,
                                                    ula_to_session=ula_to_session,
                                                    ula_no_of_days_leaves=ula_no_of_days_leaves,
                                                    ula_approved_leaves=ula_approved_leaves,
                                                    ula_rejected_leaves=ula_rejected_leaves,
                                                    ula_pending_leaves=ula_pending_leaves,
                                                    ula_balanced_leaves=ula_balanced_leaves)
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            
            

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = UsersLeaveApplications.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})

# @method_decorator([AutorizationRequired], name='dispatch')
class UserLeaveAllotmentListApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = UserLeaveAllotmentList.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = UserLeaveAllotmentList.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})
    def post(self,request):
        data = request.data
        
        org_ref=data.get('org_ref_id')
        occ_ref=data.get('occ_ref_id')
        occyl_ref=data.get('occyl_ref_id')
        occl_ref=data.get('occl_ref_id')
        ulm_ref=data.get('ulm_ref_id')
        ulal_ref_user=data.get('ulal_ref_user_id')
        ula_ref=data.get('ula_ref_id')
        ulal_allotted_leaves=data.get('ulal_allotted_leaves')
        ulal_status=data.get('ulal_status')
        ulal_type=data.get('ulal_type')
        ulal_type_of_allotment=data.get('ulal_type_of_allotment')


        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            UserLeaveAllotmentList.objects.create(org_ref_id=org_ref,
                                                    occ_ref_id=occ_ref,
                                                    occyl_ref_id=occyl_ref,
                                                    occl_ref_id=occl_ref,
                                                    ulm_ref_id=ulm_ref,
                                                    ulal_ref_user_id=ulal_ref_user,
                                                    ula_ref_id=ula_ref,
                                                    ulal_allotted_leaves=ulal_allotted_leaves,
                                                    ulal_status=ulal_status,
                                                    ulal_type=ulal_type,
                                                    ulal_type_of_allotment=ulal_type_of_allotment)


            posts = UserLeaveAllotmentList.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            


    def put(self,request,pk):
        data = request.data
        
        org_ref=data.get('org_ref_id')
        occ_ref=data.get('occ_ref_id')
        occyl_ref=data.get('occyl_ref_id')
        occl_ref=data.get('occl_ref_id')
        ulm_ref=data.get('ulm_ref_id')
        ulal_ref_user=data.get('ulal_ref_user_id')
        ula_ref=data.get('ula_ref_id')
        ulal_allotted_leaves=data.get('ulal_allotted_leaves')
        ulal_status=data.get('ulal_status')
        ulal_type=data.get('ulal_type')
        ulal_type_of_allotment=data.get('ulal_type_of_allotment')

        
        
        try:
            UserLeaveAllotmentList.objects.filter(id=pk).update(org_ref_id=org_ref,
                                                    occ_ref_id=occ_ref,
                                                    occyl_ref_id=occyl_ref,
                                                    occl_ref_id=occl_ref,
                                                    ulm_ref_id=ulm_ref,
                                                    ulal_ref_user_id=ulal_ref_user,
                                                    ula_ref_id=ula_ref,
                                                    ulal_allotted_leaves=ulal_allotted_leaves,
                                                    ulal_status=ulal_status,
                                                    ulal_type=ulal_type,
                                                    ulal_type_of_allotment=ulal_type_of_allotment)
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
                

                

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = UserLeaveAllotmentList.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})

# @method_decorator([AutorizationRequired], name='dispatch')
class UserLeaveListApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = UserLeaveList.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = UserLeaveList.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data
        
        org_ref=data.get('org_ref_id')
        ull_ref_user=data.get('ull_ref_user_id')
        olt_ref=data.get('olt_ref_id')
        occ_ref=data.get('occ_ref_id')
        ull_added_by_ref_id=data.get('ull_added_by_ref_user_id')
        ull_ref_ohcy_id=data.get('ull_ref_ohcy_id')
        ull_no_of_allotted_leaves=data.get('ull_no_of_allotted_leaves')
        ull_no_of_leaves_used=data.get('ull_no_of_leaves_used')
        ull_status=data.get('ull_status')


        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            UserLeaveList.objects.create(org_ref_id=org_ref,
                                        ull_ref_user_id=ull_ref_user,
                                        olt_ref_id=olt_ref,
                                        occ_ref_id=occ_ref,
                                        ull_added_by_ref_user_id=ull_added_by_ref_id,
                                        ull_ref_ohcy_id=ull_ref_ohcy_id,
                                        ull_no_of_allotted_leaves=ull_no_of_allotted_leaves,
                                        ull_no_of_leaves_used=ull_no_of_leaves_used,
                                        ull_status=ull_status)


            posts = UserLeaveList.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        data = request.data
        
        org_ref=data.get('org_ref_id')
        ull_ref_user=data.get('ull_ref_user_id')
        olt_ref=data.get('olt_ref_id')
        occ_ref=data.get('occ_ref_id')
        ull_added_by_ref_id=data.get('ull_added_by_ref_user_id')
        ull_ref_ohcy_id=data.get('ull_ref_ohcy_id')
        ull_no_of_allotted_leaves=data.get('ull_no_of_allotted_leaves')
        ull_no_of_leaves_used=data.get('ull_no_of_leaves_used')
        ull_status=data.get('ull_status')

        
        
        try:
            UserLeaveList.objects.filter(id=pk).update(org_ref_id=org_ref,
                                        ull_ref_user_id=ull_ref_user,
                                        olt_ref_id=olt_ref,
                                        occ_ref_id=occ_ref,
                                        ull_added_by_ref_user_id=ull_added_by_ref_id,
                                        ull_ref_ohcy_id=ull_ref_ohcy_id,
                                        ull_no_of_allotted_leaves=ull_no_of_allotted_leaves,
                                        ull_no_of_leaves_used=ull_no_of_leaves_used,
                                        ull_status=ull_status)
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = UserLeaveList.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})


# @method_decorator([AutorizationRequired], name='dispatch')
class ProjectCategoriesChecklistApiView(APIView):
    def get(self,request):
        if id:
            all_data = ProjectCategoriesChecklist.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = ProjectCategoriesChecklist.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data
        
        org_ref=data.get('org_ref_id')
        pcc_added_by_ref_user=data.get('pcc_added_by_ref_user_id')
        pc_ref=data.get('pc_ref_id')
        pcc_name=data.get('pcc_name')
        pcc_billable=data.get('pcc_billable')
        pcc_status=data.get('pcc_status')



        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            ProjectCategoriesChecklist.objects.create(org_ref_id=org_ref,
                                                        pcc_added_by_ref_user_id=pcc_added_by_ref_user,
                                                        pc_ref_id=pc_ref,
                                                        pcc_name=pcc_name,
                                                        pcc_billable=pcc_billable,
                                                        pcc_status=pcc_status)


            posts = ProjectCategoriesChecklist.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        data = request.data
        
        org_ref=data.get('org_ref_id')
        pcc_added_by_ref_user=data.get('pcc_added_by_ref_user_id')
        pc_ref=data.get('pc_ref_id')
        pcc_name=data.get('pcc_name')
        pcc_billable=data.get('pcc_billable')
        pcc_status=data.get('pcc_status')


        
        
        try:
            ProjectCategoriesChecklist.objects.filter(id=pk).update(org_ref_id=org_ref,
                                                        pcc_added_by_ref_user_id=pcc_added_by_ref_user,
                                                        pc_ref_id=pc_ref,
                                                        pcc_name=pcc_name,
                                                        pcc_billable=pcc_billable,
                                                        pcc_status=pcc_status)
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = ProjectCategoriesChecklist.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})

# @method_decorator([AutorizationRequired], name='dispatch')
class TaskProjectCategoriesChecklistApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = TaskProjectCategoriesChecklist.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})
        
        else:
            all_data = TaskProjectCategoriesChecklist.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})


    def post(self,request):
        data = request.data
        
        p_ref=data.get('p_ref_id')
        org_ref=data.get('org_ref_id')
        tpcc_added_by_ref_user=data.get('tpcc_added_by_ref_user_id')
        pc_ref=data.get('pc_ref_id')
        pcc_ref=data.get('pcc_ref_id')
        opg_ref=data.get('opg_ref_id')
        tpcc_name=data.get('tpcc_name')
        tpcc_status=data.get('tpcc_status')
        tpcc_billable=data.get('tpcc_billable')
        tpcc_assignee_people_ref_u_id=data.get('tpcc_assignee_people_ref_u_id')




        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            TaskProjectCategoriesChecklist.objects.create(p_ref_id=p_ref,
                                                            org_ref_id=org_ref,
                                                            tpcc_added_by_ref_user_id=tpcc_added_by_ref_user,
                                                            pc_ref_id=pc_ref,
                                                            pcc_ref_id=pcc_ref,
                                                            opg_ref_id=opg_ref,
                                                            tpcc_name=tpcc_name,
                                                            tpcc_status=tpcc_status,
                                                            tpcc_billable=tpcc_billable,
                                                            tpcc_assignee_people_ref_u_id=tpcc_assignee_people_ref_u_id)


            posts = TaskProjectCategoriesChecklist.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def put(self,request,pk):
        data = request.data
        
        p_ref=data.get('p_ref_id')
        org_ref=data.get('org_ref_id')
        tpcc_added_by_ref_user=data.get('tpcc_added_by_ref_user_id')
        pc_ref=data.get('pc_ref_id')
        pcc_ref=data.get('pcc_ref_id')
        opg_ref=data.get('opg_ref_id')
        tpcc_name=data.get('tpcc_name')
        tpcc_status=data.get('tpcc_status')
        tpcc_billable=data.get('tpcc_billable')
        tpcc_assignee_people_ref_u_id=data.get('tpcc_assignee_people_ref_u_id')
        
        
        try:
            TaskProjectCategoriesChecklist.objects.filter(id=pk).update(p_ref_id=p_ref,
                                                            org_ref_id=org_ref,
                                                            tpcc_added_by_ref_user_id=tpcc_added_by_ref_user,
                                                            pc_ref_id=pc_ref,
                                                            pcc_ref_id=pcc_ref,
                                                            opg_ref_id=opg_ref,
                                                            tpcc_name=tpcc_name,
                                                            tpcc_status=tpcc_status,
                                                            tpcc_billable=tpcc_billable,
                                                            tpcc_assignee_people_ref_u_id=tpcc_assignee_people_ref_u_id)
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            
            

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = TaskProjectCategoriesChecklist.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})

# @method_decorator([AutorizationRequired], name='dispatch')
class TimesheetMasterApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = TimesheetMaster.objects.filter(id=id).values()
            return Response({'result':{'status':'GET by Id','data':all_data}})
        else:
            all_data = TimesheetMaster.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data
        tm_ref_user = data.get('tm_ref_user')
        ula_ref = data.get('ula_ref')
        org_ref = data.get('org_ref')
        tm_approver_ref_user = data.get('tm_approver_ref_user')
        tm_status = data.get('tm_status')
        tm_leave_holiday_conflict = data.get('tm_leave_holiday_conflict')
        tm_auto_approved = data.get('tm_auto_approved')
        tm_deadline_status = data.get('tm_deadline_status')

        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        try:
            TimesheetMaster.objects.create(
                tm_ref_user_id = tm_ref_user,
                ula_ref_id = ula_ref,
                org_ref_id = org_ref,
                tm_approver_ref_user_id = tm_approver_ref_user,
                tm_status = tm_status,
                tm_leave_holiday_conflict = tm_leave_holiday_conflict,
                tm_auto_approved = tm_auto_approved,
                tm_deadline_status = tm_deadline_status,
            )


            posts = TimesheetMaster.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        data = request.data
        
        tm_ref_user = data.get('tm_ref_user')
        ula_ref = data.get('ula_ref')
        org_ref = data.get('org_ref')
        tm_approver_ref_user = data.get('tm_approver_ref_user')
        tm_status = data.get('tm_status')
        tm_leave_holiday_conflict = data.get('tm_leave_holiday_conflict')
        tm_auto_approved = data.get('tm_auto_approved')
        tm_deadline_status = data.get('tm_deadline_status')


        
        try:
        
            TimesheetMaster.objects.filter(id=pk).update(
                tm_ref_user_id = tm_ref_user,
                ula_ref_id = ula_ref,
                org_ref_id = org_ref,
                tm_approver_ref_user_id = tm_approver_ref_user,
                tm_status = tm_status,
                tm_leave_holiday_conflict = tm_leave_holiday_conflict,
                tm_auto_approved = tm_auto_approved,
                tm_deadline_status = tm_deadline_status,
                )
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def delete(self,request,pk):
        all_values = TimesheetMaster.objects.filter(id=pk).delete()
        return Response({'result':{'status':'deleted'}})


# @method_decorator([AutorizationRequired], name='dispatch')
class TimesheetMasterDetailsApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        all_data = TimesheetMasterDetails.objects.filter(id=id).values()
        if id:
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = TimesheetMasterDetails.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data
        
        tmd_ref_tm = data.get('tmd_ref_tm')
        tmd_ref_user = data.get('tmd_ref_user')
        org_ref = data.get('org_ref')
        c_ref = data.get('c_ref')
        p_ref = data.get('p_ref')
        tpcc_ref = data.get('tpcc_ref')
        ula_ref = data.get('ula_ref')
        tmd_approver_ref_user = data.get('tmd_approver_ref_user')
        tmd_timer_status = data.get('tmd_timer_status')
        tmd_description = data.get('tmd_description')
        tmd_status = data.get('tmd_status')
        tmd_halfday_status = data.get('tmd_halfday_status')
        tmd_leave_holiday_conflict = data.get('tmd_leave_holiday_conflict')
        tmd_auto_approved = data.get('tmd_auto_approved')
        tmd_deadline_status = data.get('tmd_deadline_status')

        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



       
        try:
            TimesheetMasterDetails.objects.create(tmd_ref_user_id=tmd_ref_user,
                                                    org_ref_id=org_ref,
                                                    c_ref_id=c_ref,
                                                    p_ref_id=p_ref,
                                                    tpcc_ref_id=tpcc_ref,
                                                    ula_ref_id=ula_ref,
                                                    tmd_approver_ref_user_id=tmd_approver_ref_user,
                                                    tmd_timer_status=tmd_timer_status,
                                                    tmd_description=tmd_description,
                                                    tmd_status=tmd_status,
                                                    tmd_halfday_status=tmd_halfday_status,
                                                    tmd_leave_holiday_conflict=tmd_leave_holiday_conflict,
                                                    tmd_auto_approved=tmd_auto_approved,
                                                    tmd_deadline_status=tmd_deadline_status)


            posts = TimesheetMasterDetails.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def put(self,request,pk):
        data = request.data
        
        tmd_ref_tm = data.get('tmd_ref_tm')
        tmd_ref_user = data.get('tmd_ref_user')
        org_ref = data.get('org_ref')
        c_ref = data.get('c_ref')
        p_ref = data.get('p_ref')
        tpcc_ref = data.get('tpcc_ref')
        ula_ref = data.get('ula_ref')
        tmd_approver_ref_user = data.get('tmd_approver_ref_user')
        tmd_timer_status = data.get('tmd_timer_status')
        tmd_description = data.get('tmd_description')
        tmd_status = data.get('tmd_status')
        tmd_halfday_status = data.get('tmd_halfday_status')
        tmd_leave_holiday_conflict = data.get('tmd_leave_holiday_conflict')
        tmd_auto_approved = data.get('tmd_auto_approved')
        tmd_deadline_status = data.get('tmd_deadline_status')



        
        try:
            TimesheetMasterDetails.objects.filter(id=pk).update(
                tmd_ref_tm_id = tmd_ref_tm,
                tmd_ref_user_id = tmd_ref_user,
                org_ref_id = org_ref,
                c_ref_id = c_ref,
                p_ref_id = p_ref,
                tpcc_ref_id = tpcc_ref,
                ula_ref_id = ula_ref,
                tmd_approver_ref_user_id = tmd_approver_ref_user,
                tmd_timer_status = tmd_timer_status,
                tmd_description = tmd_description,
                tmd_status = tmd_status,
                tmd_halfday_status = tmd_halfday_status,
                tmd_leave_holiday_conflict = tmd_leave_holiday_conflict,
                tmd_auto_approved = tmd_auto_approved,
                tmd_deadline_status = tmd_deadline_status,
            )
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            
            

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = TimesheetMasterDetails.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})



# @method_decorator([AutorizationRequired], name='dispatch')
class UserApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = CustomUser.objects.filter(id=id).values()
            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = CustomUser.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        
        data = request.data
        u_first_name = data.get('u_first_name')  
        u_last_name = data.get('u_last_name')  
        u_gender = data.get('u_gender')  
        u_marital_status = data.get('u_marital_status')  
        u_phone_no        = data.get('u_phone_no')
        email         = data.get('email')
        password      = data.get('password')
        u_org_code = data.get('org_code')
        u_designation = data.get('u_designation')
        

        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)
            if User.objects.filter(Q(username=email)|Q(email=email)).exists():
                return Response({'error':'User Already Exists'})
            else:
                try:
                    create_user = User.objects.create_user(username=email,email=email,password=password)
                    user_create = CustomUser.objects.create(
                        user_created_by_id=create_user.id,
                        u_email=email,
                        u_designation=u_designation,
                        u_phone_no=u_phone_no,
                        u_org_code=u_org_code,
                        u_first_name=u_first_name,
                        u_last_name=u_last_name,
                        u_gender=u_gender,
                        u_marital_status=u_marital_status,
                        )

                    posts = CustomUser.objects.all().values()
                    paginator = Paginator(posts,10)
                    try:
                        page_obj = paginator.get_page(selected_page_no)
                    except PageNotAnInteger:
                        page_obj = paginator.page(1)
                    except EmptyPage:
                        page_obj = paginator.page(paginator.num_pages)
                    return Response({'result':{'status':'Created','data':list(page_obj)}})
                except IntegrityError as e:
                    error_message = e.args
                    return Response({
                    'error':{'message':'DB error!',
                    'detail':error_message,
                    'status_code':status.HTTP_400_BAD_REQUEST,
                    }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        
        data = request.data
        user_id = data.get('user_id')  
        custom_user_id = data.get('custom_user_id')  
        u_first_name = data.get('u_first_name')  
        u_last_name = data.get('u_last_name')  
        u_gender = data.get('u_gender')  
        u_marital_status = data.get('u_marital_status')  
        u_phone_no        = data.get('u_phone_no')
        email         = data.get('email')
        password      = data.get('password')
        u_org_code = data.get('org_code')
        u_designation = data.get('u_designation')
        

        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)
            if User.objects.filter(Q(username=email)|Q(email=email)).exists():
                return Response({'error':'User Already Exists'})
            else:
                try:
                    create_user = User.objects.filter(id=user_id).update(username=email,email=email,password=password)
                    user_create = CustomUser.objects.filter(id=custom_user_id).update(
                        user_created_by_id=create_user.id,
                        u_email=email,
                        u_designation=u_designation,
                        u_phone_no=u_phone_no,
                        u_org_code=u_org_code,
                        u_first_name=u_first_name,
                        u_last_name=u_last_name,
                        u_gender=u_gender,
                        u_marital_status=u_marital_status,
                        )

                    posts = CustomUser.objects.all().values()
                    paginator = Paginator(posts,10)
                    try:
                        page_obj = paginator.get_page(selected_page_no)
                    except PageNotAnInteger:
                        page_obj = paginator.page(1)
                    except EmptyPage:
                        page_obj = paginator.page(paginator.num_pages)
                    return Response({'result':{'status':'updated','data':list(page_obj)}})
                except IntegrityError as e:
                    error_message = e.args
                    return Response({
                    'error':{'message':'DB error!',
                    'detail':error_message,
                    'status_code':status.HTTP_400_BAD_REQUEST,
                    }},status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
        test = (0,{})
        c_values = CustomUser.objects.filter(user_created_by_id=pk).delete()         
        u_values = User.objects.filter(id=pk).delete()
        
        if test == c_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})



# @method_decorator([AutorizationRequired], name='dispatch')
class  PrefixSuffixApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = PrefixSuffix.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = PrefixSuffix.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data
        prefix = data.get('prefix')
        suffix = data.get('suffix')
        prefixsuffix_status=data.get('prefixsuffix_status')
        


        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            PrefixSuffix.objects.create(prefix=prefix,
                                        suffix=suffix,
                                        prefixsuffix_status=prefixsuffix_status
                                        )


            posts = PrefixSuffix.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        data = request.data
        
        prefix = data.get('prefix')
        suffix = data.get('suffix')
        prefixsuffix_status=data.get('prefixsuffix_status')
        


        
        
        try:
            PrefixSuffix.objects.filter(id=pk).update(prefix=prefix,
                                        suffix=suffix,
                                        prefixsuffix_status=prefixsuffix_status)
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = PrefixSuffix.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})



# @method_decorator([AutorizationRequired], name='dispatch')
class  CenterApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = Center.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = Center.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data
        center_name = data.get('center_name')
        sd=data.get('year_start_date')
        yed=data.get('year_end_date')
        center_status=data.get('center_status')
        
        


        selected_page_no =1 
        page_number = request.GET.get('page')

        year_start_date = time.mktime(datetime.datetime.strptime(sd, "%d/%m/%Y").timetuple())
        year_end_date = time.mktime(datetime.datetime.strptime(yed, "%d/%m/%Y").timetuple())
        
        
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            Center.objects.create(center_name=center_name,year_start_date=year_start_date,
                                                        year_end_date=year_end_date,center_status=center_status)


            posts = Center.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        data = request.data
        
        center_name = data.get('center_name')
        sd=data.get('year_start_date')
        yed=data.get('year_end_date')
        center_status=data.get('center_status')

        year_start_date = time.mktime(datetime.datetime.strptime(sd, "%d/%m/%Y").timetuple())
        year_end_date = time.mktime(datetime.datetime.strptime(yed, "%d/%m/%Y").timetuple())
        

        
        try:
            Center.objects.filter(id=pk).update(center_name=center_name,year_start_date=year_start_date,
                                                        year_end_date=year_end_date,center_status=center_status
                                        )
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = Center.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})




# @method_decorator([AutorizationRequired], name='dispatch')
class  PeopleApiView(GenericAPIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = People.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = People.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data

        # name = data['name']
        prefix_suffix  = data.get('prefix_suffix_id')
        department= data.get('department_id')
        role= data.get('role_id')
        cost_center= data.get('cost_center_id')
        reporting_manager=data.get('reporting_manager_id')
        first_name= data.get('first_name')
        last_name= data.get('last_name')
        email_id= data.get('email_id')
        marital_status= data.get('marital_status')
        gender= data.get('gender')
        designation= data.get('designation')
        tags= data.get('tags')
        doj=data.get('date_of_joining')
        people_status=data.get('people_status')
        
        photo = data['photo']
        base64_data = photo
        split_base_url_data=photo.split(';base64,')[1]
        imgdata1 = base64.b64decode(split_base_url_data)

        data_split = photo.split(';base64,')[0]
        extension_data = re.split(':|;', data_split)[1] 
        guess_extension_data = guess_extension(extension_data)

        filename1 = "/eztime/site/public/media/photo/"+first_name+guess_extension_data
        # filename1 = "/Users/apple/EzTime/eztimeproject/media/photo"+first_name+guess_extension_data
        fname1 = '/photo/'+first_name+guess_extension_data
        ss=  open(filename1, 'wb')
        print(ss)
        ss.write(imgdata1)
        ss.close()   
        
        
        

        # photo =  request.FILES['photo']
        # print(photo,'pppppppppppppppp')

        
        

                       

        selected_page_no =1 
        page_number = request.GET.get('page')
        date_of_joining = time.mktime(datetime.datetime.strptime(doj, "%d/%m/%Y").timetuple())
        print(date_of_joining,'dateeeeeeeeeeeeeeeeeee')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            people_data = People.objects.create(prefix_suffix_id=prefix_suffix,
                                    department_id=department,
                                    role_id=role,
                                    cost_center_id=cost_center,
                                    reporting_manager_id=reporting_manager,
                                    first_name=first_name,
                                    last_name=last_name,
                                    email_id=email_id,
                                    marital_status=marital_status,
                                    gender=gender,
                                    designation=designation,
                                    tags=tags,
                                    date_of_joining=date_of_joining,
                                    people_status=people_status,
                                    photo =fname1,
                                    base64=base64_data)


            print(type(people_data.photo),'peoplee dattt')
            if photo:
                # people_data.photo_path = 'http://127.0.0.1:8000/media/photo/'+ (str(people_data.photo)).split('photo/')[1]
                people_data.photo_path = 'https://eztime.thestorywallcafe.com/media/photo/'+ (str(people_data.photo)).split('photo/')[1]
                people_data.save()



            posts = People.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        data = request.data
        prefix_suffix  = data.get('prefix_suffix_id')
        department= data.get('department_id')
        role= data.get('role_id')
        cost_center= data.get('cost_center_id')
        reporting_manager=data.get('reporting_manager_id')
        first_name= data.get('first_name')
        last_name= data.get('last_name')
        email_id= data.get('email_id')
        marital_status= data.get('marital_status')
        gender= data.get('gender')
        designation= data.get('designation')
        tags= data.get('tags')
        doj=data.get('date_of_joining')
        people_status=data.get('people_status')
        # photo =  request.FILES['photo']
        # photo_path = data.get('photo_path')
        # name = data['name']
        date_of_joining = time.mktime(datetime.datetime.strptime(doj, "%d/%m/%Y").timetuple())
        photo = data['photo']
        print(photo,'Attttttttttttttttttttt')
        if photo == '':
            print('in if nulll looopp')
            try:
                People.objects.filter(id=pk).update(prefix_suffix_id=prefix_suffix,
                                    department_id=department,
                                    role_id=role,
                                    cost_center_id=cost_center,
                                    reporting_manager_id=reporting_manager,
                                    first_name=first_name,
                                    last_name=last_name,
                                    email_id=email_id,
                                    marital_status=marital_status,
                                    gender=gender,
                                    designation=designation,
                                    tags=tags,
                                    date_of_joining=date_of_joining,
                                    people_status=people_status,
                                    # photo =fname1,
                                    # base64=base64_data
                                        )


                return Response({'result':{'status':'Updated'}})
            except IntegrityError as e:
                error_message = e.args
                return Response({
                'error':{'message':'DB error!',
                'detail':error_message,
                'status_code':status.HTTP_400_BAD_REQUEST,
                }},status=status.HTTP_400_BAD_REQUEST)
                




        base64_data =photo
        split_base_url_data=photo.split(';base64,')[1]
        imgdata1 = base64.b64decode(split_base_url_data)

        data_split = photo.split(';base64,')[0]
        extension_data = re.split(':|;', data_split)[1] 
        guess_extension_data = guess_extension(extension_data)

        filename1 = "/eztime/site/public/media/photo/"+first_name+guess_extension_data
        # filename1 = "/Users/apple/EzTime/eztimeproject/media/photo"+first_name+guess_extension_data
        fname1 = '/photo/'+first_name+guess_extension_data
        ss=  open(filename1, 'wb')
        print(ss)
        ss.write(imgdata1)
        ss.close()   
        
        


        # date_of_joining = time.mktime(datetime.datetime.strptime(doj, "%d/%m/%Y").timetuple())
        # print(date_of_joining)
        
        try:
            People.objects.filter(id=pk).update(prefix_suffix_id=prefix_suffix,
                                    department_id=department,
                                    role_id=role,
                                    cost_center_id=cost_center,
                                    reporting_manager_id=reporting_manager,
                                    first_name=first_name,
                                    last_name=last_name,
                                    email_id=email_id,
                                    marital_status=marital_status,
                                    gender=gender,
                                    designation=designation,
                                    tags=tags,
                                    date_of_joining=date_of_joining,
                                    people_status=people_status,
                                    photo =fname1,
                                    base64=base64_data
                                        )
           
            people_data = People.objects.get(id=pk)
            print(str(people_data),'all_dataaaaaaaaaaaaa')
            print(type(people_data.photo),'peoplee dattt')
            if photo:
                # people_data.photo_path = 'http://127.0.0.1:8000/media/photo/'+ (str(people_data.photo)).split('photo/')[1]
                
                people_data.photo_path = 'https://eztime.thestorywallcafe.com/media/photo/'+ (str(people_data.photo)).split('photo/')[1]
                people_data.save()


            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = People.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})



# @method_decorator([AutorizationRequired], name='dispatch')
class  TagApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = Tag.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = Tag.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data
        tag_name = data.get('tag_name')
        tage_status = data.get('tage_status')
        
        


        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            Tag.objects.create(tag_name=tag_name,
                                    tage_status=tage_status)


            posts = Tag.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        data = request.data
        
        tag_name = data.get('tag_name')
        tage_status=data.get('tage_status')

        
        try:
            Tag.objects.filter(id=pk).update(tag_name=tag_name,tage_status=tage_status
                                        )
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = Tag.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})



# @method_decorator([AutorizationRequired], name='dispatch')
class  TimeSheetApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = TimeSheet.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = TimeSheet.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data
        client  = data.get('client_id')
        project= data.get('project_id')
        task= data.get('task_id')
        time_spent= data.get('time_spent')
        description= data.get('description')
        timesheet_status= data.get('timesheet_status')
        tdt= data.get('timesheet_date')
        timesheet_date_timestamp = time.mktime(datetime.datetime.strptime(tdt, "%d/%m/%Y").timetuple())
        print(timesheet_date_timestamp,'stamppppppppppppppp')


        selected_page_no =1 
        page_number = request.GET.get('page')
        
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            TimeSheet.objects.create(client_id=client,
                                    project_id=project,
                                    task_id=task,
                                    time_spent=time_spent,
                                    description=description,
                                    timesheet_status=timesheet_status,
                                    timesheet_date_timestamp=timesheet_date_timestamp,)


            posts = TimeSheet.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        data = request.data
        
        client  = data.get('client_id')
        project= data.get('project_id')
        task= data.get('task_id')
        time_spent= data.get('time_spent')
        description= data.get('description')
        timesheet_status= data.get('timesheet_status')
        tdt= data.get('timesheet_date')
        timesheet_date_timestamp = time.mktime(datetime.datetime.strptime(tdt, "%d/%m/%Y").timetuple())
        print(timesheet_date_timestamp,'stamppppppppppppppp')

        

        
        try:
            TimeSheet.objects.filter(id=pk).update(client_id=client,
                                    project_id=project,
                                    task_id=task,
                                    time_spent=time_spent,
                                    description=description,
                                    timesheet_status=timesheet_status,
                                    timesheet_date_timestamp=timesheet_date_timestamp,
                                        )
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = TimeSheet.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})



# @method_decorator([AutorizationRequired], name='dispatch')
class  MasterLeaveTypesApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = MasterLeaveTypes.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = MasterLeaveTypes.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data
        leave_title = data.get('leave_title')
        leave_type= data.get('leave_type')
        no_of_leaves= data.get('no_of_leaves')
        carry_forward_per= data.get('carry_forward_per')
        gracefull_days= data.get('gracefull_days')
        encashment= data.get('encashment')
        max_encashments= data.get('max_encashments')
        action= data.get('action')
        description =data.get('description')
        accrude_monthly=data.get('accrude_monthly')
        yearly_leaves=data.get('yearly_leaves')
        monthly_leaves=data.get('monthly_leaves')
        leave_applicable_for=data.get('leave_applicable_for')
        
        
        

        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            MasterLeaveTypes.objects.create(leave_title=leave_title,
                                                leave_type=leave_type,
                                                no_of_leaves=no_of_leaves,
                                                carry_forward_per=carry_forward_per,
                                                gracefull_days=gracefull_days,
                                                encashment=encashment,
                                                max_encashments=max_encashments,
                                                action=action,
                                                description=description,
                                                accrude_monthly=accrude_monthly,
                                                yearly_leaves=yearly_leaves,
                                                monthly_leaves=monthly_leaves,
                                                leave_applicable_for=leave_applicable_for,)


            posts = MasterLeaveTypes.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        data = request.data
        
        leave_title = data.get('leave_title')
        leave_type= data.get('leave_type')
        no_of_leaves= data.get('no_of_leaves')
        carry_forward_per= data.get('carry_forward_per')
        gracefull_days= data.get('gracefull_days')
        encashment= data.get('encashment')
        max_encashments= data.get('max_encashments')
        action= data.get('action')
        description =data.get('description')
        accrude_monthly=data.get('accrude_monthly')
        yearly_leaves=data.get('yearly_leaves')
        monthly_leaves=data.get('monthly_leaves')
        leave_applicable_for=data.get('leave_applicable_for')
        
        

        
        try:
            MasterLeaveTypes.objects.filter(id=pk).update(leave_title=leave_title,
                                                leave_type=leave_type,
                                                no_of_leaves=no_of_leaves,
                                                carry_forward_per=carry_forward_per,
                                                gracefull_days=gracefull_days,
                                                encashment=encashment,
                                                max_encashments=max_encashments,
                                                action=action,
                                                description=description,
                                                accrude_monthly=accrude_monthly,
                                                yearly_leaves=yearly_leaves,
                                                monthly_leaves=monthly_leaves,
                                                leave_applicable_for=leave_applicable_for,)
                                        
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = MasterLeaveTypes.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})



# @method_decorator([AutorizationRequired], name='dispatch')
class  leaveApplicationApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = leaveApplication.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = leaveApplication.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):
        data = request.data
        leave_type=data.get('leave_type_id')
        reason=data.get('reason')
        contact_details=data.get('contact_details')
        leave_application_file_attachment=data.get('leave_application_file_attachment')
        cc_to=data.get('cc_to')
        lfd=data.get('leaveApplication_from_date')
        ltd=data.get('leaveApplication_to_date')
        days=data.get('days')
        from_session=data.get('from_session')
        to_session=data.get('to_session')
        balance=data.get('balance')

        leaveApplication_from_date = time.mktime(datetime.datetime.strptime(lfd, "%d/%m/%Y").timetuple())
        print(leaveApplication_from_date,'stamppppppppppppppp')

        leaveApplication_to_date = time.mktime(datetime.datetime.strptime(ltd, "%d/%m/%Y").timetuple())
        print(leaveApplication_to_date,'stamppppppppppppppp')
        
        


        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)



        
        try:
            leaveApplication.objects.create(leave_type_id=leave_type,
                                            reason=reason,
                                            contact_details=contact_details,
                                            leave_application_file_attachment=leave_application_file_attachment,
                                            cc_to=cc_to,
                                            leaveApplication_from_date=leaveApplication_from_date,
                                            leaveApplication_to_date=leaveApplication_to_date,
                                            days=days,
                                            from_session=from_session,
                                            to_session=to_session,
                                            balance=balance,)


            posts = leaveApplication.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        data = request.data
        
        leave_type=data.get('leave_type_id')
        reason=data.get('reason')
        contact_details=data.get('contact_details')
        leave_application_file_attachment=data.get('leave_application_file_attachment')
        cc_to=data.get('cc_to')
        leaveApplication_from_date=data.get('leaveApplication_from_date')
        leaveApplication_to_date=data.get('leaveApplication_to_date')
        days=data.get('days')
        from_session=data.get('from_session')
        to_session=data.get('to_session')
        balance=data.get('balance')
        

        
        try:
            leaveApplication.objects.filter(id=pk).update(leave_type_id=leave_type,
                                            reason=reason,
                                            contact_details=contact_details,
                                            leave_application_file_attachment=leave_application_file_attachment,
                                            cc_to=cc_to,
                                            leaveApplication_from_date=leaveApplication_from_date,
                                            leaveApplication_to_date=leaveApplication_to_date,
                                            days=days,
                                            from_session=from_session,
                                            to_session=to_session,
                                            balance=balance,
                                        )
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = leaveApplication.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})





# @method_decorator([AutorizationRequired], name='dispatch')
class  ProfileApiView(APIView):
    def get(self,request):
        id = request.query_params.get('id')
        if id:
            all_data = Profile.objects.filter(id=id).values()
            if not all_data:
                return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)

            return Response({'result':{'status':'GET by Id','data':all_data}})


        else:
            all_data = Profile.objects.all().values()
            return Response({'result':{'status':'GET','data':all_data}})

    def post(self,request):

        data = request.data

        first_name=data.get('first_name')
        last_name=data.get('last_name')
        designation=data.get('designation')
        email_id=data.get('email_id')
        user_address_details=data.get('user_address_details')
        country=data.get('country')
        state=data.get('state')
        city=data.get('city')
        address=data.get('address')
        phone_number=data.get('phone_number')
        dob=data.get('dob')
        tags=data.get('tags')
        postal_code=data.get('postal_code')
        # user_profile_photo=request.FILES['user_profile_photo']

        date_of_birth = time.mktime(datetime.datetime.strptime(dob, "%d/%m/%Y").timetuple())
        
        user_profile_photo = data['user_profile_photo']
        base64_data =user_profile_photo
        split_base_url_data=user_profile_photo.split(';base64,')[1]
        imgdata1 = base64.b64decode(split_base_url_data)

        data_split = user_profile_photo.split(';base64,')[0]
        extension_data = re.split(':|;', data_split)[1] 
        guess_extension_data = guess_extension(extension_data)

        # print(guess_extension_data,'guess_extension_data')
        filename1 = "/eztime/site/public/media/user_profile_photo/"+first_name+guess_extension_data
        # filename1 = "D:/EzTime/eztimeproject/media/photo/"+name+'.png'
        fname1 = '/user_profile_photo/'+first_name+guess_extension_data
        ss=  open(filename1, 'wb')
        print(ss)
        ss.write(imgdata1)
        ss.close()   

        
        


        selected_page_no =1 
        page_number = request.GET.get('page')
        if page_number:
            selected_page_no = int(page_number)

        try:
            profile_data = Profile.objects.create(first_name=first_name,
                last_name=last_name,
                designation=designation,
                email_id=email_id,
                user_address_details=user_address_details,
                country=country,
                state=state,
                city=city,
                address=address,
                phone_number=phone_number,
                dob=date_of_birth,
                tags=tags,
                postal_code=postal_code,
                base64=base64_data,

                user_profile_photo=fname1,
                
                )

            if user_profile_photo:
                # profile_data.photo_path = 'http://127.0.0.1:8000/media/user_profile_photo/'+ (str(profile_data.user_profile_photo)).split('user_profile_photo/')[1]
                profile_data.photo_path = 'https://eztime.thestorywallcafe.com/media/user_profile_photo/'+ (str(profile_data.user_profile_photo)).split('user_profile_photo/')[1]
                profile_data.save()



            posts = Profile.objects.all().values()
            paginator = Paginator(posts,10)
            try:
                page_obj = paginator.get_page(selected_page_no)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            return Response({'result':{'status':'Created','data':list(page_obj)}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,pk):
        
        data = request.data

        first_name=data.get('first_name')
        last_name=data.get('last_name')
        designation=data.get('designation')
        email_id=data.get('email_id')
        user_address_details=data.get('user_address_details')
        country=data.get('country')
        state=data.get('state')
        city=data.get('city')
        address=data.get('address')
        phone_number=data.get('phone_number')
        dob=data.get('dob')
        tags=data.get('tags')
        postal_code=data.get('postal_code')
        # user_profile_photo=request.FILES['user_profile_photo']
        date_of_birth = time.mktime(datetime.datetime.strptime(dob, "%d/%m/%Y").timetuple())
        
        user_profile_photo = data['user_profile_photo']
        print(user_profile_photo,'Attttttttttttttttttttt')
        if user_profile_photo == '':
            print('in if nulll looopp')
            try:
                Profile.objects.filter(id=pk).update(
                    first_name=first_name,
                    last_name=last_name,
                    designation=designation,
                    email_id=email_id,
                    user_address_details=user_address_details,
                    country=country,
                    state=state,
                    city=city,
                    address=address,
                    phone_number=phone_number,
                    tags=tags,
                    postal_code=postal_code,
                    dob=date_of_birth,
                    # base64 =base64_data,

                    # user_profile_photo=fname1,
                                        )

                return Response({'result':{'status':'Updated'}})
            except IntegrityError as e:
                error_message = e.args
                return Response({
                'error':{'message':'DB error!',
                'detail':error_message,
                'status_code':status.HTTP_400_BAD_REQUEST,
                }},status=status.HTTP_400_BAD_REQUEST)
                




        base64_data =user_profile_photo
        split_base_url_data=user_profile_photo.split(';base64,')[1]
        imgdata1 = base64.b64decode(split_base_url_data)
        
        data_split = user_profile_photo.split(';base64,')[0]
        extension_data = re.split(':|;', data_split)[1] 
        guess_extension_data = guess_extension(extension_data)

        filename1 = "/eztime/site/public/media/user_profile_photo/"+first_name+guess_extension_data
        # filename1 = "D:/EzTime/eztimeproject/media/photo/"+name+'.png'
        fname1 = '/user_profile_photo/'+first_name+guess_extension_data
        ss=  open(filename1, 'wb')
        print(ss)
        ss.write(imgdata1)
        ss.close()   
        

        
        try:
            Profile.objects.filter(id=pk).update(first_name=first_name,
                last_name=last_name,
                designation=designation,
                email_id=email_id,
                user_address_details=user_address_details,
                country=country,
                state=state,
                city=city,
                address=address,
                phone_number=phone_number,
                tags=tags,
                postal_code=postal_code,
                dob=date_of_birth,
                base64 =base64_data,

                user_profile_photo=fname1,
                                        )
            profile_data = Profile.objects.get(id=pk)
            if user_profile_photo:
                # profile_data.photo_path = 'http://127.0.0.1:8000/media/user_profile_photo/'+ (str(profile_data.user_profile_photo)).split('user_profile_photo/')[1]
                profile_data.photo_path = 'https://eztime.thestorywallcafe.com/media/user_profile_photo/'+ (str(profile_data.user_profile_photo)).split('user_profile_photo/')[1]
                profile_data.save()
            return Response({'result':{'status':'Updated'}})
        except IntegrityError as e:
            error_message = e.args
            return Response({
            'error':{'message':'DB error!',
            'detail':error_message,
            'status_code':status.HTTP_400_BAD_REQUEST,
            }},status=status.HTTP_400_BAD_REQUEST)
            

    def delete(self,request,pk):
        test = (0,{})
            
        all_values = Profile.objects.filter(id=pk).delete()
        if test == all_values:

            return Response({
                'error':{'message':'Record not found!',
                'status_code':status.HTTP_404_NOT_FOUND,
                }},status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'result':{'status':'deleted'}})


# @method_decorator([AutorizationRequired], name='dispatch')
class DashBoardview(APIView):
    def post(self,request):
        data = request.data
   
        roles = OrganizationRoles.objects.filter().count()
        print(roles,'rollll')
        industry = TypeOfIndustries.objects.filter().count()

        department = OrganizationDepartment.objects.filter().count()

        return Response({'result':{'no_of_roles':roles,'no_of_industries':industry,'no_of_department':department}})






















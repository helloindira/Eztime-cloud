from django.urls import path, include,re_path
from . import views

from rest_framework import routers
from django.conf.urls.static import static
from django.conf.urls import url
from eztimeapp.views import *
from .views import *


app_name = 'eztimeapp'

urlpatterns = [

    path('register', RegistrationApiVew.as_view()),
    path('login', LoginView.as_view()),
    path('forgot-password-send-otp', ForgotPasswordSendOtp.as_view()),
    path('otp-verify-forgot-pass', OtpVerificationForgotpass.as_view()),
    path('password-reset', ForgotPasswordReset.as_view()),
    path('change-password', ChangePassword.as_view(), name="ChangePassword"),

    path('organization', OrganizationApiView.as_view()),
    path('organization/<int:pk>', OrganizationApiView.as_view()),

    path('type-of-industries', TypeOfIndustriesApiView.as_view()),
    path('type-of-industries/<int:pk>', TypeOfIndustriesApiView.as_view()),

    path('clients', ClientsApiView.as_view()),
    path('clients/<int:pk>', ClientsApiView.as_view()),


    path('org-people-group', OrgPeopleGroupView.as_view()),
    path('org-people-group/<int:pk>', OrgPeopleGroupView.as_view()),

    path('organization-department', OrganizationDepartmentView.as_view()),
    path('organization-department/<int:pk>', OrganizationDepartmentView.as_view()),

    path('organization-cost-centers', OrganizationCostCentersView.as_view()),
    path('organization-cost-centers/<int:pk>', OrganizationCostCentersView.as_view()),

    path('organization-roles', OrganizationRolesView.as_view()),
    path('organization-roles/<int:pk>', OrganizationRolesView.as_view()),

    path('clients-dms', ClientsDMS.as_view()),
    path('clients-dms/<int:pk>', ClientsDMS.as_view()),


    path('clients-other-contact-details', ClientsOtherContactDetailsView.as_view()),
    path('clients-other-contact-details/<int:pk>', ClientsOtherContactDetailsView.as_view()),

    path('project-categories', ProjectCategoriesView.as_view()),
    path('project-categories/<int:pk>', ProjectCategoriesView.as_view()),

    
###########################Fara##########################################

    path('projects', ProjectsAPIView.as_view()),
    path('projects/<int:pk>', ProjectsAPIView.as_view()),

    path('task-project-categories', TaskProjectCategoriesApiView.as_view()),
    path('task-project-categories/<int:pk>', TaskProjectCategoriesApiView.as_view()),


    path('project-categories-files-templates', ProjectCategoriesFilesTemplatesApiView.as_view()),
    path('project-categories-files-templates/<int:pk>', ProjectCategoriesFilesTemplatesApiView.as_view()),



    path('project-status-main-category', ProjectStatusMainCategoryApiView.as_view()),
    path('project-status-main-category/<int:pk>', ProjectStatusMainCategoryApiView.as_view()),


    path('project-history', ProjectHistoryApiView.as_view()),
    path('project-history/<int:pk>', ProjectHistoryApiView.as_view()),

    path('project-status-sub-category', ProjectStatusSubCategoryApiView.as_view()),
    path('project-status-sub-category/<int:pk>', ProjectStatusSubCategoryApiView.as_view()),


    path('project-files', ProjectFilesApiView.as_view()),
    path('project-files/<int:pk>', ProjectFilesApiView.as_view()),


    path('geo-zones', GeoZonesApiView.as_view()),
    path('geo-zones/<int:pk>', GeoZonesApiView.as_view()),


    path('geo-time-zones', GeoTimezonesApiView.as_view()),
    path('geo-time-zones/<int:pk>', GeoTimezonesApiView.as_view()),


    path('geo-currencies', GeoCurrenciesApiView.as_view()),
    path('geo-currencies/<int:pk>', GeoCurrenciesApiView.as_view()),


    path('geo-countries', GeoCountriesApiView.as_view()),
    path('geo-countries/<int:pk>', GeoCountriesApiView.as_view()),

    path('geo-states', GeoStatesApiView.as_view()),
    path('geo-states/<int:pk>', GeoStatesApiView.as_view()),


    path('geo-cities', GeoCitiesApiView.as_view()),
    path('geo-cities/<int:pk>', GeoCitiesApiView.as_view()),


    path('geo-countries-currencies', GeoCountriesCurrenciesApiView.as_view()),
    path('geo-countries-currencies/<int:pk>', GeoCountriesCurrenciesApiView.as_view()),

    path('geo-continents', GeoContinentsApiView.as_view()),
    path('geo-continents/<int:pk>', GeoContinentsApiView.as_view()),

    path('geo-sub-continents', GeoSubContinentsApiView.as_view()),
    path('geo-sub-continents/<int:pk>', GeoSubContinentsApiView.as_view()),
#-------
    path('product-details', ProductDetailsView.as_view()),
    path('product-details/<int:pk>', ProductDetailsView.as_view()),

    path('organization-leave-type', OrganizationLeaveTypeApiView.as_view()),
    path('organization-leave-type/<int:pk>', OrganizationLeaveTypeApiView.as_view()),

    path('organization-cost-centers', OrganizationCostCentersApiView.as_view()),
    path('organization-cost-centers/<int:pk>', OrganizationCostCentersApiView.as_view()),

    path('organization-cost-centers-leave-type', OrganizationCostCentersLeaveTypeApiView.as_view()),
    path('organization-cost-centers-leave-type/<int:pk>', OrganizationCostCentersLeaveTypeApiView.as_view()),

    path('users-leave-master', UsersLeaveMasterApiView.as_view()),
    path('users-leave-master/<int:pk>', UsersLeaveMasterApiView.as_view()),

    path('organization-cost-centers-year-list', OrganizationCostCentersYearListApiView.as_view()),
    path('organization-cost-centers-year-list/<int:pk>', OrganizationCostCentersYearListApiView.as_view()),

    path('users-leave-applications', UsersLeaveApplicationsApiView.as_view()),
    path('users-leave-applications/<int:pk>', UsersLeaveApplicationsApiView.as_view()),

    path('user-leaves-allotment-list', UserLeaveAllotmentListApiView.as_view()),
    path('user-leaves-allotment-list/<int:pk>', UserLeaveAllotmentListApiView.as_view()),

    path('user-leave-list', UserLeaveListApiView.as_view()),
    path('user-leave-list/<int:pk>', UserLeaveListApiView.as_view()),

    path('project-categories-checklist', ProjectCategoriesChecklistApiView.as_view()),
    path('project-categories-checklist/<int:pk>', ProjectCategoriesChecklistApiView.as_view()),

    path('task-project-categories-checklist', TaskProjectCategoriesChecklistApiView.as_view()),
    path('task-project-categories-checklist/<int:pk>', TaskProjectCategoriesChecklistApiView.as_view()),

    path('timesheet-master-details', TimesheetMasterDetailsApiView.as_view()),
    path('timesheet-master-details/<int:pk>', TimesheetMasterDetailsApiView.as_view()),

    path('timesheet-master', TimesheetMasterApiView.as_view()),
    path('timesheet-master/<int:pk>', TimesheetMasterApiView.as_view()),

    path('custom-user', UserApiView.as_view()),
    path('custom-user/<int:pk>', UserApiView.as_view()),



    path('prefix-suffix', PrefixSuffixApiView.as_view()),
    path('prefix-suffix/<int:pk>', PrefixSuffixApiView.as_view()),
    

    path('center', CenterApiView.as_view()),
    path('center/<int:pk>', CenterApiView.as_view()),

    path('people', PeopleApiView.as_view()),
    path('people/<int:pk>', PeopleApiView.as_view()),

    path('tag', TagApiView.as_view()),
    path('tag/<int:pk>', TagApiView.as_view()),

    path('time-sheet', TimeSheetApiView.as_view()),
    path('time-sheet/<int:pk>', TimeSheetApiView.as_view()),

    path('master-leave-types', MasterLeaveTypesApiView.as_view()),
    path('master-leave-types/<int:pk>', MasterLeaveTypesApiView.as_view()),

    path('leave-application', leaveApplicationApiView.as_view()),
    path('leave-application/<int:pk>', leaveApplicationApiView.as_view()),

    path('profile', ProfileApiView.as_view()),
    path('profile/<int:pk>', ProfileApiView.as_view()),

    path('dash-board', DashBoardview.as_view()),
    
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin

# Register your models here.
model_list = [
    CustomUser,
    Organization,
    TypeOfIndustries,
    Clients,
    MasterLeaveTypes,
    PrefixSuffix,
    OrgPeopleGroup,
    ProjectCategories,
    Projects,
    TaskProjectCategories,
    ProjectCategoriesFilesTemplates,
    ProjectStatusMainCategory,
    ProjectHistory,
    ProjectStatusSubCategory,
    ProjectFiles,
    GeoZones,
    GeoTimezones,
    GeoCurrencies,
    GeoCountries,
    GeoStates,
    GeoCities,
    GeoCountriesCurrencies,
    GeoContinents,
    GeoSubContinents,
    OrganizationDepartment,
    OrganizationCostCenters,
    ClientsDms,
    ClientsOtherContactDetails,
    OrganizationRoles,
]    
admin.site.register(model_list)   


# @admin.register(Account)
# class AccountAdmin(ImportExportModelAdmin):
#     list_display = ('industry','business_type','account_type','account_name','description')

from django.db.models import fields
# from fitbit.views import getactivitylog
from .models import *
from  rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):


    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user







class CustomUserTableSerializers(serializers.ModelSerializer):
    class Meta:
        model : CustomUser
        fields = '__all__'





class OrganizationTableSerializers(serializers.ModelSerializer):
    class Meta:
        model : Organization
        fields = '__all__'


class TaskProjectCategoriesSerializers(serializers.ModelSerializer):
    class Meta:
        model : TaskProjectCategories
        fields = '__all__'

class ProjectsSerializers(serializers.ModelSerializer):
    class Meta:
        model : Projects
        fields = '__all__'


class ProjectCategoriesFilesTemplatesSerializers(serializers.ModelSerializer):
    class Meta:
        model : ProjectCategoriesFilesTemplates
        fields = '__all__'

class TypeOfIndustriesSerializers(serializers.ModelSerializer):
    class Meta:
        model : TypeOfIndustries
        fields = '__all__'

class ProjectCategoriesSerializers(serializers.ModelSerializer):
    class Meta:
        model : ProjectCategories
        fields = '__all__'

class ProjectStatusMainCategorySerializers(serializers.ModelSerializer):
    class Meta:
        model : ProjectStatusMainCategory
        fields = '__all__'


class OrgPeopleGroupsSerializers(serializers.ModelSerializer):
    class Meta:
        model : OrgPeopleGroup
        fields = '__all__'


class ProjectHistorySerializers(serializers.ModelSerializer):
    class Meta:
        model : ProjectHistory
        fields = '__all__'


class TaskProjectCategoriesSerializers(serializers.ModelSerializer):
    class Meta:
        model : TaskProjectCategories
        fields = '__all__'


class ProjectStatusSubCategorySerializers(serializers.ModelSerializer):
    class Meta:
        model : ProjectStatusSubCategory
        fields = '__all__'


class ProjectFilesCategorySerializers(serializers.ModelSerializer):
    class Meta:
        model : ProjectFiles
        fields = '__all__'

class GeoZonesCategorySerializers(serializers.ModelSerializer):
    class Meta:
        model : GeoZones
        fields = '__all__'
        

class GeoTimezonesSerializers(serializers.ModelSerializer):
    class Meta:
        model : GeoTimezones
        fields = '__all__'

class GeoCurrenciesSerializers(serializers.ModelSerializer):
    class Meta:
        model : GeoCurrencies
        fields = '__all__'


class GeoCountriesCurrenciesSerializers(serializers.ModelSerializer):
    class Meta:
        model : GeoCountriesCurrencies
        fields = '__all__'

class GeoStatesSerializers(serializers.ModelSerializer):
    class Meta:
        model : GeoStates
        fields = '__all__'

class GeoContinentsSerializers(serializers.ModelSerializer):
    class Meta:
        model : GeoContinents
        fields = '__all__'

class GeoSubContinentsSerializers(serializers.ModelSerializer):
    class Meta:
        model : GeoSubContinents
        fields = '__all__'










from django.contrib import admin
# from import_export.admin import ImportExportModelAdmin
from .models import *


@admin.register(QuestionType)
class QuestionType(admin.ModelAdmin):
    list_display = ['id','name']


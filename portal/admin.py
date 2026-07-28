from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

@admin.register(CitizenAccount)
class CitizenAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Ariza.uz", {"fields": ("middle_name","phone","normalized_phone","telegram_username","telegram_id","preferred_contact_method","department")}),)
for model in [MainCategory, SubCategory, Region, District, Neighborhood, Department, RoutingRule, ApplicationDraft, DraftAttachment, Application, Attachment, AuditLog]:
    admin.site.register(model)

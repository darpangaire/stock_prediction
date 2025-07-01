from django.contrib import admin
from .models import CustomUser
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Register your models here.
class CustomUserAdmin(BaseUserAdmin):
  list_display = ["email", "username","first_name","last_name", "is_admin"]
  list_filter = ["username"]
  fieldsets =[]
  search_fields = ["username"]
  ordering = ["username","email"]
  filter_horizontal = []
  
admin.site.register(CustomUser,CustomUserAdmin)


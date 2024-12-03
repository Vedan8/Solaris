from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser,Subscriber  # Replace with your actual custom user model

admin.site.register(CustomUser, UserAdmin)
admin.site.register(Subscriber)
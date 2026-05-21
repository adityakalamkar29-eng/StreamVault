from django.contrib import admin
from .models import Category, Video, Subscription

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'required_plan', 'created_at')
    list_filter = ('category', 'required_plan')
    search_fields = ('title', 'description')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'active', 'started_at')
    list_filter = ('plan', 'active')

from .models import Category, Video, Subscription, Plan

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'monthly_price', 'annual_price', 'max_screens', 'video_quality', 'ad_free', 'updated_at')

from django.urls import path
from . import views

urlpatterns = [
    # ── USER PANEL ──
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('category/<int:id>/', views.category, name='category'),
    path('delete-my-account/', views.delete_own_account, name='delete_own_account'),
    path('check-field/', views.check_field, name='check_field'),

    # ── SUBSCRIPTION & RAZORPAY PAYMENT ──
    path('pricing/', views.pricing, name='pricing'),
    path('subscribe/<str:plan>/', views.subscribe, name='subscribe'),
    path('payment/<str:plan>/', views.payment_gateway, name='payment_gateway'),
    path('create-razorpay-order/', views.create_razorpay_order, name='create_razorpay_order'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
    path('payment-history/', views.payment_history, name='payment_history'),
    path('razorpay-webhook/', views.razorpay_webhook, name='razorpay_webhook'),

    # ── ADMIN PANEL ──
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-category/', views.admin_category, name='admin_category'),
    path('admin-add-category/', views.add_category, name='add_category'),
    path('admin-add-video/', views.add_video, name='add_video'),
    path('admin-delete-category/<int:id>/', views.delete_category, name='delete_category'),
    path('admin-delete-video/<int:id>/', views.delete_video, name='delete_video'),
    path('admin-manage-videos/', views.manage_videos, name='manage_videos'),
    path('admin-update-video-plan/<int:id>/', views.update_video_plan, name='update_video_plan'),
    path('admin-plans/', views.admin_plans, name='admin_plans'),
    path('admin-update-plan/<int:id>/', views.update_plan, name='update_plan'),
    path('admin-manage-users/', views.manage_users, name='manage_users'),
    path('admin-update-user/<int:id>/', views.update_user, name='update_user'),
    path('admin-payments/', views.admin_payments, name='admin_payments'),
]

from django.conf import settings
from django.urls import path
from .views import home, lead_form, success_page, custom_admin_login, custom_admin_panel, custom_admin_logout, admin_lead_detail, webhook

urlpatterns = [
    path('', home, name='fillright_home'),  # Home page for fillright.silvara.uz
    
    path('lead-form/', lead_form, name='lead_form'),
    path('success/', success_page, name='success_page'),
    
    path("admin-login/", custom_admin_login, name="custom_admin_login"),
    path("admin-panel/", custom_admin_panel, name="custom_admin_panel"),
    path("admin-logout/", custom_admin_logout, name="custom_admin_logout"),
    
    path("admin/leads/<int:lead_id>/", admin_lead_detail, name="admin_lead_detail"),
    
    path(f'webhook/{settings.TELEGRAM_BOT_TOKEN}/', webhook, name='webhook'),
]
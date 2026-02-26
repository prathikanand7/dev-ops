from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.contrib.auth import views as auth_views
from . import ui_views, api_views

router = DefaultRouter()
router.register(r'notebooks', api_views.NotebookViewSet, basename='notebook')
router.register(r'jobs', api_views.JobViewSet, basename='job')

urlpatterns = [
    # ---- Authentication Paths ----
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # ---- UI Paths ----
    path('dashboard/', ui_views.DashboardView.as_view(), name='dashboard'),
    path('upload/', ui_views.NotebookUploadView.as_view(), name='upload_notebook'),

    # ---- API Token Paths ----
    path('api/token/status/', api_views.TokenStatusAPIView.as_view(), name='token_status'),
    path('api/token/generate/', api_views.GenerateTokenAPIView.as_view(), name='generate_token'),

    # ---- API Resource Paths ----
    path('api/', include(router.urls)),
]
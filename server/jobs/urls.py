from django.urls import path, include
from django.conf import settings
from rest_framework.routers import DefaultRouter
from django.contrib.auth import views as auth_views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from .views.ui_views.dashboard_view import DashboardView
from .views.ui_views.notebook_upload_view import NotebookUploadView
from .views.api_views.token_status_api_view import TokenStatusAPIView
from .views.api_views.generate_token_api_view import GenerateTokenAPIView
from .views.api_views.notebook_viewset import NotebookViewSet
from .views.api_views.job_viewset import JobViewSet

router = DefaultRouter()
router.register(r'notebooks', NotebookViewSet, basename='notebook')
router.register(r'jobs', JobViewSet, basename='job')

urlpatterns = [
    # ---- Authentication Paths ----
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # ---- UI Paths ----
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('upload/', NotebookUploadView.as_view(), name='upload_notebook'),

    # ---- API Token Paths ----
    path('api/token/status/', TokenStatusAPIView.as_view(), name='token_status'),
    path('api/token/generate/', GenerateTokenAPIView.as_view(), name='generate_token'),

    # ---- API Resource Paths ----
    path('api/', include(router.urls)),
]

# ---- DEBUG ONLY: OpenAPI Schema & Docs ----
if settings.DEBUG:
    urlpatterns += [
        path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
        path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    ]
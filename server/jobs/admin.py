from django.contrib import admin
from .models import Notebook, Job, InputFile

@admin.register(Notebook)
class NotebookAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at')
    readonly_fields = ('parameter_schema',)

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('notebook', 'user', 'status', 'created_at')
    list_filter = ('status', 'created_at')
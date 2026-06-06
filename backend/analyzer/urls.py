from django.urls import path
from . import views
urlpatterns = [path('upload/', views.upload_file, name='upload_file'), path('status/<int:carte_id>/', views.check_status, name='check_status'), path('books/', views.list_books, name='list_books')]
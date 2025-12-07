from django.urls import path
from . import views

urlpatterns = [
    path('evalio/', views.home, name='home'),
    path('join/', views.join, name='join'),
    path('interview/', views.interview, name='interview'),
    path('tool/', views.tool, name='tool'),
    path('interview/feedback/', views.feedback, name='feedback'),
    path('proctoring/', views.proctoring_view, name='proctoring'),
   
]
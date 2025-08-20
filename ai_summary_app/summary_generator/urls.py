from django.urls import path
from . import views


urlpatterns = [
  path('',      views.index,       name='index'),
  path('login/',  views.user_login,  name='login'),
  path('signup/', views.user_signup, name='signup'),
  path('logout/', views.user_logout, name='logout'),
  path('generate-summary/', views.generate_summary, name='generate-summary'),
  path('history/', views.history, name='history'),
  path('history-item/<int:pk>/', views.history_item, name='history-item'),
]
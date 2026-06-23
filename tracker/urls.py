from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register_view, name='register'),
    path('daily-submit/', views.daily_submit, name='daily_submit'),
    path('reports/', views.reports, name='reports'),
    path('goals/', views.GoalListView.as_view(), name='goal_list'),
    path('goals/create/', views.GoalCreateView.as_view(), name='goal_create'),
    path('goals/<int:pk>/edit/', views.GoalUpdateView.as_view(), name='goal_update'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/<uuid:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('users/me/', views.CurrentUserView.as_view(), name='current-user'),
    
    path('pages/', views.DeparturePageListView.as_view(), name='departurepage-list'),
    path('pages/<uuid:pk>/', views.DeparturePageDetailView.as_view(), name='departurepage-detail'),
    path('pages/<uuid:pk>/publish/', views.DeparturePagePublishView.as_view(), name='departurepage-publish'),
    path('pages/<uuid:pk>/share/', views.DeparturePageShareView.as_view(), name='departurepage-share'),
    path('pages/<uuid:pk>/view/', views.DeparturePageViewReadingView.as_view(), name='departurepage-view'),
    
]
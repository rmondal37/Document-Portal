from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('<str:user_name>/upload_file',
         views.UploadView.as_view(),
         name='upload_file'),
    path('profile/<str:user_name>',
         views.ProfileView.as_view(),
         name='profile'),
    path('delete/<int:post_id>', views.DeleteView.as_view(), name='delete'),
    path('search/', views.SearchView.as_view(), name='search')
]
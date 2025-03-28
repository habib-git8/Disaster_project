
from django.urls import path
from django.http import HttpResponse
from . import views
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home),
    path('profile/', views.profile),
    path('contact/', views.create_post),
    path('feed/', views.feed, name='feed'),  # View all posts
    path('create/', views.create_post, name='create_post'),  # Create post
    path('update/<uuid:post_id>/', views.update_post, name='update_post'),  # Edit post
    path('delete/<uuid:post_id>/', views.delete_post, name='delete_post'), 
    path("signup/", views.signup, name="signup"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("donation/", views.donation, name="donation"), 
    path('donate/<uuid:post_id>/', views.donation_page, name='donation_page'),
    path('paypalpayment/<uuid:post_id>/', views.paypalpayment, name='paypalpayment'),
    path('paypal-success/', views.paypal_success, name='paypal_success'),
    path('paypal-cancel/', views.paypal_cancel, name='paypal_cancel'),
    path('download-receipt/<uuid:donation_id>/', views.download_receipt, name='download_receipt'),
    # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]
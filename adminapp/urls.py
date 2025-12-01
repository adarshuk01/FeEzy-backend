from django.urls import path

from adminapp import views

urlpatterns = [

    path('category/',views.CategoryCreateApiView.as_view()),

    path('user/',views.ClientRegisterApiView.as_view()),

    path('token/',views.GetTokenApiView.as_view()),

    path('update-password/',views.PasswordUpdateApiView.as_view()),

    path('client/<int:pk>/',views.ClientUpdateRetrieveDeleteView.as_view()),

    path('clients/<int:pk>/renew/',views.ClientRenewApiView.as_view()),

    path('forgot-password/',views.ForgotPasswordApiView.as_view()),

    path('batch/',views.BatchCreateListApiView.as_view()),

    path('<int:pk>/batch/',views.BatchUpdateRetriveDeleteApiView.as_view()),

     path("subscriptions/",views.SubscriptionListCreateAPIView.as_view()),

    path("subscriptions/<int:pk>/",views.SubscriptionRetrieveUpdateDestroyAPIView.as_view())

    


]
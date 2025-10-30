from django.urls import path

from adminapp import views

urlpatterns = [

    path('category/',views.CategoryCreateApiView.as_view())


]
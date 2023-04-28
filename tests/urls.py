from django.urls import include, path

urlpatterns = [
    path('cml', include('cml.urls')),
]

from __future__ import absolute_import
from django.urls import path
from . import views

# main_view = views.CommerceMlExchangeView.as_view()

urlpatterns = [
    path('1c_exchange.php', views.front_view),
    path('exchange', views.front_view),
]

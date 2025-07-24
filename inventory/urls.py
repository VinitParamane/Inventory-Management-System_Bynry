from django.urls import path
from . import views

urlpatterns = [
    path('products', views.create_product),
    path('companies/<int:company_id>/alerts/low-stock', views.low_stock_alerts),

]

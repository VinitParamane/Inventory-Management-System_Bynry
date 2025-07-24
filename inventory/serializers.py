from rest_framework import serializers
from .models import Product, Inventory, Warehouse, Supplier

class ProductCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    #Stock Keeping Unit (SKU) — must be unique across all products.
    sku = serializers.CharField(max_length=50)
    # Price — stored as a decimal to avoid floating-point errors
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    warehouse_id = serializers.IntegerField()
    initial_quantity = serializers.IntegerField(min_value=0)
    supplier_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_sku(self, value):
        # If another product already uses this SKU, we reject the request.
        if Product.objects.filter(sku=value).exists():
            raise serializers.ValidationError("SKU must be unique.")
        return value

    def validate_warehouse_id(self, value):
        if not Warehouse.objects.filter(id=value).exists():
            raise serializers.ValidationError("Warehouse not found.")
        return value

    def validate_supplier_id(self, value):
        if value is not None and not Supplier.objects.filter(id=value).exists():
            raise serializers.ValidationError("Supplier not found.")
        return value

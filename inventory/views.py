from django.shortcuts import render
from datetime import timedelta
from django.utils import timezone
from .models import InventoryChangeLog

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .serializers import ProductCreateSerializer
from .models import Product, Inventory, Warehouse, Supplier

@api_view(['POST'])
def create_product(request):
    serializer = ProductCreateSerializer(data=request.data)
    if not serializer.is_valid():
        ## If the input is invalid, return detailed error messages.
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    try:
        #Use a transaction to ensure that both product and inventory  are saved together — if anything fails, nothing is written to the DB.
       
        with transaction.atomic():
            supplier = None
            if data.get('supplier_id'):
                supplier = Supplier.objects.get(id=data['supplier_id'])

            #Create the product record with the given info.
            product = Product.objects.create(
                name=data['name'],
                sku=data['sku'],
                price=data['price'],
                supplier=supplier
            )
            #Look up the target warehouse.
            warehouse = Warehouse.objects.get(id=data['warehouse_id'])

            Inventory.objects.create(
                product=product,
                warehouse=warehouse,
                quantity=data['initial_quantity']
            )
        #Return a success response with the new product's ID.
        return Response({"message": "Product created", "product_id": product.id}, status=status.HTTP_201_CREATED)

    except Exception as e:
        #If anything fails (unexpected), return a server error.
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
def low_stock_alerts(request, company_id):
    #recent sales — here, the last 30 days.
    thirty_days_ago = timezone.now() - timedelta(days=30)
    alerts = []

    # Get all warehouses for this company
    #A company may have multiple warehouses, and we need to check each.
    warehouses = Warehouse.objects.filter(company_id=company_id)

    # Loop through inventories in these warehouses
    inventories = Inventory.objects.filter(warehouse__in=warehouses).select_related('product', 'warehouse')

    for inventory in inventories:
        product = inventory.product
        warehouse = inventory.warehouse

        # Skip if product has no threshold
        if not product.low_stock_threshold:
            continue

        # Check if current stock is below threshold
        #If the current quantity is above the threshold, no alert needed.
        if inventory.quantity >= product.low_stock_threshold:
            continue

        # Get sales in the last 30 days (assume negative changes = sales)
        logs = InventoryChangeLog.objects.filter(
            inventory=inventory,
            change__lt=0,
            timestamp__gte=thirty_days_ago
        )

        total_sold = sum(abs(log.change) for log in logs)
        daily_rate = total_sold / 30 if total_sold > 0 else 0
        days_until_stockout = int(inventory.quantity / daily_rate) if daily_rate > 0 else None

        # Include only if there was recent sales activity
        #If there are no recent sales, we skip alerting — it's likely inactive.
        if total_sold == 0:
            continue
        #Build the alert entry with all required info.
        alerts.append({
            "product_id": product.id,
            "product_name": product.name,
            "sku": product.sku,
            "warehouse_id": warehouse.id,
            "warehouse_name": warehouse.name,
            "current_stock": inventory.quantity,
            "threshold": product.low_stock_threshold,
            "days_until_stockout": days_until_stockout,
            "supplier": {
                "id": product.supplier.id if product.supplier else None,
                "name": product.supplier.name if product.supplier else None,
                "contact_email": product.supplier.contact_email if product.supplier else None
            }
        })

    #Return the full list of alerts with a count.
    return Response({
        "alerts": alerts,
        "total_alerts": len(alerts)
    })



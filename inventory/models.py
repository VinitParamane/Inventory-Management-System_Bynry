from django.db import models

# Create your models here.

# Company can have multiple warehouses
class Company(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# Warehouses belong to companies
class Warehouse(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='warehouses')
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.company.name})"


# Suppliers provide products to companies
class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_email = models.EmailField()

    def __str__(self):
        return self.name


# Products can exist in multiple warehouses
class Product(models.Model):
    name = models.CharField(max_length=100)
    sku = models.CharField(max_length=50, unique=True)  # SKU must be unique
    price = models.DecimalField(max_digits=10, decimal_places=2)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    low_stock_threshold = models.PositiveIntegerField(default=10)

    def __str__(self):
        return f"{self.name} ({self.sku})"


# Inventory per product per warehouse
class Inventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventories')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='inventories')
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product', 'warehouse')  # A product can only exist once per warehouse


# Tracks when inventory levels change
class InventoryChangeLog(models.Model):
    # Logs any change in inventory quantity
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    change = models.IntegerField()  # +ve for add, -ve for removal
     # Timestamp of when the change occurred
    timestamp = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255, null=True, blank=True)


# Bundles are products that contain other products
class Bundle(models.Model):
    bundle_product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='bundle')
    components = models.ManyToManyField(Product, related_name='used_in_bundles')
    # You could extend this to store quantities of each component if needed

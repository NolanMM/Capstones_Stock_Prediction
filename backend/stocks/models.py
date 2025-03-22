from django.db import models

# Create your models here.
class StockPrice(models.Model):
    name = models.CharField(max_length=10)
    priceAtClose = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    afterHoursPrice = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    priceToEarnings = models.DecimalField(max_digits=10, decimal_places=2, null=True) 
    priceToBook = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    date = models.DateField(null=True)
    
    class Meta:
        db_table = 'StockPriceSilverData_Table'
        managed = False
        
    def __str__(self):
        return f"{self.name} - {self.date}"

class Article(models.Model):
    stock_name = models.CharField(max_length=10)
    title = models.CharField(max_length=255)
    date = models.DateField()
    description = models.TextField()
    link = models.URLField()
    
    def __str__(self):
        return self.title
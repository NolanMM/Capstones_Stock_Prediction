from django.db import models

# Create your models here.
class StockPrice(models.Model):
    Date = models.CharField(max_length=20)
    Close_Prices = models.CharField(max_length=30)
    High_Prices = models.CharField(max_length=30)
    Low_Prices = models.CharField(max_length=30)
    Open_Prices = models.CharField(max_length=30)
    Volume = models.CharField(max_length=30)
    Symbol = models.CharField(max_length=10)
    Market_Index = models.CharField(max_length=20)
    
    class Meta:
        managed = False
        db_table = 'StockPriceSilverData_Table'
        unique_together = ('Date', 'Symbol', 'Market_Index')
        
    def __str__(self):
        return f"{self.Symbol} ({self.Date})"

class Article(models.Model):
    stock_name = models.CharField(max_length=10)
    title = models.CharField(max_length=255)
    date = models.DateField()
    description = models.TextField()
    link = models.URLField()
    
    def __str__(self):
        return self.title
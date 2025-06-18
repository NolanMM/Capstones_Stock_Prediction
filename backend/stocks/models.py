from django.db import models

# Create your models here.
class StockPrice(models.Model):
    Date = models.CharField(max_length=20)
    Close_Prices = models.CharField(max_length=30)
    High_Prices = models.CharField(max_length=30)
    Low_Prices = models.CharField(max_length=30)
    Open_Prices = models.CharField(max_length=30)
    Volume = models.CharField(max_length=30)
    Stock_Symbol = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = '[Bronze].[Historical_Prices]'
        unique_together = ('Date', 'Stock_Symbol')

    def str(self):
        return f"{self.Stock_Symbol} ({self.Date})"

class Article(models.Model):
    stock_name = models.CharField(max_length=10)
    title = models.CharField(max_length=255)
    date = models.DateField()
    description = models.TextField()
    link = models.URLField()

    def str(self):
        return self.title
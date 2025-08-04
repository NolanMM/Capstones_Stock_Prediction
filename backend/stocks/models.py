from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    
class StockPriceSilver(models.Model):
    Open = models.FloatField()
    High = models.FloatField()
    Low = models.FloatField()
    Close = models.FloatField()
    Volume = models.IntegerField()
    Dividends = models.FloatField()
    Stock_Symbol = models.CharField(max_length=10)
    Stock_Splits = models.FloatField()
    Date = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = '[Silver].[Historical_Prices]'

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

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture_url = models.URLField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class PortfolioItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolio_items')
    stock_symbol = models.CharField(max_length=10)

    class Meta:
        unique_together = ('user', 'stock_symbol')

    def __str__(self):
        return f'{self.user.username} - {self.stock_symbol}'
    
class ContactMessages(models.Model):
    user_name = models.CharField(max_length=255)
    user_email = models.EmailField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=50, null=True, blank=True)
    email_subject = models.CharField(max_length=255, null=True, blank=True)
    message_text = models.TextField()
    submission_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.user_name}"
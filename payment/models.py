from django.db import models
from api.models import TelegramUser
from django.utils import timezone


# # Create your models here.
class UserProfile(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE,null=True,blank=True)
    is_pro = models.BooleanField(default=False)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    telegram_link_token = models.CharField(max_length=255, blank=True, null=True)
    daily_prediction_count = models.IntegerField(default=0)
    last_prediction_date = models.DateField(auto_now=True)
    
    def reset_count_if_new_day(self):
        from django.utils import timezone
        today = timezone.now().date()
        if self.last_prediction_date != today:
            self.daily_prediction_count = 0
            self.last_prediction_date = today
            self.save()

    

    def __str__(self):
        return f"{self.user} Profile"
      

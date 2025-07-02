from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import JSONField

# Create your models here.
User = get_user_model()

class Prediction(models.Model):
  user = models.ForeignKey(User,on_delete=models.CASCADE)
  ticker = models.CharField(max_length=10)
  created_at = models.DateTimeField(auto_now_add=True)
  next_day_price = models.FloatField()
  metrics = models.JSONField()
  plot_history_path = models.CharField(max_length=255)
  plot_pred_path = models.CharField(max_length=255)
  
  def __str__(self):
    return f"{self.ticker} prediction by {self.user.username} at {self.created_at}"
  

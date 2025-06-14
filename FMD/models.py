from django.db import models
from django.contrib.auth.models import User

class FootandMouth(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions')
    current_reference = models.IntegerField()
    year = models.IntegerField()
    cattle_density = models.IntegerField()
    rainfall = models.FloatField()
    max_temp = models.FloatField()
    adjacent_national_parks = models.FloatField()
    international_boarder = models.FloatField()
    prediction = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

 
    def __str__(self):
        return f"Prediction {self.id} for {self.user.username}"

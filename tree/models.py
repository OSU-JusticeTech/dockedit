from django.db import models

# Create your models here.


class EntryText(models.Model):
    text = models.CharField(max_length=400)

    def __str__(self):
        return self.text

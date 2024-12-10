# models.py

from django.db import models

class ProcessedModel(models.Model):
    obj_file = models.FileField(upload_to='', null=True, blank=True)
    mtl_file = models.FileField(upload_to='', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Processed Model {self.id}"

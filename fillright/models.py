from django.db import models

class Lead(models.Model):
    MEUBEL_OPTIONS = [
        ('oshxona', 'Oshxona mebeli'),
        ('yotoqxona', 'Yotoqxona mebeli'),
        ('bolalar', 'Bolalar mebeli'),
        ('yumshoq', 'Yumshoq mebellar'),
        ('shkaf', 'Shkaf va gardirob'),
        ('eshik', 'Eshiklar'),
    ]

    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    furniture_type = models.CharField(max_length=20, choices=MEUBEL_OPTIONS)

    def __str__(self):
        return f"{self.name} - {self.phone_number} - {self.furniture_type}"

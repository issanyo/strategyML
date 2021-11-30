from django.db import models


class Data(models.Model):
    price = models.FloatField()
    volume = models.FloatField()
    liquidity = models.FloatField()
    timestamp = models.DateTimeField()
    fees_pool_level = models.FloatField(verbose_name = 'fees pool level')
    fees_vault = models.FloatField(verbose_name = 'fees vault')
    il = models.FloatField(verbose_name  = 'IL')
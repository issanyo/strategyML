# Generated by Django 3.2.8 on 2021-11-30 11:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('keeperbot', '0002_rename_keeperdata_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='data',
            name='fees_pool_level',
            field=models.FloatField(verbose_name='fees_pool_level pool level'),
        ),
        migrations.AlterField(
            model_name='data',
            name='liquidity',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='data',
            name='price',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='data',
            name='timestamp',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='data',
            name='volume',
            field=models.FloatField(),
        ),
    ]

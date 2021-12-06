from django.core.management.base import BaseCommand
from datetime import datetime
from ... import views

class Command(BaseCommand):
     help = 'Fetch data from vault and strategy contracts'
     def handle(self, *args, **kwargs):
        now = datetime.now()    
        print('Downloading data on: ' + str(now))
        views.fetch()
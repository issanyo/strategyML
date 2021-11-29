from django.http import HttpResponse


def index(request):
    return HttpResponse("Keeper bot starting page")
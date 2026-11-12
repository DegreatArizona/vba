from django.middleware.csrf import get_token

def csrf_token(request):
    return {'csrf_token': get_token(request)}

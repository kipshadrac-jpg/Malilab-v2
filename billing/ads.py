"""The app-ads.txt file that AdMob asks for. It tells ad buyers which sellers are allowed to sell ads in the MaliLab app."""
from django.http import HttpResponse
from django.views.decorators.cache import cache_control

LINES = [
    'google.com, pub-4769800577067926, DIRECT, f08c47fec0942fa0',
]


@cache_control(public=True, max_age=3600)
def app_ads(request):
    return HttpResponse('\n'.join(LINES) + '\n', content_type='text/plain; charset=utf-8')

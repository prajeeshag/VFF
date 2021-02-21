from django.shortcuts import render
from django.urls import path
from django.views.generic.base import TemplateView
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator


from fixture.models import Matches
from .models import CarouselItem
from stats.models import ClubStat, PlayerStat

urlpatterns = []


##@method_decorator(cache_page(60*15), name='dispatch')
class LandingPageView(TemplateView):
    template_name = 'public/landing_page.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['upcomingmatches'] = Matches.objects.filter(
            status__in=(Matches.STATUS.fixed, Matches.STATUS.tentative)).select_related()
        ctx['pastmatches'] = Matches.objects.filter(
            status=Matches.STATUS.done).select_related().order_by('-date')
        ctx['carosels'] = CarouselItem.objects.filter(active=True)
        ctx['stats'] = ClubStat.objects.all().order_by(
            '-points', '-goal_difference',
            '-goals_for', 'goals_against').select_related()
        ctx['topscorers'] = PlayerStat.objects.filter(
            goals__gt=0).order_by('-goals').select_related()
        return ctx


urlpatterns += [path('', LandingPageView.as_view(), name='home')]

from django.shortcuts import render
from django.views.generic.base import TemplateView

from fixture.models import Matches


class LandingPageView(TemplateView):
    template_name = 'public/landing_page.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['matches'] = Matches.get_upcoming_matches()[:10]
        return ctx


class Calendar(TemplateView):
    template_name = 'public/calendar.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['matches'] = Matches.get_upcoming_matches()
        return ctx

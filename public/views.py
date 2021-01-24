from django.shortcuts import render
from django.views.generic.base import TemplateView

from fixture.models import Fixture


class LandingPageView(TemplateView):
    template_name = 'public/brochure.html'


class Calendar(TemplateView):
    template_name = 'public/calendar.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['fixture'] = Fixture.objects.first()
        return ctx

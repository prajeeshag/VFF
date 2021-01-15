from django.shortcuts import render
from django.views.generic.base import TemplateView


class LandingPageView(TemplateView):
    template_name = 'public/brochure.html'

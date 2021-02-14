from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _

from django.views import View
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from django.urls import reverse_lazy, reverse, path, include
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import PasswordChangeView
from django.core.exceptions import PermissionDenied

from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_http_methods

from guardian.shortcuts import get_objects_for_user
import rules

from extra_views import UpdateWithInlinesView, InlineFormSetFactory, ModelFormSetView

from core.mixins import viewMixins
from formtools.wizard.views import SessionWizardView

from fixture.models import Matches
from users.models import PlayerProfile, PhoneNumber

LOGIN_URL = reverse_lazy('login')

urlpatterns = []


class fixMatches(LoginRequiredMixin, viewMixins, View):
    template_name = 'dashboard/fixture/fix_matches.html'

    def get(self, request, *arg, **kwargs):
        ctx = {}
        ctx['tentative_matches'] = Matches.get_tentative_matches()
        ctx['fixed_matches'] = Matches.get_fixed_matches()
        return render(request, self.template_name, ctx)

    def post(self, request, *args, **kwargs):
        fix_pk = request.POST.get('fix_pk', None)
        ten_pk = request.POST.get('ten_pk', None)
        cancel_pk = request.POST.get('cancel_pk', None)
        post_pk = request.POST.get('post_pk', None)
        dicts = {
            fix_pk: Matches.STATUS.fixed,
            ten_pk: Matches.STATUS.tentative,
            post_pk: Matches.STATUS.postponed,
            cancel_pk: Matches.STATUS.canceled,
        }

        for pk, status in dicts.items():
            if pk:
                match = get_object_or_404(Matches, pk=pk)
                match.status = status
                match.save()
                msg = "Match {} marked {}".format(match, status)
                messages.add_message(
                    self.request, messages.WARNING, msg)

        return redirect(self.backurl)


urlpatterns += [path('fixmatches/',
                     fixMatches.as_view(),
                     name='fixmatches'), ]

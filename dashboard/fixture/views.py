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
        obj_pks_fix = request.POST.getlist('checksFix')
        obj_pks_unfix = request.POST.getlist('checksUnFix')
        if obj_pks_fix:
            Matches.objects.filter(pk__in=obj_pks_fix).update(
                status=Matches.STATUS.fixed)
        if obj_pks_unfix:
            Matches.objects.filter(pk__in=obj_pks_unfix).update(
                status=Matches.STATUS.tentative)

        fix_pk = request.POST.get('fix_pk')
        unfix_pk = request.POST.get('unfix_pk')
        if fix_pk:
            Matches.objects.filter(pk=fix_pk).update(
                status=Matches.STATUS.fixed)

        if unfix_pk:
            Matches.objects.filter(pk=unfix_pk).update(
                status=Matches.STATUS.tentative)
        return redirect(self.backurl)


urlpatterns += [path('fixmatches/',
                     fixMatches.as_view(),
                     name='fixmatches'), ]


class finalizeMatches(LoginRequiredMixin, View):
    template_name = 'dashboard/fixture/finalize_matches.html'

    def get(self, request, *arg, **kwargs):
        ctx = {}
        ctx['finalized_matches'] = Matches.get_done_matches()
        ctx['fixed_matches'] = Matches.get_fixed_matches()
        return render(request, self.template_name, ctx)

    def post(self, request, *args, **kwargs):
        obj_pks_fix = request.POST.getlist('checksFix')
        obj_pks_unfix = request.POST.getlist('checksUnFix')
        if obj_pks_fix:
            Matches.objects.filter(pk__in=obj_pks_fix).update(
                status=Matches.DONE)
        if obj_pks_unfix:
            Matches.objects.filter(pk__in=obj_pks_unfix).update(
                status=Matches.FIXED)

        ctx = {}
        ctx['finalized_matches'] = Matches.get_done_matches()
        ctx['fixed_matches'] = Matches.get_fixed_matches()
        return render(request, self.template_name, ctx)


urlpatterns += [path('finalizematches/',
                     finalizeMatches.as_view(),
                     name='finalizematches'), ]

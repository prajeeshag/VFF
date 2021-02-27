
from django import forms
from django.db.models import Count, Q, F
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _

from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView, SingleObjectMixin
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

import rules
from guardian.shortcuts import get_objects_for_user

from extra_views import UpdateWithInlinesView, InlineFormSetFactory, ModelFormSetView

from core.mixins import formviewMixins, viewMixins
from formtools.wizard.views import SessionWizardView

from .forms import EditGoalForm, EditCardForm

from . import models
from users.models import PlayerProfile
from fixture.models import Matches

urlpatterns = []


class MatchManagerRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        is_match_manager = rules.test_rule('manage_match', request.user)
        if not is_match_manager:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class EnterMatchDetailMixin:

    def get_match(self):
        return self.object

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['back_url'] = reverse(
            'dash:enterpastmatchdetails',
            kwargs={'pk': self.get_match().pk})
        return ctx

    def get_success_url(self):
        return reverse('dash:enterpastmatchdetails',
                       kwargs={'pk': self.get_match().pk})


class Squad(viewMixins, DetailView):
    template_name = 'match/squad.html'
    model = models.Squad


urlpatterns += [path('squad/<int:pk>/', Squad.as_view(), name='squad'), ]


class Substitution(viewMixins, DetailView):
    template_name = 'match/Substitution.html'
    model = models.Substitution


urlpatterns += [path('substitution/<int:pk>/',
                     Substitution.as_view(),
                     name='substitution'), ]


class MatchTimeLine(viewMixins, DetailView):
    template_name = 'match/matchtimeline.html'
    model = models.MatchTimeLine

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx


urlpatterns += [path('matchtimeline/<int:pk>/',
                     MatchTimeLine.as_view(),
                     name='matchtimeline'), ]


class SuspensionList(MatchManagerRequiredMixin, TemplateView):
    template_name = 'match/suspensions.html'

    def get_context_data(self, **kwargs):
        mdl = models.Suspension
        ctx = super().get_context_data(**kwargs)
        ctx['pending_suspensions'] = mdl.pending.all().select_related()
        ctx['other_suspensions'] = mdl.objects.exclude(
            status=mdl.STATUS.pending).select_related()
        return ctx


urlpatterns += [path('suspensions/',
                     SuspensionList.as_view(),
                     name='suspensions'), ]


class CardList(TemplateView):
    template_name = 'match/cards.html'

    def get_context_data(self, **kwargs):
        mdl = models.Cards
        ctx = super().get_context_data(**kwargs)
        ctx['cards'] = mdl.objects.filter(
            is_removed=False).select_related().order_by('-created')
        reds = mdl.objects.filter(
            color=mdl.COLOR.red, is_removed=False).values(
            'player').annotate(num=Count('player'))
        yellows = mdl.objects.filter(
            color=mdl.COLOR.yellow, is_removed=False).values(
            'player').annotate(num=Count('player'))
        num_red = {obj['player']: obj['num'] for obj in reds}
        num_yellow = {obj['player']: obj['num'] for obj in yellows}
        keys = list(set(list(num_red)) | set(list(num_yellow)))
        players = PlayerProfile.objects.filter(pk__in=keys)
        ctx['players'] = [{'player': player, 'num_red': num_red.get(player.pk, 0),
                           'num_yellow': num_yellow.get(player.pk, 0)} for player in players]

        return ctx


urlpatterns += [path('cards/',
                     CardList.as_view(),
                     name='cards'), ]


class FinalizeMatch(MatchManagerRequiredMixin,
                    SingleObjectMixin,
                    EnterMatchDetailMixin,
                    FormView):
    form_class = forms.forms.Form
    template_name = 'dashboard/base_form.html'
    model = Matches

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Confirm finalize {} Match?'.format(self.object)
        return ctx

    def form_valid(self, form):
        self.object.finalize_match()
        return super().form_valid(form)


urlpatterns += [path('finalizematch/<int:pk>/',
                     FinalizeMatch.as_view(),
                     name='finalizematch'), ]


class EditGoal(MatchManagerRequiredMixin, UpdateView):
    model = models.Goal
    form_class = EditGoalForm
    template_name = 'dashboard/base_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Edit Goal - {}'.format(self.object.match)
        ctx['back_url'] = reverse(
            'dash:enterpastmatchdetails', kwargs={'pk': self.object.match.pk})
        return ctx

    def get_success_url(self):
        match = self.object.match
        return reverse('dash:enterpastmatchdetails', kwargs={'pk': match.pk})


urlpatterns += [path('editgoal/<int:pk>/',
                     EditGoal.as_view(),
                     name='editgoal'), ]


class EditCard(MatchManagerRequiredMixin, UpdateView):
    model = models.Cards
    form_class = EditCardForm
    template_name = 'dashboard/base_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Edit Card - {}'.format(self.object.match)
        ctx['back_url'] = reverse(
            'dash:enterpastmatchdetails', kwargs={'pk': self.object.match.pk})
        return ctx

    def get_success_url(self):
        match = self.object.match
        return reverse('dash:enterpastmatchdetails', kwargs={'pk': match.pk})


urlpatterns += [path('editcard/<int:pk>/',
                     EditCard.as_view(),
                     name='editcard'), ]


class CreateSuspension(MatchManagerRequiredMixin, CreateView):
    model = models.Suspension
    fields = ['status', 'player', 'reason', 'got_in']
    template_name = 'dashboard/base_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Create Suspension'
        ctx['back_url'] = reverse('match:suspensions')
        return ctx

    def get_success_url(self):
        return reverse('match:suspensions')


urlpatterns += [path('createsuspension/',
                     CreateSuspension.as_view(),
                     name='createsuspension'), ]


class DeleteSuspension(MatchManagerRequiredMixin, DeleteView):
    model = models.Suspension
    template_name = 'dashboard/base_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Delete Suspension'
        ctx['back_url'] = reverse('match:updatesuspension', kwargs={
                                  'pk': self.object.pk})
        return ctx

    def get_success_url(self):
        return reverse('match:suspensions')


urlpatterns += [path('deletesuspension/<int:pk>/',
                     DeleteSuspension.as_view(),
                     name='deletesuspension'), ]


class UpdateSuspension(MatchManagerRequiredMixin, UpdateView):
    model = models.Suspension
    fields = ['status', 'player', 'reason', 'got_in', 'completed_in']
    template_name = 'dashboard/base_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Update Suspension'
        ctx['back_url'] = reverse('match:suspensions')
        ctx['delete_url'] = reverse('match:deletesuspension',
                                    kwargs={'pk': self.object.pk})
        return ctx

    def get_success_url(self):
        return reverse('match:suspensions')


urlpatterns += [path('updatesuspension/<int:pk>/',
                     UpdateSuspension.as_view(),
                     name='updatesuspension'), ]


class Attr(MatchManagerRequiredMixin, ListView):
    template_name = 'match/event_attr.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = self.kind.capitalize() + ' Attributes'
        ctx['create_url'] = reverse('match:create{}attr'.format(self.kind))
        ctx['edit_url'] = 'match:update{}attr'.format(self.kind)
        return ctx


class CreateAttr(MatchManagerRequiredMixin, CreateView):
    fields = ['text']
    template_name = 'dashboard/base_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Add {} reason'.format(self.kind)
        ctx['back_url'] = reverse('match:{}attr'.format(self.kind))
        return ctx

    def get_success_url(self):
        return reverse('match:{}attr'.format(self.kind))


class UpdateAttr(MatchManagerRequiredMixin, UpdateView):
    fields = ['text']
    template_name = 'dashboard/base_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Update {} reason'.format(self.kind)
        ctx['back_url'] = reverse('match:{}attr'.format(self.kind))
        return ctx

    def get_success_url(self):
        return reverse('match:{}attr'.format(self.kind))


def attrmakeurls(kind):
    urls = []
    pathstring = '{}attr/'.format(kind)
    clsname = '{}Attr'.format(kind.capitalize())
    pathname = '{}attr'.format(kind)
    cls = globals()[clsname]
    urls += [path(pathstring,
                  cls.as_view(),
                  name=pathname), ]
    pathstring = 'create{}attr/'.format(kind)
    clsname = 'Create{}Attr'.format(kind.capitalize())
    pathname = 'create{}attr'.format(kind)
    cls = globals()[clsname]
    urls += [path(pathstring,
                  cls.as_view(),
                  name=pathname), ]
    pathstring = 'update{}attr/<int:pk>/'.format(kind)
    clsname = 'Update{}Attr'.format(kind.capitalize())
    pathname = 'update{}attr'.format(kind)
    cls = globals()[clsname]
    urls += [path(pathstring,
                  cls.as_view(),
                  name=pathname), ]

    return urls


class SuspensionAttr(Attr):
    model = models.SuspensionReason
    kind = 'suspension'


class CreateSuspensionAttr(CreateAttr):
    model = models.SuspensionReason
    kind = 'suspension'


class UpdateSuspensionAttr(UpdateAttr):
    model = models.SuspensionReason
    kind = 'suspension'


urlpatterns += attrmakeurls('suspension')


class GoalAttr(Attr):
    model = models.GoalAttr
    kind = 'goal'


class CreateGoalAttr(CreateAttr):
    model = models.GoalAttr
    kind = 'goal'


class UpdateGoalAttr(UpdateAttr):
    model = models.GoalAttr
    kind = 'goal'


urlpatterns += attrmakeurls('goal')


class CardAttr(Attr):
    model = models.CardReason
    kind = 'card'


class CreateCardAttr(CreateAttr):
    model = models.CardReason
    kind = 'card'


class UpdateCardAttr(UpdateAttr):
    model = models.CardReason
    kind = 'card'


urlpatterns += attrmakeurls('card')

from django.shortcuts import reverse


class ExtraContextMixin:
    extra_context = {}

    def get_context_data(self, **kwargs):
        ctx = {}
        if hasattr(super(), 'get_context_data'):
            ctx = super().get_context_data(**kwargs)
        for key, item in self.extra_context.items():
            ctx[key] = item
        return ctx


class BackUrlMixin:
    default_redirect = '/'

    def get(self, request, *args, **kwargs):
        request.session['previous_page'] = request.META.get(
            'HTTP_REFERER', self.default_redirect)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = {}
        if hasattr(super(), 'get_context_data'):
            ctx = super().get_context_data(**kwargs)
        ctx['back_url'] = self.request.session.get('previous_page', None)
        return ctx


class RedirectToPreviousMixin(BackUrlMixin):

    def get_success_url(self):
        url = None
        if self.request.method == 'POST':
            url = self.request.POST.get('redirect_url', None)
        if url is None:
            url = self.request.session.get('previous_page', None)
        if url is None:
            url = self.request.META.get('HTTP_REFERER', self.default_redirect)
        return url


class viewMixins(BackUrlMixin, ExtraContextMixin):
    pass


class formviewMixins(RedirectToPreviousMixin, ExtraContextMixin):
    pass

from django.shortcuts import reverse


class RedirectToPreviousMixin:
    default_redirect = '/'

    def get(self, request, *args, **kwargs):
        request.session['previous_page'] = request.META.get(
            'HTTP_REFERER', self.default_redirect)
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        url = self.request.session.get('previous_page',None)
        if url is None:
            url = request.META.get('HTTP_REFERER', self.default_redirect)
        return url


class breadcrumbMixin:

    breadcrumbs = []

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['breadcrumbs'] = self.get_breadcrumbs()
        return ctx

    def get_breadcrumbs(self):
        breadcrumbs = []
        for bc in self.breadcrumbs:
            breadcrumbs.append(self.make_breadcrumbs(
                name=bc[0], viewname=bc[1]))
        return breadcrumbs

    def make_breadcrumbs(self, name=None, viewname=None, obj=None):
        bcname = name
        if not bcname:
            if obj:
                bcname = str(obj)
            else:
                return None

        if not viewname:
            bclink = None
        elif obj:
            bclink = reverse(viewname, kwargs={'pk': obj.pk})
        else:
            bclink = reverse(viewname)

        return (bcname, bclink)

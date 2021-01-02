from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class AuthBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()

        if username is None or password is None:
            return

        try:
            # below line gives query set,you can change the queryset as per your requirement
            user = UserModel.objects.filter(
                Q(username__iexact=username) |
                Q(email__iexact=username)
            ).distinct()
        except UserModel.DoesNotExist:
            UserModel().set_password(password)

        if user.exists():
            ''' get the user object from the underlying query set,
            there will only be one object since username and email
            should be unique fields in your models.'''
            user_obj = user.first()
            if user_obj.check_password(password) and self.user_can_authenticate(user_obj):
                return user_obj
        else:
            UserModel().set_password(password)

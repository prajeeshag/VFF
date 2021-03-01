
import datetime
from io import BytesIO
import posixpath
from PIL import Image as Img
from PIL import ExifTags

from django.shortcuts import reverse
from django.db import models, transaction
from django.contrib.auth.models import AbstractUser
from django.conf import settings

from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.core.validators import MinLengthValidator, FileExtensionValidator
from django.core.exceptions import ValidationError

from core.validators import validate_Indian_pincode, validate_phone_number
from core.utils import get_image_upload_path

from guardian.models import UserObjectPermissionBase
from guardian.models import GroupObjectPermissionBase

from model_utils.models import StatusModel, TimeStampedModel, SoftDeletableModel
from model_utils import Choices


class PhoneNumber(models.Model):
    number = models.CharField(_('Phone number'), max_length=10,
                              validators=[validate_phone_number, ],
                              unique=True, blank=False)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return self.number


class Email(models.Model):
    email = models.EmailField(_('Email'), unique=True, blank=False)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return self.email


class User(AbstractUser):
    CLUB = 'CLUB'
    PLAYER = 'PLAYER'
    CLUBOFFICIAL = 'CLUB OFFICIAL'
    OTHER = 'OTHER'

    ACCOUNT_TYPE_CHOICES = [
        (CLUB, _('Club Account')),
        (PLAYER, _('Player')),
        (CLUBOFFICIAL, _('Club Secretary/President/Manager')),
        (OTHER, _('OTHER')),
    ]
    user_type = models.CharField(_('User type'), max_length=50,
                                 choices=ACCOUNT_TYPE_CHOICES,
                                 default=OTHER)

    email = models.EmailField(unique=True, blank=True, null=True)

    phone_number = models.OneToOneField(
        PhoneNumber, on_delete=models.PROTECT, null=True)

    ph_number = models.CharField(_('Phone number'), max_length=10,
                                 validators=[validate_phone_number, ],
                                 unique=True, blank=True, null=True)

    class Meta:
        db_table = 'auth_user'

    def is_club(self):
        return self.user_type == self.CLUB

    def is_player(self):
        return self.user_type == self.PLAYER

    def is_clubofficial(self):
        return self.user_type == self.CLUBOFFICIAL

    def get_profile(self):
        if self.user_type == self.CLUBOFFICIAL:
            return getattr(self, 'clubofficialsprofile', None)
        if self.user_type == self.PLAYER:
            return getattr(self, 'playerprofile', None)
        return None

    def get_profilepicture(self):
        profile = self.get_profile()
        dp = None
        if profile:
            dp = profile.profilepicture
        return dp

    def get_club(self):
        club = None
        profile = self.get_profile()
        if profile:
            club = profile.get_club()
        if not club:
            return getattr(self, 'clubprofile', None)
        return club


class Grounds(models.Model):
    """ Home grounds of club """
    name = models.CharField(max_length=50, blank=False, unique=True)
    address = models.TextField(max_length=200, blank=True)

    def __str__(self):
        return "%s" % (self.name)


class ClubProfile(models.Model):
    """ Club Profile """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='clubprofile')
    name = models.CharField(_('Name'), max_length=50, blank=False, unique=True)
    address = models.TextField(_('Address'), max_length=200, blank=False)
    pincode = models.CharField(_("Pincode"), max_length=10, validators=[
                               validate_Indian_pincode, ], blank=False)
    year_of_formation = models.IntegerField(
        _('Year of formation'), blank=True, null=True)
    abbr = models.CharField(_('Abbreviation'), max_length=4, validators=[
                            MinLengthValidator(3), ], blank=True, null=True, unique=True)
    logo = models.FileField(upload_to="logo/club/", null=True,
                            validators=[FileExtensionValidator(['svg', 'png'])])
    home_ground = models.ForeignKey(
        Grounds, null=True,
        related_name='club',
        on_delete=models.SET_NULL)

    registered = models.BooleanField(_('Registered'), default=False)

    def __str__(self):
        return "%s" % (self.name)

    def get_absolute_url(self):
        return reverse('users:clubdetails', kwargs={'pk': self.pk})

    def manager(self):
        officials = self.officials.filter(
            role=ClubOfficialsProfile.MANAGER)
        if not officials:
            return None
        return officials[0]

    def president(self):
        officials = self.officials.filter(
            role=ClubOfficialsProfile.PRESIDENT)
        if not officials:
            return None
        return officials[0]

    def secretary(self):
        officials = self.officials.filter(
            role=ClubOfficialsProfile.SECRETARY)
        if not officials:
            return None
        return officials[0]

    def total_players(self):
        return self.clubsignings.filter(accepted=True).count()

    def player_quota_left(self):
        return PlayerCount.MAX_NUM_PLAYERS-self.total_players()

    def get_contact_number(self):
        if self.manager():
            return "{} (Team Manager)".format(self.manager().phone_number)

        if self.president():
            return "{} (President)".format(self.president().phone_number)

        if self.secretary():
            return "{} (Secretary)".format(self.secretary().phone_number)

    def num_undern_players(self, n):
        players = self.get_players()
        num = 0
        for player in players:
            if player.get_age() <= n:
                num = num + 1
        return num

    def num_under19_players(self):
        return self.num_undern_players(19)

    def num_under21_players(self):
        return self.num_undern_players(21)-self.num_under19_players()

    def get_players(self):
        return self.players.all()

    def get_invited_players(self):
        q = self.clubsignings.filter(accepted=False).prefetch_related('player')
        return [s.player for s in q]

    def release_player(self, player):
        if player not in self.get_players():
            return False
        signings = self.clubsignings.filter(player=player).first()
        if signings:
            signings.release()
            return True


class AbstractImage(models.Model):

    __original_image = None

    image = models.ImageField(
        upload_to=get_image_upload_path, max_length=255)

    x1 = models.PositiveIntegerField("Cropbox (left)", default=0)
    y1 = models.PositiveIntegerField("Cropbox (top)", default=0)
    x2 = models.PositiveIntegerField("Cropbox (right)", default=0)
    y2 = models.PositiveIntegerField("Cropbox (bottom)", default=0)
    checked = models.BooleanField(default=False)
    orientation = models.PositiveSmallIntegerField(default=1)

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super(AbstractImage, self).__init__(*args, **kwargs)
        self.__original_image = self.image

    def save(self, set_orientation=False, *args, **kwargs):
        EXIF_ORIENTATION = 0x0112
        if self.image != self.__original_image or set_orientation:
            pilImage = Img.open(BytesIO(self.image.read()))
            try:
                exif = pilImage._getexif()
            except Exception:
                exif = None

            orientation = 1
            if exif:
                orientation = exif.get(EXIF_ORIENTATION)

            if not orientation:
                orientation = 1

            self.orientation = orientation

        return super(AbstractImage, self).save(*args, **kwargs)

    def cropbox(self):
        W, H = self.get_dimensions()
        w, h = W, H
        if self.orientation > 4:
            w, h = H, W
        if (self.x1 + self.y1 + self.x2 + self.y2 == 0 or
                self.x1 >= self.x2 or self.y1 >= self.y2):
            wh = min(w, h)
            x1, y1 = int((w-wh)*0.5), 0
            x2, y2 = int(x1+wh), int(y1+wh)
            return '{},{},{},{}'.format(x1, y1, x2, y2)
        return '{},{},{},{}'.format(self.x1, self.y1, self.x2, self.y2)

    def get_cropbox_frac(self):
        W, H = self.get_dimensions()
        w, h = W, H
        if self.orientation > 4:
            w, h = H, W
        if (self.x1 + self.y1 + self.x2 + self.y2 == 0 or
                self.x1 >= self.x2 or self.y1 >= self.y2):
            wh = min(w, h)
            x1, y1 = (w-wh)*0.5/w, 0.
            x2, y2 = (x1+wh)/w, (y1+wh)/h

            return (x1, y1, x2, y2)

        x1, x2 = self.x1/w, self.x2/w
        y1, y2 = self.y1/h, self.y2/h

        return (x1, y1, x2, y2)

    def set_cropbox_frac(self, x1, y1, x2, y2):
        W, H = self.get_dimensions()
        w, h = W, H
        if self.orientation > 4:
            w, h = H, W

        self.x1, self.x2 = w * x1, w * x2
        self.y1, self.y2 = h * y1, h * y2

    def get_dimensions(self):
        return (self.image.width, self.image.height)


class ProfilePicture(AbstractImage):

    def __str__(self):
        return "Profile picture"


class Documents(models.Model):
    num = models.PositiveIntegerField(default=0)


class Document(AbstractImage):
    PHOTOID = 'Photo ID'
    AGEPROOF = 'Age Proof'
    document_type_choices = [
        (_(PHOTOID), _('Photo ID proof')),
        (_(AGEPROOF), _('Age proof'))
    ]
    document_type = models.CharField(_('Document Type'),
                                     max_length=50, blank=False,
                                     choices=document_type_choices)
    collection = models.ForeignKey(
        Documents, on_delete=models.CASCADE,
        related_name='documents')

    class Meta:
        unique_together = ['collection', 'document_type']


class Jersey(AbstractImage):
    HOME = 'Home'
    AWAY = 'Away'
    NEUTRAL = 'Neutral'
    jersey_type_choices = [
        (HOME, 'Home Jersey'),
        (AWAY, 'Away Jersey'),
        (NEUTRAL, 'Neutral Jersey'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='jerseypictures')

    jersey_type = models.CharField(
        _('Jersey Type'), max_length=10,
        choices=jersey_type_choices)

    class Meta:
        unique_together = ['user', 'jersey_type']

    def __str__(self):
        return "Jersey of %s" % (self.user,)


class Profile(models.Model):
    """ Abstract model for all Profiles """
    first_name = models.CharField(_('First Name'), max_length=100, blank=False)
    last_name = models.CharField(_('Last Name'), max_length=100, blank=False)
    name = models.CharField(_('Name'), max_length=100, blank=True)
    nickname = models.CharField(_('nickname'), max_length=20, blank=True)
    dob = models.DateField(_("Birthday"), blank=False)
    address = models.TextField(_('Address'), max_length=200, blank=False)
    pincode = models.CharField(_("Pincode"), max_length=10, validators=[
                               validate_Indian_pincode, ], blank=False)
    student = models.BooleanField(_("Are you a Student"), default=False)
    occupation = models.CharField(_('Occupation'), max_length=100, blank=True)

    profilepicture = models.OneToOneField(
        ProfilePicture, on_delete=models.SET_NULL, null=True)

    phone_number = models.OneToOneField(
        PhoneNumber, on_delete=models.SET_NULL, null=True)

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        blank=True, null=True,
        on_delete=models.SET_NULL)

    class Meta:
        abstract = True

    def __str__(self):
        return('{} {}'.format(self.first_name, self.last_name))

    def get_age(self):
        if self.dob is not None:
            today = timezone.now()
            dob = self.dob
            return today.year - dob.year - ((1, 1) < (dob.month, dob.day))
        return None

    def get_phone_number(self):
        phone_number = ''
        if self.user:
            if self.user.phone_number:
                phone_number = self.user.phone_number
        if not phone_number:
            phone_number = self.phone_number

        return phone_number


class ClubOfficialsProfile(Profile):
    PRESIDENT = 'President'
    SECRETARY = 'Secretary'
    MANAGER = 'Manager'
    role_choices = [
        (PRESIDENT, 'President of the Club'),
        (SECRETARY, 'Secretary of the Club'),
        (MANAGER, 'Manager of the Team'),
    ]
    role = models.CharField(_('Role'), max_length=10, choices=role_choices)
    club = models.ForeignKey(
        ClubProfile, on_delete=models.CASCADE,
        related_name='officials')

    class Meta:
        unique_together = ['club', 'role']

    def get_absolute_url(self):
        return reverse('users:clubofficialsprofile', kwargs={'pk': self.pk})

    def get_club(self):
        return self.club


class PlayerProfile(Profile):
    """ Players Profile """
    foot_choices = [
        ('Left', 'Left foot'),
        ('Right', 'Right foot')
    ]

    position_choices = [
        ('Defender', 'Defender'),
        ('Midfield', 'Midfield'),
        ('Forward', 'Forward'),
        ('Goalkeeper', 'Goalkeeper'),
    ]

    height = models.IntegerField(
        _('Height (cm)'), blank=False, help_text=_("in Centimeters"))
    weight = models.IntegerField(
        _('Weight (kg)'), blank=False, help_text=_("in Kilograms"))
    prefered_foot = models.CharField(
        max_length=10, blank=False, choices=foot_choices)
    favorite_position = models.CharField(
        max_length=20, blank=False, choices=position_choices)

    club = models.ForeignKey(
        ClubProfile, on_delete=models.SET_NULL,
        null=True, related_name='players')

    documents = models.OneToOneField(
        Documents, on_delete=models.SET_NULL,
        null=True)

    class Meta:
        permissions = (
            ('edit', 'Edit'),
        )
        ordering = ['first_name', 'last_name']

    def get_height(self):
        return "{} cm".format(self.height)

    def get_weight(self):
        return "{} kg".format(self.weight)

    def get_absolute_url(self):
        return reverse('users:playersprofile', kwargs={'pk': self.pk})

    def get_offer_from_club(self, club):
        offer = self.clubsignings.filter(club=club).first()
        return offer

    def get_all_offers(self):
        offers = self.clubsignings.filter(
            accepted=False).order_by('-created')
        return offers

    def get_club(self):
        if self.club:
            return self.club
        offer = self.clubsignings.filter(accepted=True).first()
        if offer:
            self.club = offer.club
            self.save()
            return offer.club
        return None

    def is_under19(self):
        return self.get_age() <= 19

    def is_under21(self):
        return (self.get_age() > 19 and self.get_age() <= 21)


class PlayerUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE)


class PlayerGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE)


class PlayerCount(models.Model):

    MAX_NUM_PLAYERS = 30

    club = models.OneToOneField(
        ClubProfile,
        on_delete=models.CASCADE,
        related_name='playercount'
    )

    count = models.PositiveIntegerField(default=0)

    class MaximumLimitReached(Exception):
        pass

    def queryset(self):
        return self.__class__.objects.filter(id=self.id)

    def increment(self, n=1):
        with transaction.atomic():
            obj = self.queryset().select_for_update().get()
            obj.count += n
            if obj.count > self.MAX_NUM_PLAYERS:
                raise self.MaximumLimitReached()
            if obj.count < 0:
                obj.count = 0
            obj.save()


class ClubSignings(TimeStampedModel):
    club = models.ForeignKey(
        ClubProfile,
        on_delete=models.CASCADE,
        related_name='clubsignings')
    player = models.ForeignKey(
        PlayerProfile,
        on_delete=models.CASCADE,
        related_name='clubsignings')
    accepted = models.BooleanField(default=False)

    class Meta:
        unique_together = ['club', 'player']

    class MaximumLimitReached(Exception):
        pass

    class PlayerCountNotFound(Exception):
        pass

    class AcceptedOfferExist(Exception):
        pass

    @classmethod
    def get_all_accepted(cls, club=None):
        if not club:
            return cls.objects.filter(accepted=True).prefetch_related('player', 'club')
        else:
            return (cls.objects.filter(club=club)
                    .filter(accepted=True)
                    .prefetch_related('player', 'club'))

    def accept(self):
        accepted_offers = self.player.clubsignings.filter(accepted=True)

        if accepted_offers:
            raise self.AcceptedOfferExist()

        playercount, created = PlayerCount.objects.get_or_create(
            club=self.club)

        try:
            playercount.increment()
        except playercount.MaximumLimitReached:
            raise self.MaximumLimitReached()

        self.player.club = self.club
        self.accepted = True
        self.player.save()
        self.save()
        self.player.clubsignings.filter(accepted=False).delete()

    def release(self):
        if not self.accepted:
            return

        playercount, created = PlayerCount.objects.get_or_create(
            club=self.club)
        playercount.increment(-1)
        self.player.club = None
        self.player.save()
        self.delete()

import datetime

from django.shortcuts import reverse
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

from django.utils.translation import ugettext_lazy as _
from django.core.validators import MinLengthValidator

from core.validators import validate_Indian_pincode, validate_phone_number
from core.utils import get_image_upload_path


class User(AbstractUser):
    CLUB = 'CLUB'
    PLAYER = 'PLAYER'
    CLUBOFFICIAL = 'CLUB OFFICIAL'
    OTHER = 'OTHER'

    ACCOUNT_TYPE_CHOICES = [
        (CLUB, _('Club Account')),
        (PLAYER, _('Player Account')),
        (CLUBOFFICIAL, _('Club Secretary/President/Manager')),
        (OTHER, _('OTHER')),
    ]
    email = models.EmailField(_('Email'), unique=True, blank=False)
    user_type = models.CharField(_('User type'), max_length=50,
                                 choices=ACCOUNT_TYPE_CHOICES,
                                 default=OTHER)

    class Meta:
        db_table = 'auth_user'

    def is_club(self):
        return self.user_type == self.CLUB

    def is_player(self):
        return self.user_type == self.PLAYER

    def is_clubofficial(self):
        return self.user_type == self.CLUBOFFICIAL


class PhoneNumber(models.Model):
    number = models.CharField(_('Phone number'), max_length=10,
                              validators=[validate_phone_number, ],
                              unique=True, blank=False)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return("%s" % (self.number,))


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
        return self.players.all().count()

    def get_contact_number(self):
        if self.manager():
            return "{} (Team Manager)".format(self.manager().phone_number)

        if self.president():
            return "{} (President)".format(self.president().phone_number)

        if self.secretary():
            return "{} (Secretary)".format(self.secretary().phone_number)

    def num_undern_players(self, n):
        players = self.players.all()
        num = 0
        for player in players:
            if player.get_age() <= n:
                num = num + 1
        return num

    def num_under19_players(self):
        return self.num_undern_players(19)

    def num_under21_players(self):
        return self.num_undern_players(21)-self.num_under19_players()


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
        return "Profile picture of %s" % (self.user)

    def get_absolute_url(self):
        return reverse('dp_edit', kwargs={'pk': self.pk})

    def get_upload_url(self):
        return reverse('dp_upload', kwargs={'pk': self.pk})


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
    dob = models.DateField(_("Birthday"), blank=False)
    address = models.TextField(_('Address'), max_length=200, blank=False)
    pincode = models.CharField(_("Pincode"), max_length=10, validators=[
                               validate_Indian_pincode, ], blank=False)
    student = models.BooleanField(_("Student"), default=False)
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
            today = datetime.date.today()
            dob = self.dob
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return None


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

    def get_height(self):
        return "{} cm".format(self.height)

    def get_weight(self):
        return "{} kg".format(self.weight)

    def get_absolute_url(self):
        return reverse('users:playersprofile', kwargs={'pk': self.pk})

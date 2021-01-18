
import datetime
from io import BytesIO
import posixpath
from PIL import Image as Img
from PIL import ExifTags

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.files.images import get_image_dimensions
from django.conf import settings
from django.urls import reverse
from django.core.files import File


class Club(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='club')
    club_name = models.CharField(
        max_length=50, blank=False, help_text="Name of the Club")

    def __str__(self):
        return "%s" % (self.club_name)

    def get_absolute_url(self):
        return reverse('ClubDetail', kwargs={'pk': self.pk})

    def president(self):
        officials = self.Officials.all()
        for official in officials:
            if official.is_president():
                return official
        return None

    def secretary(self):
        officials = self.Officials.all()
        for official in officials:
            if official.is_secretary():
                return official
        return None

    def manager(self):
        officials = self.Officials.all()
        for official in officials:
            if official.is_manager():
                return official
        return None

    def total_players(self):
        players = self.Officials.filter(role="Player")
        return players.count()

    def get_contact_number(self):
        if self.manager():
            return "{} (Team Manager)".format(self.manager().phone_number)
        return "{} (Club Admin)".format(self.clubdetails.contact_number)

    def num_undern_players(self, n):
        players = self.Officials.filter(role="Player")
        num = 0
        for player in players:
            if player.get_age() <= n:
                num = num + 1
        return num

    def num_under21_players(self):
        return self.num_undern_players(21)

    def num_under19_players(self):
        return self.num_undern_players(19)


class ClubDetails(models.Model):
    club = models.OneToOneField(
        Club, on_delete=models.CASCADE, related_name='clubdetails')
    address = models.TextField(
        max_length=200, blank=False, help_text="Address of the Club")
    contact_number = models.CharField(
        max_length=10, blank=False, help_text="Contact number")
    date_of_formation = models.IntegerField(
        null=True, blank=True, verbose_name="Year of formation of the Club")
    abbr = models.CharField(max_length=4, blank=True, null=True, unique=True,
                            verbose_name="Club abbreviation(3-4 characters)")

    def __str__(self):
        return "%s details" % (self.club)


class Officials(models.Model):
    role_choices = [
        ('President', 'President of the Club'),
        ('Secretary', 'Secretary of the Club'),
        ('Manager', 'Manager of the Football Team'),
        ('Player', 'Player'),
    ]

    first_name = models.CharField(
        max_length=100, help_text="First name", blank=False)
    last_name = models.CharField(
        max_length=100, help_text="Last name/Initials", blank=False)
    date_of_birth = models.DateField(blank=False)
    address = models.TextField(max_length=200,
                               blank=False, help_text="Address")
    phone_number = models.CharField(
        max_length=10, blank=False, help_text="Mobile/Phone number")
    email = models.EmailField(blank=True, help_text="Email Id")
    occupation = models.CharField(
        max_length=100, help_text="Occupation", blank=True)

    club = models.ForeignKey(Club, blank=True, null=True,
                             on_delete=models.CASCADE, related_name="Officials")

    user = models.OneToOneField(settings.AUTH_USER_MODEL, blank=True, null=True,
                                on_delete=models.SET_NULL, related_name="Official")

    role = models.CharField(max_length=10, choices=role_choices)

    def __str__(self):
        return "%s %s" % (self.first_name, self.last_name)

    def is_president(self):
        return self.role in {'President'}

    def is_secretary(self):
        return self.role in {'Secretary'}

    def is_manager(self):
        return self.role in {'Manager'}

    def is_player(self):
        return self.role in {'Player'}

    def get_age(self):
        if self.date_of_birth is not None:
            today = datetime.date.today()
            dob = self.date_of_birth
            return today.year - dob.year - \
                ((today.month, today.day) < (dob.month, dob.day))
        return None

    def get_absolute_url(self):
        return reverse('OfficialsProfileView', kwargs={'pk': self.pk})


class PlayerInfo(models.Model):

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

    official = models.OneToOneField(
        Officials, blank=True, on_delete=models.CASCADE, related_name='Player')
    height = models.IntegerField(
        blank=False, help_text="Height in Centimeters")
    weight = models.IntegerField(
        blank=False, help_text="Weight in Kilograms")
    prefered_foot = models.CharField(
        max_length=10, blank=False, choices=foot_choices)
    favorite_position = models.CharField(
        max_length=20, blank=False, choices=position_choices)

    def __str__(self):
        return "%s's player info" % (self.official,)

    def get_height(self):
        return "{} cm".format(self.height)

    def get_weight(self):
        return "{} kg".format(self.weight)


def get_image_upload_path(instance, filename):

    if hasattr(instance.user, 'user') and instance.user.user:
        username = instance.user.user.username
    else:
        username = instance.user.club.user.username

    return posixpath.join(username, datetime.datetime.now().strftime("%Y/%m/%d/%H/%M/%S"), filename)


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


class AddressProof(AbstractImage):
    user = models.OneToOneField(
        Officials, on_delete=models.CASCADE, related_name='addressproof')

    def __str__(self):
        return "Address proof of %s" % (self.user,)


class AgeProof(AbstractImage):
    user = models.OneToOneField(
        Officials, on_delete=models.CASCADE, related_name='ageproof')

    def __str__(self):
        return "Age proof of %s" % (self.user,)


class ProfilePicture(AbstractImage):
    user = models.OneToOneField(
        Officials, on_delete=models.CASCADE, related_name='profilepicture')

    def __str__(self):
        user = 'User'
        if hasattr(self, 'user'):
            user = self.user
        return "Photo of %s" % (user,)

    def get_absolute_url(self):
        return reverse('dp_edit', kwargs={'pk': self.pk})

    def get_upload_url(self):
        return reverse('dp_upload', kwargs={'pk': self.pk})


class JerseyPicture(AbstractImage):
    user = models.ForeignKey(
        Club, on_delete=models.CASCADE, related_name='jerseypictures')

    def __str__(self):
        return "Jersey of %s" % (self.user,)


class Invitations(models.Model):
    player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='invitations',
        blank=False, null=False)
    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name='invitations',
        blank=False, null=False)
    profile = models.OneToOneField(
        Officials,
        on_delete=models.CASCADE,
        related_name='invitation',
        blank=True, null=True
    )

    class Meta:
        unique_together = ['player', 'club']

    def __str__(self):
        return "Invitation for {} by {} ".format(self.player, self.club)


# class Verify(models.Model):
    # official = models.OneToOneField(
        # Officials, on_delete=models.CASCADE, null=True)
    # verified = models.BooleanField(default=False)
    # message = models.TextField(blank=True)

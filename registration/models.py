from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.files.images import get_image_dimensions
import datetime
import posixpath
from django.conf import settings


class Club(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='club')
    club_name = models.CharField(
        max_length=50, blank=False, help_text="Name of the Club")

    def __str__(self):
        return "%s" % (self.club_name)

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


class ClubDetails(models.Model):
    club = models.OneToOneField(
        Club, on_delete=models.CASCADE, related_name='clubdetails')
    address = models.TextField(
        max_length=200, blank=False, help_text="Address of the Club")
    contact_number = models.CharField(
        max_length=10, blank=False, help_text="Contact number")
    date_of_formation = models.IntegerField(
        null=True, blank=True, verbose_name="Year of formation of the Club")

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
                                on_delete=models.CASCADE, related_name="Official")

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


def get_image_upload_path(instance, filename):

    if hasattr(instance.user, 'user') and instance.user.user:
        username = instance.user.user.username
    else:
        username = instance.user.club.user.username

    return posixpath.join(username, datetime.datetime.now().strftime("%Y/%m/%d/%H/%M/%S"), filename)


class AbstractImage(models.Model):
    image = models.ImageField(
        upload_to=get_image_upload_path, max_length=255)

    x1 = models.PositiveIntegerField("Cropbox (left)", default=0)
    y1 = models.PositiveIntegerField("Cropbox (top)", default=0)
    x2 = models.PositiveIntegerField("Cropbox (right)", default=0)
    y2 = models.PositiveIntegerField("Cropbox (bottom)", default=0)

    class Meta:
        abstract = True

    def cropbox(self):
        width, height = get_image_dimensions(self.original)
        if (self.x1 >= self.x2 or self.y1 >= self.y2 or self.x1 < 0
                or self.y1 < 0 or self.x2 > width or self.y2 > height):
            return '{},{},{},{}'.format(0, 0, width, height)
        return '{},{},{},{}'.format(self.x1, self.y1, self.x2, self.y2)

    def cropbox_percent(self):
        width, height = get_image_dimensions(self.original)
        if (self.x1 >= self.x2 or self.y1 >= self.y2 or self.x1 < 0
                or self.y1 < 0 or self.x2 > width or self.y2 > height):
            return '{} {} {} {}'.format(0, 0, 100, 100)
        x1 = self.x1/width*100
        x2 = self.x2/width*100
        y1 = self.y1/height*100
        y2 = self.y2/height*100
        return ('{:.2f} {:.2f} {:.2f} {:.2f}').format(x1, y1, x2, y2)


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
        return "Photo of %s" % (self.user,)


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

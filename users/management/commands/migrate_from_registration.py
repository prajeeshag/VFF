from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

from registration.models import Grounds as Grnds1
from users.models import Grounds as Grnds2
from users.models import (
    ClubProfile, ClubOfficialsProfile, PlayerProfile,
    Jersey, ProfilePicture, Documents, Document,
)


class Command(BaseCommand):
    help = 'Migrate data from registration app to users'

    def add_arguments(self, parser):
        pass
        # parser.add_argument('--resetall', action='store_true',
        # help='resets all email ids')

    def copy_clubProfile(self, user):
        club_name = user.club.club_name
        club_address = user.club.clubdetails.address
        club_abbr = user.club.clubdetails.abbr
        year_of_formation = user.club.clubdetails.date_of_formation
        home_ground_name = user.club.clubdetails.home_ground.name
        home_ground = Grnds2.objects.get(name=home_ground_name)
        club_pincode = '000000'
        obj, created = ClubProfile.objects.get_or_create(
            user=user,
            name=club_name,
            address=club_address,
            pincode=club_pincode,
            year_of_formation=year_of_formation,
            abbr=club_abbr,
            home_ground=home_ground)

        if created:
            print("Copied clubProfile for : %s" % (club_name,))

        i = -1
        for jersey in user.club.jerseypictures.all():
            i += 1
            jersey_type = Jersey.jersey_type_choices[i][0]
            image = jersey.image
            x1 = jersey.x1
            x2 = jersey.x2
            y1 = jersey.y1
            y2 = jersey.y2
            orientation = jersey.orientation

            _, created = Jersey.objects.get_or_create(
                user=user, image=image, x1=x1, x2=x2, y1=y1,
                y2=y2, checked=False, jersey_type=jersey_type)

            if created:
                print("Created %s Jersey for %s" %
                      (jersey_type, user.clubprofile.name))
        return obj

    def create_dp(self, dp):
        image = dp.image
        x1 = dp.x1
        x2 = dp.x2
        y1 = dp.y1
        y2 = dp.y2
        orientation = dp.orientation

        dpNew, created = ProfilePicture.objects.get_or_create(
            image=image,
            x1=x1, x2=x2,
            y1=y1, y2=y2,
            orientation=orientation,
        )

    def create_docs(self, obj, objNew):

        if objNew.documents is not None:
            documents = objNew.documents
        else:
            documents = Documents.objects.create()
            objNew.documents = documents
            objNew.save()

        print(documents.id)

        img = obj.addressproof
        document_type = Document.PHOTOID
        image = img.image
        orientation = img.orientation
        _, created = Document.objects.get_or_create(
            collection=documents,
            image=image,
            document_type=document_type,
            orientation=orientation)
        if created:
            print("Created %s for %s of %s" % (
                document_type, objNew, objNew.club))

        img = obj.ageproof
        document_type = Document.AGEPROOF
        image = img.image
        orientation = img.orientation
        _, created = Document.objects.get_or_create(
            collection=documents,
            image=image,
            document_type=document_type,
            orientation=orientation)
        if created:
            print("Created %s for %s of %s" % (
                document_type, objNew, objNew.club))

    def copy_OfficialsProfile(self, obj, role, clubNew):
        first_name = obj.first_name
        last_name = obj.last_name
        address = obj.address
        dob = obj.date_of_birth
        occupation = obj.occupation
        student = False
        pincode = '000000'
        objNew, created = ClubOfficialsProfile.objects.get_or_create(
            first_name=first_name,
            last_name=last_name,
            address=address,
            dob=dob,
            occupation=occupation,
            student=student,
            pincode=pincode,
            role=role,
            club=clubNew
        )
        if created:
            print("Created club %s for %s" % (role, clubNew.name))

        dp = obj.profilepicture
        dpNew = self.create_dp(dp)
        objNew.profilepicture = dpNew
        objNew.save()

    def copy_clubOfficialsProfile(self, user):
        club = user.club
        clubNew = user.clubprofile
        # officials = club.Officials.exclude(role="Player")
        obj = club.manager()
        if obj:
            role = ClubOfficialsProfile.MANAGER
            self.copy_OfficialsProfile(obj, role, clubNew)

        obj = club.president()
        if obj:
            role = ClubOfficialsProfile.PRESIDENT
            self.copy_OfficialsProfile(obj, role, clubNew)

        obj = club.secretary()
        if obj:
            role = ClubOfficialsProfile.SECRETARY
            self.copy_OfficialsProfile(obj, role, clubNew)

    def copy_clubPlayersProfile(self, user):
        club = user.club
        clubNew = user.clubprofile
        Players = club.Officials.filter(role="Player")
        for obj in Players:
            first_name = obj.first_name
            last_name = obj.last_name
            address = obj.address
            dob = obj.date_of_birth
            occupation = obj.occupation
            student = False
            pincode = '000000'
            height = obj.Player.height
            weight = obj.Player.weight
            prefered_foot = obj.Player.prefered_foot
            favorite_position = obj.Player.favorite_position
            objNew, created = PlayerProfile.objects.get_or_create(
                first_name=first_name,
                last_name=last_name,
                address=address,
                dob=dob,
                occupation=occupation,
                student=student,
                pincode=pincode,
                height=height,
                weight=weight,
                prefered_foot=prefered_foot,
                favorite_position=favorite_position,
                club=clubNew)

            if created:
                print("Created Player %s %s of %s" %
                      (first_name, last_name, clubNew.name))

            dp = obj.profilepicture
            dpNew = self.create_dp(dp)
            objNew.profilepicture = dpNew
            objNew.save()
            self.create_docs(obj, objNew)

    def handle(self, *args, **kwargs):

        # Create Grounds
        for grnd1 in Grnds1.objects.all():
            obj, created = Grnds2.objects.get_or_create(
                name=grnd1.name
            )
            if created:
                print("Created Ground: %s" % (obj.name))

        User = get_user_model()
        users = User.objects.all()
        for user in users:
            if not user.is_staff:
                if user.user_type == 'PERSONAL':
                    user.delete()
                elif user.user_type == 'CLUB':
                    print("Club account: %s" % (user.username))
                    if hasattr(user, 'club'):
                        self.copy_clubProfile(user)
                        self.copy_clubOfficialsProfile(user)
                        self.copy_clubPlayersProfile(user)
                    else:
                        user.delete()
            else:
                user.user_type = user.OTHER
                user.save()

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import (
    Officials, Club, PlayerInfo, JerseyPicture, ProfilePicture,
    AgeProof, AddressProof,
)


class ImageWidget(forms.ClearableFileInput):
    template_name = 'widgets/image.html'


class SignUpForm(UserCreationForm):

    club_name = forms.CharField(
        label='Name of the Club', max_length=100, required=True)

    address = forms.CharField(
        label='Address of the Club', max_length=200, required=True,
        widget=forms.Textarea)

    contact_number = forms.CharField(
        label='Contact number', max_length=10, min_length=10, required=True)

    class Meta:
        model = User
        fields = ('username', 'club_name', 'address',
                  'contact_number', 'password1', 'password2')


class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = ProfilePicture
        fields = ['image', 'x1', 'x2', 'y1', 'y2']

        widgets = {
            # 'image': ImageWidget(),
            'x1': forms.HiddenInput(),
            'x2': forms.HiddenInput(),
            'y1': forms.HiddenInput(),
            'y2': forms.HiddenInput(),
        }


class AgeProofForm(forms.ModelForm):
    class Meta:
        model = AgeProof
        fields = ['image', 'x1', 'x2', 'y1', 'y2']

        widgets = {
            # 'image': ImageWidget(),
            'x1': forms.HiddenInput(),
            'x2': forms.HiddenInput(),
            'y1': forms.HiddenInput(),
            'y2': forms.HiddenInput(),
        }


class AddressProofForm(forms.ModelForm):
    class Meta:
        model = AddressProof
        fields = ['image', 'x1', 'x2', 'y1', 'y2']

        widgets = {
            # 'image': ImageWidget(),
            'x1': forms.HiddenInput(),
            'x2': forms.HiddenInput(),
            'y1': forms.HiddenInput(),
            'y2': forms.HiddenInput(),
        }


class JerseyForm(forms.ModelForm):
    class Meta:
        model = JerseyPicture
        fields = ['image', 'x1', 'x2', 'y1', 'y2']

        widgets = {
            'x1': forms.HiddenInput(),
            'x2': forms.HiddenInput(),
            'y1': forms.HiddenInput(),
            'y2': forms.HiddenInput(),
        }


class OfficialsUpdateForm(forms.ModelForm):
    class Meta:
        model = Officials
        fields = ['first_name', 'last_name', 'address',
                  'phone_number', 'date_of_birth', 'email',
                  'occupation']
        widgets = {
            'date_of_birth': forms.SelectDateWidget(
                years=[*range(1950, 2010, 1)]),
        }


class OfficialsCreationForm(forms.ModelForm):
    image = forms.ImageField(max_length=255, label='Photo')
    x1 = forms.IntegerField(min_value=0, widget=forms.HiddenInput, initial=0)
    x2 = forms.IntegerField(min_value=0, widget=forms.HiddenInput, initial=0)
    y1 = forms.IntegerField(min_value=0, widget=forms.HiddenInput, initial=0)
    y2 = forms.IntegerField(min_value=0, widget=forms.HiddenInput, initial=0)

    class Meta:
        model = Officials
        fields = ['first_name', 'last_name', 'role',
                  'date_of_birth', 'address', 'phone_number',
                  'occupation']
        # fields = '__all__'

        widgets = {
            'role': forms.HiddenInput(),
            'date_of_birth': forms.SelectDateWidget(
                years=[*range(1950, 2010, 1)]),
        }


class PlayerCreationForm(OfficialsCreationForm):
    height = forms.IntegerField(
        required=True, min_value=100, max_value=200,
        help_text="Height in Centimeters")
    weight = forms.IntegerField(
        required=True, help_text="Weight in Kilograms")
    prefered_foot = forms.ChoiceField(
        choices=PlayerInfo.foot_choices, required=True)
    favorite_position = forms.ChoiceField(
        choices=PlayerInfo.position_choices, required=True)
    address_proof = forms.ImageField(help_text="Document for address proof")
    age_proof = forms.ImageField(help_text="Documents for age proof")


class PlayerUpdateForm(OfficialsUpdateForm):
    height = forms.IntegerField(
        required=True, min_value=100, max_value=200,
        help_text="Height in Centimeters")
    weight = forms.IntegerField(
        required=True, help_text="Weight in Kilograms")
    prefered_foot = forms.ChoiceField(
        choices=PlayerInfo.foot_choices, required=True)
    favorite_position = forms.ChoiceField(
        choices=PlayerInfo.position_choices, required=True)

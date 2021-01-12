import re

from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.forms.models import ModelChoiceIterator
from django.forms.widgets import FileInput
from django.utils import formats
from django.utils.encoding import force_str


class ImageInput(FileInput):
    """
    Widget providing a input element for file uploads based on the
    Django ``FileInput`` element. It hides the actual browser-specific
    input element and shows the available image for images that have
    been previously uploaded. Selecting the image will open the file
    dialog and allow for selecting a new or replacing image file.
    """
    template_name = 'myapp/widgets/image_input_widget.html'

    def __init__(self, attrs=None):
        if not attrs:
            attrs = {}
        attrs['accept'] = 'image/*'
        super().__init__(attrs=attrs)

    def get_context(self, name, value, attrs):
        ctx = super().get_context(name, value, attrs)

        ctx['image_url'] = ''
        if value and not isinstance(value, InMemoryUploadedFile):
            # can't display images that aren't stored - pass empty string to context
            ctx['image_url'] = value

        ctx['image_id'] = "%s-image" % ctx['widget']['attrs']['id']
        return ctx

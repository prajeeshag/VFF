
import datetime
import posixpath
from functools import wraps


def get_image_upload_path(instance, filename):
    return posixpath.join(
        'image_uploads', datetime.datetime.now().strftime("%Y/%m/%d/%H/%M/%S"), filename)


def disable_for_loaddata(signal_handler):
    """ Decorator that turns off signal_handler when loading fixture data """
    @wraps(signal_handler)
    def wrapper(*args, **kwargs):
        if kwargs.get('raw'):
            return
        signal_handler(*args, **kwargs)
    return wrapper

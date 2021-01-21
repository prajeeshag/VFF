
import datetime
import posixpath


def get_image_upload_path(instance, filename):
    return posixpath.join(
        'image_uploads', datetime.datetime.now().strftime("%Y/%m/%d/%H/%M/%S"), filename)

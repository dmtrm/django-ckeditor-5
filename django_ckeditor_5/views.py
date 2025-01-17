from django import get_version
from django.http import Http404
from django.utils.module_loading import import_string

from django.utils.translation import ugettext_lazy as _

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import JsonResponse
from PIL import Image

from .forms import UploadFileForm


class NoImageException(Exception):
    pass


def get_storage_class():
    storage_setting = getattr(settings, "CKEDITOR_5_FILE_STORAGE", None)
    default_storage_setting = getattr(settings, "DEFAULT_FILE_STORAGE", None)
    storages_setting = getattr(settings, "STORAGES", {})
    default_storage_name = storages_setting.get("default", {}).get("BACKEND")

    if storage_setting:
        return import_string(storage_setting)
    elif default_storage_setting:
        try:
            return import_string(default_storage_setting)
        except ImportError:
            raise ImproperlyConfigured(f"Invalid default storage class: {default_storage_setting}")
    elif default_storage_name:
        try:
            return import_string(default_storage_name)
        except ImportError:
            raise ImproperlyConfigured(f"Invalid default storage class: {default_storage_name}")
    else:
        raise ImproperlyConfigured(
            "Either CKEDITOR_5_FILE_STORAGE, DEFAULT_FILE_STORAGE, or STORAGES['default'] setting is required.")


storage = get_storage_class()


def image_verify(f):
    try:
        Image.open(f).verify()
    except OSError:
        raise NoImageException


def handle_uploaded_file(f):
    fs = storage()
    filename = fs.save(f.name, f)
    return fs.url(filename)


def upload_file(request):
    if request.method == "POST" and request.user.is_staff:
        form = UploadFileForm(request.POST, request.FILES)
        try:
            image_verify(request.FILES["upload"])
        except NoImageException as ex:
            return JsonResponse({"error": {"message": f"{str(ex)}"}})
        if form.is_valid():
            url = handle_uploaded_file(request.FILES["upload"])
            return JsonResponse({"url": url})
    raise Http404(_("Page not found."))

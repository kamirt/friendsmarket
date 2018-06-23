import os, uuid
import sys
from PIL import Image
from io import BytesIO
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile

def get_upload_path(instance, filename, path):
    ext = os.path.splitext(filename)[1]
    filename = str(uuid.uuid4()) + ext
    return os.path.join(path, filename)

def save_resized_image(imagefile, width, ratio):
    # Пересохраняем только если такого файла еще нет
    if os.path.isfile(settings.MEDIA_ROOT + "/" + imagefile.name):
        return imagefile

    img = Image.open(imagefile)
    output = BytesIO()

    crop = [
        min(round(img.size[1] * ratio), img.size[0]),
        min(round(img.size[0] / ratio), img.size[1])
    ]
    box = (
        (img.size[0] - crop[0])/2,
        (img.size[1] - crop[1])/2,
        (img.size[0] + crop[0])/2,
        (img.size[1] + crop[1])/2
    )
    factor = 1 if crop[0] < width else width/crop[0]
    size = (
        round(crop[0] * factor),
        round(crop[1] * factor)
    )

    img = img.resize(size=size, resample=Image.BILINEAR, box=box)
    img.save(output, format='JPEG', quality=80)
    imagefile = InMemoryUploadedFile(output, 'ImageField',
        "%s.jpg" % imagefile.name.split('.')[0], 'image/jpeg',
        sys.getsizeof(output), None)
    return imagefile

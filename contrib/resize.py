
import os
import sys
from PIL import Image

class Model(object):
    def __init__(self, filename):
        self.profile_photo = filename

    def save(self, output):
        width = 800
        ratio = 16/9

        img = Image.open(self.profile_photo)

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
        img.save(output, format='JPEG', quality=100)

resized_dir = 'resized'
if not os.path.exists(resized_dir):
    os.makedirs(resized_dir)

for filename in os.listdir('.'):
    if filename.endswith('.jpg') or filename.endswith('.png'):
        m = Model(filename)
        m.save('%s/%s.jpg' % (resized_dir, filename.split('.')[0]))

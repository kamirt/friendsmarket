from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Q
from django.conf import settings
from django.core.mail import send_mail

import json
from urllib.request import Request, urlopen

from fm.models import User, Post, Comment

def fcm_send(data):
    url = "https://fcm.googleapis.com/fcm/send"
    key = "AAAA521LTfA:APA91bFiWuoIlaMAXFW29x5AYGDNm4ROt4Sc0Q3hQ6mnoV5Ekj8Edy366JVM7RVWcI3hIsrcPuEQkHayFFDeF10ELlxAdV5C28vjhOQg-3qnoSOS5hDmaD40QbOvFdDzKUsWPlzBEhA7"

    request = json.dumps(data, separators=(",", ":")).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": "key=%s" % (key),
        "Content-Length": str(len(request)),
    }
    request = Request(url, request, headers)
    response = urlopen(request).read().decode("utf-8")
    return response


@receiver(post_save, sender=Comment)
def notify_comment(sender, instance, created, **kwargs):
    if not created:
    	return None

    # Находим всех кто следит за этим постом + владельца поста;
    # выбираем только тех у кого включены оповещения и исключаем автора комментария;
    # исключаем тех у кого нет registration_id от FireBase (вдруг есть такие);
    # без сортировки, только неповторяющиеся, списком токенов
    filt = Q(post_follows=instance.post) | Q(pk=instance.post.author_id)

    if instance.parent is not None:
        # Сообщение об ответе на коментарий
        filt |= Q(pk=instance.parent.author_id)

    ids = User.objects.filter(filt) \
        .filter(enable_notif=True).exclude(pk=instance.author_id) \
        .exclude(android_regid__exact='').exclude(android_regid__isnull=True) \
        .order_by().distinct().values_list('android_regid', flat=True)

    if not ids:
        return None

    body = "{}: {}".format(instance.author.get_full_name(),
        instance.note.title if instance.post.typeContent is Post.QUESTION else 
        instance.comment)
    data = {"title": instance.post.title, "body": body, "post": instance.post.pk, "comment": instance.pk}
    payload = {"registration_ids": list(ids), "data": data}

    if settings.DEBUG:
        print('PUSH-message payload:', payload)
        return None

    return fcm_send(payload)

@receiver(post_save, sender=Post)
def notify_post(sender, instance, created, **kwargs):
    if not created:
        return None

    # Находим всех пользователей которые следят за автором поста
    # выбираем из них тех у кого включены оповещения;
    # исключаем тех у кого нет registration_id от FireBase (вдруг есть такие);
    # без сортировки, только неповторяющиеся, списком токенов
    ids = User.objects.filter(my_friends__friend=instance.author, my_friends__follow=True) \
        .filter(enable_notif=True) \
        .exclude(android_regid__exact='').exclude(android_regid__isnull=True) \
        .order_by().distinct().values_list('android_regid', flat=True)

    if not ids:
        return None

    data = {"title": instance.author.get_full_name(), "body": instance.title, "post": instance.pk, "comment": 0}
    payload = {"registration_ids": list(ids), "data": data}

    if settings.DEBUG:
        print('PUSH-message payload:', payload)
        return None

    return fcm_send(payload)

@receiver(post_save, sender=User)
def send_greetings(sender, instance, created, **kwargs):
    if not created:
        return None

    subject = 'Добро пожаловать в Friendmarket!'
    message = 'Здравствуйте!\n\nДобро пожаловать в Friendmarket, социальную сеть друзей!\n\n--\n\nС уважением,\nВаш Friendmarket'

    email_from = getattr(settings, 'DEFAULT_FROM_EMAIL')

    send_mail(subject, message, email_from, [instance.email], fail_silently=True)

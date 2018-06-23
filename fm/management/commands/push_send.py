#!/usr/bin/env python3

from django.core.management.base import BaseCommand, CommandError

from fm.models import User
from fm.signals import fcm_send

class Command(BaseCommand):
    help = 'Sends PUSH-message to user'

    def add_arguments(self, parser):
        parser.add_argument('-p', dest='post_id', nargs='?', type=int, default=0)
        parser.add_argument('-c', dest='comment_id', nargs='?', type=int, default=0)
        parser.add_argument('-t', dest='title', nargs='?', default='Мега пост')
        parser.add_argument('-b', dest='body', nargs='?', default='Сообщение')
        parser.add_argument('-u', dest='user', nargs='*', default='admin@friendmarket.com')

    def handle(self, *args, **options):
        ids = User.objects.filter(email__in=options['user']) \
            .order_by().distinct().values_list('android_regid', flat=True)
        if not ids:
            raise CommandError('No valid user(s) defined: %s' % options['user'])

        data = {"title": options['title'], "body": options['body'], "post": options['post_id'], "comment": options['comment_id']}
        payload = {"registration_ids": list(ids), "data": data}

        print('PUSH messaege payload:', payload)

        ret = fcm_send(payload)
        print('FCM returned:', ret)

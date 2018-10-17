from django.test import TestCase
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
def send(request):
    msg='<a href="哈哈哈" target="_blank">点击激活</a>'
    send_mail('标题','内容',settings.EMAIL_FROM,
               '目标邮箱',
               html_message=msg)
    return HttpResponse('ok')
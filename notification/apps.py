from django.apps import AppConfig


class Config(AppConfig):
    name = "notifications"
    verbose_name = '通知管理系统'

    def ready(self):
        super(Config, self).ready()
        # this is for backwards compability
        import notification.signals
        notification.notify = notification.signals.notify

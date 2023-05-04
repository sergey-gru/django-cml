from __future__ import absolute_import
from enum import Enum
from django.db import models
from django.conf import settings
# from django.utils.translation import gettext_lazy as _


class ExchangeState(Enum):
    INIT  = 'init' # noqa
    DONE  = 'DONE' # noqa
    ABORT = 'abort' # noqa

    @classmethod
    def choices(cls):
        return tuple((str(st), st.name) for st in cls)

    def __str__(self):
        return self.value


class Exchange(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.SET_NULL,
                             null=True)
    state = models.CharField(max_length=15,
                             choices=ExchangeState.choices(),
                             default=str(ExchangeState.INIT))
    dt_start = models.DateTimeField(auto_now_add=True)
    dt_action = models.DateTimeField(auto_now=True, blank=True)

    operation = models.CharField(max_length=30, default='', null=True)
    file_name = models.CharField(max_length=250, default='', null=True)

    c_up = models.IntegerField(default=0)
    c_up_xml = models.IntegerField(default=0)
    c_up_img = models.IntegerField(default=0)

    c_imp_classifier = models.IntegerField(default=0)
    c_imp_catalogue = models.IntegerField(default=0)
    c_imp_offers_pack = models.IntegerField(default=0)
    c_imp_doc = models.IntegerField(default=0)

    c_exp_doc = models.IntegerField(default=0)

    report = models.CharField(max_length=2048, default='')

    class Meta:
        verbose_name = 'Exchange log entry'
        verbose_name_plural = 'Exchange logs'
        ordering = ['-dt_action']

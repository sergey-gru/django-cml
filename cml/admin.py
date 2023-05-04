from __future__ import absolute_import
from datetime import timedelta
from django.contrib import admin
from .models import *


@admin.register(Exchange)
class ExchangeAdmin(admin.ModelAdmin):
    list_display = (
        'dt_start_iso',
        'duration',
        'user',
        'uploaded',
        'imported',
        'exported',
        'operation',
        'file_name_short',
        'state',
        'report_short',
    )
    list_display_links = ('dt_start_iso', 'report_short',)
    readonly_fields = (
        'user',
        'dt_start',
        'file_name',
        'c_up',
        'c_up_xml',
        'c_up_img',
        'c_imp_classifier',
        'c_imp_catalogue',
        'c_imp_offers_pack',
        'c_imp_doc',
        'c_exp_doc',
        'state',
        'report',
    )
    ordering = ('-dt_start', )

    def dt_start_iso(self, rec):
        return rec.dt_start.isoformat(timespec='seconds')
    dt_start_iso.short_description = 'date start'

    def dt_action_iso(self, rec):
        return rec.dt_action.isoformat(timespec='seconds')
    dt_action_iso.short_description = 'date action'

    @staticmethod
    def duration(rec):
        diff = rec.dt_action - rec.dt_start
        sec = round(diff.total_seconds())
        diff = timedelta(seconds=sec)
        return str(diff)

    @staticmethod
    def uploaded(rec):
        fmt = 'xml={}\nimg={}\nall={}'
        return fmt.format(rec.c_up_xml,
                          rec.c_up_img,
                          rec.c_up)

    @staticmethod
    def imported(rec):
        fmt = 'cl={}\ncat={}\noff={}\ndocs={}'
        return fmt.format(rec.c_imp_classifier,
                          rec.c_imp_catalogue,
                          rec.c_imp_offers_pack,
                          rec.c_imp_doc)

    @staticmethod
    def exported(rec):
        fmt = 'docs={}'
        return fmt.format(rec.c_exp_doc)

    @staticmethod
    def _get_str_cut(val: str, max_len: int, cut_left=True) -> str:
        if len(val) <= max_len:
            return val
        if cut_left:
            return '...' + val[-(max_len-3):]
        else:
            return val[:max_len-3] + '...'

    def report_short(self, rec):
        return self._get_str_cut(rec.report, 30, False)
    report_short.short_description = 'report'

    def file_name_short(self, rec):
        return self._get_str_cut(rec.file_name, 15, True)
    file_name_short.short_description = 'file name'

    def has_add_permission(self, request):
        return False

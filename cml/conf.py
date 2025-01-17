import os
from django.conf import settings
from appconf import AppConf


class CMLAppCong(AppConf):
    UPLOAD_ROOT = os.path.join(settings.MEDIA_ROOT, 'cml', 'tmp')
    DELETE_FILES_AFTER_IMPORT = True

    MAX_EXEC_TIME = 60
    USE_ZIP = False
    FILE_LIMIT = 0

from __future__ import absolute_import
import typing
import os
import shutil
import datetime
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.db import transaction
from django.http import (HttpRequest, HttpResponse)
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from . import logger
from . import (auth, utils, items)
from .models import Exchange, ExchangeState


# Test configuration of delegate. If delegate was not configured,
utils.AbstractUserDelegate.get_child_class()

RESPONSE_SUCCESS = 'success'
RESPONSE_PROGRESS = 'progress'
RESPONSE_ERROR = 'failure'


@csrf_exempt
@auth.has_perm_or_basicauth("cml.add_exchange")
@auth.logged_in_or_basicauth()
def front_view(request):
    return ProtocolView().dispatch(request)


class ResponseException(Exception):
    def __init__(self, response: HttpResponse):
        self.res = response


def response_success(msg='') -> HttpResponse:
    res = "{}\n{}".format(RESPONSE_SUCCESS, msg)
    return HttpResponse(res)


def response_progress(msg='') -> HttpResponse:
    res = "{}\n{}".format(RESPONSE_PROGRESS, msg)
    return HttpResponse(res)


def response_error(msg='') -> HttpResponse:
    res = "{}\n{}".format(RESPONSE_ERROR, msg)
    return HttpResponse(res)


msg_err_srv = 'An internal error occurred. We already know about it. We will try to fix it soon.'


# Protocol description:
#
# Legend:
# - required step
# ? possible step
#
# Import catalog:
# ? api_catalog_check_auth()
# - api_catalog_init()
# ? api_catalog_file(filename='import_files/24/243564***.png')
# - api_catalog_file(filename='import.xml')
# - api_catalog_import(filename='import.xml')
#
# Import offers:
# - api_catalog_check_auth()
# - api_catalog_init()
# - api_catalog_file(filename='offers.xml')
# - api_catalog_import(filename='offers.xml')
#
# Request orders:
# - api_sale_check_auth()
# - api_sale_query()
# - api_sale_success()


class HttpRequestAuth(HttpRequest):
    user: any = None
    session: any = None


class ProtocolSession(object):
    def __init__(self, pv: 'ProtocolView', user=None, create=True, operation='init', filename=''):
        self._pv = pv
        self.user = user
        self.create = create
        self.operation = operation
        self.filename = filename
        self._rec = None

    def close(self):
        self._rec.state = ExchangeState.DONE

    def set_operation(self, operation, filename):
        self._rec.operation = operation
        self._rec.file_name = filename
        self._rec.save()

    def __enter__(self):
        """
        get or create `_rec`
        """
        with transaction.atomic():
            if self.create:
                aa = Exchange.objects.filter(state=ExchangeState.INIT)  # type: ignore[attr-defined]
                aa.filter(user=self.user).update(
                    state=ExchangeState.ABORT,
                    report='Aborted by the same user'
                )
                aa.exclude(user=self.user).update(
                    state=ExchangeState.ABORT,
                    report=f'Aborted by another user: {self.user.username}'
                )

                tz = timezone.get_current_timezone()
                rec = Exchange.objects.create(  # type: ignore[attr-defined]
                    state=ExchangeState.INIT,
                    user=self.user,
                    dt_start=datetime.datetime.now(tz=tz)
                )
            else:
                try:
                    rec = Exchange.objects.get(state=ExchangeState.INIT, user=self.user)  # type: ignore[attr-defined]
                except Exception:
                    msg = 'Session has not been started. Try to make init request.'
                    logger.info(msg)
                    raise ResponseException(response_error(msg))

        self._rec = rec
        pv = self._pv

        if not self.create:
            # Here load saved or default data into `self._rec`
            pv.c_up = rec.c_up
            pv.c_up_xml = rec.c_up_xml
            pv.c_up_img = rec.c_up_img

            pv.c_imp_classifier = rec.c_imp_classifier
            pv.c_imp_catalogue = rec.c_imp_catalogue
            pv.c_imp_offers_pack = rec.c_imp_offers_pack
            pv.c_imp_doc = rec.c_imp_doc

            pv.c_exp_doc = rec.c_exp_doc

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        suppress = False
        rec = self._rec
        pv = self._pv
        ud = pv.user_delegate

        with transaction.atomic():
            # Here save data into `rec`
            rec.c_up = pv.c_up
            rec.c_up_xml = pv.c_up_xml
            rec.c_up_img = pv.c_up_img

            rec.c_imp_classifier = pv.c_imp_classifier
            rec.c_imp_catalogue = pv.c_imp_catalogue
            rec.c_imp_offers_pack = pv.c_imp_offers_pack
            rec.c_imp_doc = pv.c_imp_doc

            rec.c_exp_doc = pv.c_exp_doc

            if exc_type is not None:
                rec.state = ExchangeState.ABORT
                rec.report = str(exc_val)  # register last error
            else:
                # Call user report function only if no exception
                try:
                    rec.report = ud.get_report()
                except Exception as e:
                    msg = f'Exception get_report: {e}'
                    rec.report = msg
                    logger.error(msg, exc_info=True)
                    # result of operation will be OK.
                    # This Exception is only server's problem that cannot abort process

            rec.save()

        return suppress


# ref: https://v8.1c.ru/tekhnologii/obmen-dannymi-i-integratsiya/standarty-i-formaty/protokol-obmena-s-saytom/


class ProtocolView(View):
    """
    This class created for manage of import sessions,
    for access control
    for registration and logging exchanges
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)  # type: ignore
        self.routes_map: dict[str, typing.Callable[[HttpRequestAuth], HttpResponse]] = {
            ('catalog', 'checkauth'): self.api_check_auth,
            ('catalog', 'init'): self.api_init,
            ('catalog', 'file'): self.api_file,
            ('catalog', 'import'): self.api_import,
            ('import', 'import'): self.api_import,
            ('sale', 'checkauth'): self.api_check_auth,
            ('sale', 'init'): self.api_init,
            ('sale', 'file'): self.api_file,
            ('sale', 'query'): self.api_query,
            ('sale', 'success'): self.api_success,
        }

        self.user_delegate = utils.AbstractUserDelegate.get_child_instance()
        self._check_cml_upload_root(items.FileRef.base_path)
        self.operation = None

        self.c_up = 0
        self.c_up_xml = 0
        self.c_up_img = 0

        self.c_imp_classifier = 0
        self.c_imp_catalogue = 0
        self.c_imp_offers_pack = 0
        self.c_imp_doc = 0

        self.c_exp_doc = 0

    @staticmethod
    def _check_cml_upload_root(path: str):
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except OSError:
                logger.error(f'Cannot create upload directory: {path}')
                raise

    def import_pack(self, pack: items.Packet):
        if pack.classifier:
            self.user_delegate.import_classifier(pack.classifier)
            self.c_imp_classifier += 1
        if pack.catalogue:
            self.user_delegate.import_catalogue(pack.catalogue)
            self.c_imp_catalogue += 1
        if pack.offers_pack:
            self.user_delegate.import_offers(pack.offers_pack)
            self.c_imp_offers_pack += 1
        for doc in pack.docs:
            self.user_delegate.import_document(doc)
            self.c_imp_doc += 1

    # Check GET parameter filename and fix it, return (response, filename)
    @staticmethod
    def _get_param_filename(request: HttpRequestAuth) -> str:
        filename = request.GET['filename']
        if not filename:  # None or ''
            msg = f'GET parameter <filename>="{filename}" is empty.'
            logger.info(msg)
            raise ResponseException(response_error(msg))
        return filename

    def session(self, request: HttpRequestAuth, is_init=False):
        return ProtocolSession(self, request.user, is_init)

    # @csrf_exempt
    # @auth.has_perm_or_basicauth('cml.add_exchange')
    # @auth.logged_in_or_basicauth()
    def dispatch(self, request: HttpRequestAuth, *args, **kwargs) -> HttpResponse:
        get_kwargs = request.GET.dict()
        logger.debug(f'user="{request.user}" {request.method} ({get_kwargs})')

        p_type = request.GET.get('type')
        p_mode = request.GET.get('mode')
        self.operation = f'{p_type}_{p_mode}'

        api_method = self.routes_map.get((p_type, p_mode))
        if not api_method:
            msg = f'Unknown GET sequence: {get_kwargs}'
            logger.info(msg)
            return response_error(msg)

        try:
            res = api_method(request)
        except Exception as e:
            logger.error(f'Internal server error: method={api_method.__name__} msg="{e}" '
                         f'GET: {get_kwargs}  user="{request.user}"',
                         exc_info=True)
            return response_error(f'Internal server error. GET args: {get_kwargs}')

        return res

    @classmethod
    def api_check_auth(cls, request: HttpRequestAuth):
        logger.info(f'catalog_check_auth(user={request.user}): OK')

        session = request.session
        res = '{}\n{}'.format(settings.SESSION_COOKIE_NAME, session.session_key)
        return response_success(res)

    def api_init(self, request: HttpRequestAuth):
        with self.session(request, is_init=True):
            logger.info(f'catalog_init(user={request.user}): OK')

            result = 'zip={}\nfile_limit={}'.format(
                'yes' if settings.CML_USE_ZIP else 'no',
                settings.CML_FILE_LIMIT
            )
            return HttpResponse(result)

    # Receiving import file
    def api_file(self, request: HttpRequestAuth):
        if request.method != 'POST':
            msg = f'Bad request method: {request.method}'
            logger.info(msg)
            return response_error(msg)

        with self.session(request) as cur:
            filename = self._get_param_filename(request)
            cur.set_operation(self.operation, filename)

            fref = items.FileRef(filename)
            folder_path = fref.full_path.parent

            temp_file = SimpleUploadedFile(filename, request.read())
            try:
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)

                f = open(fref.full_path, 'wb')
                for chunk in temp_file.chunks():
                    f.write(chunk)
            except Exception as e:
                logger.error(f'Cannot write to file. msg: {e}')
                return response_error('Cannot write to buffer file')

            logger.info(f'File loaded: {fref.path}')

            self.c_up += 1
            if fref.path.suffix == '.xml':
                self.c_up_xml += 1
            if fref.is_image_type():
                self.c_up_img += 1

            if request.GET['type'] == 'sale':
                # Here is a code for import orders statuses
                logger.info(f'Order status import signal. Filename: {fref.path}')

            return response_success()

    # Processing import received file
    def api_import(self, request: HttpRequestAuth):
        with self.session(request) as cur:
            filename = self._get_param_filename(request)
            cur.set_operation(self.operation, filename)

            fref = items.FileRef(filename)
            if not fref.full_path.exists():
                msg = f'File not found: {fref.path}'
                logger.info(msg)
                return response_error(msg)

            pack = items.Packet.parse(fref.full_path)
            self.import_pack(pack)

            if settings.CML_DELETE_FILES_AFTER_IMPORT:
                try:
                    shutil.rmtree(items.FileRef.base_path)
                except OSError as e:
                    logger.warning(f'Cannot delete files after import: {e}')

            logger.info(f'Import completed. filename: {filename}')
            cur.close()
            return response_success()

    def api_query(self, request: HttpRequestAuth):
        with self.session(request, is_init=True) as cur:
            cur.set_operation(self.operation, 'query')

            pack = items.Packet()
            pack.docs = self.user_delegate.export_orders()

            data = pack.compose()
            self.c_exp_doc += 1

            logger.info(f'sale_success(user={request.user}): OK')
            return HttpResponse(data, content_type='text/xml')

    def api_success(self, request: HttpRequestAuth):
        with self.session(request) as cur:
            cur.close()
            logger.info(f'sale_success(user={request.user}): OK')
            return response_success()

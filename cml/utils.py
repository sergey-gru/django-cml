# -*- coding: utf-8 -
from __future__ import absolute_import
import importlib
import inspect
from . import logger
from . import items, xml
from .conf import settings


class AbstractUserDelegate(object):
    def __init__(self):
        pass

    @classmethod
    def get_child_class(cls) -> type:
        try:
            module_name = settings.CML_USER_DELEGATE
        except AttributeError:
            logger.error('CML_PROJECT_PIPELINES is not configured in settings. '
                         'You can create pipeline file by command: python manage.py cmlpipelines')
            raise

        try:
            user_module = importlib.import_module(module_name)
        except ImportError as e:
            logger.error(f'Cannot import module: "{module_name}" {e}')
            raise

        user_delegate_class = None
        if inspect.isclass(user_module):
            if issubclass(user_module, cls):  # type: ignore
                user_delegate_class = user_module
        elif inspect.ismodule(user_module):
            for name, obj in inspect.getmembers(user_module):
                if inspect.isclass(obj) and issubclass(obj, cls):
                    user_delegate_class = obj
                    break

        if user_delegate_class is None:
            msg = f'{module_name} is not valid class or module.'
            logger.warning(msg)
            raise AttributeError(msg)

        return user_delegate_class

    @classmethod
    def get_child_instance(cls, *args, **kwargs) -> 'AbstractUserDelegate':
        user_delegate_class = cls.get_child_class()
        return user_delegate_class(*args, **kwargs)  # type: ignore

    #
    # Section: user delegate methods
    # These methods are called
    # 1. strictly in this order
    # 2. only if the corresponding object is not None
    #

    def import_classifier(self, cl: items.Classifier):
        raise NotImplementedError()

    def import_catalogue(self, cat: items.Catalogue):
        raise NotImplementedError()

    def import_offers(self, off_pack: items.OffersPack):
        raise NotImplementedError()

    def import_document(self, doc: items.Document):
        raise NotImplementedError()

    def export_orders(self) -> [items.Document]:
        raise NotImplementedError()

    def get_report(self) -> str:  # noqa
        """
        Creates str summary after all import/export process.
        This method calls after each whole operation import/export
        """
        return 'OK'

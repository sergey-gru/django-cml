# -*- coding: utf-8 -
"""
This file was generated with the cml_init management command.
It contains UserDelegate class with methods for import one CML packet.
All you need is implement these methods.

All data structures explained in `cml.items` module.
"""
import logging
from cml import items, utils

# Some libraries you may need also
import os
from datetime import datetime, timezone, timedelta
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.db import transaction
from django.conf import settings


logger = logging.getLogger(__name__)


class UserDelegate(utils.AbstractUserDelegate):
    """This object is created every time, when new xml CML packet imports"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # type: ignore

        # Example of statistics
        self.c_del_img = 0
        self.c_saved_img = 0

    def get_report(self) -> str:
        """Report a custom message for finished process"""
        return 'OK: '\
               f'del_img={self.c_del_img}, '\
               f'saved_img={self.c_saved_img}'

    def import_classifier(self, item: items.Classifier):
        """update_or_create groups, predefined fields"""
        pass

    def import_catalogue(self, cat: items.Catalogue):
        """update_or_create products from catalogue, delete all others if need"""
        # Update statistics:
        # self.c_del_img += 1
        # self.c_saved_img += 1
        pass

    def import_offers(self, off_pack: items.OffersPack):
        """update_or_create prices of loaded products from catalogue"""
        pass

    def import_document(self, doc: items.Document):
        """Import document such an order or delivery. See doc.doc_type"""
        pass

    def export_orders(self) -> [items.Document]:
        """Create documents-orders for sending back. """
        pass

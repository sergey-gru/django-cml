# -*- coding: utf-8 -
from __future__ import absolute_import
import os
from decimal import Decimal
from datetime import datetime
from enum import Enum, IntEnum
from pathlib import Path
from . import logger
from .conf import settings
from .xml import XmlElement


def time_from_string(s: str) -> datetime.time:
    return datetime.strptime(s, '%H:%M:%S').time()


def time_to_string(time: datetime.time) -> str:
    return time.isoformat(timespec='seconds')
    # return time.strftime('%H:%M:%S')


def date_from_string(s: str) -> datetime.date:
    return datetime.fromisoformat(s).date()


def date_to_string(dt: datetime.date) -> str:
    return dt.isoformat()


class Packet(object):
    """Represent packet with current supported version.
    Has methods for parsing and packing xml"""

    def __init__(self):
        self.version = '2.08'
        self.create_date: datetime = datetime.now()

        self.classifier: Classifier or None = None
        self.catalogue: Catalogue or None = None
        self.offers_pack: OffersPack or None = None
        self.docs: [Document] = []

    @classmethod
    def parse(cls, source: str or bytes) -> 'Packet':
        el = XmlElement.parse(source)
        return cls.parse_xml(el)

    def compose(self) -> bytes:
        el = self.compose_xml()
        return el.compose()

    @classmethod
    def parse_xml(cls, el: XmlElement) -> 'Packet':
        ver = el.get_attr('ВерсияСхемы', converter=str)
        if ver != "2.08":
            logger.warning('Version of scheme is no 2.08. Errors unattended possibly')

        pack = cls()
        pack.version = ver
        pack.create_date = el.get_attr('ДатаФормирования', converter=datetime.fromisoformat)
        pack.classifier = el.find('Классификатор', converter_xml=Classifier.parse_xml, required=False)
        pack.catalogue = el.find('Каталог', converter_xml=Catalogue.parse_xml, required=False)
        pack.offers_pack = el.find('ПакетПредложений', converter_xml=OffersPack.parse_xml, required=False)
        pack.docs = el.findall('Документ', converter_xml=Document.parse_xml)
        return pack

    def compose_xml(self, tag='КоммерческаяИнформация') -> XmlElement:
        el = XmlElement(tag)
        el.set_attr('ВерсияСхемы', '2.08')
        el.set_attr('ДатаФормирования', self.create_date.isoformat(timespec='seconds'))
        if self.classifier:
            el.append(self.classifier.compose_xml())
        if self.catalogue:
            el.append(self.catalogue.compose_xml())
        if self.offers_pack:
            el.append(self.offers_pack.compose_xml())
        for doc in self.docs:
            el.append(doc.compose_xml())
        return el


# Base element for any xml parsing
class ItemBase(object):
    def __init__(self, xml_element=None, *args, **kwargs):
        self.xml_element = xml_element


def as_bool(value: str) -> bool:
    return value == 'true'


#
# Classifier section
#


class Classifier(ItemBase):
    def __init__(self, *args, **kwargs):
        super(Classifier, self).__init__(*args, **kwargs)  # type: ignore
        self.uid = ''
        self.name = ''
        self.owner = {}
        self.groups: [Group] = []  # This is main classification hierarchy for site
        self.props: [Property] = []
        self.categories: [Category] = []  # Don't use this data for naming product groups
        self.units: [Unit] = []

    @classmethod
    def parse_xml(cls, el: XmlElement) -> 'Classifier':
        it = cls(el)
        it.uid = el.find('Ид', converter=str)
        it.name = el.find('Наименование', converter=str)
        it.owner = el.findall('Владелец', converter_xml=Partner.parse_xml)
        it.groups = el.findall('Группы/Группа', converter_xml=Group.parse_xml)
        it.props = el.findall('Свойства/Свойство', converter_xml=Property.parse_xml)
        it.categories = el.findall('Категории/Категория', converter_xml=Category.parse_xml)
        it.units = el.findall('ЕдиницыИзмерения/ЕдиницаИзмерения', converter_xml=Unit.parse_xml)
        return it

    def compose_xml(self, tag='Классификатор') -> XmlElement:
        el = XmlElement(tag)
        el.append(self.owner.compose_xml())
        for gr in self.groups:
            el.append(gr.compose_xml())

        return el

    def __str__(self):
        s = 'Classifier:\n' \
            f'id="{self.uid}"\n' \
            f'name="{self.name}"\n'
        s += f'groups: {self.groups}\n'
        s += f'properties: {self.props}\n'
        s += f'categories: {self.categories}\n'
        s += f'units: {self.units}\n'
        return s


class Partner(ItemBase):
    def __init__(self, *args, **kwargs):
        super(Partner, self).__init__(*args, **kwargs)  # type: ignore
        self.uid = ''
        self.name = ''
        self.fields = {}

    @classmethod
    def parse_xml(cls, el: XmlElement) -> 'Partner':
        it = cls(el)
        it.uid = el.find('Ид', converter=str, default='')
        it.name = el.find('Наименование', converter=str, default='')
        # for eli in el.findall('*'):
        #     it.fields[eli.tag] = eli.text
        return it


class Group(ItemBase):
    def __init__(self, *args, **kwargs):
        super(Group, self).__init__(*args, **kwargs)  # type: ignore
        self.uid = ''
        self.name = ''
        self.description = ''
        self.groups: [Group] = []

    @classmethod
    def parse_xml(cls, el: XmlElement):
        it = cls(el)
        it.uid = el.find('Ид', converter=str)
        it.name = el.find('Наименование', converter=str)
        it.description = el.find('Описание', converter=str, required=False)
        it.groups = el.findall('Группы/Группа', converter_xml=Group.parse_xml)
        return it

    def __repr__(self):
        return f'{self.name}: {self.groups}'


class ValueType(Enum):
    STRING = 'Строка'  # Boolean values represents as strings "Yes" "No"
    NUMBER = 'Число'   # float number
    DATETIME = 'Время'
    LIST = 'Справочник'


class Property(ItemBase):
    def __init__(self, *args, **kwargs):
        super(Property, self).__init__(*args, **kwargs)  # type: ignore
        self.uid = ''
        self.name = ''
        self.value_type: ValueType = ValueType.STRING
        self.is_multi = False
        self.is_required = False
        self.for_products = False
        self.variants_list: [PropertyValue] = []  # Values with uid, for ValueType.LIST (values bordered by list)
        self.variants: [str] = []  # Optional just values for regular text field. Just list of recommendations

    def __repr__(self):
        if self.value_type == 'Справочник':
            return f'[{self.name}]'
        else:
            return f'{self.name}: {self.value_type}'

    @classmethod
    def parse_xml(cls, el: XmlElement):
        it = cls(el)
        it.uid = el.find('Ид', converter=str)
        it.name = el.find('Наименование', converter=str)
        it.value_type = el.find('ТипЗначений', converter=ValueType)
        it.is_multi = el.find('Множественное', converter=as_bool, default=False)
        it.is_required = el.find('Обязательное', converter=as_bool, default=False)
        it.for_products = el.find('ДляТоваров', converter=as_bool)

        it.variants = el.findall('ВариантыЗначений/*/Значение', converter=str)
        if it.value_type == ValueType.LIST:
            it.variants_list = el.findall('ВариантыЗначений/Справочник',
                                          converter_xml=PropertyVariant.parse_xml)
        return it


class PropertyVariant(ItemBase):
    def __init__(self, *args, **kwargs):
        super(PropertyVariant, self).__init__(*args, **kwargs)  # type: ignore
        self.uid = ''
        self.value = ''

    def __repr__(self):
        return str(self.value)

    @classmethod
    def parse_xml(cls, el: XmlElement):
        it = cls(el)
        it.uid = el.find('ИдЗначения', converter=str)
        it.value = el.find('Значение', converter=str)
        return it


class Category(ItemBase):
    def __init__(self, *args, **kwargs):
        super(Category, self).__init__(*args, **kwargs)  # type: ignore
        self.uid = ''
        self.name = ''
        self.property_ids: [str] = []  # Some of these property id could not be present in Classifier().props

    @classmethod
    def parse_xml(cls, el: XmlElement):
        it = cls(el)
        it.uid = el.find('Ид', converter=str)
        it.name = el.find('Наименование', converter=str)
        it.property_ids = el.findall('Свойства/Ид', converter=str)
        return it

    def __repr__(self):
        return f'{self.name}'


class Unit(ItemBase):
    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)  # type: ignore
        self.unit_id: int = 796  # Piece code
        self.name_full = 'Штука'
        self.abbr_intern = 'PCE'

    @classmethod
    def parse_xml_ref(cls, el: XmlElement):
        it = cls(el)
        it.unit_id = el.get_attr('Код', converter=int)
        it.name_full = el.get_attr('НаименованиеПолное')
        it.abbr_intern = el.get_attr('МеждународноеСокращение')
        return it

    def compose_xml_ref(self, tag='БазоваяЕдиница') -> XmlElement:
        el = XmlElement(tag)
        el.set_attr('Код', self.unit_id)
        el.set_attr('НаименованиеПолное', self.name_full)
        el.set_attr('МеждународноеСокращение', self.abbr_intern)
        return el

    @classmethod
    def parse_xml(cls, el: XmlElement):
        it = cls(el)
        it.unit_id = el.find('Код', converter=int)
        it.name_full = el.find('НаименованиеПолное', converter=str)
        it.name_intern = el.find('МеждународноеСокращение', converter=str)
        return it

    def compose_xml(self, tag='ЕдиницаИзмерения'):
        el = XmlElement(tag)
        el.append(XmlElement('Код')).text = self.unit_id
        el.append(XmlElement('НаименованиеПолное')).text = self.name_full
        el.append(XmlElement('МеждународноеСокращение')).text = self.abbr_intern
        return el

    def __repr__(self):
        return f'{self.name_full}={self.unit_id}'

#
# Section: Catalogue
#


class Catalogue(ItemBase):
    def __init__(self, *args, **kwargs):
        super(Catalogue, self).__init__(*args, **kwargs)  # type: ignore
        self.has_changes_only = False
        self.uid = ''
        self.classify_id = ''
        self.name = ''
        self.owner = {}
        self.products: [Product] = []

    @classmethod
    def parse_xml(cls, el: XmlElement):
        it = cls(el)
        it.has_changes_only = el.get_attr('СодержитТолькоИзменения', converter=bool, default=False)
        it.uid = el.find('Ид', converter=str)
        it.classify_id = el.find('ИдКлассификатора', converter=str)
        it.name = el.find('Наименование', converter=str)
        it.owner = el.findall('Владелец', converter_xml=Partner.parse_xml)
        it.products = el.findall('Товары/Товар', converter_xml=Product.parse_xml)
        return it

    def compose_xml(self) -> XmlElement:
        el = XmlElement('Каталог')
        el.set_attr('СодержитТолькоИзменения', str(self.has_changes_only))
        return el

    def __repr__(self):
        s = f'Catalogue(has_changes_only={self.has_changes_only}):\n'
        s += f'id="{self.uid}"\n'
        s += f'name="{self.name}"\n'
        s += f'classify_id="{self.classify_id}"\n'
        s += f'products_count: {len(self.products)}\n'

        return s


class ProductStatus(Enum):
    NEW = 'Новый'
    CHANGED = 'Изменен'
    REMOVED = 'Удален'


class Product(ItemBase):
    def __init__(self, *args, **kwargs):
        super(Product, self).__init__(*args, **kwargs)  # type: ignore
        self.status = ProductStatus.NEW
        self.uid = ''
        self.vendor_code = ''
        self.code = ''
        self.name = ''
        self.unit = Unit()
        self.group_uids: [str] or None = None  # Note: if this is None, add product to the global group
        self.category_uid = ''
        self.desc = ''
        self.prop_values: [PropertyValue] = []
        self.requisites: {str, str} = {}
        self.files: [FileRef] = []
        self.images: [FileRef] = []  # Order is important. First record represent main image

        self.sku_id = ''
        self.tax_name = ''

    def __repr__(self):
        return self.name

    @staticmethod
    def _imp_requisites(el: XmlElement) -> {str, str}:
        res = {}
        for el_req in el.findall('ЗначенияРеквизитов/ЗначениеРеквизита'):
            id_ = el_req.find('Наименование', converter=str)
            val = el_req.find('Значение', converter=str)
            res[id_] = val
        return res

    @classmethod
    def parse_xml(cls, el: XmlElement):
        it = cls(el)
        it.status = el.get_attr('Статус', converter=ProductStatus, default=ProductStatus.CHANGED)
        it.uid = el.find('Ид', converter=str)
        it.vendor_code = el.find('Артикул', converter=str)
        it.code = el.find('Код', converter=str)
        it.name = el.find('Наименование', converter=str)
        it.unit = el.find('БазоваяЕдиница', converter_xml=Unit.parse_xml_ref)
        it.group_uids = el.findall('Группы/Ид', converter=str)
        it.category_uid = el.find('Категория', converter=str)
        it.desc = el.find('Описание', converter=str, default='')

        pvals = el.findall('ЗначенияСвойств/ЗначенияСвойства', converter_xml=PropertyValue.parse_xml)
        it.prop_values = [pval for pval in pvals if not pval.is_empty()]

        it.requisites = cls._imp_requisites(el)
        # files, images
        for fr in el.findall('Картинка', converter=FileRef):
            if fr.is_image_type():
                it.images.append(fr)
            else:
                it.files.append(fr)
        it.taxes = el.findall('СтавкиНалогов/СтавкаНалога', converter_xml=Tax.parse_xml)

        return it


class PropertyValue(ItemBase):
    def __init__(self, *args, **kwargs):
        super(PropertyValue, self).__init__(*args, **kwargs)  # type: ignore
        self.uid = ''
        self.values: [str] = []

    def is_empty(self):
        return len(self.values) == 0

    def get_value(self):
        return None if self.is_empty() else self.values[0]

    def __repr__(self):
        return f'{self.uid}[0..{len(self.values)})={self.get_value()}'

    @classmethod
    def parse_xml(cls, el: XmlElement) -> 'PropertyValue':
        it = cls(el)
        it.uid = el.find('Ид', converter=str)
        it.values = el.findall('Значение', converter=str)
        return it


class FileState(IntEnum):
    UPDATED = 1   # Replace file
    PREVIOUS = 2  # Don't do anything


class FileRef(object):
    def __init__(self, raw_path: str, base_path: str = None):
        path = raw_path.strip()
        if len(path) == 0:
            raise ValueError('Path must be not empty.')

        p = Path('/', path).resolve()  # Prevent ../ or ./ in raw_path
        self.path = Path(str(p)[1:])  # Cut first symbol '/', because it's relative path

        self.full_path = Path(base_path or self.base_path, self.path).resolve()  # Finally make absolute and safe path

    base_path = settings.CML_UPLOAD_ROOT
    _image_suffixes = ['.png', '.gif', '.jpg', '.jpeg']

    def is_image_type(self):
        return self.path.suffix in self._image_suffixes

    def get_state(self) -> FileState:
        if os.path.exists(self.full_path):
            return FileState.UPDATED
        else:
            return FileState.PREVIOUS


class Tax(ItemBase):
    def __init__(self, *args, **kwargs):
        super(Tax, self).__init__(*args, **kwargs)  # type: ignore
        self.name = ''
        self.value = Decimal()

    @classmethod
    def parse_xml(cls, el: XmlElement) -> 'Tax':
        it = cls(el)
        it.name = el.find('Наименование', converter=str)
        it.value = el.find('Ставка', converter=Decimal)
        return it


#
# Section: Offers
#


class OffersPack(ItemBase):
    def __init__(self, *args, **kwargs):
        super(OffersPack, self).__init__(*args, **kwargs)  # type: ignore
        self.has_changes_only = False
        self.uid = ''
        self.name = ''
        self.catalogue_uid = ''
        self.classify_uid = ''

        self.owner = Partner()
        self.price_types: [PriceType] = []
        self.stocks: [Stock] = []
        self.offers: [Offer] = []

    @classmethod
    def parse_xml(cls, el: XmlElement):
        it = cls(el)
        it.uid = el.find('Ид', converter=str)
        it.name = el.find('Наименование', converter=str)
        it.catalogue_uid = el.find('ИдКаталога', converter=str)
        it.classify_uid = el.find('ИдКлассификатора', converter=str)
        it.owner = el.find('Владелец', converter_xml=Partner.parse_xml)
        it.price_types = el.findall('ТипыЦен/ТипЦены', converter_xml=PriceType.parse_xml)
        it.stocks = el.findall('Склады/Склад', converter_xml=Stock.parse_xml)
        it.offers = el.findall('Предложения/Предложение', converter_xml=Offer.parse_xml)
        return it

    def compose_xml(self) -> XmlElement:
        el = XmlElement('ПакетПредложений')
        el.set_attr('Ид', self.uid)
        return el


class PriceType(ItemBase):
    def __init__(self, *args, **kwargs):
        super(PriceType, self).__init__(*args, **kwargs)  # type: ignore
        self.uid = ''
        self.name = ''
        self.currency_name = ''
        self.tax_name = ''
        self.tax_in_sum = False

    @classmethod
    def parse_xml(cls, el: XmlElement):
        it = cls(el)
        it.uid = el.find('Ид', converter=str)
        it.name = el.find('Наименование', converter=str)
        it.currency_name = el.find('Валюта', converter=str)
        it.tax_name = el.find('Налог/Наименование', converter=str)
        it.tax_in_sum = el.find('Налог/УчтеноВСумме', converter=as_bool)
        return it


class Stock(ItemBase):
    def __init__(self, *args, **kwargs):
        super(Stock, self).__init__(*args, **kwargs)  # type: ignore
        self.uid = ''
        self.name = ''
        self.addr_repr = ''
        self.addr_details = {}
        self.phones: [PhoneNumber] = []

    @classmethod
    def parse_xml(cls, el: XmlElement):
        it = cls(el)
        it.uid = el.find('Ид', converter=str)
        it.name = el.find('Наименование', converter=str)
        return it


class PhoneNumber(ItemBase):
    def __init__(self, *args, **kwargs):
        super(PhoneNumber, self).__init__(*args, **kwargs)  # type: ignore
        self.type = ''
        self.phone = ''
        self.comment = ''


class Offer(ItemBase):
    def __init__(self, *args, **kwargs):
        super(Offer, self).__init__(*args, **kwargs)  # type: ignore
        self.product_uid = ''
        self.name = ''
        self.vendor_code = ''

        self.prices: [Price] = []
        self.stocks: [StockCount] = []
        self.stock_count = 0
        self.unit = Unit()

    @classmethod
    def parse_xml(cls, el: XmlElement):
        it = cls(el)
        it.product_uid = el.find('Ид', converter=str)
        it.name = el.find('Наименование', converter=str)
        it.vendor_code = el.find('Артикул', converter=str, default='')

        # Filter zero prices. Sometimes 1C exports zero prices for unsetted price types
        prices = el.findall('Цены/Цена', converter_xml=Price.parse_xml)
        it.prices = [it_1 for it_1 in prices if it_1.price != 0]
        it.stocks = el.findall('Склад', converter_xml=StockCount.parse_xml)
        it.stock_count = el.find('Количество', converter=int)
        it.unit = el.find('БазоваяЕдиница', converter_xml=Unit.parse_xml_ref)

        return it


class Price(ItemBase):
    def __init__(self, *args, **kwargs):
        super(Price, self).__init__(*args, **kwargs)  # type: ignore
        self.price_type_uid = ''
        self.price = Decimal()
        self.currency_name = ''
        self.unit_name = ''
        self.mul = 1

        self.description = ''
        self.uid = ''
        self.price = Decimal()
        self.unit_name = ''
        self.ratio = Decimal()

    @classmethod
    def parse_xml(cls, el: XmlElement):
        it = cls(el)
        it.desc = el.find('Представление', converter=str)
        it.uid = el.find('ИдТипаЦены', converter=str)
        it.price = el.find('ЦенаЗаЕдиницу', converter=Decimal)
        it.currency_name = el.find('Валюта', converter=str)
        it.unit_name = el.find('Единица', converter=str)
        it.ratio = el.find('Коэффициент', converter=Decimal)
        return it


class StockCount(ItemBase):
    def __init__(self, *args, **kwargs):
        super(StockCount, self).__init__(*args, **kwargs)  # type: ignore
        self.stock_uid = ''
        self.count = Decimal()

    @classmethod
    def parse_xml(cls, el: XmlElement) -> 'StockCount':
        it = cls(el)
        it.stock_uid = el.get_attr('ИдСклада', converter=str)
        it.count = el.get_attr('КоличествоНаСкладе', converter=Decimal)
        return it

#
# Section: Documents
#


class DocumentType(Enum):
    OTHER            = 'Прочие' # noqa
    INVOICE_FACTURA  = 'Счет-фактура' # noqa
    INVOICE_PAYMENT  = 'Счет на оплату' # noqa
    ORDER_GOODS      = 'Заказ товара' # noqa
    PAYMENT_CASH     = 'Выплата наличных денег' # noqa
    PAYMENT_NON_CASH = 'Выплата безналичных денег' # noqa
    REFUND_CASH      = 'Возврат наличных денег' # noqa
    REFUND_NON_CASH  = 'Возврат безналичных денег' # noqa
    REPORT_SALES_CONSIGNMENT   = 'Отчет о продажах комиссионного товара' # noqa
    RETURN_CONSIGNMENT_GOODS   = 'Возврат комиссионного товара' # noqa
    RETURN_GOODS               = 'Возврат товара' # noqa
    REVALUATION_GOODS          = 'Переоценка товаров' # noqa
    SHIPMENT_GOODS             = 'Отпуск товара' # noqa
    TRANSFER_GOODS_CONSIGNMENT = 'Передача товара на комиссию' # noqa


class CounterpartyRole(Enum):
    SELLER = 'Продавец'
    BUYER = 'Покупатель'
    PAYER = 'Плательщик'
    PRINCIPAL = 'Комитент'
    COMMISSION_AGENT = 'Комиссионер'


class Document(ItemBase):
    def __init__(self, *args, **kwargs):
        super(Document, self).__init__(*args, **kwargs)  # type: ignore
        self.uid = ''
        self.number = ''
        self.date = datetime.now().date()
        self.time = datetime.now().time() or None
        self.doc_type = DocumentType.ORDER_GOODS
        self.counterparty_role = CounterpartyRole.SELLER

        self.currency_name = 'USD'
        self.currency_rate = Decimal(1)  # related to basic currency
        self.sum = Decimal()
        self.comment = ''

        self.counterparties: [Counterparty] = []
        self.products: [ProductRef] = []

    def __repr__(self):
        return f'Document: "{self.doc_type.value}" from: ({self.counterparty_role.value}) {self.uid}'

    @classmethod
    def parse_xml(cls, el: XmlElement):
        it = cls(el)
        it.uid = el.find('Ид', converter=str)
        it.number = el.find('Номер', converter=str)
        # Date and time
        it.date = el.find('Дата', converter=date_from_string)
        it.time = el.find('Время', converter=time_from_string, required=False)

        it.doc_type = el.find('ХозОперация', converter=DocumentType)
        it.counterparty_role = el.find('Роль', converter=CounterpartyRole)
        it.counterparties = el.findall('Контрагенты/Контрагент', converter_xml=Counterparty.parse_xml)
        it.products = el.findall('Товары/Товар', converter_xml=ProductRef.parse_xml)

        it.currency_name = el.find('Валюта', converter=str)
        it.currency_rate = el.find('Курс', converter=Decimal)
        it.sum = el.find('Сумма', converter=Decimal)
        it.comment = el.find('Комментарий', converter=str)

        return it

    def compose_xml(self) -> XmlElement:
        el = XmlElement('Документ')
        el.append(XmlElement('Ид')).text = self.uid
        el.append(XmlElement('Номер')).text = self.number
        # Date and time
        el.append(XmlElement('Дата')).text = self.date.isoformat()
        if self.time is not None:
            el.append(XmlElement('Время')).text = time_to_string(self.time)
        el.append(XmlElement('ХозОперация')).text = self.doc_type.value
        el.append(XmlElement('Роль')).text = self.counterparty_role.value

        el.append(XmlElement('Валюта')).text = self.currency_name
        el.append(XmlElement('Курс')).text = str(self.currency_rate)
        el.append(XmlElement('Сумма')).text = str(self.sum)
        el.append(XmlElement('Комментарий')).text = self.comment

        clients = el.append(XmlElement('Контрагенты'))
        for c in self.counterparties:
            clients.append(c.compose_xml())

        products = el.append(XmlElement('Товары'))
        for pref in self.products:
            products.append(pref.compose_xml('Товар'))

        return el


class ProductRef(ItemBase):
    def __init__(self, *args, **kwargs):
        super(ProductRef, self).__init__(*args, **kwargs)  # type: ignore
        self.product_uid = ''
        self.product_name: str or None = None
        self.unit = Unit()
        self.price = Decimal()
        self.quantity = Decimal()
        self.sum = Decimal()

    @classmethod
    def parse_xml(cls, el: XmlElement) -> 'ProductRef':
        it = cls(el)
        it.uid = el.find('Ид', converter=str)
        it.name = el.find('Наименование', converter=str, required=False)
        it.unit = el.find('БазоваяЕдиница', converter=Unit.parse_xml_ref)
        return it

    def compose_xml(self, tag='Товар') -> XmlElement:
        el = XmlElement(tag)
        el.append(XmlElement('Ид')).text = self.product_uid
        if self.product_name is not None:
            el.append(XmlElement('Наименование')).text = self.product_name
        el.append(self.unit.compose_xml_ref())
        el.append(XmlElement('ЦенаЗаЕдиницу')).text = str(self.price)
        el.append(XmlElement('Количество')).text = str(self.quantity)
        el.append(XmlElement('Сумма')).text = str(self.sum)
        return el


class AddressField(Enum):
    INDEX     = 'Почтовый индекс'  # noqa
    COUNTRY   = 'Страна'  # noqa
    REGION    = 'Регион'  # noqa
    RAYON     = 'Район'  # noqa
    VILLAGE   = 'Населенный пункт'  # noqa
    TOWN      = 'Город'  # noqa
    STREET    = 'Улица'  # noqa
    HOME      = 'Дом'  # noqa
    CORP      = 'Корпус'  # noqa
    APARTMENT = 'Квартира'  # noqa


class Address(ItemBase):
    def __init__(self, *args, **kwargs):
        super(Address, self).__init__(*args, **kwargs)  # type: ignore
        self.content = ''
        self.comment = ''
        self.fields: dict[AddressField, str] = {fn: '' for fn in AddressField}

    @staticmethod
    def _parse_addr_field(el: XmlElement) -> tuple[AddressField, str]:
        typ = el.find('Тип', converter=AddressField)
        val = el.find('Значение', converter=str)
        return typ, val

    @staticmethod
    def _compose_addr_field(typ: AddressField, val: str) -> XmlElement:
        el = XmlElement('АдресноеПоле')
        el.append(XmlElement('Тип')).text = typ.value
        el.append(XmlElement('Значение')).text = val
        return el

    @classmethod
    def parse_xml(cls, el: XmlElement) -> 'Address':
        it = cls(el)
        it.content = el.find('Представление', converter=str)
        it.comment = el.find('Комментарий', converter=str, default='')
        fields = el.findall('АдресноеПоле', converter_xml=cls._parse_addr_field)
        it.fields = {k: v for k, v in fields}
        return it

    def compose_xml(self, tag='Адрес') -> XmlElement:
        el = XmlElement(tag)
        el.append(XmlElement('Представление')).text = self.content
        if len(self.comment):
            el.append(XmlElement('Комментарий')).text = self.comment

        for k, v in self.fields:
            el.append(self._compose_addr_field(k, v))

        return el


class Counterparty(ItemBase):
    def __init__(self, *args, **kwargs):
        super(Counterparty, self).__init__(*args, **kwargs)  # type: ignore
        self.uid = ''
        self.role = CounterpartyRole.BUYER
        self.full_name = ''
        self.name = ''
        self.first_name = ''
        self.last_name = ''
        self.address: Address or None = None

    @classmethod
    def parse_xml(cls, el: XmlElement) -> 'Counterparty':
        it = cls(el)
        it.uid = el.find('Ид', converter=str)
        it.role = el.find('Роль', converter=CounterpartyRole)
        it.full_name = el.find('ПолноеНаименование', converter=str)
        it.name = el.find('Имя', converter=str)
        it.last_name = el.find('Фамилия', converter=str)
        it.address = el.find('Адрес', converter=Address.parse_xml)
        return it

    def compose_xml(self, tag='Контрагент') -> XmlElement:
        el = XmlElement(tag)
        el.append(XmlElement('Ид')).text = self.uid
        el.append(XmlElement('Роль')).text = self.role.value
        el.append(XmlElement('ПолноеНаименование')).text = self.full_name
        el.append(XmlElement('Имя')).text = self.name
        el.append(XmlElement('Фамилия')).text = self.last_name
        el.append(self.address.compose_xml())
        return el

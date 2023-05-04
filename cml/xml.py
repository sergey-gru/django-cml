# -*- coding: utf-8 -
import typing
from io import BytesIO
from lxml import etree


class XmlImportException(Exception):
    pass


class XmlElement(object):
    """
    It's analogue of etree.Element().__class__.
    This class was created for fixing poor behavior of etree.Element() objects.
    """

    def __init__(self, el):
        if isinstance(el, str):
            self.el = etree.Element(el)  # el is str = tag name
        else:
            self.el = el

    #
    # Section: Emulating
    #

    @classmethod
    def parse(cls, source, parser=None, base_url=None):
        et = etree.parse(source, parser=parser, base_url=base_url)
        return cls(et.getroot())

    def compose(self, encoding='UTF-8', xml_declaration=True) -> bytes:
        # return etree.tostring(self.el, encoding=encoding, xml_declaration=xml_declaration)
        f = BytesIO()
        et = etree.ElementTree(self.el)
        et.write(f, encoding=encoding, xml_declaration=xml_declaration)
        return f.getvalue()

    @property
    def text(self):
        return self.el.text

    @text.setter
    def text(self, value):
        if not isinstance(value, str):
            raise TypeError('text must be a string')
        self.el.text = value

    @property
    def tag(self):
        return self.el.tag

    @tag.setter
    def tag(self, value):
        if not isinstance(value, str):
            raise TypeError(f'tag must be a string')
        self.el.tag = value

    def append(self, child: 'XmlElement') -> 'XmlElement':
        self.el.append(child.el)
        return child

    #
    # Section: Data extracting
    #

    def get_xpath(self):
        tree = self.el.getroottree()
        xpath = tree.getelementpath(self.el)
        ns_none = '{%s}' % self.el.nsmap.get(None, None)
        return xpath.replace(ns_none, '').replace('{}', '')

    def set_attr(self, key: str, value):
        self.el.set(key, value)

    def get_attr(self, attr_name: str, *,
                 converter: typing.Callable[[str], any] = None,
                 required=True,
                 default=None) -> any:
        """Get attribute of xml element.

        Args:
            attr_name (str): Name of attribute.
            converter: callback function for converting str value to any you want
            required: If attribute doesn't exist, raise `XmlImportException` or just return `default` value
            default: (any) default value for return
        """

        attr_val = self.el.get(attr_name)
        if attr_val is None:
            if not required or default is not None:
                return default
            xpath = self.get_xpath()
            raise XmlImportException(f'AttributeNotFound: xpath="{xpath}[{attr_name}]"')

        if converter is None or converter == str:
            return attr_val

        try:
            res = converter(attr_val)
        except Exception as e:
            xpath = self.get_xpath()
            raise XmlImportException(f'ConverterError: xpath="{xpath}[{attr_name}]" '
                                     f'type={converter.__name__} '
                                     f'raw_value="{attr_val}" msg: {str(e)}')
        return res

    def find(self, path: str, *,
             converter: typing.Callable[[str], any] = None,
             converter_xml: typing.Callable[['XmlElement'], any] = None,
             required=True,
             default: any = None) -> any:
        """Find element by `path`

        Try to convert text value if `converter` presents.
        Try to convert `XmlElement` value if `converter_xml` presents.

        Raise an XmlImportException error with description if required but not found.
        If default value not None, it supposed to be required=False

        Args:
            path: xpath for search
            converter: callback function for build result object by string `el.text`.
                       If text value is empty (None) converter hasn't called.
                       If you need `None`s use `converter_xml` parameter.
                       Works if `converter_xml` is None.
            converter_xml: callback function for build result object by `XmlElement`
            required: flag controlling if `XmlImportException` raises when attribute doesn't exist
                      or return `default`.
            default: (any) default value for return
        """

        _el_res = self.el.find(path, namespaces=self.el.nsmap)
        if _el_res is None:
            if not required or default is not None:
                return default

            xpath = self.get_xpath()
            raise XmlImportException(f'ElementNotFound: xpath="{xpath}/{path}"')

        if converter_xml is not None:
            return converter_xml(XmlElement(_el_res))

        if converter is not None:
            raw = _el_res.text

            if raw is None:
                return default

            try:
                res = converter(raw)
            except Exception as e:
                xpath = self.get_xpath()
                raise XmlImportException(f'ConverterError: xpath="{xpath}" '
                                         f'type={converter.__name__} '
                                         f'raw_value="{raw}" msg: {str(e)}')
            return res

        return XmlElement(_el_res)

    def findall(self, path: str, *,
                converter: typing.Callable[[str], any] = None,
                converter_xml: typing.Callable[['XmlElement'], any] = None,
                required=False) -> [any]:
        """
        Find a collection of elements by path.

        Args:
            path: xpath for search
            converter: callback function for build result object by string `el.text`.
                       If text value is empty (None) converter hasn't called.
                       If you need `None`s use `converter_xml` parameter.
                       Works if `converter_xml` is None.
            converter_xml: callback function for build result object by `XmlElement`
            required: flag controlling if `XmlImportException` raises when result collection is empty
                      or return empty collection.
        """

        _els = self.el.findall(path, namespaces=self.el.nsmap)

        _els_count = len(_els)
        if _els_count == 0:
            if not required:
                return _els
            xpath = self.get_xpath()
            raise XmlImportException(f'ElementNotFound: xpath="{xpath}/{path}"')

        if converter_xml is not None:
            arr_res = []
            for el in _els:
                arr_res.append(converter_xml(XmlElement(el)))
            return arr_res

        if converter is not None:
            arr_res = []
            for i in range(_els_count):
                raw = _els[i].text
                if raw is None:
                    continue

                try:
                    res = converter(raw)
                    arr_res.append(res)
                except Exception as e:
                    xpath = self.get_xpath()
                    raise XmlImportException(f'ConverterError: xpath="{xpath}[{i}]"'
                                             f'type={converter.__name__} '
                                             f'raw_value="{raw}" msg: {str(e)}')
            if required and len(arr_res) == 0:
                xpath = self.get_xpath()
                raise XmlImportException(f'ElementsAreNone: xpath="{xpath}/{path}"')

            return arr_res

        return [XmlElement(_el) for _el in _els]

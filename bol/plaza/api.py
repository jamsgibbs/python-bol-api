import time
import requests
import hmac
import hashlib
import base64
from datetime import datetime
import collections

from xml.etree import ElementTree

from .models import Orders, Payments, Shipments, ProcessStatus


__all__ = ['PlazaAPI']

# https://developers.bol.com/documentatie/plaza-api/developer-guide-plaza-api/appendix-a-transporters/
TRANSPORTER_CODES = {
    'DHLFORYOU',
    'UPS',
    'KIALA_BE',
    'KIALA_NL',
    'TNT',
    'TNT_EXTRA',
    'TNT_BRIEF',
    'SLV',
    'DYL',
    'DPD_NL',
    'DPD_BE',
    'BPOST_BE',
    'BPOST_BRIEF',
    'BRIEFPOST',
    'GLS',
    'FEDEX_NL',
    'FEDEX_BE',
    'OTHER',
    'DHL',
}


class MethodGroup(object):

    def __init__(self, api, group):
        self.api = api
        self.group = group

    def request(self, method, name='', payload=None):
        uri = '/services/rest/{group}/{version}/{name}'.format(
            group=self.group,
            version=self.api.version,
            name=name)
        xml = self.api.request(method, uri, payload)
        return xml

    def create_request_xml(self, root, **kwargs):
        elements = self._create_request_xml_elements(1, **kwargs)
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<{root} xmlns="https://plazaapi.bol.com/services/xsd/v2/plazaapi.xsd">
{elements}
</{root}>
""".format(root=root, elements=elements)
        return xml

    def _create_request_xml_elements(self, indent, **kwargs):
        # sort to make output deterministic
        kwargs = collections.OrderedDict(sorted(kwargs.items()))
        xml = ''
        for tag, value in kwargs.items():
            if value is not None:
                prefix = ' ' * 4 * indent
                if isinstance(value, dict):
                    text = '\n{}\n{}'.format(
                        self._create_request_xml_elements(
                            indent + 1, **value),
                        prefix)
                elif isinstance(value, datetime):
                    text = value.isoformat()
                else:
                    text = str(value)
                # TODO: Escape! For now this will do I am only dealing
                # with track & trace codes and simplistic IDs...
                if xml:
                    xml += '\n'
                xml += prefix
                xml += "<{tag}>{text}</{tag}>".format(
                    tag=tag,
                    text=text
                )
        return xml


class OrderMethods(MethodGroup):

    def __init__(self, api):
        super(OrderMethods, self).__init__(api, 'orders')

    def list(self):
        xml = self.request('GET')
        return Orders.parse(self.api, xml)


class PaymentMethods(MethodGroup):

    def __init__(self, api):
        super(PaymentMethods, self).__init__(api, 'payments')

    def list(self, year, month):
        xml = self.request('GET', '%d%02d' % (year, month))
        return Payments.parse(self.api, xml)


class ShipmentMethods(MethodGroup):

    def __init__(self, api):
        super(ShipmentMethods, self).__init__(api, 'shipments')

    def list(self, page=1):
        # TODO: use page
        xml = self.request('GET')
        return Shipments.parse(self.api, xml)

    def create(self, order_item_id, date_time, expected_delivery_date,
               shipment_reference=None, transporter_code=None,
               track_and_trace=None):
        if transporter_code:
            assert transporter_code in TRANSPORTER_CODES
        xml = self.create_request_xml(
            'ShipmentRequest',
            OrderItemId=order_item_id,
            DateTime=date_time,
            ShipmentReference=shipment_reference,
            ExpectedDeliveryDate=expected_delivery_date,
            Transport={
                'TransporterCode': transporter_code,
                'TrackAndTrace': track_and_trace
            })
        response = self.request('POST', payload=xml)
        return ProcessStatus.parse(self.api, response)


class PlazaAPI(object):

    def __init__(self, public_key, private_key, test=False, timeout=None):
        self.public_key = public_key
        self.private_key = private_key
        self.url = 'https://%splazaapi.bol.com' % ('test-' if test else '')
        self.version = 'v2'
        self.timeout = timeout
        self.orders = OrderMethods(self)
        self.payments = PaymentMethods(self)
        self.shipments = ShipmentMethods(self)

    def request(self, method, uri, payload=None):
        content_type = 'application/xml; charset=UTF-8'
        date = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())
        msg = """{method}

{content_type}
{date}
x-bol-date:{date}
{uri}""".format(content_type=content_type,
                date=date,
                method=method,
                uri=uri)
        h = hmac.new(
            self.private_key.encode('utf-8'),
            msg.encode('utf-8'), hashlib.sha256)
        b64 = base64.b64encode(h.digest())

        signature = self.public_key.encode('utf-8') + b':' + b64

        headers = {'Content-Type': content_type,
                   'X-BOL-Date': date,
                   'X-BOL-Authorization': signature}
        if method == 'GET':
            resp = requests.get(
                self.url + uri,
                headers=headers,
                timeout=self.timeout)
        elif method == 'POST':
            resp = requests.post(
                self.url + uri,
                headers=headers,
                data=payload,
                timeout=self.timeout)
        else:
            raise ValueError
        resp.raise_for_status()
        tree = ElementTree.fromstring(resp.content)
        return tree
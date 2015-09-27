# -*- coding: utf-8 -*-
from unittest import TestCase
from datetime import datetime

import six

from simplemodels.exceptions import ValidationError, ValidationRequiredError, \
    ValidationDefaultError, ImmutableDocumentError
from simplemodels.fields import SimpleField, IntegerField, CharField, \
    DocumentField, FloatField
from simplemodels.models import AttributeDict, Document, ImmutableDocument


### Test model classes ###


class MailboxItem(Document):
    subject = SimpleField(default='')
    body = SimpleField(default='')
    type = SimpleField(choices=["SUGGESTION", "MAIL"],
                       max_length=10,
                       default='MAIL')
    # received_at = SimpleField(default=timezone.now)
    received_at = SimpleField(default='')
    is_read = SimpleField(default=False)

    def __init__(self, **kwargs):
        super(MailboxItem, self).__init__(**kwargs)
        if 'received_at' not in kwargs and not self.received_at:
            self.received_at = datetime.now()

    def __repr__(self):
        return six.u("<{}({}): {}>".format(
            self.__class__.__name__, self.type, self.subject))

    def __unicode__(self):
        return six.u("<{}({}): {}>".format(
            self.__class__.__name__, self.type, self.subject))


class Address(Document):
    street = SimpleField()


class Person(Document):
    name = SimpleField(required=True)
    address = SimpleField(validatos=[Address])


#### End of test model classes ###


class AttributeDictTest(TestCase):
    def test_dict(self):

        ad = AttributeDict()
        ad._id = 1
        self.assertEqual(ad['_id'], 1)
        self.assertEqual(ad._id, 1)
        self.assertEqual(getattr(ad, '_id'), 1)

    def test_system_methods(self):
        from copy import deepcopy

        attr_d = AttributeDict(a=1)
        ad_copy = deepcopy(attr_d)
        self.assertTrue(ad_copy)


class DocumentTest(TestCase):
    def test_document(self):
        class Money(Document):

            """Nested"""

            xsi_type = SimpleField('Money')
            microAmount = SimpleField()

        class BidEmbedded(Document):
            xsi_type = SimpleField('BidEmbedded')
            # xsi_type = fields.StringField(default='BidEmbedded')
            contentBid = SimpleField(default=Money())

        bid = BidEmbedded()

        self.assertIsInstance(bid, dict)
        self.assertIsInstance(bid._fields, dict)
        self.assertIsInstance(bid._required_fields, tuple)
        self.assertEqual(
            sorted(bid._fields), sorted(('xsi_type', 'contentBid'))
        )

        self.assertEqual(
            bid,
            {
                'xsi_type': 'BidEmbedded',
                'contentBid': {'xsi_type': 'Money', 'microAmount': None}
            }
        )

    def test_simple_field_default(self):
        class A(Document):
            f = SimpleField(default=10)
            l = SimpleField(default=list)

        a = A()
        self.assertEqual(a.f, 10)
        self.assertEqual(a.l, [])

    def test_simple_field_required(self):
        class TestDictDocument(Document):
            xsi_type = SimpleField(required=True)

        self.assertRaises(ValidationRequiredError, TestDictDocument)
        self.assertRaises(
            ValidationRequiredError, TestDictDocument, xsi_type='')
        self.assertRaises(
            ValidationRequiredError, TestDictDocument, xsi_type=None)
        self.assertTrue(TestDictDocument(xsi_type='html'))

    def test_default_values_with_several_instances(self):
        td = MailboxItem()
        td_2 = MailboxItem(is_read=True)

        self.assertFalse(td.is_read)
        self.assertTrue(td_2.is_read)

        td.is_read = True
        td_2.is_read = False
        self.assertTrue(td.is_read)
        self.assertFalse(td_2.is_read)

    def test_getting_classname(self):
        self.assertEqual(Address.__name__, 'Address')

    def test_property_getter(self):
        class DocumentWithProperty(Document):
            a = SimpleField()
            b = SimpleField()

            @property
            def c(self):
                return str(self.a) + str(self.b)

        document = DocumentWithProperty(a=1, b=2)

        self.assertEqual(document.c, '12')

    def test_fields_container(self):
        """ get_instance method should guarantee that object contains exactly
        same fields as described


        """
        class TestModel(Document):
            a = SimpleField()
            b = SimpleField()

        source_data = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
        obj = TestModel(**source_data)
        self.assertEqual(len(obj), len(TestModel._fields))
        for field_name in obj.keys():
            self.assertIn(field_name, TestModel._fields)

    def test_field_type(self):
        class PostAddress(Document):
            street = SimpleField(validators=[str])

        class User(Document):
            id = SimpleField(validators=[int])
            name = SimpleField(required=True, default='TestName')
            address = DocumentField(model=PostAddress)

        a = User(id='1', name='Maks', address=PostAddress(street=999))
        self.assertIsInstance(a, User)
        self.assertIsInstance(a.address, PostAddress)
        self.assertEqual(a.id, 1)
        self.assertEqual(a.address.street, '999')

        a = User(
            id='1', name='Maks',
            address={'street': 999, 'city': 'Saint-Petersburg'}
        )
        self.assertIsInstance(a, User)
        self.assertIsInstance(a.address, PostAddress)
        self.assertEqual(a.id, 1)
        self.assertEqual(a.address.street, '999')
        # city is not declared as an Address field
        self.assertRaises(KeyError, getattr, a.address, 'city')

        # Expect a ValidationError: wrong 'address' format is passed
        self.assertRaises(
            ValidationError, User,
            id='1', name='Maks', address=[('street', 999), ]
        )

    def test_model_with_validator(self):
        class Timestamp(Document):
            hour = SimpleField(validators=[int])
            minute = SimpleField(validators=[int])

        class Moment(Document):
            start_date = SimpleField(
                validators=[lambda value: datetime.strptime(
                    value, '%Y-%m-%dT%H:%M:%SZ')])
            count = SimpleField(validators=[int])
            timestamp = DocumentField(model=Timestamp)
            ts = DocumentField(model=Timestamp)

        moment = Moment(
            start_date='2009-04-01T23:51:23Z',
            count='1',
            timestamp=dict(hour=10, minute=59),
            ts=Timestamp(hour=10, minute=59)
        )
        self.assertIsInstance(moment.start_date, datetime)
        self.assertIsInstance(moment.count, int)
        self.assertIsInstance(moment.timestamp, Timestamp)
        self.assertIsInstance(moment.ts, Timestamp)

        self.assertRaises(ValidationError, Moment, count='a')

    def test_model_verbose_name(self):
        class RateModel(Document):
            InterestRate = FloatField(name='Interest Rate')

        data = {"Interest Rate": "1.01"}
        my_model = RateModel(**data)
        self.assertEqual(len(my_model), 1)
        self.assertEqual(my_model.InterestRate, 1.01)

        my_model = RateModel(**data)
        self.assertEqual(len(my_model), 1)
        self.assertEqual(my_model.InterestRate, 1.01)
        self.assertEqual(my_model['Interest Rate'], 1.01)

    def test_model_verbose_name_required(self):
        class RateModel(Document):
            InterestRate = FloatField(name='Interest Rate', required=True)
        data = {"Interest Rate": "1.01"}
        my_model = RateModel(**data)
        self.assertEqual(my_model['Interest Rate'], 1.01)
        self.assertRaises(ValidationRequiredError, RateModel)

    def test_allow_extra_fields_attribute(self):
        """ Create document with ALLOW_EXTRA_FIELDS = True and expect that all
         extra fields will be stored, otherwise will be filtered

        """

        class LogMessage(Document):
            ALLOW_EXTRA_FIELDS = True

            timestamp = CharField()
            app_name = CharField()
            text = CharField(max_length=500)

        msg = LogMessage(
            timestamp=datetime.now(),
            app_name='Logger',
            text='test log message',
            level='DEBUG'  # extra field isn't described in the document
        )
        self.assertEqual(msg.level, 'DEBUG')

    def test_choices_option(self):
        class LogMessage(Document):
            level = CharField(choices=['INFO', 'DEBUG', 'ERROR'])
            text = CharField(max_length=500)

        with self.assertRaises(ValueError):
            # Put wrong log level
            message = LogMessage(level='FATAL', text='Test log message')
            self.assertIsNone(message)

        message = LogMessage(level='DEBUG', text='Test log message')
        self.assertTrue(message)

        with self.assertRaises(ValueError) as err:
            class Message(Document):
                tag = CharField(choices='INFO, DEBUG')
            self.assertIn('Wrong choices data type', str(err))


class ValidationTest(TestCase):
    def test_raise_validation_error(self):
        street = 'Pagoda street'
        self.assertRaises(ValidationError, Person, address=street)

    def test_validation_with_default_values(self):
        # Expect an error on class initialization step
        with self.assertRaises(ValidationDefaultError):
            class A(Document):
                id = IntegerField(default='a')

        # Accepted case: string to int will be forced
        class B(Document):
            id = IntegerField(default='1')

        b = B()
        self.assertEqual(b.id, 1)

        # Unicode case
        # with self.assertRaises(ValidationDefaultError):
        #     class C(Document):
        #         name = CharField(default=u'\x80')


class ImmutableDocumentTest(TestCase):
    def test_immutable_document(self):
        class User(ImmutableDocument):
            id = IntegerField(default=1)
            name = CharField(default='John')

        user = User()
        self.assertEqual(user.id, 1)
        with self.assertRaises(ImmutableDocumentError):
            user.name = 'Jorge'

        with self.assertRaises(ImmutableDocumentError):
            setattr(user, 'name', 'Jorge')

        with self.assertRaises(ImmutableDocumentError):
            user['name'] = 'Jorge'

    def test_immutable_nested_document(self):
        class MetaInfo(ImmutableDocument):
            id = CharField(default='unknown')
            login = CharField(default='guest')

        class User(Document):
            name = CharField()
            meta = DocumentField(model=MetaInfo)

        user = User()

        # Check init params
        self.assertEqual(user.meta.login, 'guest')

        # Try to set immutable nested doc field, expect error
        with self.assertRaises(ImmutableDocumentError):
            user.meta.login = 'admin'

        # Try to set mutable top-level name field
        user.name = 'Jorge'
        self.assertEqual(user.name, 'Jorge')
# -*- coding: utf-8 -*-

import random
import datetime

# Third Party Stuff
import requests
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.core.cache import cache
from django.conf import settings
from django.utils.module_loading import import_string


class BaseBackend:
    SECURITY_CODE_VERIFIED = 0
    SECURITY_CODE_INVALID = 1
    SECURITY_CODE_NOTFOUND = 2
    KEY_PREFIX = 'phone_verification_'
    KEY_NOTFOUND = 'not_found'
    DEFAULT_TOKEN_LENGTH = 6
    DEFAULT_TIME_OUT = 180  # seconds

    @classmethod
    def generate_security_code(cls):
        """
        Returns a unique random `security_code` for given `TOKEN_LENGTH` in the settings.
        """
        token_length = getattr(
            settings, 'PHONE_VERIFICATION_TOKEN_LENGTH', cls.DEFAULT_TOKEN_LENGTH)
        return get_random_string(token_length, allowed_chars="0123456789")

    @classmethod
    def cache_key(cls, number):
        return "{}{}".format(cls.KEY_PREFIX, number)

    @classmethod
    def get_key_expiration(cls, number):
        key = cls.cache_key(number)
        expiration_unix_timestamp = cache._expire_info.get(
            cache.make_key(key), None)
        if expiration_unix_timestamp is None:
            return 0
        expiration_date_time = datetime.datetime.fromtimestamp(
            expiration_unix_timestamp)
        now = datetime.datetime.now()
        if expiration_date_time < now:
            return 0
        delta = expiration_date_time - now

        return delta.seconds

    @classmethod
    def send_verification_code(cls, number):
        code, created = cls.get_or_create_security_code(number)
        if created:
            pass
            # url = cls.get_url(number, code)
            # response = requests.request("GET", url)
            # data = response.json()
        raise NotImplementedError()

    @classmethod
    def get_or_create_security_code(cls, number):
        """
        Creates a temporary `security_code` if the number key is not present in the cache.
        Else retrive the security_code from cache.
        `security_code` is the code that user would enter to verify their phone_number.
        :param number: Phone number of recipient
        :return security_code: string of sha security_code
        """
        key = cls.cache_key(number)
        security_code = cache.get(key, cls.KEY_NOTFOUND)
        created = False
        if security_code == cls.KEY_NOTFOUND:
            timeout = getattr(
                settings, 'PHONE_VERIFICATION_TIME_OUT', cls.DEFAULT_TIME_OUT)
            security_code = cls.generate_security_code()
            cache.set(key, security_code, timeout=timeout)
            created = True

        return security_code, created

    @classmethod
    def validate_security_code(cls, number, security_code):
        """
        A utility method to verify if the `security_code` entered is valid for
        a given `number` along with the `session_token` used.

        :param security_code: Security code entered for verification
        :param number: Phone number to be verified

        :return status: Status for the stored_verification object.
        Can be one of the following:
            - `BaseBackend.SECURITY_CODE_INVALID`
            - `BaseBackend.SECURITY_CODE_NOTFOUND`
            - `BaseBackend.SECURITY_CODE_VERIFIED`
        """
        key = cls.cache_key(number)
        code = cache.get(key, cls.KEY_NOTFOUND)
        if code == cls.KEY_NOTFOUND:
            return cls.SECURITY_CODE_NOTFOUND

        if code == security_code:
            return cls.SECURITY_CODE_VERIFIED

        return cls.SECURITY_CODE_INVALID


class test(BaseBackend):
    @classmethod
    def send_verification_code(cls, number):
        return 0

    @classmethod
    def validate_security_code(cls, number, security_code):
        if security_code == 'verify' or security_code == '12345':
            return cls.SECURITY_CODE_VERIFIED
        if security_code == 'timeout':
            return cls.SECURITY_CODE_NOTFOUND
        return cls.SECURITY_CODE_INVALID


class fast2smsBackend(BaseBackend):

    base_url = 'https://www.fast2sms.com/dev/bulk?'
    url_template = "&".join([
        'authorization={api_key}',
        'sender_id={sender_id}',
        'language=english',
        'route=qt',
        'numbers={number}',
        'message={template_id}',
        'variables={variables}',
        'variables_values={values}'
    ])

    @classmethod
    def get_url(cls, number, otp):
        api_key = getattr(settings, 'FAST2SMS_API_KEY', '')
        sender_id = getattr(settings, 'FAST2SMS_SENDER_ID', '')
        template_id = getattr(settings, 'FAST2SMS_TEMPLATE_ID', '')
        variables = getattr(settings, 'FAST2SMS_VARIABLES', '')

        return cls.base_url+cls.url_template.format(
            api_key=api_key,
            sender_id=sender_id,
            template_id=template_id,
            variables=variables,
            number=str(number),
            values=str(otp))

    @ classmethod
    def send_verification_code(cls, number):
        code, created = cls.get_or_create_security_code(number)
        if created:
            url = cls.get_url(number, code)
            response = requests.request("GET", url)
            data = response.json()


def get_backend():
    backend_string = getattr(settings, 'PHONE_VERIFICATION_BACKEND', None)
    if not backend_string:
        return fast2smsBackend
    return import_string(backend_string)

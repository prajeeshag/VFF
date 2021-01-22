
from .base import BaseBackend
from django.conf import settings

import requests


class Backend(BaseBackend):

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

    def get_url(self, number, otp):
        api_key = settings.FAST2SMS_API_KEY
        sender_id = settings.FAST2SMS_SENDER_ID
        template_id = settings.FAST2SMS_TEMPLATE_ID
        variables = settings.FAST2SMS_VARIABLES

        return self.base_url+self.url_template.format(
            api_key=api_key,
            sender_id=sender_id,
            template_id=template_id,
            variables=variables,
            number=str(number),
            values=str(otp))

    def send_otp(self, number):
        code, token = self.create_security_code_and_session_token(number)
        url = self.get_url(number, code)
        response = requests.request("GET", url)
        data = response.json()

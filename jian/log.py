# -*- encoding:utf-8 -*-
"""
@ Created by Seven on  2019/01/19 <https://7yue.in>
"""

from functools import wraps
import re
from flask import Response, request
from flask_jwt_extended import get_current_user
from .core import find_info_by_ep, Log

REG_XP = r'[{](.*?)[}]'
OBJECTS = ['user', 'response', 'request']


class Logger(object):
    # message template
    template = None

    def __init__(self, template=None):
        if template:
            self.template: str = template
        elif self.template is None:
            raise Exception('template must not be None!')
        self.message = ''
        self.response = None
        self.user = None

    def __call__(self, func):
        @wraps(func)
        def wrap(*args, **kwargs):
            response: Response = func(*args, **kwargs)
            self.response = response
            self.user = get_current_user()
            self.message = self._parse_template()
            self.write_log()
            return response

        return wrap

    def write_log(self):
        info = find_info_by_ep(request.endpoint)
        authority = info.auth if info is not None else ''
        status_code = getattr(self.response, 'status_code', None)
        if status_code is None:
            status_code = getattr(self.response, 'code', None)
        if status_code is None:
            status_code = 0
        Log.create_log(message=self.message, user_id=self.user.id, user_name=self.user.nickname,
                       status_code=status_code, method=request.method,
                       path=request.path, authority=authority, commit=True)

    # 解析自定义模板
    def _parse_template(self):
        message = self.template
        total = re.findall(REG_XP, message)
        for it in total:
            assert '.' in it, '%s中必须包含 . ,且为一个' % it
            i = it.rindex('.')
            obj = it[:i]
            assert obj in OBJECTS, '%s只能为user,response,request中的一个' % obj
            prop = it[i + 1:]
            if obj == 'user':
                item = getattr(self.user, prop, '')
            elif obj == 'response':
                item = getattr(self.response, prop, '')
            else:
                item = getattr(request, prop, '')
            message = message.replace('{%s}' % it, str(item))
        return message

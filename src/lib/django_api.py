#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import django


class DjangoApi:
    def __init__(self):
        from cannon_manage import env
        self.setting_file = 'cannon.settings_%s' % env

    def os_environ_update(self):
        os.environ.update({"DJANGO_SETTINGS_MODULE": self.setting_file})
        django.setup()
        return True


if __name__ == "__main__":
    DjangoApi().os_environ_update()

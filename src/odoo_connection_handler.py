#!/usr/bin/env python3

import logging
from odoo_ule_handler.odoo_handler import OdooHandler

logger = logging.getLogger(__name__)


class OdooConnectionHandler(object):
    def __init__(self, url="", db="", username="", password="", self_signed=False):
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.self_signed = self_signed
        self.connection = None

    def connect(self, url=None, db=None, username=None, password=None, self_signed=False):
        url_ = url if url else self.url
        db_ = db if db else self.db
        username_ = username if username else self.username
        password_ = password if password else self.password
        self_signed_ = self_signed if self_signed else self.self_signed

        self.connection = OdooHandler(url_, self_signed_)

        try:
            self.connection.connect(db_, username_, password_)
        except:
            raise

        return self.connection


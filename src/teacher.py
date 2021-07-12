#!/usr/bin/env python3

import logging

logger = logging.getLogger(__name__)


class Teacher(object):
    def __init__(self, teacher_id, user_id="", name="", identification_code="", rfid_code=''):
        self.teacher_id = teacher_id
        self.user_id = user_id
        self.name = name
        self.identification_code = identification_code
        self.rfid_code = rfid_code

    def get_barcode(self):
        return self.identification_code

    def to_array(self):
        return [self.name, self.identification_code, self.rfid_code]

    def export_to_csv(self):
        barcode = self.get_barcode()
        csv_line = "{},{},{},{}".format(self.name, self.identification_code, barcode, self.rfid_code)
        return csv_line
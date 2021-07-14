#!/usr/bin/env python3

import logging

logger = logging.getLogger(__name__)


class Student(object):

    BARCODE_LENGTH = 9 # 8 digits + 1 letter

    def __init__(self, student_id, user_id="", name="", identification_code="", student_code="", courses=[], rfid_code=''):
        self.student_id = student_id
        self.user_id = user_id
        self.name = name
        self.identification_code = identification_code
        self.student_code = str(student_code)
        self.courses = courses
        self.rfid_code = rfid_code

    def get_barcode(self):
        if self.student_code:
            previous_zeros = self.BARCODE_LENGTH - len(self.student_code)
            prefix = "0" * previous_zeros
            return prefix + self.student_code
        else:
            return self.identification_code

    def is_in_course(self, course_name):
        return course_name in self.courses

    def to_array(self):
        return [self.name, self.identification_code, self.student_code, self.rfid_code]

    def export_to_csv(self):
        barcode = self.get_barcode()
        csv_line = "{},{},{},{},{}".format(self.name, self.identification_code, self.student_code, barcode, self.rfid_code)
        return csv_line
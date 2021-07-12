#!/usr/bin/env python3

import collections
import logging
from teacher import Teacher

logger = logging.getLogger(__name__)


def from_odoo_list_to_dict(element_list):
    if not isinstance(element_list, list):
        return {}
    return { element.get("id"): element for element in element_list}


class TeachersHandler(object):

    csv_headline = "Nombre,DNI,Barcode,RFID"

    def __init__(self, odoo_connection):
        self.odoo_connection = odoo_connection
        self.all_teachers = collections.OrderedDict()
        self.selected_teachers = collections.OrderedDict()
        self.users = None
        self.__refresh_info()

    def __refresh_info(self):
        self.users = from_odoo_list_to_dict(self.odoo_connection.get_all_users())

    def __get_teacher_user(self, odoo_teacher):
        try:
            teacher_user_id = odoo_teacher.get("user_id")[0]
            return self.users.get(teacher_user_id)
        except TypeError:
            return None

    def __search_local_teacher(self, identification_code):
        for id, teacher in self.all_teachers.items():
            if teacher.identification_code == identification_code:
                return id

    def write_rfid_codes(self, info):
        for teacher_id, new_rfid in info.items():
            teacher_user_id = self.all_teachers[teacher_id].user_id
            self.odoo_connection.write_user_rfid(teacher_user_id, new_rfid)

    def refresh_teachers(self):
        self.all_teachers.clear()
        self.selected_teachers.clear()
        self.__refresh_info()
        odoo_teachers = self.odoo_connection.get_all_teachers()
        for odoo_teacher in odoo_teachers:
            teacher_id = odoo_teacher.get("id")
            teacher_name = odoo_teacher.get("display_name")
            teacher_identification_code = odoo_teacher.get("identification_code") or ""
            teacher_user = self.__get_teacher_user(odoo_teacher)
            if not teacher_user:
                logger.error("User for teacher '{}' does not exist".format(teacher_name))
                continue
            user_id = teacher_user.get("id")
            teacher_rfid = teacher_user.get("kardex_remstar_xp_rfid") or ""
            teacher = Teacher(teacher_id, user_id, teacher_name, teacher_identification_code, teacher_rfid)
            self.all_teachers[teacher_id] = teacher

        self.selected_teachers = self.all_teachers

    def filter(self, with_rfid=True):
        if with_rfid:
            self.selected_teachers = self.all_teachers
        else:
            self.selected_teachers = { id: teacher for id, teacher in self.all_teachers.items() if not teacher.rfid_code}

    def build_list(self):
        return [teacher.to_array() for teacher in self.selected_teachers.values()]

    def export_to_csv(self):
        csv_content = ""
        csv_content = self.csv_headline + "\n"
        for teacher in self.selected_teachers.values():
            new_line = teacher.export_to_csv()
            csv_content = csv_content + new_line + "\n"

        with open('teacher.csv', 'w') as f:
            f.write(csv_content)

    def import_csv(self, file_path):
        if not file_path:
            raise AttributeError("No file selected")

        new_rfid_codes = {}
        with open(file_path, 'r') as f:
            lines = f.readlines()
            if len(lines) <= 1:
                raise AttributeError("No valid data")

            headline = lines[0].strip()
            if headline != self.csv_headline:
                raise AttributeError("Invalid headline format")

            teacher_lines = lines[1:]
            for teacher_line in teacher_lines:
                teacher_line_list = teacher_line.strip().split(",")
                identification_code = teacher_line_list[1]
                new_rfid_code = teacher_line_list[3]
                teacher_id = self.__search_local_teacher(identification_code)
                if not teacher_id:
                    logger.error(f"Teacher with identification code '{identification_code}' does not exist")
                    continue
                if self.all_teachers.get(teacher_id).rfid_code:
                    logger.warn(f"Teacher '{teacher_id}' already has an RFID code assigned")
                    continue

                new_rfid_codes[teacher_id] = new_rfid_code
                
        return new_rfid_codes
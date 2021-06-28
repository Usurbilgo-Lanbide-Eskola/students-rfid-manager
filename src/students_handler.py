#!/usr/bin/env python3

import collections
import logging
from student import Student

logger = logging.getLogger(__name__)


def from_odoo_list_to_dict(element_list):
    if not isinstance(element_list, list):
        return {}
    return { element.get("id"): element for element in element_list}


class StudentsHandler(object):

    csv_headline = "Nombre,DNI,Código alumno,Barcode,RFID"

    def __init__(self, odoo_connection):
        self.odoo_connection = odoo_connection
        self.all_students = collections.OrderedDict()
        self.selected_students = collections.OrderedDict()
        self.courses = None
        self.enrollments = None
        self.users = None
        self.__refresh_info()

    def __refresh_info(self):
        self.courses = from_odoo_list_to_dict(self.odoo_connection.get_all_courses())
        self.enrollments = from_odoo_list_to_dict(self.odoo_connection.get_all_enrollments())
        self.users = from_odoo_list_to_dict(self.odoo_connection.get_all_users())

    def __get_student_courses(self, odoo_student):
        course_detail_ids = odoo_student.get("course_detail_ids")
        student_courses = set()
        for course_detail_id in course_detail_ids:
            course_name = self.enrollments.get(course_detail_id).get("course_id")[1]
            student_courses.add(course_name)
        return student_courses

    def __get_student_user(self, odoo_student):
        student_user_id = odoo_student.get("user_id")[0]
        return self.users.get(student_user_id)

    def __search_local_student(self, identification_code): # Should be replaced by student code
        for id, student in self.all_students.items():
            if student.identification_code == identification_code:
                return id

    def write_rfid_codes(self, info):
        for student_id, new_rfid in info.items():
            student_user_id = self.all_students[student_id].user_id
            self.odoo_connection.write_user_rfid(student_user_id, new_rfid)

    def get_courses_names(self):
        return [course.get("display_name") for course in self.courses.values()]

    def refresh_students(self):
        self.all_students.clear()
        self.selected_students.clear()
        self.__refresh_info()
        odoo_students = self.odoo_connection.get_all_students()
        for odoo_student in odoo_students:
            student_id = odoo_student.get("id")
            student_name = odoo_student.get("display_name")
            student_identification_code = odoo_student.get("identification_code") or ""
            student_gr_no = odoo_student.get("gr_no") or ""
            student_courses = self.__get_student_courses(odoo_student)
            student_user = self.__get_student_user(odoo_student)
            if not student_user:
                logger.error("User for student '{}' does not exist".format(student_name))
                continue
            user_id = student_user.get("id")
            student_rfid = student_user.get("kardex_remstar_xp_rfid") or ""
            student = Student(student_id, user_id, student_name, student_identification_code, student_gr_no, student_courses, student_rfid)
            self.all_students[student_id] = student

        self.selected_students = self.all_students

    def filter(self, course_name="", with_rfid=True):
        course_filtered_students = { id: student for id, student in self.all_students.items() if student.is_in_course(course_name)} if course_name else self.all_students
        if with_rfid:
            self.selected_students = course_filtered_students
        else:
            self.selected_students = { id: student for id, student in course_filtered_students.items() if not student.rfid_code}

    def build_list(self):
        return [student.to_array() for student in self.selected_students.values()]

    def export_to_csv(self):
        csv_content = ""
        csv_content = self.csv_headline + "\n"
        for student in self.selected_students.values():
            new_line = student.export_to_csv()
            csv_content = csv_content + new_line + "\n"

        with open('students.csv', 'w') as f:
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

            student_lines = lines[1:]
            for student_line in student_lines:
                student_line_list = student_line.strip().split(",")
                identification_code = student_line_list[1] # Should be replaced by student code
                new_rfid_code = student_line_list[4]
                student_id = self.__search_local_student(identification_code)
                if not student_id:
                    logger.error(f"Student with student code '{identification_code}' does not exist") # Should be replaced by student code
                    continue
                if self.all_students.get(student_id).rfid_code:
                    logger.warn(f"Student '{student_id}'' already has an RFID code assigned")
                    continue

                new_rfid_codes[student_id] = new_rfid_code
                
        return new_rfid_codes
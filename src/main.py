#!/usr/bin/env python3

import logging
import socket
from odoo_connection_handler import OdooConnectionHandler
import PySimpleGUI as sg
from students_handler import StudentsHandler
from teachers_handler import TeachersHandler
import sys
import xmlrpc

logging.basicConfig(format='%(asctime)s %(levelname)-6s - %(name)-16s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

ODOO_DEFAULT_URL = "https://odoo-tailerra.lhusurbil.eus"
ODOO_DEFAULT_DB = "Taller40_pruebas"

students_headings = ["Name", "DNI", "Student Code", "RFID"]
students_data = [["" for i in range(len(students_headings))]]
default_course_filter = "All"
course_names = [default_course_filter]

teachers_headings = ["Name", "DNI", "RFID"]
teachers_data = [["" for i in range(len(teachers_headings))]]

login_layout = [[sg.Text("Odoo server"), sg.InputText(ODOO_DEFAULT_URL)],
                 [sg.Text("Database"), sg.InputText(ODOO_DEFAULT_DB), sg.Checkbox('Self signed certificate', default=True)],
                 [sg.Text("Username"), sg.InputText()],
                 [sg.Text("Password"), sg.InputText(password_char="*")],
                 [sg.Button("Exit"), sg.Button("Login")],
                 [sg.Text("", key="error_message", visible=False, background_color="red", text_color="white", size=(70,1))]]

students_tab_layout = [[sg.Button("Refresh", key="refresh_students"), sg.Button("Export", key="export_students"), sg.Button("Import", key="import_students"), sg.Checkbox('Show users with RFID', key="students_with_rfid", default=True, enable_events=True)],
                        [sg.Text("Course filter"), sg.Combo(course_names, key='course_filter', default_value="All", size=(55,1), enable_events=True)],
                        [sg.Table(values=students_data, headings=students_headings, enable_events=True,  col_widths=[20,15,15,15,30],
                        num_rows=30, justification='center', auto_size_columns=False, key='students')]]
teachers_tab_layout = [[sg.Button("Refresh", key="refresh_teachers"), sg.Button("Export", key="export_teachers"), sg.Button("Import", key="import_teachers"), sg.Checkbox('Show users with RFID', key="teachers_with_rfid", default=True, enable_events=True)],
                        [sg.Table(values=teachers_data, headings=teachers_headings, enable_events=True,  col_widths=[20,15,15,15,30],
                        num_rows=30, justification='center', auto_size_columns=False, key='teachers')]]

main_layout = [[sg.TabGroup([[sg.Tab("Students", students_tab_layout), sg.Tab('Teachers', teachers_tab_layout)]])]]

is_logged = False
are_students_loaded = False
are_teachers_loaded = False


if __name__ == "__main__":
    logger.info("Starting RFID Cards Manager")

    sg.theme('SystemDefault')
    window = sg.Window('ULE RFID Manager - Login', login_layout)

    while not is_logged:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            sys.exit()
        elif event in (sg.Button, "Exit"):
            sys.exit()
        elif event in (sg.Button, "Login"):
            url, db, self_signed, username, password = values.values()

            odoo_connection_handler = OdooConnectionHandler()
            try:
                odoo_connection = odoo_connection_handler.connect(url, db, username, password, self_signed)
                is_logged = True
            except AttributeError:
                window["error_message"].update("All login parameters must be set", visible=True)
            except ConnectionRefusedError:
                window["error_message"].update(f"Connection with the user '{username}' could not be authenticated", visible=True)
            except ConnectionError:
                window["error_message"].update(f"Connection to the database '{db}' could not be stablished", visible=True)
            except socket.gaierror:
                window["error_message"].update(f"Connection to the server '{url}' could not be stablished", visible=True)
            except xmlrpc.client.Fault:
                window["error_message"].update(f"Connection to the database '{db}' could not be stablished", visible=True)
    
    window.close()
    window = sg.Window('ULE RFID Manager', main_layout)

    students_handler = StudentsHandler(odoo_connection)
    teachers_handler = TeachersHandler(odoo_connection)

    course_names = course_names + students_handler.get_courses_names()
  
    while(True):
        event, values = window.read(100, timeout_key='timeout')
        if not are_students_loaded or not are_teachers_loaded:
            students_handler.refresh_students()
            window['course_filter'].update(values=course_names)
            window['students'].update(values=students_handler.build_list())
            window['course_filter'].update(set_to_index=0)
            are_students_loaded = True
            teachers_handler.refresh_teachers()
            window['teachers'].update(values=teachers_handler.build_list())
            are_teachers_loaded = True
        if event == 'timeout':
            continue
        elif event == sg.WIN_CLOSED:
            sys.exit()
        elif event == "course_filter" or event == "students_with_rfid":
            with_rfid = values.get("students_with_rfid")
            course_name = values.get("course_filter")
            course_name = "" if course_name == default_course_filter else course_name
            students_handler.filter(course_name, with_rfid)
            window['students'].update(values=students_handler.build_list())
        elif event == "teachers_with_rfid":
            with_rfid = values.get("teachers_with_rfid")
            teachers_handler.filter(with_rfid)
            window['teachers'].update(values=teachers_handler.build_list())
        elif event == "refresh_students":
            response = sg.popup_ok_cancel("Are you sure you want to refresh all students?", title="Refresh")
            if response == "OK":
                students_handler.refresh_students()
                window['course_filter'].update(set_to_index=0)
                window['students'].update(values=students_handler.build_list())
        elif event == "refresh_teachers":
            response = sg.popup_ok_cancel("Are you sure you want to refresh all teachers?", title="Refresh")
            if response == "OK":
                teachers_handler.refresh_teachers()
                window['teachers'].update(values=teachers_handler.build_list())
        elif event == "export_students":
            response = sg.popup_ok_cancel("Are you sure you want to export displayed students?", title="Export")
            if response == "OK":
                students_handler.export_to_csv()
        elif event == "export_teachers":
            response = sg.popup_ok_cancel("Are you sure you want to export displayed teachers?", title="Export")
            if response == "OK":
                teachers_handler.export_to_csv()
        elif event == "import_students":
            file_path = sg.popup_get_file("CSV file to open")
            try:
                new_rfid_codes = students_handler.import_csv(file_path)
            except AttributeError as e:
                sg.popup(e, title="Error")
                continue
            response = sg.popup_ok_cancel("Are you sure you want to import {} new rfid code(s)?".format(len(new_rfid_codes.keys())), title="Import")
            if response == "OK":
                students_handler.write_rfid_codes(new_rfid_codes)
                students_handler.refresh_students()
                window['course_filter'].update(set_to_index=0)
                window['students'].update(values=students_handler.build_list())
        elif event == "import_teachers":
            file_path = sg.popup_get_file("CSV file to open")
            try:
                new_rfid_codes = teachers_handler.import_csv(file_path)
            except AttributeError as e:
                sg.popup(e, title="Error")
                continue
            response = sg.popup_ok_cancel("Are you sure you want to import {} new rfid code(s)?".format(len(new_rfid_codes.keys())), title="Import")
            if response == "OK":
                teachers_handler.write_rfid_codes(new_rfid_codes)
                teachers_handler.refresh_teachers()
                window['teachers'].update(values=teachers_handler.build_list())
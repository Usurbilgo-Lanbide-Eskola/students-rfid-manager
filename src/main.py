#!/usr/bin/env python3

import logging
import socket
from odoo_connection_handler import OdooConnectionHandler
import PySimpleGUI as sg
from students_handler import StudentsHandler
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

login_layout = [[sg.Text("Odoo server"), sg.InputText(ODOO_DEFAULT_URL)],
                 [sg.Text("Database"), sg.InputText(ODOO_DEFAULT_DB), sg.Checkbox('Self signed certificate', default=True)],
                 [sg.Text("Username"), sg.InputText()],
                 [sg.Text("Password"), sg.InputText(password_char="*")],
                 [sg.Button("Exit"), sg.Button("Login")],
                 [sg.Text("", key="error_message", visible=False, background_color="red", text_color="white", size=(70,1))]]

main_layout = [[sg.Text("Odoo Students"), sg.Button("Refresh", key="refresh"), sg.Button("Export", key="export"), sg.Button("Import", key="import")],
                [sg.Text("Course filter"), sg.Combo(course_names, key='course_filter', default_value="All", size=(55,1), enable_events=True), sg.Checkbox('With RFID', key="with_rfid", default=True, enable_events=True)],
                [sg.Table(values=students_data, headings=students_headings, enable_events=True,  col_widths=[20,15,15,15,30],
                num_rows=30, justification='center', auto_size_columns=False, key='students')]]

is_logged = False
are_students_loaded = False


if __name__ == "__main__":
    logger.info("Starting RFID Cards Manager")

    sg.theme('SystemDefault')
    window = sg.Window('Students RFID Manager - Login', login_layout)

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
    window = sg.Window('Students RFID Manager', main_layout)

    students_handler = StudentsHandler(odoo_connection)

    course_names = course_names + students_handler.get_courses_names()
  
    while(True):
        event, values = window.read(100, timeout_key='timeout')
        if not are_students_loaded:
            students_handler.refresh_students()
            window['course_filter'].update(values=course_names)
            window['students'].update(values=students_handler.build_list())
            window['course_filter'].update(set_to_index=0)
            are_students_loaded = True
        if event == 'timeout':
            continue
        elif event == sg.WIN_CLOSED:
            sys.exit()
        elif event == "course_filter" or event == "with_rfid":
            with_rfid = values.get("with_rfid")
            course_name = values.get("course_filter")
            course_name = "" if course_name == default_course_filter else course_name
            students_handler.filter(course_name, with_rfid)
            window['students'].update(values=students_handler.build_list())
        elif event == "refresh":
            response = sg.popup_ok_cancel("Are you sure you want to refresh all students?", title="Refresh")
            if response == "OK":
                students_handler.refresh_students()
                window['course_filter'].update(set_to_index=0)
                window['students'].update(values=students_handler.build_list())
        elif event == "export":
            response = sg.popup_ok_cancel("Are you sure you want to export displayed students?", title="Export")
            if response == "OK":
                students_handler.export_to_csv()
        elif event == "import":
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
from PySide2.QtCore import * 
from PySide2.QtGui import * 
from PySide2.QtWidgets import *
from shiboken2 import wrapInstance
from functools import partial
import sys
import math

import maya.OpenMayaUI as omui
from riggingTools.iris import EyeballRig


# Utility function to get Maya window
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance

def get_maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)
# Main UI window
from PySide2 import QtWidgets, QtCore
import maya.cmds as cmds

from PySide2 import QtWidgets, QtCore
import maya.cmds as cmds

class EyeballRigUI(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(EyeballRigUI, self).__init__(parent)
        self.setWindowTitle("Eyeball Rigging Tool")
        self.setGeometry(300, 300, 300, 200)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)  # Set window to stay on top
        self.eye_style_names = ["circle", "oval", "star", "heart", "diamond", "clover"]
        self.eye_style_dict = {}
        self.selected_iris_edges = None
        self.selected_pupil_edges = None
        self.selected_iris_faces = None
        self.selected_pupil_faces = None
        self.shape_paths = {
            "clover": "/Users/ericahetherington/Library/Preferences/Autodesk/maya/2023/prefs/scripts/eyeRigBuilder/resources/clover.png",
            "oval": "/Users/ericahetherington/Library/Preferences/Autodesk/maya/2023/prefs/scripts/eyeRigBuilder/resources/oval.png",
            "star": "/Users/ericahetherington/Library/Preferences/Autodesk/maya/2023/prefs/scripts/eyeRigBuilder/resources/stars.png",
            "diamond": "/Users/ericahetherington/Library/Preferences/Autodesk/maya/2023/prefs/scripts/eyeRigBuilder/resources/diamond.png",
            "heart": "/Users/ericahetherington/Library/Preferences/Autodesk/maya/2023/prefs/scripts/eyeRigBuilder/resources/heart.png",
            "circle": "/Users/ericahetherington/Library/Preferences/Autodesk/maya/2023/prefs/scripts/eyeRigBuilder/resources/round.png"
        }
        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        # Build Eye Rig Group Box
        self.build_eye_rig_group_box = QtWidgets.QGroupBox("Select Eye Edges")
        self.iris_edges_label = QtWidgets.QLabel("Iris Loop:")
        self.iris_edges_line_edit = QtWidgets.QLineEdit()
        self.iris_load_button = QtWidgets.QPushButton("Load")
        self.iris_clear_button = QtWidgets.QPushButton("Clear")
        self.pupil_edges_label = QtWidgets.QLabel("Pupil Loop:")
        self.pupil_edges_line_edit = QtWidgets.QLineEdit()
        self.pupil_load_button = QtWidgets.QPushButton("Load")
        self.pupil_clear_button = QtWidgets.QPushButton("Clear")
        self.r_eye_checkbox = QtWidgets.QCheckBox("Right Eye")
        self.create_rig_button = QtWidgets.QPushButton("Create Rig")
        self.create_rig_button.setStyleSheet(self._major_action_button_style())
        self.create_rig_button.setMinimumSize(50, 22)

        # Build Face Rig Group Box
        self.build_face_rig_group_box = QtWidgets.QGroupBox("Select Eye Faces")
        self.iris_faces_label = QtWidgets.QLabel("Sclera Faces:")
        self.iris_faces_line_edit = QtWidgets.QLineEdit()
        self.iris_faces_load_button = QtWidgets.QPushButton("Load")
        self.iris_faces_clear_button = QtWidgets.QPushButton("Clear")
        self.pupil_faces_label = QtWidgets.QLabel("Iris Faces:")
        self.pupil_faces_line_edit = QtWidgets.QLineEdit()
        self.pupil_faces_load_button = QtWidgets.QPushButton("Load")
        self.pupil_faces_clear_button = QtWidgets.QPushButton("Clear")
        self.skin_eye_button = QtWidgets.QPushButton("Skin Eye")
        self.skin_eye_button.setStyleSheet(self._major_action_button_style())
        self.skin_eye_button.setMinimumSize(50, 22)

        self.iris_edges_line_edit.setStyleSheet(self._style_line_edit())
        self.pupil_edges_line_edit.setStyleSheet(self._style_line_edit())
        self.iris_faces_line_edit.setStyleSheet(self._style_line_edit())
        self.pupil_faces_line_edit.setStyleSheet(self._style_line_edit())

        load_push_buttons = [self.iris_load_button, self.pupil_load_button, self.iris_faces_load_button, self.pupil_faces_load_button]
        clear_push_buttons = [self.iris_clear_button, self.pupil_clear_button, self.iris_faces_clear_button, self.pupil_faces_clear_button]
        for i in load_push_buttons:
            i.setStyleSheet(self._major_action_button_style())
            i.setMinimumSize(50, 22)

        for i in clear_push_buttons:
            i.setStyleSheet(self._major_action_button_style())
            i.setMinimumSize(50, 22)

    def create_rig_menu_buttons(self):
        button = QPushButton()
        # button.setCheckable(True)
        button.setMinimumWidth(75)
        button.setMinimumHeight(75)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        return button

    def set_icon_on_push_button(self, button, size=55):
        button.setIconSize(QtCore.QSize(size, size))  # Set correct size


    def create_layout(self):
        # Layout for Build Eye Rig Group Box
        iris_layout = QtWidgets.QHBoxLayout()
        iris_layout.addWidget(self.iris_edges_line_edit)
        iris_layout.addWidget(self.iris_load_button)
        iris_layout.addWidget(self.iris_clear_button)

        pupil_layout = QtWidgets.QHBoxLayout()
        pupil_layout.addWidget(self.pupil_edges_line_edit)
        pupil_layout.addWidget(self.pupil_load_button)
        pupil_layout.addWidget(self.pupil_clear_button)

        eye_form_layout = QtWidgets.QFormLayout()
        eye_form_layout.addRow(self.iris_edges_label, iris_layout)
        eye_form_layout.addRow(self.pupil_edges_label, pupil_layout)
        eye_form_layout.addRow(self.r_eye_checkbox)
        eye_form_layout.addRow(self.create_rig_button)
        self.build_eye_rig_group_box.setLayout(eye_form_layout)

        # Layout for Build Face Rig Group Box
        iris_faces_layout = QtWidgets.QHBoxLayout()
        iris_faces_layout.addWidget(self.iris_faces_line_edit)
        iris_faces_layout.addWidget(self.iris_faces_load_button)
        iris_faces_layout.addWidget(self.iris_faces_clear_button)

        pupil_faces_layout = QtWidgets.QHBoxLayout()
        pupil_faces_layout.addWidget(self.pupil_faces_line_edit)
        pupil_faces_layout.addWidget(self.pupil_faces_load_button)
        pupil_faces_layout.addWidget(self.pupil_faces_clear_button)





        face_form_layout = QtWidgets.QFormLayout()
        face_form_layout.addRow(self.iris_faces_label, iris_faces_layout)
        face_form_layout.addRow(self.pupil_faces_label, pupil_faces_layout)
        face_form_layout.addRow(self.skin_eye_button)
        self.build_face_rig_group_box.setLayout(face_form_layout)

        # Main Layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.build_eye_rig_group_box)
        main_layout.addWidget(self.build_face_rig_group_box)
        self.create_eye_style_menu(main_layout)
        self.setLayout(main_layout)

    def create_eye_style_menu(self, main_layout):
        """
        Create top horizontal menu array for the different types of rigs
        """

        eye_style_group_box = QtWidgets.QGroupBox("Choose Eye Style")

        # Create a stacked vertical layout for two rows of buttons
        stacked_layout = QVBoxLayout()
        stacked_layout.setContentsMargins(6, 6, 6, 6)  # Add margins for spacing
        stacked_layout.setSpacing(6)  # Add spacing between rows

        # Create two horizontal layouts for button rows
        first_buttons_layout = QHBoxLayout()
        first_buttons_layout.setSpacing(6)  # Add spacing between buttons

        second_buttons_layout = QHBoxLayout()
        second_buttons_layout.setSpacing(6)

        # Add both horizontal layouts to the vertical stacked layout
        stacked_layout.addLayout(first_buttons_layout)
        stacked_layout.addSpacing(12)
        stacked_layout.addLayout(second_buttons_layout)

        # Set the stacked layout to the group box
        eye_style_group_box.setLayout(stacked_layout)

        for index, type in enumerate(self.eye_style_names):
            button_layout = QVBoxLayout()

            icon_name = type.lower()
            icon_path = self.shape_paths.get(icon_name, "")
            eye_icon = QIcon(icon_path)

            label = QtWidgets.QLabel(type)
            label.setAlignment(QtCore.Qt.AlignCenter)

            button = self.create_rig_menu_buttons()
            button.setIcon(eye_icon)  # Apply the icon
            button.setEnabled(True)

            button_layout.addWidget(button)
            button_layout.addWidget(label) 

            if index < 3:
               
                first_buttons_layout.addLayout(button_layout)
            else:  
                second_buttons_layout.addLayout(button_layout)

            self.set_icon_on_push_button(button, 60)
            button.clicked.connect(self.update_button_states_on_off)

            self.eye_style_dict[type] = {
                "button": button,
                "label": label
            }

            if index == 0:
                button.setChecked(True)
                button.setStyleSheet(self._square_menu_on_style())
                label.setStyleSheet(self._style_label_enabled())

            else:
                button.setChecked(False)
                button.setStyleSheet(self._square_menu_off_style())
                label.setStyleSheet(self._style_label_disabled())

        # Add the group box to the main layout
        main_layout.addWidget(eye_style_group_box)

    def _square_menu_on_style(self):
        return """
        QPushButton {
            border: 2px solid #f28cc6; /* Add border width and solid style */
            border-radius: 6px;
            background-color: transparent; /* Default background */
        }
        QPushButton:checked {
            background-color: #f28cc6; /* Background color same as the border when checked */
            color: white;  /* Optional: Change text color when checked */
        }
        """
    def _style_line_edit(self):
        return """
        QLineEdit {
            background-color: #2b2b2b;
            color: white;
            border: none;  /* Remove border when not focused */
            border-radius: 4px;
        }
        QLineEdit:focus {
            background-color: #2b2b2b;  /* Color when selected/focused */
            border: 1px solid #f28cc6;  /* Thin border when focused */
        }
        """

    def _style_label_enabled(self):
        return """
            QLabel {
                color: #f28cc6;
            }
        """

    def _style_label_disabled(self):
        return """
            QLabel {
                color: #b4b4b4;
            }
        """

    def _square_menu_off_style(self):
        return """
        QPushButton {
            border: 2px solid #5c5c5c; /* Same as above */
            border-radius: 6px;
        }
        """
    def _button_style(self):
        return """
        QPushButton {
            border: 2px solid #5c5c5c; /* Same as above */
            border-radius: 6px;
        }
        """

    def _major_action_button_style(self):
        return """
            QPushButton {
                background-color: #5c5c5c;
                color: #efefee;
                border: 1px solid #5c5c5c;  /* Border color and width */
                border-radius: 4px;
                outline: none;  /* Remove focus border */
                box-shadow: none;  /* Remove any shadow */
            }
            QPushButton:focus {
                outline: none;  /* Disable focus outline */
                box-shadow: none;  /* Remove focus shadow */
            }
            QPushButton:hover {
                background-color: #909090;   /* Button color on hover */
            }
            QPushButton:pressed {
                background-color: #404040;   /* Custom color for pressed state */
            }
        """


    def create_connections(self):
        # Eye Rig connections
        self.iris_load_button.clicked.connect(self.load_iris_edges)
        self.iris_clear_button.clicked.connect(self.clear_iris_edges)
        self.pupil_load_button.clicked.connect(self.load_pupil_edges)
        self.pupil_clear_button.clicked.connect(self.clear_pupil_edges)

        self.create_rig_button.clicked.connect(lambda: self.create_rig(self.selected_iris_edges, self.selected_pupil_edges))

        # Face Rig connections
        self.iris_faces_load_button.clicked.connect(self.load_iris_faces)
        self.iris_faces_clear_button.clicked.connect(self.clear_iris_faces)
        self.pupil_faces_load_button.clicked.connect(self.load_pupil_faces)
        self.pupil_faces_clear_button.clicked.connect(self.clear_pupil_faces)

        self.skin_eye_button.clicked.connect(lambda: self.skin_eye_clicked(self.selected_iris_faces, self.selected_pupil_faces))


    def update_button_states_on_off(self):
        # Get the button that was clicked
        clicked_button = self.sender()

        for rig_data in self.eye_style_dict.values():
            button = rig_data["button"]
            label = rig_data["label"]
            label_text = label.text().lower()

            # If the button is not the one clicked, turn it off
            if button != clicked_button:
                button.setChecked(False)
                button.setStyleSheet(self._square_menu_off_style())
                label.setStyleSheet(self._style_label_disabled())
            else:
                button.setChecked(True)
                button.setStyleSheet(self._square_menu_on_style())  # Apply style
                label.setStyleSheet(self._style_label_enabled())
                if self.rig is not None:
                    self.rig.switch_blendshape_target_on_off(label_text)


    def load_iris_edges(self):
        self.selected_iris_edges = cmds.ls(selection=True, flatten=True)
        if self.selected_iris_edges:
            iris_edges_str = ', '.join(self.selected_iris_edges)
            self.iris_edges_line_edit.setText(iris_edges_str)
            self.iris_edges_line_edit.setFocus()


    def clear_iris_edges(self):
        self.iris_edges_line_edit.clear()
        self.selected_iris_edges = None

    def load_pupil_edges(self):
        self.selected_pupil_edges = cmds.ls(selection=True, flatten=True)
        if self.selected_pupil_edges:
            pupil_edges_str = ', '.join(self.selected_pupil_edges)
            self.pupil_edges_line_edit.setText(pupil_edges_str)
            self.pupil_edges_line_edit.setFocus()  # Set focus to the line edit


    def clear_pupil_edges(self):
        self.pupil_edges_line_edit.clear()
        self.selected_pupil_edges = None

    def load_iris_faces(self):
        self.selected_iris_faces = cmds.ls(selection=True, flatten=True)
        if self.selected_iris_faces:
            # Join the list into a single string, with a separator like a comma
            iris_faces_str = ', '.join(self.selected_iris_faces)
            self.iris_faces_line_edit.setText(iris_faces_str)
            self.iris_faces_line_edit.setFocus()

    def clear_iris_faces(self):
        self.iris_faces_line_edit.clear()
        self.selected_iris_faces = None

    def load_pupil_faces(self):
        self.selected_pupil_faces = cmds.ls(selection=True, flatten=True)
        if self.selected_pupil_faces:
            pupil_faces_str = ', '.join(self.selected_pupil_faces)
            self.pupil_faces_line_edit.setText(pupil_faces_str)
            self.pupil_faces_line_edit.setFocus()

    def clear_pupil_faces(self):
        self.pupil_faces_line_edit.clear()
        self.selected_pupil_faces = None

    def create_rig(self, iris_edges, pupil_edges):
        if iris_edges is None or pupil_edges is None:
            # Handle the case where iris_edges or pupil_edges is None
            print("Error: Missing iris or pupil edges!")
            return
        else:
            r_eye_flag = self.r_eye_checkbox.isChecked()
            self.rig = EyeballRig(iris_edges, pupil_edges, r_eye_flag)


    def skin_eye_clicked(self, iris_faces, pupil_faces):
        try:
            if self.rig is None:
                raise AttributeError("Rig not created yet")

            elif iris_faces is None or pupil_faces is None:
                # Handle the case where iris_edges or pupil_edges is None
                print("Error: Missing schlera or iris faces")
                return

            else:

                pupil_joints = [f"l_pupilScale{str(i).zfill(2)}_jnt" for i in range(24)]  # Pupil joints
                iris_joints = [f"l_irisTip{str(i).zfill(2)}_jnt" for i in range(24)]

                self.rig.assign_influence_to_eye_aim('l', iris_faces)
                self.rig.assign_influence_to_eye_aim('l', pupil_faces)
                self.rig.skin_eye_verts("l", iris_faces, iris_joints, iris_flag=True)
                self.rig.skin_eye_verts("l", pupil_faces, pupil_joints, iris_flag=False)

                print(f"Left eye skin recalulated.")

                r_eye_flag = self.r_eye_checkbox.isChecked()
                if r_eye_flag:
                    r_pupil_faces = [face.replace("l_eye_geo", "r_eye_geo") for face in pupil_faces]
                    r_iris_faces  = [face.replace("l_eye_geo", "r_eye_geo") for face in iris_faces]
                    r_pupil_joints = [f"r_pupilScale{str(i).zfill(2)}_jnt" for i in range(24)]
                    r_iris_joints = [f"r_irisTip{str(i).zfill(2)}_jnt" for i in range(24)]

                    self.rig.assign_influence_to_eye_aim("r", r_iris_faces)
                    self.rig.assign_influence_to_eye_aim("r", r_pupil_faces)
                    self.rig.skin_eye_verts("r", r_iris_faces, r_iris_joints, iris_flag=True)
                    self.rig.skin_eye_verts("r", r_pupil_faces, r_pupil_joints, iris_flag=False)

                    print(f"Right eye skin recalulated.")

        except AttributeError as e:
            # If rig is not created, print a custom message
            print("Create rig first.")

# cmds.blendShape(combined_bs, edit=True, weight=[(0, 1), (1, 1)])


# Main function to run the UI
def show_ui():
    parent = get_maya_main_window()  # Get Maya's main window as the parent
    ui = EyeballRigUI(parent)
    ui.show()

# Execute the UI
show_ui()

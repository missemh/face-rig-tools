from PySide2 import QtCore, QtGui, QtWidgets
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui

from functools import partial
import sys
import math


def get_maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class UvCopyUi(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(UvCopyUi, self).__init__(parent)
        self.setWindowTitle("Copy UVs")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)  # Keep window on top
        
        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        # UV Transfer Group Box
        self.uv_group_box = QtWidgets.QGroupBox()
        
        # Source
        self.uv_source_label = QtWidgets.QLabel("Source:")
        self.uv_source_line_edit = QtWidgets.QLineEdit()
        self.uv_load_button = QtWidgets.QPushButton("Load")
        self.uv_clear_button = QtWidgets.QPushButton("Clear")

        # Targets
        self.targets_label = QtWidgets.QLabel("Target(s):")
        self.targets_line_edit = QtWidgets.QLineEdit()
        self.targets_load_button = QtWidgets.QPushButton("Load")
        self.targets_clear_button = QtWidgets.QPushButton("Clear")

        # Sample Space Dropdown
        self.sample_space_label = QtWidgets.QLabel("Sample Space:")
        self.sample_space_combo_box = QtWidgets.QComboBox()
        self.sample_space_combo_box.addItems([
            "World",
            "Local",
            "UV",
            "Component",
            "Topology"
        ])

        # Transfer Button
        self.copy_uvs_button = QtWidgets.QPushButton("Transfer UVs")
        self.copy_uvs_button.setStyleSheet(self._major_action_button_style())
        self.copy_uvs_button.setMinimumSize(50, 22)

        # Style inputs
        self.uv_source_line_edit.setStyleSheet(self._style_line_edit())
        self.targets_line_edit.setStyleSheet(self._style_line_edit())

        for button in [self.uv_load_button, self.targets_load_button, self.uv_clear_button, self.targets_clear_button]:
            button.setStyleSheet(self._major_action_button_style())
            button.setMinimumSize(50, 22)


    def create_layout(self):
        # UV Source Layout
        source_layout = QtWidgets.QHBoxLayout()
        source_layout.addWidget(self.uv_source_line_edit)
        source_layout.addWidget(self.uv_load_button)
        source_layout.addWidget(self.uv_clear_button)

        # UV Target Layout
        target_layout = QtWidgets.QHBoxLayout()
        target_layout.addWidget(self.targets_line_edit)
        target_layout.addWidget(self.targets_load_button)
        target_layout.addWidget(self.targets_clear_button)

        # UV Group Form Layout
        uv_form_layout = QtWidgets.QFormLayout()
        uv_form_layout.addRow(self.uv_source_label, source_layout)
        uv_form_layout.addRow(self.targets_label, target_layout)
        uv_form_layout.addRow(self.sample_space_label, self.sample_space_combo_box)
        uv_form_layout.addRow(self.copy_uvs_button)

        uv_form_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.uv_group_box.setLayout(uv_form_layout)

        # Main Layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.uv_group_box)
        self.setLayout(main_layout)

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
            border: 1px solid #db9456;  /* Thin border when focused */
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

 
    def _button_style(self):
        return """
        QPushButton {
            border: 2px solid #5c5c5c; /* Same as above */
            border-radius: 6px;
        }
        """

    

    def create_connections(self):
        # Eye Rig connections
        self.uv_load_button.clicked.connect(self.load_uv_source_mesh)
        self.uv_clear_button.clicked.connect(self.clear_uv_source_mesh)

        self.targets_load_button.clicked.connect(self.load_target_mesh_selection)
        self.targets_clear_button.clicked.connect(self.clear_target_selection)

        self.copy_uvs_button.clicked.connect(lambda: self.transfer_uvs(self.uv_source_mesh, self.selected_target_meshes))

    def load_uv_source_mesh(self):
        selection = cmds.ls(selection=True, dag=True, type="mesh")

        if not selection:
            cmds.warning("No mesh selected.")
            return

        # If more than one mesh is selected, show an error
        if len(selection) > 1:
            cmds.warning("More than one mesh selected. Please select only one.")
            return

        # Get the transform node of the mesh
        self.uv_source_mesh = cmds.listRelatives(selection[0], parent=True, fullPath=True)[0]
        self.uv_source_line_edit.setText( self.uv_source_mesh)
        self.uv_source_line_edit.setFocus()

    def clear_uv_source_mesh(self):
        self.uv_source_line_edit.clear()
        self.selected_uv_source = None


    def load_target_mesh_selection(self):
        selection = cmds.ls(selection=True, flatten=True)

        if not selection:
            cmds.warning("No mesh selected.")
            return

        self.selected_target_meshes = selection

        if self.selected_target_meshes:
            target_meshes = ', '.join(self.selected_target_meshes)
            self.targets_line_edit.setText(target_meshes)
            self.targets_line_edit.setFocus()  # Set focus to the line edit

    def clear_target_selection(self):
        self.targets_line_edit.clear()
        self.selected_target_meshes = None


    def transfer_uvs(self, source, targets):
        if source is None or targets is None:
            # Handle the case where iris_edges or pupil_edges is None
            print("Error: Missing iris or pupil edges!")
            return
        else:
            transfer_method = self.sample_space_combo_box.currentText()
            transfer_uvs_via_mesh_attributes(source, targets, transfer_method)


def transfer_uvs_via_mesh_attributes(source, targets, transfer_method):
    method_map = {
            "World": 0,
            "Local": 1,
            "UV": 2,
            "Component": 3,
            "Topology": 4
        }

    if transfer_method not in method_map:
        cmds.warning(f"Invalid transfer method: {transfer_method}")
        return

    sample_space = method_map[transfer_method]

    for target in targets:
        try:
            cmds.transferAttributes(
                source, target,
                transferUVs=2,              # 2 = Transfer UVs
                sampleSpace=sample_space,
                searchMethod=3,             # Closest point
                flipUVs=0,
                colorBorders=1
            )
            cmds.delete(target, constructionHistory=True)
            print(f"Transferred UVs from {source} to {target} using '{transfer_method}'")
        except Exception as e:
            cmds.warning(f"Failed to transfer UVs to {target}: {e}")


# Main function to run the UI
def show_ui():
    parent = get_maya_main_window()  # Get Maya's main window as the parent
    ui = UvCopyUi(parent)
    ui.show()

# Execute the UI
show_ui()


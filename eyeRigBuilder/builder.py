from PySide2.QtCore import * 
from PySide2.QtGui import * 
from PySide2.QtWidgets import *
import sys
from functools import partial

from autoRigger.Ui.operations import UiActions
from autoRigger.dictionaries import colors
from autoRigger.dictionaries import icons
from autoRigger.Ui.style import Styler
from enum import Enum

class HandleSide(Enum):
    LEFT = 'L'
    RIGHT = 'R'
    CENTER = 'C'

    @staticmethod
    def get_side_prefix(side):
        # Use the `value` of the side to generate the prefix
        return f"{side.value}_"


class UiBuilder():
    def __init__(self):
        self.styler = Styler()

    def create_combo_box(self, items_to_add, alignment=Qt.AlignCenter, fixed=False, width=150, height=40, enabled=True, style=None):
        combo_box = QComboBox()
        combo_box.addItems(items_to_add)
        combo_box.setEnabled(enabled)

        if fixed:
            combo_box.setFixedSize(width, height)
        else:
            combo_box.setMinimumWidth(width)
            combo_box.setFixedHeight(height)

        if style:
            self.styler.apply_style(combo_box, style)

        return combo_box

    def create_line_edit(self, alignment=Qt.AlignCenter, read_only=True, min_width=150, min_height=40, style=None):
        line_edit = QLineEdit()
        line_edit.setAlignment(alignment)
        line_edit.setReadOnly(read_only)
        line_edit.setMinimumWidth(min_width)
        line_edit.setFixedHeight(min_height)

        if style:
            self.styler.apply_style(line_edit, style)

        return line_edit

    def create_rig_menu_buttons(self, top_layout, rig_type_name):
        button = QPushButton()
        button.setCheckable(True)
        button.setMinimumWidth(75)
        button.setMinimumHeight(75)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        top_layout.addWidget(button) # Add the push button to the top layout

        return button

    def set_icon_on_push_button(self, button, icon, size):
        button.setIcon(icon)
        button.setIconSize(QSize(size, size))

    def create_rig_vertical_menu_buttons(self, vertical_menu_layout, heading, color):

        if heading.lower() in icons.rig_parts:
            left_icon_path = icons.rig_parts[heading.lower()]
        else:
            left_icon_path = icons.arrow_icons[color + "Down"]
        right_icon_path = icons.arrow_icons["downArrow"]
        
        drop_down_button = CustomButton(heading, left_icon_path, right_icon_path)

        arrow_label = drop_down_button.right_icon_label

        self.styler.apply_style(drop_down_button, "button_drop_down")

        drop_down_button.setChecked(False)

        return drop_down_button, arrow_label

    def create_custom_button_two_icons(self, text, color):
        """Method to create a custom button with icons and text."""
        if text.lower() in icons.rig_parts:
            left_icon_path = icons.rig_parts[text.lower()]
        else:
            left_icon_path = icons.arrow_icons[color + "Down"]
        right_icon_path = icons.arrow_icons["sideArrow"]

        button = CustomButton(text, left_icon_path, right_icon_path)
        
        return button

    def create_custom_button_side_arrow(self, text):
        """Method to create a custom button with just the side arrow and text."""
        button = CustomButtonSideArrow(text)
        
        return button


    def create_generic_button(self, text, min_width=60, min_height=26, fixed_size=False, enabled=True, visible=True, expanding=True, style=None):
        button = QPushButton(text)
        button.setEnabled(enabled)
        button.setVisible(visible)
        button.setMinimumWidth(min_width)
        button.setFixedHeight(min_height)

        if fixed_size:
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        elif expanding:
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if style:
            self.styler.apply_style(button, style)

        return button

    def create_switch_button(self, text, min_width=60, min_height=26, fixed_size=False, enabled=True, visible=True, expanding=True, style=None, style_color=None):
        button = QPushButton(text)
        button.setEnabled(enabled)
        button.setVisible(visible)
        button.setMinimumWidth(min_width)
        button.setFixedHeight(min_height)

        if fixed_size:
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        elif expanding:
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if style:
            self.styler.apply_style(button, style, style_color)

        return button

    def create_action_button(self, text, min_width=60, min_height=40, fixed_size=False, enabled=True, visible=True, expanding=True, style=None):
        button = QPushButton(text)
        button.setEnabled(enabled)
        button.setVisible(visible)
        button.setMinimumWidth(min_width)
        button.setFixedHeight(min_height)

        if fixed_size:
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        elif expanding:
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if style:
            self.styler.apply_style(button, style)

        return button

    def create_slider(self, min_value=0, max_value=100, initial_value=0, enabled=True, style=None, style_color="red"):
        slider = QSlider(Qt.Horizontal)
        slider.setFixedHeight(24)
        slider.setMinimum(min_value)
        slider.setMaximum(max_value)
        slider.setValue(initial_value)

        if not enabled:
            slider.setEnabled(False)

        if style:
            self.styler.apply_style(slider, style, style_color)

        return slider

    def create_upload_buttons(self, key_type, edge_names, layout, joints_flag=False, numbers_for_combo=None):
        button_dict = {}
        rows = []
        heading_names = ["Upload", "Check", "Clear", "Loaded", "Number of\nJoints"]
        button_names = ["load", "check", "clear", "green", "red"]

        heading_layout = QHBoxLayout()
        layout.addLayout(heading_layout)

        # Add an empty QLabel to act as a spacer in the headings, so there's no heading above the "type" column.
        empty_label = QLabel("")
        self.styler.apply_style(empty_label, "label_enabled")
        empty_label.setFixedSize(70, 26)  # Adjust size if needed
        heading_layout.addWidget(empty_label)

        # Add headings only for the buttons, not for the "type" column
        if joints_flag:
            headings = heading_names
        else:
            headings = heading_names[:-1]

        for heading in headings:
            label = QLabel(heading)
            label.setAlignment(Qt.AlignCenter)  # Center the text
            label.setFixedSize(45, 26)
            label.setWordWrap(True)  # Enable word wrapping
            heading_layout.addWidget(label)

        # Create buttons for each edge
        for key in edge_names:
            new_row = QHBoxLayout()

            # Add the edge type label in the first column
            label = QLabel(key)
            self.styler.apply_style(label, "label_enabled")
            label.setFixedSize(70, 26)
            new_row.addWidget(label)

            for name in button_names:
                button = QPushButton("")
                button.setEnabled(True)
                button.setFixedSize(45, 26)
                if name in ["green", "red"]:
                    self.styler.apply_style(button, "button_traffic_light")
                else:
                    self.styler.apply_style(button, "button_minor_action")

                icon = QIcon(icons.upload_edge_icons[name])
                button.setIcon(icon)
                button.setIconSize(QSize(16, 16))

                if name == "green":
                    button.setVisible(False)  # Hide the green button

                new_row.addWidget(button)

                # Add the button to the dictionary
                button_dict.setdefault(key, {})[name] = button

            button_dict.setdefault(key, {})[key_type] = [] # Create empty list to store edge selection
            layout.addLayout(new_row)  # Add the row to the main layout
            rows.append(new_row)  # Keep track of rows

        # Add the combo box if joints_flag is enabled
        if joints_flag and numbers_for_combo:
            for row, numbers in zip(rows, numbers_for_combo):
                combo_box = QComboBox()
                combo_box.addItems(numbers)
                self.styler.apply_style(combo_box, "combo_box")
                row.addWidget(combo_box)

                button_dict.setdefault(edge, {})["combo_box"] = combo_box



        return button_dict


class CustomButtonSideArrow(QPushButton):
    def __init__(self, text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """
        Custom drop-down button. Icon on the left side and right side with centered text.
        Right icon rotates on button press.
        """
        self.styler = Styler()
        self.right_icon_path = icons.arrow_icons["sideArrow"]
        self.text = text
        self.rotation = 0
        self.rotated = False  # Track rotation state

        # Initialize UI
        self.set_initial_pixmap()
        self.set_button_layout()

        self.setFixedHeight(40)  # Set fixed height
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setSizePolicy(size_policy)

    def rotate_item(self):
        """
        Rotate the image 90 degrees clockwise or reset to original.
        """
        if not self.rotated:
            self.rotation += 90
            self.rotated = True
        else:
            self.rotation -= 90
            self.rotated = False
        
        self.update_pixmap()

    def update_pixmap(self):
        """
        Update the button with the rotated pixmap.
        """
        rectF = QRectF(0, 0, self.right_icon_pixmap.width(), self.right_icon_pixmap.height())
        pix = QPixmap(self.right_icon_pixmap.size())
        pix.fill(Qt.transparent)  # Ensure the background is transparent
        
        painter = QPainter(pix)
        painter.translate(rectF.center())
        painter.rotate(self.rotation)
        painter.translate(-rectF.center())
        painter.drawPixmap(0, 0, self.right_icon_pixmap)
        painter.end()
        
        self.right_icon_label.setPixmap(pix)

    def set_initial_pixmap(self):
        """
        Initialize the pixmaps and set them to the labels.
        """
        self.right_icon_pixmap = QPixmap(self.right_icon_path).scaled(QSize(30, 30), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # Create labels for icons
        self.right_icon_label = QLabel()
        self.styler.apply_style(self.right_icon_label, "label_enabled")
        
        # Set initial pixmap
        self.right_icon_label.setPixmap(self.right_icon_pixmap)

    def set_button_layout(self):
        """
        Set up the layout of the button.
        """

        # Create the main horizontal layout for the button
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 5, 5, 5)  # Adjust margins as needed
        main_layout.setSpacing(5)  # Adjust spacing between elements if needed
        
        # Add the left icon and text to the left layout
        text_label = QLabel(self.text)
        text_label.setStyleSheet("margin-left: 0px;")
        self.styler.apply_style(text_label, "label_enabled")
        main_layout.addWidget(text_label, alignment=Qt.AlignLeft)
        
        # Add spacer to push right icon to the end
        spacer = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum)
        main_layout.addItem(spacer)
        
        # Add the right icon label to the main layout with alignment to the right
        main_layout.addWidget(self.right_icon_label, alignment=Qt.AlignRight)
        
        # Set the layout to the button
        self.setLayout(main_layout)
        
        # Connect button click to rotate method
        self.clicked.connect(self.rotate_item)


class CustomButton(QPushButton):
    def __init__(self, text, left_icon_path, right_icon_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """
        Custom drop-down button. Icon on the left side and right side with centered text.
        Right icon rotates on button press.

        """

        self.left_icon_path = left_icon_path
        self.right_icon_path = right_icon_path
        self.text = text
        self.rotation = 0
        self.rotated = False  # Track rotation state

        # Initialize UI
        self.set_initial_pixmaps()
        self.set_button_layout()

    def rotate_item(self):
        """
        Rotate the image 90 degrees clockwise or reset to original.
        """
        if not self.rotated:
            self.rotation += 90
            self.rotated = True
        else:
            self.rotation -= 90
            self.rotated = False
        
        self.update_pixmap()

    def update_pixmap(self):
        """
        Update the button with the rotated pixmap.
        """
        rectF = QRectF(0, 0, self.right_icon_pixmap.width(), self.right_icon_pixmap.height())
        pix = QPixmap(self.right_icon_pixmap.size())
        pix.fill(Qt.transparent)  # Ensure the background is transparent
        
        painter = QPainter(pix)
        painter.translate(rectF.center())
        painter.rotate(self.rotation)
        painter.translate(-rectF.center())
        painter.drawPixmap(0, 0, self.right_icon_pixmap)
        painter.end()
        
        self.right_icon_label.setPixmap(pix)

    def set_initial_pixmaps(self):
        """
        Initialize the pixmaps and set them to the labels.
        """
        self.left_icon_pixmap = QPixmap(self.left_icon_path).scaled(QSize(20, 20), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.right_icon_pixmap = QPixmap(self.right_icon_path).scaled(QSize(30, 30), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # Create labels for icons
        self.left_icon_label = QLabel()
        self.right_icon_label = QLabel()
        
        # Set initial pixmaps
        self.left_icon_label.setPixmap(self.left_icon_pixmap)
        self.right_icon_label.setPixmap(self.right_icon_pixmap)

    def set_button_layout(self):
        """
        Set up the layout of the button.
        """

        # Create the main horizontal layout for the button
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)  # Adjust margins as needed
        main_layout.setSpacing(3)  # Adjust spacing between elements if needed
        
        # Create a layout for the left icon and text
        left_layout = QHBoxLayout()
        left_layout.setContentsMargins(3, 3, 3, 3)  # No margins
        left_layout.setSpacing(5)  # Adjust spacing if needed
        
        # Add the left icon and text to the left layout
        left_layout.addWidget(self.left_icon_label, alignment=Qt.AlignLeft)
        text_label = QLabel(self.text)
        text_label.setStyleSheet("margin-left: 0px;")
        left_layout.addWidget(text_label, alignment=Qt.AlignLeft)
        
        # Add the left layout to the main layout
        main_layout.addLayout(left_layout)

        # Add spacer to push right icon to the end
        spacer = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum)
        main_layout.addItem(spacer)
        
        # Add the right icon label to the main layout with alignment to the right
        main_layout.addWidget(self.right_icon_label, alignment=Qt.AlignRight)
        
        # Set the layout to the button
        self.setLayout(main_layout)
        
        # Connect button click to rotate method
        self.clicked.connect(self.rotate_item)


class Test(QGroupBox, UiBuilder, UiActions):
    def __init__(self, color, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.expanded_height = None
        self.color = color

        self.styler = Styler()

        self.setLayout(self.create_main_layout())
        self.styler.apply_style(self, "group_box_drop_down", self.color)


    def create_main_layout(self):
        # Main layout for the group box
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignTop)

        main_layout.addLayout(self._create_main_button())

        container_layout = self._create_container_widget()
        main_layout.addWidget(self.container_widget)

        self._create_group_box_one(container_layout)
        self._create_group_box_two(container_layout)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        main_layout.setSizeConstraint(QLayout.SetMinAndMaxSize)
        self.adjustSize()

        # Add an expanding spacer at the bottom to ensure proper layout behavior
        # expanding_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        # main_layout.addItem(expanding_spacer)

        self.expanded_height = self.height()
        self.container_widget.setVisible(False)
        
        return main_layout

    def _create_main_button(self):
        """Create and style the title layout with the dropdown button."""
        first_row = QHBoxLayout()
        first_row.setContentsMargins(0, 0, 0, 0)

        left_icon_path = icons.rig_parts.get("test")
        right_icon_path = icons.arrow_icons["sideArrow"]

        # Create and style the custom button
        self.drop_down_button = self.create_custom_button_side_arrow("Test")
        self.styler.apply_style(self.drop_down_button, "button_drop_down")


        # Add the button to the title layout
        first_row.addWidget(self.drop_down_button)

        return first_row


    def _create_container_widget(self):
        """Create and set up the container widget with opacity effect and additional controls."""
        self.container_widget = QWidget()

        self.styler.apply_style(self.container_widget, "container_widget")
        
        # Set the size policy to allow vertical expansion
        self.container_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Create the layout for the container widget
        container_layout = QVBoxLayout(self.container_widget)
        container_layout.setContentsMargins(5, 0, 5, 5)
        
        # Set the size constraint to allow the layout to expand fully
        container_layout.setSizeConstraint(QLayout.SetMinAndMaxSize)

        return container_layout


    def _create_group_box_one(self, layout):
        # Create and style the group box
        group_box_one = QGroupBox()
        self.styler.apply_style(group_box_one, "group_box_separator")
        
        # Create a vertical layout for the group box
        group_box_layout = QVBoxLayout(group_box_one)

        for test_button in ["test1", "test2", "test3"]:
            row = QHBoxLayout()
            test_button = self.create_action_button(test_button, visible=True, style="button_major_action")
            row.addWidget(test_button)
            group_box_layout.addLayout(row)

        # Add the group box to the container layout
        layout.addWidget(group_box_one)

    def _create_group_box_two(self, layout):
        # Create and style the group box
        group_box_two = QGroupBox()
        self.styler.apply_style(group_box_two, "group_box_separator")
        
        # Create a vertical layout for the group box
        group_box_two_layout = QVBoxLayout(group_box_two)

        for test_button in ["test1", "test2", "test3"]:
            row = QHBoxLayout()
            test_button = self.create_action_button(test_button, visible=True, style="button_major_action")
            row.addWidget(test_button)
            group_box_two_layout.addLayout(row)

        # Add the group box to the container layout
        layout.addWidget(group_box_two)






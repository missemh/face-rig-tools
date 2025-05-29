from PySide2.QtCore import * 
from PySide2.QtGui import * 
from PySide2.QtWidgets import *
import sys

from autoRigger.dictionaries import colors
from autoRigger.dictionaries import icons


ui_colors = {
    "window": "#2b2b2b",
    "groupBox": "#3c3c3c",
    "rigTypeButton": "#343434",
    "dropDownMenu": "#3c3c3c",
    "switchOn": "#efefee",
    "buttonEnabled": "#5c5c5c",
    "buttonDisabled": "#444444",
    "actionHover": "#909090",
    "hover": "#c0c0c0",
    "actionButton": "#676767",
    "slider": "#404040",
    "pressed": "#b0b0b0",
    "purple": "#8879a7",
    "red": "#d85b50",
    "blue": "#6ebee9",
    "green": "#4db065",
    "pink": "#d57391",
    "whiteBorder": "#bdbdbd",
    "white": "#efefee",
    "extraColour": "#f2e4a6",
    "disabledText": "#babbbf",
    "whiteText": "#efefee",
    "highlight": "#87bbd7"
}


class Styler:
    def __init__(self):
        self.styles = {
            "button_drop_down": self._drop_down_style,
            "button_square_menu_on": self._square_menu_on_style,
            "button_square_menu_off": self._square_menu_off_style,
            "button_switch_on": self._switch_on_style,
            "button_switch_off": self._switch_off_style,
            "button_traffic_light": self._button_traffic_light_style,
            "button_minor_action": self._minor_action_button_style,
            "button_major_action": self._major_action_button_style,
            "line_edit_without_text": self._style_line_edit_without_text,
            "line_edit_with_text": self._style_line_edit_with_text,
            "slider": self._style_slider,
            "label_enabled": self._style_label_enabled,
            "label_disabled": self._style_label_disabled,
            "label_title": self._style_label_title,
            "group_box_drop_down": self._style_drop_down_group_box,
            "group_box_separator": self._style_seperator_group_box,
            "group_box_base_info": self._style_base_info_group_box,
            "combo_box": self._style_combo_box_straight_curvy,
            "scroll_area": self._style_scrollable_area,
            "widget_menu": self._style_widget,
            "container_widget": self._style_container_widget
        }

    def apply_style(self, widget, style_name, *args):
        style_function = self.styles.get(style_name)
        if style_function:
            if callable(style_function):
                style = style_function(*args)  # Call the style function with arguments
            else:
                style = style_function
            widget.setStyleSheet(style)

    def _drop_down_style(self):
        return f"""
        QPushButton {{
            background-color: {ui_colors["dropDownMenu"]};
            border-radius: 6px;
        }}
        """

    def _square_menu_on_style(self, color):
        return f"""
        QPushButton {{
            background-color: {ui_colors[color]};
            border-radius: 6px;
        }}
        """

    def _square_menu_off_style(self):
        return f"""
        QPushButton {{
            background-color: {ui_colors["rigTypeButton"]};
            border-radius: 6px;
        }}
        QPushButton:hover {{
            background-color: {ui_colors["dropDownMenu"]}; /* Slightly different color on hover */
        }}
        QPushButton:pressed {{
            background-color: {ui_colors["dropDownMenu"]}; /* Custom color for pressed state */
            border-radius: 6px;
        }}
        """

    def _switch_on_style(self, color):
        return f"""
        QPushButton {{
            background-color: {ui_colors[color]};
            color: {ui_colors['window']};
            border-radius: 4px;
        }}
        """

    def _switch_off_style(self, color):
        return f"""
        QPushButton {{
        background-color: {ui_colors[color]};
        color: {ui_colors['whiteText']};
        border-radius: 4px;
        }}
        QPushButton:disabled {{
            background-color: {ui_colors["buttonDisabled"]};
            color: {ui_colors["disabledText"]};
            border-radius: 4px; /* Kept consistent with the default state */
        }}
        QPushButton:hover {{
            background-color: {ui_colors[color]};
        }}
        QPushButton:pressed {{
            background-color: {ui_colors[color]};
            border-radius: 4px;
        }}
        """

    def _button_traffic_light_style(self):
        return f"""
        QPushButton {{
            background-color: {ui_colors["groupBox"]};
            color: {ui_colors['whiteText']};
            border-radius: 4px;
        }}
        QPushButton:disabled {{
            background-color: {ui_colors["groupBox"]};
            color: {ui_colors["disabledText"]}; /* Corrected spelling */
            border-radius: 4px; /* Kept consistent with the default state */
        }}
        QPushButton:hover {{
            background-color: {ui_colors["groupBox"]}; /* Slightly different color on hover */
        }}
        QPushButton:pressed {{
            background-color: #ccc;  /* Grey background on press */
        }}
        """

    def _minor_action_button_style(self):
        return f"""
        QPushButton {{
            background-color: {ui_colors["buttonEnabled"]};
            color: {ui_colors['whiteText']};
            border-radius: 4px;
        }}
        QPushButton:disabled {{
            background-color: {ui_colors["buttonDisabled"]};
            color: {ui_colors["disabledText"]}; /* Corrected spelling */
            border-radius: 4px; /* Kept consistent with the default state */
        }}
        QPushButton:hover {{
            background-color: {ui_colors["actionHover"]}; /* Slightly different color on hover */
        }}
        QPushButton:pressed {{
            background-color: #ccc;  /* Grey background on press */
        }}
        """

    def _major_action_button_style(self):
        return f"""
            QPushButton {{
                background-color: {ui_colors['actionButton']};
                color: {ui_colors['whiteText']};
                border: 1px solid {ui_colors["actionButton"]};  /* Border color and width */
                border-radius: 6px;
                outline: none;  /* Remove focus border */
                box-shadow: none;  /* Remove any shadow */
            }}
            QPushButton:focus {{
                outline: none;  /* Disable focus outline */
                box-shadow: none;  /* Remove focus shadow */
            }}
            QPushButton:hover {{
                background-color: {ui_colors['hover']};   /* Button color on hover */
            }}
            QPushButton:pressed {{
                background-color: #404040;   /* Custom color for pressed state */
            }}
            QPushButton:disabled {{
                background-color: {ui_colors["buttonDisabled"]};
                color: {ui_colors["disabledText"]}; /* Corrected spelling */
                border: 1px solid {ui_colors["buttonDisabled"]};  /* Border color and width */
                border-radius: 6px; /* Kept consistent with the default state */
            }}
        """



    def _style_line_edit_with_text(self):
        return f"""
            QLineEdit {{
                background-color: {ui_colors['window']};
                border: 1.0px solid {ui_colors["highlight"]};
                border-radius: 6px;
            }}
        """

    def _style_line_edit_without_text(self):
        return f"""
            QLineEdit {{
                background-color: {ui_colors["window"]};
                border: 1px solid {ui_colors["disabledText"]};
                border-radius: 6px;
            }}
        """

    def _style_slider(self, color):
        return f"""
            QSlider::groove:horizontal {{
                background: {ui_colors["slider"]}; /* Track color */
                height: 2px;                               /* Reduced track height */
                border-radius: 1px;                        /* Rounded corners for the track */
                margin: 0px 0;                             /* No margin for the track */
            }}

            QSlider::handle:horizontal {{
                background: {ui_colors[color]}; /* Handle color */
                width: 7px;                             /* Reduced handle width */
                height: 12px;                            /* Reduced handle height */
                border-radius: 8px;                      /* Adjust rounded corners */
                margin: -7px 0;                          /* Adjust handle position */
                padding: 0px;                           /* Adjust the padding if needed */
            }}
            QSlider::handle:horizontal:disabled {{
                background: {ui_colors["actionHover"]}; /* Handle color when disabled */
                border-radius: 5px;                      /* Ensure rounded corners for the disabled handle */
            }}
        """

    def _style_label_enabled(self):
        return f"""
            QLabel {{
                font-size: 11px;
                color: {ui_colors['disabledText']};
                background-color: {ui_colors["groupBox"]};
            }}
        """

    def _style_label_disabled(self):
        return f"""
            QLabel {{
                font-size: 11px;
                color: {ui_colors['disabledText']};
                background-color: {ui_colors["groupBox"]};
            }}
        """

    def _style_label_title(self):
        return f"""
        QLabel {{
            font-size: 16px;
            color: {ui_colors['disabledText']};
            }}
        """


    def _style_drop_down_group_box(self, color):
        return f"""
            QGroupBox {{
                background-color: {ui_colors["groupBox"]};
                border: 1px solid {ui_colors[color]};
                border-radius: 6px;
            }}
        """

    def _style_seperator_group_box(self):
        return f"""
            QGroupBox {{
                background-color: {ui_colors["groupBox"]};
                border: 1px solid {ui_colors["rigTypeButton"]};
                border-radius: 6px;
            }}
        """

    def _style_base_info_group_box(self):
        return f"""
            QGroupBox {{
                background-color: {ui_colors["window"]};
                border-radius: 6px;
            }}
        """

    def _style_combo_box_straight_curvy(self):
        return f"""
        QComboBox {{
            font-size: 11px;
            color: {ui_colors["white"]};
            background: {ui_colors["buttonEnabled"]};       /* Background color when closed */
            border: 1px solid {ui_colors["buttonEnabled"]};  /* Border color and width */
            border-radius: 6px;                               /* Rounded corners */
            padding-left: 5px;                                    /* Optional: adjust padding as needed */
        }}

        QComboBox:disabled {{
            background-color: {ui_colors["buttonDisabled"]};  /* Background color when disabled */
            color: {ui_colors["disabledText"]};               /* Text color when disabled */
            border: 1px solid {ui_colors["buttonDisabled"]};  /* Border when disabled */
        }}

        QComboBox::drop-down {{
            width: 12px;
            border-left-width: 1px;
            border-left-color: {ui_colors["buttonEnabled"]};
            background: {ui_colors["buttonEnabled"]};
            border-left-style: solid;
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
            padding-right: 5px;
        }}

        QComboBox::drop-down:disabled {{
            background: {ui_colors["buttonDisabled"]};        /* Background color of drop-down when disabled */
            border-left-color: {ui_colors["buttonDisabled"]}; /* Border color of drop-down when disabled */
        }}

        QComboBox::down-arrow {{
        image: url("/Users/ericahetherington/Library/Preferences/Autodesk/maya/2023/prefs/scripts/autoRigger/resources/rig_utils/down_arrow_red.png");             /* Replace with path to your arrow image */
        width: 25px;  /* Adjust the width of the arrow */
        height: 25px; /* Adjust the height of the arrow */
        }}

        QComboBox QAbstractItemView {{
            color: {ui_colors["white"]};
            background-color: {ui_colors["buttonEnabled"]};
            selection-background-color: {ui_colors["actionHover"]};
            selection-color: {ui_colors["white"]};
            padding-left: 10;
            padding-right: 10;
            border-radius: 6px;
        }}
        """

    def _style_scrollable_area(self):
        return f"""
            QScrollArea {{
                border: none;
                background-color: {ui_colors['window']};
            }}
                QScrollBar:vertical, QScrollBar:horizontal {{
                border: none;
                background-color: {ui_colors['window']};
                width: 10px;
            }}
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
                background-color: {ui_colors['rigTypeButton']};
                border-radius: 0px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                border: none;
                background: transparent;
            }}
        """


    def _style_widget(self):
        return f"""
            QWidget {{
                border: none;
                background-color: {ui_colors['window']};
            }}

        """

    def _style_container_widget(self):
        return f"""
            QWidget {{
                border: none;
                background-color: {ui_colors['groupBox']};
            }}

        """







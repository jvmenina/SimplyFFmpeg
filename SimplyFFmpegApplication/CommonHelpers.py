import os
from typing import Any
from sys import stderr

custom_CSS = """
    * {
        margin: 0; padding: 0;
    }
    *:disabled {color: rgba(125,125,125,0.5);}

    QPushButton {
        padding: 0.5em 1em;
    }

    QLineEdit {
        padding: 0.2em;
        border: 1px solid gray; border-radius: 5px;
        color: palette(text);
    }
    QLineEdit:focus {border: 1px solid palette(highlight);}
    QLineEdit:read-only {color: rgba(125,125,125,0.5)}
    QPlainTextEdit {
        border: 1px solid gray; border-radius: 15px;
        padding: 0.5em;
        background: palette(base);
    }
    QGroupBox {
        border: 1px solid gray; border-radius: 15px;
        margin: 3ex 1ex 1ex 1ex; padding: 3px;
    }
    QGroupBox::title {
        background-clip: padding-box;
        subcontrol-origin: margin;
        margin-left: 0; left: 15%;
        padding: 0 0.5em; 
    }
    QGroupBox#is_executable_widget::title {
        left: 0; subcontrol-position: top center;
    }
    QComboBox {
        padding: 0.2em;
    }
"""

def print_log(*message: Any) -> None:
    print(">> (LOG) ", end="")
    print(*message, sep=" ")
    return

def print_error(*message: Any) -> None:
    print(">> (LOG) ", end="", file=stderr)
    print(*message, sep=" ", file=stderr)
    return

def is_output_path_valid(output_path: str) -> bool:
    output_directory: str
    output_file: str
    output_directory, output_file = os.path.split(output_path)
    
    output_file_name: str
    output_file_extension: str
    output_file_name, output_file_extension = os.path.splitext(output_file)
    
    return os.path.isdir(output_directory) and len(output_file_name) > 0 and len(output_file_extension) > 0
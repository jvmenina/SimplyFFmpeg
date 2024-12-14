from CommonHelpers import is_output_path_valid
from CommonWidgets import States


from PyQt6.QtCore import QMimeData, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import QFileDialog, QGridLayout, QGroupBox, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget


import os
import re


class Widget_InputOutput(QWidget):
    def __init__(self, app_state: States, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.states: States = app_state
        # self.states.valueChanged.connect(self.setOutputPathFromInput)
        self.states.extensionChanged.connect(self.fixOutputPathExtension)

        ##### Main layout
        main_layout = QVBoxLayout(self)
        # self.setLayout(main_layout)
        main_layout.setContentsMargins(0,0,0,0)

        io_widget = QGroupBox("Input and Output", self)
        io_widget_layout = QGridLayout(io_widget)
        main_layout.addWidget(io_widget)

        ##### Input layout
        self.input_field = QLineEdit(self)
        # self.setAcceptDrops(True)
        self.input_field.setAcceptDrops(True)
        self.input_field.dragEnterEvent = self.inputDragEnterEvent
        self.input_field.dropEvent = self.inputDropEvent
        io_widget_layout.addWidget(self.input_field, 0, 0)

        input_button = QPushButton("Browse Input")
        input_button.clicked.connect(self.browseInputFile)
        io_widget_layout.addWidget(input_button, 0, 1)

        ##### Output layout
        self.output_field = QLineEdit()
        io_widget_layout.addWidget(self.output_field, 1, 0)

        output_button = QPushButton("Browse Output")
        output_button.clicked.connect(self.browseOutputDirectory)
        self.output_field.textEdited.connect(self.fixOutputPathExtension)
        io_widget_layout.addWidget(output_button, 1, 1)

        ##### Checkers
        input_checker_widget = QLabel("")
        input_checker_widget.setFixedWidth(50)

        output_checker_widget = QLabel("")
        output_checker_widget.setFixedWidth(50)

        io_widget_layout.addWidget(input_checker_widget, 0, 2)
        io_widget_layout.addWidget(output_checker_widget, 1, 2)

        # Listeners
        def inputCheckerHandler() -> None:
            code: int = self.verifyInputFile()
            message: str = "OK" if (code == 1) else ("INVALID")
            input_checker_widget.setText(message)
        self.input_field.textChanged.connect(inputCheckerHandler)

        def outputCheckerHandler() -> None:
            code: int = self.verifyOutputFile()
            message: str = "OK" if (code == 1) else (
                "INVALID" if (code == 0) else ("EXISTS")
            )
            output_checker_widget.setText(message)
        self.output_field.textChanged.connect(outputCheckerHandler)

    def verifyInputFile(self) -> int:
        """
        Output Codes:
            0   -> Input file doesn't exist
            1   -> OK
        """
        input_file: str = self.input_field.text()
        if not (input_file and os.path.isfile(input_file)):
            return 0
        return 1

    def verifyOutputFile(self) -> int:
        """
        Output Codes:
            -1  -> Output file already exists
            0   -> Output path is invalid
            1   -> OK
        """
        input_file: str = self.input_field.text()
        output_file: str = self.output_field.text()
        if not is_output_path_valid(output_file) or os.path.normcase(os.path.normpath(output_file)) == os.path.normcase(os.path.normpath(input_file)):
            return 0
        if os.path.isfile(output_file):
            return -1
        return 1

    def browseInputFile(self) -> None:
        file_name: str = QFileDialog.getOpenFileName(self, "Select Input File")[0]
        if file_name:
            self.input_field.setText(file_name)
            self.setOutputPathFromInput()
        return

    def browseOutputDirectory(self) -> None:
        directory_name: str = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory_name:
            self.output_field.setText(directory_name)
            self.setOutputPathFromInput()
        return

    def fixOutputPathExtension(self) -> None:
        if not (self.input_field.text() and self.output_field.text()):
            return
        
        text: str = self.output_field.text()
        extension: str = self.states.getExtension()
        assert extension

        if re.search(fr"\.{extension}$", text) is None:
            self.output_field.setText(text + f".{extension}")
        return

    def setOutputPathFromInput(self) -> None:
        ##### Check input field, do nothing if invalid
        new_input_path: str = self.input_field.text()
        
        input_directory: str
        input_file: str
        input_directory, input_file = os.path.split(new_input_path)
        input_file_name: str = os.path.splitext(input_file)[0]
        if not os.path.isdir(input_directory):
            self.output_field.setText(None)
            return

        ##### Check output field
        #   -> If output directory is already valid, keep output directory
        #   -> Otherwise, use input directory as output directory
        # Then, replace output filename based on the input filename
        output_field: str = self.output_field.text()
        output_directory: str = output_field if os.path.isdir(output_field) else os.path.split(output_field)[0]
        extension: str = self.states.getExtension()
        final_directory: str = output_directory if os.path.isdir(output_directory) else input_directory
        self.output_field.setText(os.path.join(final_directory, f"{input_file_name}_ed.{extension}"))

        return

    ##### Input layout drag event handling
    def inputDragEnterEvent(self, a0: QDragEnterEvent | None) -> None:
        if (a0 is None):
            return

        data: QMimeData | None = a0.mimeData()
        if data is not None and data.hasUrls():
            a0.acceptProposedAction()
        else:
            a0.ignore()

    def inputDropEvent(self, a0: QDropEvent | None) -> None:
        if (a0 is None):
            return

        data: QMimeData | None = a0.mimeData()
        if data is not None and data.hasUrls():
            url: QUrl = data.urls()[0]
            if url:
                self.input_field.setText(url.toLocalFile())
                self.setOutputPathFromInput()
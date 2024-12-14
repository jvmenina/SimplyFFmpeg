from WidgetFFmpegOptions import Widget_FFmpegOptions
from WidgetInputOutput import Widget_InputOutput
from CommonHelpers import print_log
from CommonWidgets import FFmpegWorkerProcess, Preset, QRadioTextButton, States


from PyQt6.QtCore import QProcess
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import QAbstractButton, QButtonGroup, QHBoxLayout, QMainWindow, QMessageBox, QPlainTextEdit, QPushButton, QStatusBar, QVBoxLayout, QWidget


class SimpleFFmpeg(QMainWindow):
    def __init__(self) -> None:
        ##############################
        # Initializations
        ##############################
        
        ##### Initializing main window
        super().__init__()
        
        self.setWindowTitle("SimpleFFmpeg")
        self.setGeometry(300, 200, 500, 300)
        self.setStyleSheet("""
            QPushButton { 
                padding: 0.35em; 
            } 
            QLineEdit {
                padding: 0.15em;
            }
        """)
        
        ##### Initialize app-wide states
        self.states = States()

        ##############################
        # Central Widget
        ##############################

        ##### Central widget and main layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        central_layout = QVBoxLayout(central_widget)
        # central_widget.setLayout(central_layout)

        ##############################
        # IO Section
        ##############################

        self.io_widget = Widget_InputOutput(self.states, central_widget)
        central_layout.addWidget(self.io_widget)

        ##############################
        # Options Section
        ##############################

        self.options_widget = Widget_FFmpegOptions(self.states, central_widget)
        central_layout.addWidget(self.options_widget)

        ##############################
        # Command Preview Section
        ##############################

        # Note that there is no need to add a QWidget to group widgets
        preview_layout = QHBoxLayout(None)
        central_layout.addLayout(preview_layout)
        # preview_layout.setSpacing(100)

        self.command_preview = QPlainTextEdit(central_widget)
        self.command_preview.setFont(QFont("Lucida Console"))
        self.command_preview.setReadOnly(True)
        self.command_preview.ensureCursorVisible()
        # self.command_preview.setCenterOnScroll(True)
        preview_layout.addWidget(self.command_preview)

        preview_button = QPushButton("Preview Command")
        # preview_button.setStyleSheet("padding: 1em;")
        preview_button.clicked.connect(self.previewCommand)
        preview_layout.addWidget(preview_button)

        ##############################
        # Convert Section
        ##############################

        ##### Convert button
        convert_button = QPushButton("Start!")
        convert_button.clicked.connect(self.convertVideo)
        central_layout.addWidget(convert_button)

        ##### Initialize FFmpeg worker
        self.worker_process = FFmpegWorkerProcess()
        self.worker_process.readyReadStandardOutput.connect(self.onStdoutSignal)
        self.worker_process.readyReadStandardError.connect(self.onStderrSignal)
        self.worker_process.started.connect(self.onStartedSignal)
        self.worker_process.finished.connect(self.onFinishedSignal)

        ##### Console output area
        self.output_area = QPlainTextEdit()
        self.output_area.setFont(QFont("Lucida Console"))
        self.output_area.setReadOnly(True)
        self.output_area.ensureCursorVisible()
        self.output_area.setCenterOnScroll(True)
        central_layout.addWidget(self.output_area)

        ##### Status Bar
        self.setStatusBarStatus("Ready")

    def appendOutput(self, text: str | None) -> None:
        self.output_area.appendPlainText(text)
        return

    def displayError(self, text: str | None) -> None:
        QMessageBox.critical(self, "Error", text)
        return

    def displayInfo(self, text: str | None) -> None:
        QMessageBox.information(self, "Information", text)

    def compileCommand(self) -> tuple[str, list[str]] | None:
        ##### Validate IO
        input_file: str = self.io_widget.input_field.text()
        output_file: str = self.io_widget.output_field.text()

        if not (input_file and output_file):
            QMessageBox.warning(self, "Error", "Please specify both input and output files.")
            return

        input_file_validity: int = self.io_widget.verifyInputFile()
        output_file_validity: int = self.io_widget.verifyOutputFile()
        if input_file_validity != 1:
            QMessageBox.warning(self, "Error", "Please fix the input field.\nInput file doesn't exist!")
            return
        if output_file_validity != 1:
            if output_file_validity == 0:
                QMessageBox.warning(self, "Error", "Please fix the output field.\nOutput path is invalid!")
                return
            elif output_file_validity == -1 and not self.options_widget.overwrite.isChecked():
                QMessageBox.warning(self, "Error", "Please fix the output field.\nOutput file already exists!")
                return
            
        ##### Get values from options
        options: list[str] = []
        
        # Check for presets
        if self.options_widget.preset.currentIndex() != 0:
            preset: Preset = self.options_widget.preset.currentData()
            if type(preset) is not Preset or not preset:
                QMessageBox.warning(self, "Error", "FATAL ERROR! Preset data is invalid.")
                return
            options.extend(preset.getOptionsAsStr())

        # Filter helpers
        add_filter = lambda base, addition: base + ";" + addition if base != "" else addition
        
        # Video Options
        if (
            self.options_widget.preset.currentIndex() == 0 
            and self.options_widget.video_options_widget.isChecked()
        ):
            # CRF and ABR
            quality_options: QButtonGroup = self.options_widget.video_bitrate_form
            crf_radio_button: QAbstractButton | None = quality_options.button(0)
            if (
                crf_radio_button is not None
                and crf_radio_button.isChecked()
                and type(crf_radio_button) is QRadioTextButton
                and crf_radio_button.get_value() != ""
            ):
                options.extend(("-crf", crf_radio_button.get_value()))

            abr_radio_button: QAbstractButton | None = quality_options.button(1)
            if (
                abr_radio_button is not None
                and abr_radio_button.isChecked()
                and type(abr_radio_button) is QRadioTextButton
                and abr_radio_button.get_value() != ""
            ):
                options.extend(("-b:v", abr_radio_button.get_value()))

            # Video filters
            video_filters: str = ""

            fps: str = self.options_widget.fps.getValue()
            if (fps):
                video_filters = add_filter(video_filters, f"fps={fps}")

            if (video_filters):
                options.extend(("-filter_complex", f"{video_filters}"))
        elif (self.options_widget.preset.currentIndex() == 0):
            options.extend(("-c:v", "copy"))

        if (
            self.options_widget.preset.currentIndex() == 0
            and self.options_widget.audio_options_widget.isChecked()
        ):
            # Audio filters
            audio_filters: str = ""

            volume: str = self.options_widget.volume.getValue()
            if (volume):
                audio_filters = add_filter(audio_filters, f"volume={volume}")

            if (audio_filters):
                options.extend(("-filter:a", f"{audio_filters}"))
        elif (self.options_widget.preset.currentIndex() == 0):
            options.extend(("-c:a", "copy"))

        ##### Set FFmpeg command
        #   -> QProcess will automatically add quotes to arguments with spaces
        program: str = "ffmpeg"
        arguments: list[str] = [
            "-i", f"{input_file}"
        ]
        
        if self.options_widget.overwrite.isChecked():
            arguments.append("-y")
        else:
            arguments.append("-n")

        for option in options:
            if not option:
                continue
            arguments.append(option)
        arguments.append(f"{output_file}")

        return (program, arguments)

    def previewCommand(self) -> None:
        full_command: tuple[str, list[str]] | None = self.compileCommand()
        if full_command is None:
            return
        program, arguments = full_command
        self.command_preview.clear()
        self.command_preview.appendPlainText(program)
        
        prev_argument: str = ""
        for argument in arguments[:-1]:
            if argument[0] == "-" or (prev_argument and prev_argument[0] != "-"):
                self.command_preview.insertPlainText("\n    ")
            else:
                self.command_preview.insertPlainText(" ")
                
            if argument[0] == "-":
                self.command_preview.insertPlainText("[" + argument + "]")
            else:
                self.command_preview.insertPlainText(argument)
            self.command_preview.moveCursor(QTextCursor.MoveOperation.End)
            prev_argument = argument
        self.command_preview.appendPlainText("    " + arguments[-1])

    def convertVideo(self) -> None:
        ##### Check if there is an existing FFmpeg process
        if self.worker_process.processId():
            QMessageBox.critical(self, "Error", "Already active")
            return

        full_command: tuple[str, list[str]] | None = self.compileCommand()
        if full_command is None:
            return
        program, arguments = full_command

        ##### Execute FFmpeg command
        self.output_area.clear()
        print(arguments)
        self.worker_process.start(program, arguments)

        return

    def onStdoutSignal(self) -> None:
        self.appendOutput(self.worker_process.readAllStandardOutput().data().decode().strip())
        return

    def onStderrSignal(self) -> None:
        self.appendOutput(self.worker_process.readAllStandardError().data().decode().strip())
        return

    def onStartedSignal(self) -> None:
        print_log(f"Worker {id(self.worker_process)} started.")
        self.setStatusBarStatus("Working")
        return

    def onFinishedSignal(self) -> None:
        print_log(f"Worker {id(self.worker_process)} finished!")

        if self.worker_process.exitCode() == 0:
            self.displayInfo("FFmpeg task completed successfully.")
            self.setStatusBarStatus("Previous task was successful! Ready.")
        else:
            self.displayError("FFmpeg encountered an error.")
            self.setStatusBarStatus("Previous task failed! Ready.")

        self.io_widget.input_field.textChanged.emit(self.io_widget.input_field.text())
        self.io_widget.output_field.textChanged.emit(self.io_widget.output_field.text())

        return

    def setStatusBarStatus(self, status: str) -> None:
        status_bar: QStatusBar | None = self.statusBar()
        if status_bar:
            status_bar.showMessage(status)
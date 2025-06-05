from SimpleFFmpegApplication.WidgetFFmpegOptions import Widget_FFmpegOptions
from SimpleFFmpegApplication.WidgetInputOutput import Widget_InputOutput
from SimpleFFmpegApplication.CommonHelpers import print_error, print_log
from SimpleFFmpegApplication.CommonWidgets import FFmpegWorkerProcess, GlobalSignals, Preset, QRadioTextButton, SharedStates, States


from PyQt6.QtCore import QProcess
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import QAbstractButton, QButtonGroup, QGroupBox, QHBoxLayout, QMainWindow, QMessageBox, QPlainTextEdit, QPushButton, QStatusBar, QVBoxLayout, QWidget


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
        self.shared_states = SharedStates()

        ##############################
        # Central Widget
        ##############################

        ##### Central widget and main layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        central_layout = QHBoxLayout(central_widget)
        central_layout.setContentsMargins(0,0,0,0)
        
        left_central_widget = QWidget(self)
        left_central_layout = QVBoxLayout(left_central_widget)
        
        right_central_widget = QWidget(self)
        right_central_layout = QVBoxLayout(right_central_widget)
        right_central_widget.setMinimumWidth(300)
        
        central_layout.addWidget(left_central_widget)
        central_layout.addWidget(right_central_widget)

        ##############################
        # IO Section
        ##############################

        self.io_widget = Widget_InputOutput(self.shared_states, left_central_widget)
        left_central_layout.addWidget(self.io_widget)

        ##############################
        # Options Section
        ##############################

        self.options_widget = Widget_FFmpegOptions(self.shared_states, left_central_widget)
        left_central_layout.addWidget(self.options_widget)

        ##############################
        # Command Preview Section
        ##############################

        # Note that there is no need to add a QWidget to group widgets
        # preview_layout = QVBoxLayout(None)
        # right_central_layout.addLayout(preview_layout)
        # preview_layout.setSpacing(100)
        
        preview_widget = QGroupBox("Command Preview")
        preview_layout = QVBoxLayout(preview_widget)
        right_central_layout.addWidget(preview_widget)

        self.command_preview = QPlainTextEdit(left_central_widget)
        self.command_preview.setFont(QFont("Lucida Console"))
        self.command_preview.setReadOnly(True)
        self.command_preview.ensureCursorVisible()
        # self.command_preview.setCenterOnScroll(True)

        preview_button = QPushButton("Preview")
        # preview_button.setStyleSheet("padding: 1em;")
        preview_button.clicked.connect(self.previewCommand)
        
        preview_layout.addWidget(self.command_preview)
        preview_layout.addWidget(preview_button)

        ##############################
        # Convert Section
        ##############################

        ##### Convert button
        convert_button = QPushButton("Start!")
        convert_button.clicked.connect(self.convertVideo)
        # right_central_layout.addSpacing(50)

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
        # self.output_area.setCenterOnScroll(True)
        
        right_central_layout.addWidget(self.output_area)
        right_central_layout.addWidget(convert_button)

        ##### Status Bar
        self.setStatusBarStatus("Ready")

    def appendOutput(self, text: str | None) -> None:
        self.output_area.moveCursor(QTextCursor.MoveOperation.End)
        self.output_area.insertPlainText(text)
        return

    def displayCriticalError(self, text: str | None) -> None:
        QMessageBox.critical(self, "Error", text)
    
    def displayError(self, text: str | None) -> None:
        QMessageBox.warning(self, "Error", text)

    def displayInfo(self, text: str | None) -> None:
        QMessageBox.information(self, "Information", text)

    def compileCommand(self) -> tuple[str, list[str]] | None:
        states: States = States()
        
        ##### Validate IO
        input_file: str = self.io_widget.input_field.text()
        output_file: str = self.io_widget.output_field.text()

        if not (input_file and output_file):
            QMessageBox.warning(self, "Error", "Please specify both input and output files.")
            return

        input_file_validity: int = self.io_widget.verifyInputFile()
        output_file_validity: int = self.io_widget.verifyOutputFile()
        if input_file_validity != 1:
            self.displayError("Please fix the input field.\nInput file doesn't exist!")
            return
        if output_file_validity != 1:
            if output_file_validity == 0:
                self.displayError("Please fix the output field.\nOutput path is invalid!")
                return
            elif output_file_validity == -1 and not self.options_widget.overwrite.isChecked():
                self.displayError("Please fix the output field.\nOutput file already exists!")
                return
            
        states.setIO(input_file, output_file)
        
        ##### Overwrite
        if self.options_widget.overwrite.isChecked():
            states.toggleOverwrite()
        
        ##### Check for presets
        has_selected_preset: bool = self.options_widget.preset.currentIndex() != 0
        if has_selected_preset:
            preset: Preset = self.options_widget.preset.currentData()
            if type(preset) is not Preset or not preset:
                QMessageBox.warning(self, "Error", "FATAL ERROR! Preset data is invalid.")
                return
            states.setPreset(preset)
            
        ##### Seek and Duration
        seek: str = self.options_widget.seek.getValue()
        if seek:
            states.setSeek(seek)
        duration: str = self.options_widget.duration.getValue()
        if duration:
            states.setDuration(duration)
        
        ##### Get values from options
        # Video Options
        if (
            not has_selected_preset
            and not self.options_widget.copy_video.isChecked()
        ):
            # Video CRF and ABR
            crf_radio_button: QAbstractButton | None = self.options_widget.video_bitrate_form.button(0)
            if (
                crf_radio_button is not None
                and crf_radio_button.isChecked()
                and type(crf_radio_button) is QRadioTextButton
                and crf_radio_button.getValue() != ""
            ):
                states.setVideoCRF(crf_radio_button.getValue())

            abr_radio_button: QAbstractButton | None = self.options_widget.video_bitrate_form.button(1)
            if (
                abr_radio_button is not None
                and abr_radio_button.isChecked()
                and type(abr_radio_button) is QRadioTextButton
                and abr_radio_button.getValue() != ""
            ):
                states.setVideoBitrate(abr_radio_button.getValue())
                
            # Video Preset
            video_preset: str = self.options_widget.video_preset.currentData()
            states.setVideoPreset(video_preset)

            # Video filters
            fps: str = self.options_widget.fps.getValue()
            if (fps):
                states.addVideoFilter(f"fps={fps}")
                
            video_width: str = self.options_widget.video_width.getValue()
            video_height: str = self.options_widget.video_height.getValue()
            if (video_width or video_height):
                if not video_height:
                    video_height = "-2"
                if not video_width:
                    video_width = "-2"
                states.addVideoFilter(f"scale={video_width}:{video_height}")

        elif (self.options_widget.preset.currentIndex() == 0):
            states.setCopyVideo()

        # Audio Options
        if (
            not has_selected_preset
            and not self.options_widget.copy_audio.isChecked()
        ):
            audio_bitrate: str = self.options_widget.audio_bitrate.getValue()
            if (audio_bitrate):
                states.setAudioBitrate(audio_bitrate)
            volume: str = self.options_widget.volume.getValue()
            if (volume):
                states.addAudioFilter(f"volume={volume}")

        elif (self.options_widget.preset.currentIndex() == 0):
            states.setCopyAudio()

        ##### Set FFmpeg command
        return states.compileState()

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
        self.appendOutput(self.worker_process.readAllStandardOutput().data().decode())
        return

    def onStderrSignal(self) -> None:
        self.appendOutput(self.worker_process.readAllStandardError().data().decode())
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
            self.displayCriticalError("FFmpeg encountered an error.")
            self.setStatusBarStatus("Previous task failed! Ready.")

        self.io_widget.input_field.textChanged.emit(self.io_widget.input_field.text())
        self.io_widget.output_field.textChanged.emit(self.io_widget.output_field.text())

        return

    def setStatusBarStatus(self, status: str) -> None:
        status_bar: QStatusBar | None = self.statusBar()
        if status_bar:
            status_bar.showMessage(status)
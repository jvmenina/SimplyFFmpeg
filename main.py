import os, re, sys, subprocess
from PyQt6.QtGui import (
    QDragEnterEvent,
    QDropEvent,
    QFont,
)
from PyQt6.QtWidgets import (
    QAbstractButton,
    
    QApplication, 
    QMainWindow,
    QWidget,
    
    QLineEdit, 
    QPushButton, 
    QFileDialog,
    QMessageBox, 
    QPlainTextEdit, 
    
    QStatusBar, 
    
    QBoxLayout,
    QVBoxLayout, 
    QHBoxLayout,
    QGridLayout,
    
    QGroupBox,
    QButtonGroup,
    QRadioButton,
    QLabel,
)
from PyQt6.QtCore import (
    QMimeData,
    QUrl,
    
    Qt,
    QThread, 
    QProcess,
    pyqtSignal
)

class FFmpegWorkerProcess(QProcess):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        print_log(f"New worker with ID {id(self)}")

class QRadioText(QWidget):
    __radio_id__: int = -1
    
    def __init__(self, radio_name: str, radio_id: int, default: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__radio_id__ = radio_id
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        self.__radio_button__ = QRadioTextButton(self, radio_name, self)
        self.__radio_input_field__ = QLineEdit(self)
        self.__radio_input_field__.setPlaceholderText(default)
        
        main_layout.addWidget(self.__radio_button__)
        main_layout.addWidget(self.__radio_input_field__)
        
    def getRadioButton(self) -> QRadioButton:
        return self.__radio_button__
    
    def getInputField(self) -> QLineEdit:
        return self.__radio_input_field__
    
class QRadioTextButton(QRadioButton):
    parent_radio: QRadioText
    def __init__(self, parent_radio: QRadioText, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.parent_radio = parent_radio
        
    def get_value(self) -> str:
        return self.parent_radio.getInputField().text()

class Widget_InputOutput(QWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
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
        
    def browseInputFile(self) -> None:
        file_name: str = QFileDialog.getOpenFileName(self, "Select Input File")[0]
        if file_name:
            self.input_field.setText(file_name)
            self.setOutputPathFromInput(self.input_field.text())
        return

    def browseOutputDirectory(self) -> None:
        directory_name: str = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory_name:
            self.output_field.setText(directory_name)
            self.setOutputPathFromInput(self.input_field.text())
        return
    
    def fixOutputPathExtension(self) -> None:
        text: str = self.output_field.text()
        
        if re.search(r"\.mp4$", text) is None:
            self.output_field.setText(text + ".mp4")
        return
    
    def setOutputPathFromInput(self, new_input_path: str) -> None:
        ##### Check input field, do nothing if invalid
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
        
        final_directory: str = output_directory if os.path.isdir(output_directory) else input_directory
        self.output_field.setText(os.path.join(final_directory, f"{input_file_name}_ed.mp4"))
            
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
                self.setOutputPathFromInput(self.input_field.text())

class Widget_FFmpegOptions(QWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        ##### Main layout
        main_layout = QVBoxLayout(self)
        # self.setLayout(main_layout)
        main_layout.setContentsMargins(0,0,0,0)
        
        ##### Presets        
        presets_widget = QGroupBox("Presets", self)
        main_layout.addWidget(presets_widget)
        
        presets_radio_layout = QHBoxLayout(presets_widget)
        # presets_radio_layout.setContentsMargins(0,0,0,0)
        
        self.presets_form = QButtonGroup(self)
        self.enum_presets: list[str] = [
            "None",
            "Twitter"
        ]
        for idx, preset_name in enumerate(self.enum_presets):
            preset_radio_button = QRadioButton(preset_name)
            
            if idx == 0:
                preset_radio_button.setChecked(True)
            self.presets_form.addButton(preset_radio_button, idx)
            
            presets_radio_layout.addWidget(preset_radio_button)
        # self.presets_form.buttonClicked.connect(lambda x: print(x.text()))
        
        ##### Flags
        flags_widget = QGroupBox("Flags")
        main_layout.addWidget(flags_widget)
        flags_layout = QVBoxLayout(flags_widget)
        # flags_layout.setContentsMargins(0,0,0,0)
        
        # Bitrate
        quality_widget = QGroupBox("Quality")
        flags_layout.addWidget(quality_widget)
        quality_layout = QHBoxLayout(quality_widget)
        # quality_layout.setContentsMargins(0,0,0,0)
        
        self.quality_form = QButtonGroup(self)
        self.enum_quality: list[tuple[str, str]] = [
            ("CRF", "28"),
            ("ABR", "2500k")
        ]
        for idx, (quality_name, quality_default) in enumerate(self.enum_quality):
            radio_widget = QRadioText(quality_name, idx, quality_default, self)
            quality_layout.addWidget(radio_widget)
            
            if idx == 0:
                radio_widget.getRadioButton().setChecked(True)
            self.quality_form.addButton(radio_widget.getRadioButton(), idx)
            
        grp2_layout = QHBoxLayout()
        flags_layout.addLayout(grp2_layout)
        
        # FPS
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(QLabel("Framerate:"))
        self.fps = QLineEdit()
        self.fps.setPlaceholderText("60")
        fps_layout.addWidget(self.fps)
        grp2_layout.addLayout(fps_layout)
        
        # Volume
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        self.volume = QLineEdit()
        self.volume.setPlaceholderText("1.0")
        volume_layout.addWidget(self.volume)
        grp2_layout.addLayout(volume_layout)
        
        ##### Listeners
        def on_preset_toggle() -> None:
            if (self.presets_form.checkedId() == 0):
                flags_widget.setEnabled(True)
            else:
                flags_widget.setEnabled(False)
        on_preset_toggle()
        self.presets_form.buttonToggled.connect(on_preset_toggle)
        
        def on_radiotext_toggle() -> None:
            for button in self.quality_form.buttons():
                if (type(button) is not QRadioTextButton):
                    continue
                
                if (self.quality_form.button(self.quality_form.checkedId()) == button):
                    button.parent_radio.getInputField().setEnabled(True)
                    continue
                
                button.parent_radio.getInputField().setEnabled(False)
        on_radiotext_toggle()
        self.quality_form.buttonToggled.connect(on_radiotext_toggle)
        
        # self.presets_form.buttonClicked.connect(lambda: self.presets_form.button(0).setChecked(True))

class FFmpegGUI(QMainWindow):
    worker_process: QProcess
    
    def __init__(self) -> None:
        ##### Initializing main window
        super().__init__()
        self.setWindowTitle("FFmpeg GUI")
        self.setGeometry(200, 200, 600, 300)
        # self.setStyleSheet("""
        #     QPushButton { 
        #         padding: 0.5em; 
        #     } 
        #     QLineEdit {
        #         padding: 0.25em;
        #     }
        # """)
        
        ##############################
        # Central Widget
        ##############################
        
        ##### Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_layout = QVBoxLayout(central_widget)
        
        ##############################
        # IO Section
        ##############################

        self.io_widget = Widget_InputOutput(self)
        central_layout.addWidget(self.io_widget)
        
        ##############################
        # Options Section
        ##############################
        
        self.options_widget = Widget_FFmpegOptions(self)
        central_layout.addWidget(self.options_widget)

        ##############################
        # Command Preview Section
        ##############################
        
        preview_widget = QWidget()
        preview_layout = QHBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0,0,0,0)
        # preview_layout.setSpacing(100)
        central_layout.addWidget(preview_widget)
        
        self.command_preview = QPlainTextEdit(self)
        self.command_preview.setFont(QFont("Lucida Console"))
        self.command_preview.setReadOnly(True)
        self.command_preview.ensureCursorVisible()
        self.command_preview.setCenterOnScroll(True)
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
        # status_bar: QStatusBar | None = self.statusBar()
        # if status_bar:
        #     status_bar.showMessage("Ready")
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
        if not is_output_path_valid(output_file):
            QMessageBox.warning(self, "Error", "Please fix the output field.")
            return
        
        ##### Check for presets
        
        
        ##### Get values from options
        options: list[tuple[str, str]] = []
        
        # CRF and ABR
        quality_options: QButtonGroup = self.options_widget.quality_form
        crf_radio_button: QAbstractButton | None = quality_options.button(0)
        if (
            crf_radio_button is not None
            and crf_radio_button.isChecked()
            and type(crf_radio_button) is QRadioTextButton
            and crf_radio_button.get_value() != ""
        ):
            options.append(("-crf", crf_radio_button.get_value()))
            # options.append(("-crf", crf_radio_button.get_value() or self.options_widget.enum_quality[0][1]))
        abr_radio_button: QAbstractButton | None = quality_options.button(1)
        if (
            abr_radio_button is not None
            and abr_radio_button.isChecked()
            and type(abr_radio_button) is QRadioTextButton
            and abr_radio_button.get_value() != ""
        ):
            options.append(("-b:v", abr_radio_button.get_value()))
        
        # Filter helpers
        add_filter = lambda base, addition: base + ";" + addition if base != "" else addition
        
        # Video filters
        video_filters: str = ""
        
        fps: str = self.options_widget.fps.text()
        if (fps):
            video_filters = add_filter(video_filters, f"fps={fps}")
        
        if (video_filters):
            options.append(("-filter_complex", f"{video_filters}"))
            
        # Audio filters
        audio_filters: str = ""
        
        volume: str = self.options_widget.volume.text()
        if (volume):
            audio_filters = add_filter(audio_filters, f"volume={volume}")
        
        if (audio_filters):
            options.append(("-filter:a", f"{audio_filters}"))

        ##### Set FFmpeg command
        #   -> QProcess will automatically add quotes to arguments with spaces
        program: str = "ffmpeg"
        arguments: list[str] = [
            "-i", f"{input_file}",
            "-n"
        ]
        for option in options:
            arguments.extend(option)
        arguments.append(f"{output_file}")
        
        return (program, arguments)
    
    def previewCommand(self) -> None:
        full_command: tuple[str, list[str]] | None = self.compileCommand()
        if full_command is None:
            return
        program, arguments = full_command
        self.command_preview.clear()
        self.command_preview.appendPlainText(program + "   " + "   ".join(arguments))
    
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
        
        return
    
    def setStatusBarStatus(self, status: str) -> None:
        status_bar: QStatusBar | None = self.statusBar()
        if status_bar:
            status_bar.showMessage(status)

def print_log(message: str) -> None:
    print(f">> (LOG) {message}")
    return

def is_output_path_valid(output_path: str) -> bool:
    output_directory: str
    output_file: str
    output_directory, output_file = os.path.split(output_path)
    
    output_file_name: str
    output_file_extension: str
    output_file_name, output_file_extension = os.path.splitext(output_file)
    
    return os.path.isdir(output_directory) and len(output_file_name) > 0 and len(output_file_extension) > 0

def main() -> int:
    app = QApplication([])
    window = FFmpegGUI()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())

sys.exit(1)
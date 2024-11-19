import os, sys, subprocess
from PyQt6.QtWidgets import (
    QApplication, 
    QMainWindow,
    QStatusBar, 
    QVBoxLayout, 
    QHBoxLayout,
    QGridLayout,
    QLineEdit, 
    QPushButton, 
    QFileDialog,
    QMessageBox, 
    QPlainTextEdit, 
    QWidget,
)
from PyQt6.QtCore import (
    QThread, 
    QProcess,
    pyqtSignal
)

class FFmpegWorker(QThread):
    output_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, command: str) -> None:
        super().__init__()
        self.command: str = command

    def run(self) -> None:
        try:
            process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                # shell=True
            )
            
            for line in (process.stdout or [""]):
                self.output_signal.emit(line.strip())
            
            process.wait()
            
            if process.returncode != 0:
                self.error_signal.emit("FFmpeg process failed.")
            else:
                self.output_signal.emit("FFmpeg process completed successfully.")
        except Exception as e:
            self.error_signal.emit(f"Error: {e}")
            
class FFmpegWorkerProcess(QProcess):
    def __init__(self) -> None:
        super().__init__()
        print_log(f"New worker with ID {id(self)}")

class FFmpegGUI(QMainWindow):
    worker_process: QProcess
    
    def __init__(self) -> None:
        # Initializing main window
        super().__init__()
        self.setWindowTitle("FFmpeg GUI")
        # self.setGeometry(200, 200, 600, 300)
        
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_layout = QVBoxLayout(central_widget)

        # Grid layout
        input_output_layout = QGridLayout()
        central_layout.addLayout(input_output_layout)
        
        # Input layout
        self.input_field = QLineEdit()
        input_output_layout.addWidget(self.input_field, 0, 0)

        input_button = QPushButton("Browse Input")
        input_button.clicked.connect(self.browse_input_file)
        input_output_layout.addWidget(input_button, 0, 1)

        # Output layout
        self.output_field = QLineEdit()
        self.input_field.textChanged.connect(self.set_output_path_from_input)
        input_output_layout.addWidget(self.output_field, 1, 0)

        output_button = QPushButton("Browse Output")
        output_button.clicked.connect(self.browse_output_directory)
        input_output_layout.addWidget(output_button, 1, 1)

        # Convert button
        convert_button = QPushButton("Convert to MP4")
        convert_button.clicked.connect(self.convert_video)
        central_layout.addWidget(convert_button)
        
        # Initialize FFmpeg worker
        self.worker_process = FFmpegWorkerProcess()
        self.worker_process.readyReadStandardOutput.connect(self.on_stdout_signal)
        self.worker_process.readyReadStandardError.connect(self.on_stderr_signal)
        self.worker_process.started.connect(self.on_started_signal)
        self.worker_process.finished.connect(self.on_finished_signal)

        # Console output area
        self.output_area = QPlainTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.ensureCursorVisible()
        self.output_area.setCenterOnScroll(True)
        central_layout.addWidget(self.output_area)

        # Status Bar
        status_bar: QStatusBar | None = self.statusBar()
        if status_bar:
            status_bar.showMessage("Ready")
            
    def set_output_path_from_input(self, new_input_path: str) -> None:        
        input_directory: str
        input_file: str
        input_directory, input_file = os.path.split(new_input_path)
        input_file_name: str = os.path.splitext(input_file)[0]
        if not os.path.isdir(input_directory):
            self.output_field.setText(None)
            return
        
        output_field: str = self.output_field.text()
        output_directory: str = output_field if os.path.isdir(output_field) else os.path.split(output_field)[0]
        if os.path.isdir(output_directory):
            self.output_field.setText(os.path.join(output_directory, f"{input_file_name}_ed.mp4"))
        else:
            self.output_field.setText(os.path.join(input_directory, f"{input_file_name}_ed.mp4"))
            
        return

    def is_output_path_valid(self, output_path: str) -> bool:
        output_directory: str
        output_file: str
        output_directory, output_file = os.path.split(output_path)
        
        output_file_name: str
        output_file_extension: str
        output_file_name, output_file_extension = os.path.splitext(output_file)
        
        return os.path.isdir(output_directory) and len(output_file_name) > 0 and len(output_file_extension) > 0

    def browse_input_file(self) -> None:
        file_name: str = QFileDialog.getOpenFileName(self, "Select Input File")[0]
        if file_name:
            self.input_field.setText(file_name)
        return

    def browse_output_directory(self) -> None:
        directory_name: str = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory_name:
            self.output_field.setText(directory_name)
            self.set_output_path_from_input(self.input_field.text())
        return

    def append_output(self, text: str | None) -> None:
        self.output_area.appendPlainText(text)
        return

    def display_error(self, text: str | None) -> None:
        QMessageBox.critical(self, "Error", text)
        return
    
    def display_info(self, text: str | None) -> None:
        QMessageBox.information(self, "Information", text)

    def convert_video(self) -> None:
        # Check if there is an existing FFmpeg process
        if self.worker_process.processId(): 
            QMessageBox.critical(self, "Error", "Already active")
            return
        
        # Validate IO
        input_file: str = self.input_field.text()
        output_file: str = self.output_field.text()
        if not (input_file and output_file):
            QMessageBox.warning(self, "Error", "Please specify both input and output files.")
            return
        if not self.is_output_path_valid(output_file):
            QMessageBox.warning(self, "Error", "Please fix the output field.")
            return

        # Set FFmpeg command
        program: str = "ffmpeg"
        arguments: list[str] = [
            "-i", f"{input_file}",
            "-n",
            f"{output_file}"
        ]

        # Execute FFmpeg command
        self.output_area.clear()        
        self.worker_process.start(program, arguments)
        # self.worker_process.start('python', ['-um','exit','1'])
        
        return
    
    def on_stdout_signal(self) -> None:
        self.append_output(self.worker_process.readAllStandardOutput().data().decode().strip())
        return
        
    def on_stderr_signal(self) -> None:
        self.append_output(self.worker_process.readAllStandardError().data().decode().strip())
        return
    
    def on_started_signal(self) -> None:
        print_log(f"Worker {id(self.worker_process)} started.")
        return
    
    def on_finished_signal(self) -> None:
        print_log(f"Worker {id(self.worker_process)} finished!")
        
        if self.worker_process.exitCode() == 0:
            self.display_info("FFmpeg task completed successfully.")
        else:
            self.display_error("FFmpeg encountered an error.")
        
        return

def print_log(message: str) -> None:
    print(f">> (LOG) {message}")
    return

def main() -> int:
    app = QApplication([])
    window = FFmpegGUI()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
sys.exit(1)
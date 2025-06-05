from SimpleFFmpegApplication.CommonHelpers import print_error, print_log


from PyQt6.QtWidgets import (
    QWidget, 
    QHBoxLayout, 
    QLabel, 
    QLineEdit, 
    QRadioButton
)
from PyQt6.QtCore import QProcess, pyqtSignal


class Argument:
    def __init__(self, flag: str, value: str | None = None) -> None:
        # If value is None, the Argument does not take any value
        self.__flag__: str = flag
        self.__value__: str | None = value
    
    def getFlag(self) -> str:
        return self.__flag__
    def setFlag(self, flag: str) -> None:
        self.__flag__ = flag
    
    def getValue(self) -> str | None:
        return self.__value__
    def setValue(self, value: str) -> None:
        self.__value__ = value
    def appendValue(self, value: str) -> None:
        if not self.__value__:
            self.__value__ = value
            return
        self.__value__ += f",{value}"
        
    def toList(self) -> list[str]:
        if self.__value__:
            return [self.__flag__, self.__value__]
        return [self.__flag__]
    
    def __str__(self) -> str:
        string: str = self.__flag__
        if self.__value__:
            string += f" {self.__value__}"
        return string

class Preset:
    def __init__(self, title: str, extension: str, options: list[Argument]) -> None:
        self.__title__: str = title
        self.__extension__: str = extension
        self.__options__: list[Argument] = options
    
    def getTitle(self) -> str:
        return self.__title__
    def getExtension(self) -> str:
        return self.__extension__
    def getOptions(self) -> list[Argument]:
        return self.__options__
    def getOptionsAsStr(self) -> list[str]:
        options: list[str] = []
        for option in self.__options__:
            flag: str = option.getFlag()
            value: str | None = option.getValue()
            options.append(flag)
            if value:
                options.append(value)
        return options
    
    def __str__(self) -> str:
        return f"{self.__title__ } ({self.__extension__}, {[str(i) for i in self.__options__]})"

class Defaults:
    presets_list: list[Preset] = [
        Preset("None", "mp4", []),
        Preset("Twitter Video", "mp4", [
            Argument("-b:v", "2500k"),
            Argument("-filter:v", "fps=60"), 
            Argument("-c:a", "copy")
        ]),
    ]
    
    extensions_list: list[str] = [
        "mp4",
        "mp3",
        "gif",
        "jpg",
        "png",
        "webp"
    ]
    
    video_presets_list: list[str] = [
        "ultrafast",
        "superfast",
        "veryfast",
        "faster",
        "fast",
        "medium",
        "slow",
        "slower",
        "veryslow"
    ]

class GlobalSignals(QWidget):
    extensionChanged: pyqtSignal = pyqtSignal(str)
    def __init__(self) -> None:
        super().__init__()
    
    def emitExtensionChanged(self, value: str) -> None:
        self.extensionChanged.emit(value)

class SharedStates:
    def __init__(self) -> None:
        self.signals: GlobalSignals = GlobalSignals()
        
        self.extension: str = ""
        self.signals.extensionChanged.connect(self.updateExtension)
        return
    
    def updateExtension(self, newExtension: str) -> None:
        self.extension = newExtension
        return

class States(QWidget):
    def __init__(self) -> None:
        super().__init__()
        
        self.input_file: Argument | None = None
        self.output_file: Argument | None = None
        self.overwrite_flag: Argument = Argument("-n")
        self.preset: Preset | None = None
        
        # self.extension: str | None = None
        self.copy_video: Argument | None = None
        self.copy_audio: Argument | None = None
        
        self.seek: Argument | None = None
        self.duration: Argument | None = None
        
        self.video_crf: Argument | None = None
        self.video_bitrate: Argument | None = None
        self.video_preset: Argument | None = None
        self.video_filters: Argument | None = None
        
        self.audio_bitrate: Argument | None = None
        self.audio_filters: Argument | None = None
    
    def setIO(self, input_file: str, output_file: str) -> None:
        self.input_file = Argument("-i", input_file)
        self.output_file = Argument(output_file)
    def setPreset(self, preset: Preset) -> None:
        self.preset = preset
    # def setExtension(self, extension: str) -> None:
    #     self.extension = extension
    def toggleOverwrite(self) -> None:
        self.overwrite_flag.setFlag("-y")
    def setCopyVideo(self) -> None:
        self.copy_video = Argument("-c:v", "copy")
    def setCopyAudio(self) -> None:
        self.copy_audio = Argument("-c:a", "copy")
    
    def setSeek(self, seek: str) -> None:
        self.seek = Argument("-ss", seek)
    def setDuration(self, duration: str) -> None:
        self.duration = Argument("-t", duration)
        
    def setVideoCRF(self, video_crf: str) -> None:
        self.video_crf = Argument("-crf", video_crf)
    def setVideoBitrate(self, video_bitrate: str) -> None:
        self.video_bitrate = Argument("-b:v", video_bitrate)
    def setVideoPreset(self, video_preset: str) -> None:
        self.video_preset = Argument("-preset", video_preset)
    def addVideoFilter(self, video_filter: str) -> None:
        if self.video_filters is None:
            self.video_filters = Argument("-filter_complex", "")
        self.video_filters.appendValue(video_filter)
        
    def setAudioBitrate(self, audio_bitrate: str) -> None:
        self.audio_bitrate = Argument("-b:a", audio_bitrate)
    def addAudioFilter(self, audio_filter: str) -> None:
        if self.audio_filters is None:
            self.audio_filters = Argument("-filter:a", "")
        self.audio_filters.appendValue(audio_filter)
        
    # Compiler
    def compileState(self) -> tuple[str, list[str]]:
        program: str = "ffmpeg"
        arguments: list[str] = []
        
        # Input
        if not self.input_file:
            raise Exception("Missing input file value. If you're seeing this, the initial verification failed.")
        arguments.extend(self.input_file.toList())
        
        # Overwrite
        arguments.extend(self.overwrite_flag.toList())
        
        # Preset
        if self.preset:
            arguments.extend(self.preset.getOptionsAsStr())
            
        # Options (No Preset)
        if not self.preset:
            # if self.extension:
            #     arguments.append(self.extension)
            if self.copy_video:
                arguments.extend(self.copy_video.toList())
            if self.copy_audio:
                arguments.extend(self.copy_audio.toList())
            
            if self.seek:
                arguments.extend(self.seek.toList())
            if self.duration:
                arguments.extend(self.duration.toList())
        
        if not self.preset and not self.copy_video:
            if self.video_crf:
                arguments.extend(self.video_crf.toList())
            if self.video_bitrate:
                arguments.extend(self.video_bitrate.toList())
            if self.video_preset:
                arguments.extend(self.video_preset.toList())
            if self.video_filters:
                arguments.extend(self.video_filters.toList())
        
        if not self.preset and not self.copy_audio:
            if self.audio_bitrate:
                arguments.extend(self.audio_bitrate.toList())
            if self.audio_filters:
                arguments.extend(self.audio_filters.toList())
        
        # Output
        if not self.output_file:
            raise Exception("Missing output file value. If you're seeing this, the initial verification failed.")
        arguments.extend(self.output_file.toList())
        
        # Finally
        return (program, arguments)

class FFmpegWorkerProcess(QProcess):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        print_log(f"New worker with ID {id(self)}\n")
        
class QLabelledLineEdit(QWidget):
    def __init__(self, label:str, placeholder:str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        self.__label__ = QLabel(label)
        self.__input_field__ = QLineEdit(self)
        self.__input_field__.setPlaceholderText(placeholder)
        main_layout.addWidget(self.__label__)
        main_layout.addWidget(self.__input_field__)
    
    def getLabel(self) -> QLabel:
        return self.__label__
    
    def getInputField(self) -> QLineEdit:
        return self.__input_field__
    
    def getValue(self) -> str:
        return self.__input_field__.text()

class QRadioText(QWidget):
    def __init__(self, radio_name: str, radio_id: int, default: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__radio_id__: int = radio_id
        
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
    
    def getValue(self) -> str:
        return self.__radio_input_field__.text()
    
class QRadioTextButton(QRadioButton):
    def __init__(self, parent_radio: QRadioText, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__parent_radio__: QRadioText = parent_radio
        
    def getParent(self) -> QRadioText:
        return self.__parent_radio__
    def getValue(self) -> str:
        return self.__parent_radio__.getValue()
from typing import Any
from CommonHelpers import print_log


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

class States(QWidget):
    extensionChanged: pyqtSignal = pyqtSignal(str)
    __presets_list__: list[Preset] = [
        Preset("None", "mp4", []),
        Preset("Twitter Video", "mp4", [
            Argument("-b:v", "2500k"),
            Argument("-filter:v", "fps=60"), 
            Argument("-c:a", "copy")
        ]),
    ]
    
    def __init__(self) -> None:
        # Before Python 3, explicitly indicating super() arguments is necessary
        # super(States, self).__init__(*args, **kwargs)
        
        super().__init__()
        
        self.preset = Preset("", "", [])
        self.overwrite = Argument("-n")
        
        self.seek = Argument("-ss", "")
        self.duration = Argument("-t", "")
        
        self.crf = Argument("-crf", "")
        self.abr = Argument("-b:v", "")
        self.video_preset = Argument("-preset", "")
        self.video_filters = Argument("-filter_complex", "")
        
        self.audio_bitrate = Argument("-b:a", "")
        self.audio_filters = Argument("-filter:a", "")
    
    """
    # Getter-Setter Version
    @property
    def ext(self) -> str:
        return self.__output_extension__
    @ext.setter
    def a(self, ext: str) -> None:
        self.__output_extension__ = ext
        self.valueChanged.emit(ext)
    """

    def getPresetsList(self) -> list[Preset]:
        return self.__presets_list__
    def getExtension(self) -> str:
        return self.preset.getExtension()
    
    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        if (name == "preset"):
            self.extensionChanged.emit(value.getExtension())
        return 
        
    # def __getattr__(self, name: str):
    #     return self.__dict__[f"_{name}"]
    # def __getattribute__(self, name: str) -> Any:
    #     return super().__getattribute__(name)
    # def __setattr__(self, name: str, value: Any) -> None:
    #     super().__setattr__(name, value)
    #     return 

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
    __radio_id__: int
    
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
    
    def getValue(self) -> str:
        return self.__radio_input_field__.text()
    
class QRadioTextButton(QRadioButton):
    parent_radio: QRadioText
    def __init__(self, parent_radio: QRadioText, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.parent_radio = parent_radio
        
    def get_value(self) -> str:
        return self.parent_radio.getValue()
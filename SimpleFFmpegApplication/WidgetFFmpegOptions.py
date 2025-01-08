from SimpleFFmpegApplication.CommonWidgets import Defaults, Preset, QLabelledLineEdit, QRadioText, QRadioTextButton, SharedStates


from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QButtonGroup, QCheckBox, QGridLayout, QGroupBox, QHBoxLayout, QRadioButton, QVBoxLayout, QWidget, QComboBox


class Widget_FFmpegOptions(QWidget):
    def __init__(self, shared_states: SharedStates, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.shared_states: SharedStates = shared_states
        
        ##############################
        # Main Layout
        ##############################
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)

        ##############################
        # Basic Options
        ##############################
        
        basic_options_layout = QHBoxLayout(None)
        main_layout.addLayout(basic_options_layout)
        
        ##### Presets        
        presets_widget = QGroupBox("Presets", self)
        presets_layout = QHBoxLayout(presets_widget)
        basic_options_layout.addWidget(presets_widget, 1)

        self.preset = QComboBox(presets_widget)
        presets_layout.addWidget(self.preset)
        for preset in Defaults.presets_list:
            self.preset.addItem(preset.getTitle(), preset)
        
        # self.preset.currentIndexChanged.connect(lambda: self.states.preset.)
        
        # On roles: https://doc.qt.io/qt-6/qt.html#ItemDataRole-enum (Default is userdata)
        # self.presets_form.currentIndexChanged.connect(lambda: print(self.presets_form.currentData()))
        
        ##### File Extension
        extension_widget = QGroupBox("Extension", self)
        extension_layout = QHBoxLayout(extension_widget)
        basic_options_layout.addWidget(extension_widget, 1)

        self.extension = QComboBox(extension_widget)
        extension_layout.addWidget(self.extension)
        for extension in Defaults.extensions_list:
            self.extension.addItem(extension, extension)
        
        # For shared values
        self.shared_states.signals.emitExtensionChanged(str(self.extension.currentData()))
        self.extension.currentIndexChanged.connect(lambda: self.shared_states.signals.emitExtensionChanged(str(self.extension.currentData())))

        ##### Overwrite?
        overwrite_widget = QGroupBox("Overwrite?", self)
        overwrite_layout = QHBoxLayout(overwrite_widget)
        basic_options_layout.addWidget(overwrite_widget)

        self.overwrite = QCheckBox(overwrite_widget)
        overwrite_layout.addWidget(self.overwrite, 0, Qt.AlignmentFlag.AlignCenter)
        
        ##############################
        # Preset-independent Options
        ##############################
        
        preset_independent_layout = QHBoxLayout(None)
        main_layout.addLayout(preset_independent_layout)
        
        ##### Seeking and Duration
        seek_widget = QGroupBox("Seeking", self)
        seek_layout = QHBoxLayout(seek_widget)
        preset_independent_layout.addWidget(seek_widget)
        
        tooltip: list[str] = [
            'Examples:',
            '-> "55" for 55s',
            '-> "0.2" for 0.2s',
            '-> "200ms" for 200 ms',
            '-> "12:03:45" for 12h, 03m, 45s',
            '-> "23.189" for 23.189s',
        ]
        self.seek = QLabelledLineEdit("Input Seek", "00:00:00", seek_widget)
        self.seek.setToolTip("\n".join(tooltip))
        self.duration = QLabelledLineEdit("Output Duration", "00:00:00", seek_widget)
        self.duration.setToolTip("\n".join(tooltip))
        seek_layout.addWidget(self.seek)
        seek_layout.addWidget(self.duration)

        ##############################
        # FFmpeg Options -- Video
        ##############################
        
        self.video_options_widget = QGroupBox("Video Options", self)
        self.video_options_widget.setCheckable(True)
        video_options_layout = QVBoxLayout(self.video_options_widget)
        main_layout.addWidget(self.video_options_widget)

        ##### Video Quality
        video_quality_layout = QHBoxLayout(None)
        video_options_layout.addLayout(video_quality_layout)
        
        # Scaling
        scaling_widget = QGroupBox("Scaling", self.video_options_widget)
        scaling_layout = QHBoxLayout(scaling_widget)
        video_quality_layout.addWidget(scaling_widget)
        
        self.video_width = QLabelledLineEdit("Width", "", scaling_widget)
        self.video_height = QLabelledLineEdit("Height", "", scaling_widget)
        scaling_layout.addWidget(self.video_width)
        scaling_layout.addWidget(self.video_height)

        # Bitrate
        video_bitrate_widget = QGroupBox("Video Bitrate", self.video_options_widget)
        video_bitrate_layout = QHBoxLayout(video_bitrate_widget)
        video_quality_layout.addWidget(video_bitrate_widget)

        self.video_bitrate_form = QButtonGroup(self)
        enum_video_bitrate: list[tuple[str, str]] = [
            ("CRF", "28"),
            ("ABR", "2500k")
        ]
        for idx, (name, default) in enumerate(enum_video_bitrate):
            radio_widget = QRadioText(name, idx, default, video_bitrate_widget)
            video_bitrate_layout.addWidget(radio_widget)

            if idx == 0:
                radio_widget.getRadioButton().setChecked(True)
            self.video_bitrate_form.addButton(radio_widget.getRadioButton(), idx)

        # Preset
        video_preset_widget = QGroupBox("Quality Preset", self.video_options_widget)
        video_preset_layout = QHBoxLayout(video_preset_widget)
        video_quality_layout.addWidget(video_preset_widget)

        # self.video_preset = QLabelledLineEdit("Preset:", "fast", video_preset_widget)
        self.video_preset = QComboBox(self.video_options_widget)
        for idx, vp in enumerate(Defaults.video_presets_list):
            self.video_preset.addItem(vp, vp)
            if vp == "medium":
                self.video_preset.setCurrentIndex(idx)
        video_preset_layout.addWidget(self.video_preset)

        ##### Other video options
        video_misc_widget = QGroupBox("Others", self.video_options_widget)
        video_misc_layout = QHBoxLayout(video_misc_widget)
        video_options_layout.addWidget(video_misc_widget)

        # FPS
        self.fps = QLabelledLineEdit("Framerate:", "60", self.video_options_widget)
        video_misc_layout.addWidget(self.fps)

        ##############################
        # FFmpeg Options -- Audio
        ##############################
        
        self.audio_options_widget = QGroupBox("Audio Options", self)
        self.audio_options_widget.setCheckable(True)
        main_layout.addWidget(self.audio_options_widget)
        audio_options_layout = QVBoxLayout(self.audio_options_widget)

        # Audio Bitrate
        self.audio_bitrate = QLabelledLineEdit("Bitrate:", "192k", self.audio_options_widget)
        audio_options_layout.addWidget(self.audio_bitrate)
        
        # Volume
        self.volume = QLabelledLineEdit("Volume:", "1.0", self.audio_options_widget)
        audio_options_layout.addWidget(self.volume)
        
        ##############################
        # Listeners and Handlers
        ##############################
        
        def on_preset_toggle() -> None:
            preset_dependent_widgets: list[QWidget] = [
                self.extension,
                self.video_options_widget,
                self.audio_options_widget
            ]
            if (self.preset.currentIndex() == 0):
                for widget in preset_dependent_widgets:
                    widget.setEnabled(True)
            else:
                for widget in preset_dependent_widgets:
                    widget.setEnabled(False)
                
        on_preset_toggle()
        self.preset.currentIndexChanged.connect(on_preset_toggle)

        def on_bitrate_toggle() -> None:
            for button in self.video_bitrate_form.buttons():
                if (type(button) is not QRadioTextButton):
                    continue

                if (self.video_bitrate_form.button(self.video_bitrate_form.checkedId()) == button):
                    button.getParent().getInputField().setEnabled(True)
                    continue

                button.getParent().getInputField().setEnabled(False)
                
        on_bitrate_toggle()
        self.video_bitrate_form.buttonToggled.connect(on_bitrate_toggle)

        # self.presets_form.buttonClicked.connect(lambda: self.presets_form.button(0).setChecked(True))
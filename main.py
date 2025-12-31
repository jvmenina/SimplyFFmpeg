import sys


from PyQt6.QtWidgets import QApplication, QStyleFactory


from SimplyFFmpegApplication.CoreApplication import SimplyFFmpeg


def main() -> int:
    app = QApplication([])
    
    # Set default style
    if "Fusion" in QStyleFactory.keys():
        app.setStyle("Fusion")
    curr_style = app.style()
    if curr_style:
        app.setPalette(curr_style.standardPalette())
    
    # Execute
    window = SimplyFFmpeg()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())

sys.exit(1)
import sys


from PyQt6.QtWidgets import QApplication


from CoreApplication import SimpleFFmpeg


def main() -> int:
    app = QApplication([])
    window = SimpleFFmpeg()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())

sys.exit(1)
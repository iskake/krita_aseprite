from pathlib import Path

from PyQt5.QtWidgets import QFileDialog
from krita import *

from .ase_file import read_ase_file, create_ase_document

class KritaAsepriteExtension(Extension):
    def __init__(self, parent) -> None:
        super().__init__(parent)
    
    def setup(self):
        pass

    def createActions(self, window):
        action = window.createAction("openAse", "Open Aseprite file...", "tools/scripts")
        action.triggered.connect(self.open_ase_file)

    # TODO: make it actually open the file in a new document
    def open_ase_file(self):
        file = QFileDialog().getOpenFileName(caption="Open Aseprite file...", filter="Aseprite files (*.ase *.aseprite)")

        print(f"File: {file[0]}" if file[0] else "No file selected!")
        ase_file_name = file[0]

        if not ase_file_name:
            print("No aseprite file! returning...")
        else:
            ase = read_ase_file(ase_file_name)
            if ase is not None:
                print(f"read aseprite file with size {ase.header.bounds} and {ase.header.num_frames} frame(s)")
                create_ase_document(ase, Path(ase_file_name).name)

Krita.instance().addExtension(KritaAsepriteExtension(Krita.instance()))
from pathlib import Path

from PyQt5.QtWidgets import QFileDialog
from krita import *

from .ase_file import AsepriteFile, read_ase_file, load_document_from_ase

class KritaAsepriteExtension(Extension):
    # TODO: keep track of currently loaded files?
    curr_ase_files: list[AsepriteFile] = []

    def __init__(self, parent) -> None:
        super().__init__(parent)

    def setup(self):
        pass

    def createActions(self, window):
        action = window.createAction("openAse", "Open Aseprite file...", "tools/scripts")
        action.triggered.connect(self.open_ase_file)

    def open_ase_file(self):
        files,_ = QFileDialog().getOpenFileNames(caption="Open Aseprite file(s)...", filter="Aseprite files (*.ase *.aseprite)")

        if len(files) < 1:
            return

        print(f"Got {len(files)} aseprite files: {files}")
        for ase_file_name in files:
            if not ase_file_name:
                print("No aseprite file! returning...")
            else:
                ase = read_ase_file(ase_file_name)
                if ase is not None:
                    print(f"read aseprite file with size {ase.header.bounds} and {ase.header.num_frames} frame(s)")
                    load_document_from_ase(ase, Path(ase_file_name).name)

Krita.instance().addExtension(KritaAsepriteExtension(Krita.instance()))
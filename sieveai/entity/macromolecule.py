from .molecule import Molecule

class MacroMolecule(Molecule):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

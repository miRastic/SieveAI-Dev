from .molecule import Molecule

class Compound(Molecule):
  def __init__(self, *args, **kwargs):
    _defaults = {
      'mol_cat': 'compound',
    }
    _defaults.update(kwargs)
    super().__init__(*args, **_defaults)

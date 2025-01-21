from .base import MoleculeBase

class Molecule(MoleculeBase):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    _mol_id = kwargs.get("mol_id", args[0] if len(args) > 0 else 'Unknown-XXX')
    _mol_paths = kwargs.get("mol_paths", args[1] if len(args) > 1 else [])

    self['mol_id'] = _mol_id

    _mp = None
    for _mp in _mol_paths:
      self.formats[_mp.suffix].mol_path = _mp
      self.formats[_mp.suffix].mol_hash = _mp.hash

    # prefer .pdb or set first path as mol_path
    _ext = '.pdb'

    if not _ext in self.formats:
      _ext = list(self.formats.keys())[0]

    self['mol_path'] = self.formats[_ext].mol_path

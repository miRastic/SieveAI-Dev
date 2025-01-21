from ..entity import Compound, MacroMolecule
from Bio.PDB import PDBParser
from rdkit import Chem

class Structures():
  mol_formats = {
    '.pdb': 'PDB',
    '.pdbqt': 'PDBQT',
    '.sdf': 'SDF',
    # '.fasta': 'FASTA',
    # '.fa': 'FASTA',
    # '.mol2': 'MOL2',
    # '.smi': 'MOL2',
  }

  mol_type = None

  PDB_AA = {"ALA","ARG","ASN","ASP","CYS","GLN","GLU","HIS","ILE","LEU","LYS","MET","PHE","PRO","PYL","SEC","SER","THR","TRP","TYR","VAL","DAL","DAR","DSG","DAS","DCY","DGN","DGL","DHI","DIL","DLE","DLY","MED","DPN","DPR","DSN","DTH","DTR","DTY","DVA","UNK","UNL"}

  PDB_DNT = {"A","C","G","I","U","DA","DC","DG","DI","DT","DU","N"}
  PDB_RNT = {"A","C","G","I","U","N","5MU"}

  IUPAC_maps = {
        'protein': [
            ("A", "Ala", "Alanine"),
            ("C", "Cys", "Cysteine"),
            ("D", "Asp", "Aspartic Acid"),
            ("E", "Glu", "Glutamic Acid"),
            ("F", "Phe", "Phenylalanine"),
            ("G", "Gly", "Glycine"),
            ("H", "His", "Histidine"),
            ("I", "Ile", "Isoleucine"),
            ("K", "Lys", "Lysine"),
            ("L", "Leu", "Leucine"),
            ("M", "Met", "Methionine"),
            ("N", "Asn", "Asparagine"),
            ("P", "Pro", "Proline"),
            ("Q", "Gln", "Glutamine"),
            ("R", "Arg", "Arginine"),
            ("S", "Ser", "Serine"),
            ("T", "Thr", "Threonine"),
            ("V", "Val", "Valine"),
            ("W", "Trp", "Tryptophan"),
            ("Y", "Tyr", "Tyrosine")
          ],
        'rna': [
            ("A", "Adenine"),
            ("C", "Cytosine"),
            ("G", "Guanine"),
            ("U", "Uracil"),
            ("R", "A or G"),
            ("Y", "C or T"),
            ("S", "G or C"),
            ("W", "A or T"),
            ("K", "G or T"),
            ("M", "A or C"),
            ("B", "C or G or T"),
            ("D", "A or G or T"),
            ("H", "A or C or T"),
            ("V", "A or C or G"),
            ("N", "any base"),
            (".", "gap"),
            ("-", "gap"),
         ],
        'dna': [
              ("A", "Adenine"),
              ("C", "Cytosine"),
              ("G", "Guanine"),
              ("T", "Thymine"),
              ("R", "A or G"),
              ("Y", "C or T"),
              ("S", "G or C"),
              ("W", "A or T"),
              ("K", "G or T"),
              ("M", "A or C"),
              ("B", "C or G or T"),
              ("D", "A or G or T"),
              ("H", "A or C or T"),
              ("V", "A or C or G"),
              ("N", "any base"),
              (".", "gap"),
              ("-", "gap"),
            ]
      }

  def __init__(self, *args, **kwargs):
    self.path_molecules = kwargs.get('path_molecules', args[0] if len(args) > 0 else None)
    self.mol_categories = kwargs.get('mol_categories', args[1] if len(args) > 1 else [])

    if isinstance(self.mol_categories, (str)):
      self.mol_categories = [self.mol_categories]

    self.molecules = {}

    self._discover_molecules()

  def _discover_molecules(self):
    _mol_types = set(self.mol_categories) & {'rna', 'dna', 'protein', 'macromolecule'}
    self.mol_type = MacroMolecule if len(_mol_types) > 0 else Compound

    if not self.path_molecules.exists():
      return

    _file_stems = {_f.stem for _f in self.path_molecules.files}
    for _mol_id in _file_stems:
      _molecules = list(self.path_molecules.search(f"{_mol_id}.*"))
      self.molecules[_mol_id] = self.mol_type(_mol_id, _molecules)

  def get_mol_as_pdb(self, *args, **kwargs):
    _path = kwargs.get('path', args[0] if len(args[0]) > 0 else None)

    if _path.exists():
      _pr = PDBParser()
      _structure = _pr.get_structure(_path.stem, _path)
      for _model in _structure:
        for _chain in _model:
          _heter_or_water_field = set(map(lambda _x: _x.id[0], _chain.get_residues()))
          if "".join(_heter_or_water_field) == " " or " " in _heter_or_water_field:
              _resnames = set(map(lambda _x: _x.resname, _chain.get_residues()))
              if len(_resnames & self.PDB_AA) > 0:
                return 'protein'
              elif len(_resnames & self.PDB_RNT) > 0:
                return 'rna'
              elif len(_resnames & self.PDB_DNT) > 0:
                return 'dna'
              else:
                return 'macromolecule'
          elif 'W' in _heter_or_water_field:
            return 'water'
          else: # "H", "H_CL"
            return 'compound'

    return 'molecule'

  def get_mol_as_sdf(self, *args, **kwargs):
    _path = kwargs.get('path', args[0] if len(args[0]) > 0 else None)
    if _path.exists():
      _supp = Chem.SDMolSupplier(_path)
      for _mol in _supp:
          if _mol is not None:
              return "compound"

    return 'unknown'

  def set_mol_categories(self):
    for _mol_id, _mol_obj in self.molecules.items():
      if '.pdb' in _mol_obj.formats:
        self.molecules[_mol_id]['mol_category'] = self.get_mol_as_pdb(_mol_obj.formats['.pdb'].mol_path)

      if '.sdf' in _mol_obj.formats:
        self.molecules[_mol_id]['mol_category'] = self.get_mol_as_sdf(_mol_obj.formats['.pdb'].mol_path)

  def __repr__(self, *args, **kwargs):
    return f"""N={len(self.molecules)} {*self.mol_categories,} structures from {self.path_molecules}."""

  def __getitem__(self, *args, **kwargs):
    _first_key = list(self.molecules.keys())[0] if len(self.molecules.keys()) > 0 else None
    _key = kwargs.get('key', args[0] if len(args) > 0 else _first_key)
    return self.molecules.get(_key)

  def __iter__(self, *args, **kwargs):
    for _mol_id, _mol_obj in self.molecules.items():
      yield (_mol_id, _mol_obj)

  def __len__(self):
    return len(self.molecules.keys())

  len = __len__

  def generic_converter(self, *args, **kwargs):
    path_source = kwargs.get('path_source', args[0] if len(args) > 0 else None)
    path_target = kwargs.get('path_target', args[1] if len(args) > 1 else None)
    ext_source = kwargs.get('ext_source', args[2] if len(args) > 2 else None)
    ext_target = kwargs.get('ext_target', args[3] if len(args) > 3 else None)

    print(path_source, ext_source, path_target, ext_target)
    return path_target

  def set_mol_attribute(self, attr_key='attr', method=None) -> None:
    if not callable(method):
      return
    for _mol_id, _mol_obj in self.items:
      self[_mol_id][attr_key] = method(_mol_obj)

  def set_format(self, ext='.pdbqt', mol_id=None, converter=None, **kwargs) -> None:

    ext = str(ext)
    ext = f".{ext}" if not '.' in ext else ext

    _conversion_method_maps = {
      '.pdbqt': self.generic_converter,
    }

    _method = converter if not converter is None else _conversion_method_maps.get(ext, self.generic_converter)

    if not callable(_method):
      return False

    _items = []
    if mol_id:
      _items.append((mol_id, self[mol_id]))
    else:
      _items =  self.items

    for _mol_id, _mol_obj in _items:
      if ext in _mol_obj.formats:
        continue

      _target_path = _mol_obj.mol_path.with_suffix(ext)
      self[_mol_id].formats[ext].mol_path = _target_path

      _target_path.parents[0].validate()

      _method(_mol_obj.mol_path, _target_path,
              _mol_obj.mol_path.suffix.strip('.'), ext, **kwargs)

      if _target_path.exists():
        self[_mol_id].formats[ext].mol_hash = _target_path.hash

    return True

  @property
  def items(self):
    return list(self.molecules.items())

  def keys(self):
    return list(self.molecules.keys())

  @property
  def ids(self):
    return self.keys()

  mol_ids = ids

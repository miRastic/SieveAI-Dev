
from .base import PluginBase

class StructureSync(PluginBase):
  is_ready = False
  plugin_name = "Default Molecular StructureSync"
  plugin_uid = "StructureSync"
  process = ['sync']
  url = None

  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)

    self.map_fetcher = {
        'pubchem': self.fetch_pubchem,
        'kegg': self.fetch_kegg,
        'pdb': self.fetch_pdbs,
        'drugbank': self.fetch_drugbank,
        'uniprot': self.fetch_uniprot,
    }

  def fetch_pubchem(self, *args, **kwargs):
    self._re_pubchem_cid = self.re_compile(r'^[0-9]$')

    _cids = map(lambda _x: self.digit_only(_x), self.iterate(args))

    _storage_path = kwargs.get('storage', (self.SETTINGS.user.path_base / 'unknown_molecules').validate())

    _dim = '3d'
    for _cid in _cids:
      _sdf_path = _storage_path / f"{_cid}.sdf"
      if not _sdf_path.exists():
        self.download_content(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{_cid}/SDF?record_type={_dim}", _sdf_path)
        self.sleep_random(0.5, 3)

  def fetch_pdbs(self, *args, **kwargs):
    self._re_pdbid = self.re_compile(r'^[a-zA-Z0-9]{4}$')

    # Check for PDB Model, Chain, or Residue Sequences
    # Should it done with ChimeraX?
    # Check for missing or incomplete residues

    _pdb_ids = filter(lambda _x: bool(self._re_pdbid.match(str(_x))), self.iterate(args))
    _storage_path = kwargs.get('storage', (self.SETTINGS.user.path_base / 'unknown_molecules').validate())
    for _pdb_id in _pdb_ids:
      _pdb_file_path = _storage_path / f"{_pdb_id}.pdb"
      if not _pdb_file_path.exists():
        self.get_file_content(f"https://files.rcsb.org/download/{_pdb_id}.pdb", _pdb_file_path)

  def fetch_drugbank(self, *args, **kwargs):
    """WIP"""

  def fetch_uniprot(self, *args, **kwargs):
    """WIP"""

  def fetch_kegg(self, *args, **kwargs):
    """WIP"""


  def _parse_identifiers(self, _file_path):
      _x = self.split_guess(_file_path.stem, ['.'])
      _mol_group, _db, *_ = _x
      _identifiers = filter(len, self.split_guess(_file_path.read()))

      _storage_path = self.SETTINGS.user[f"path_{_mol_group}"].validate()
      # Fetch molecule/sync in background and proceed further
      self.map_fetcher[str(_db).lower()](*_identifiers, storage=_storage_path)

  def _check_text_file_input(self):
    _ligand_lists = list(map(self._parse_identifiers, self.path_base.search('ligand*.*.txt')))
    _receptor_lists = list(map(self._parse_identifiers, self.path_base.search('receptor*.*.txt')))

  # API Methods
  def setup(self, *args, **kwargs):
    self.update_attributes(self, kwargs)

  def boot(self, *args, **kwargs):
    self.log_debug('StructureSync was initiated...')
    self._check_text_file_input()

  def _restore_progress(self, *args, **kwargs): pass

  def run(self, *args, **kwargs): pass

  def shutdown(self, *args, **kwargs): pass

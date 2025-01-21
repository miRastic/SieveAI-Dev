from vmd import molecule as VMDMol, measure as Measure, atomsel as AtomSel
from ..process.analysis import PluginAnalysisBase

class VMDPython(PluginAnalysisBase):
  is_ready = False
  plugin_name = "VMD Python"
  plugin_uid = "VMDPython"
  plugin_version = "1.0"
  assignments = ['analysis']
  current_assignment = None
  url = "https://vmd.robinbetz.com/"
  _matrix_columns = ['distance',
                   'SASA_1', 'SASA_2', 'Contact_1', 'Contact_2',
                   'HBond_1_don', 'HBond_2_acc', 'HBond_12_proton',
                   'HBond_2_don', 'HBond_1_acc', 'HBond_21_proton',
                   ]

  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)
    self.require('math', 'Math')

  def parse_molecule(self, mol_path, mol_type="pdb"):
    _mol_id = VMDMol.load(mol_type, str(mol_path))
    return _mol_id

  def get_atom_sel(self, query, mol_id):
    _atoms = AtomSel(query, mol_id)
    return _atoms

  def get_pdb_structure_df(self, atom_sel):
    *_atoms_records, = zip(atom_sel.name, atom_sel.type, atom_sel.index, atom_sel.serial, atom_sel.mass, atom_sel.atomicnumber, atom_sel.element, atom_sel.altloc, atom_sel.insertion, atom_sel.numbonds,
                       atom_sel.beta, atom_sel.occupancy, atom_sel.charge, atom_sel.radius, atom_sel.helix, atom_sel.alpha_helix, atom_sel.helix_3_10, atom_sel.pi_helix, atom_sel.beta_sheet, atom_sel.extended_beta, atom_sel.bridge_beta, atom_sel.turn, atom_sel.coil, atom_sel.structure, atom_sel.pucker,
                       atom_sel.residue, atom_sel.resid, atom_sel.resname, atom_sel.chain, atom_sel.segname, atom_sel.segid, atom_sel.fragment, atom_sel.pfrag, atom_sel.nfrag, atom_sel.phi, atom_sel.psi, atom_sel.backbone, atom_sel.sidechain, atom_sel.protein, atom_sel.nucleic, atom_sel.water, atom_sel.waters, atom_sel.vmd_fast_hydrogen,
                       atom_sel.x,atom_sel.y,atom_sel.z,atom_sel.vx,atom_sel.vy,atom_sel.vz,atom_sel.ufx,atom_sel.ufy,atom_sel.ufz)
    _cols = ["name", "type", "index", "serial", "mass", "atomicnumber", "element", "altloc", "insertion", "numbonds", "beta", "occupancy", "charge", "radius", "helix", "alpha_helix", "helix_3_10", "pi_helix", "beta_sheet", "extended_beta", "bridge_beta", "turn", "coil", "structure", "pucker", "residue", "resid", "resname", "chain", "segname", "segid", "fragment", "pfrag", "nfrag", "phi", "psi", "backbone", "sidechain", "protein", "nucleic", "water_or_waters", "waters", "vmd_fast_hydrogen", "x", "y", "z", "vx", "vy", "vz", "ufx", "ufy", "ufz"]
    _df = self.DF(_atoms_records, columns=_cols)
    return _df

  def get_interaction_matrix(self, _set1, _set2):
    _sasa1, _sasa2 = _set1.sasa(1.2), _set2.sasa(1.2)

    try:
      _dist = self.Math.dist(_set1.center(), _set2.center())
    except ValueError as _e:
      _dist = -999

    _contact1, _contact2 = _set1.contacts(_set2, cutoff=3.5)

    _hb1_a, _hb2_d, _hd12_p = _set1.hbonds(cutoff=3, maxangle=100, acceptor=_set2)
    _hb1_d, _hb2_a, _hd21_p = _set2.hbonds(cutoff=3, maxangle=100, acceptor=_set1)

    return (_dist, _sasa1, _sasa2, _contact1, _contact2, _hb1_a, _hb2_d, _hd12_p, _hb1_d, _hb2_a, _hd21_p)

  def get_interactions(self, _rec_obj, _lig_obj):
    _con_mat = None

    if all([len(_rec_obj) > 0, len(_lig_obj) > 0]):
      _con_mat = self.get_interaction_matrix(_rec_obj, _lig_obj)
      _con_mat = dict(zip(self._matrix_columns, _con_mat))

      _rec_df = self.get_pdb_structure_df(_rec_obj)
      _lig_df = self.get_pdb_structure_df(_lig_obj)

      _c1 = _con_mat['Contact_1']
      if len(_c1) > 0:
        _c1_df = _rec_df[_rec_df['index'].isin(_c1)]
        _c1_list = _c1_df.resname +":"+_c1_df.resid.astype(str)
        _c1 = list(_c1_list.unique())

      _c2 = _con_mat['Contact_2']
      if len(_c2) > 0:
        _c2_df = _lig_df[_lig_df['index'].isin(_c2)]
        _c2_list = _c2_df.resname +":"+_c2_df.resid.astype(str)
        _c2 = list(_c2_list.unique())

      _h1d = _con_mat['HBond_1_don']
      if len(_h1d) > 0:
        _h1d_df = _rec_df[_rec_df['index'].isin(_h1d)]
        _h1d_list = _h1d_df.resname +":"+_h1d_df.resid.astype(str)
        _h1d = list(_h1d_list.unique())

      _h2d = _con_mat['HBond_2_don']
      if len(_h2d) > 0:
        _h2d_df = _lig_df[_lig_df['index'].isin(_h2d)]
        _h2d_list = _h2d_df.resname +":"+_h2d_df.resid.astype(str)
        _h2d = list(_h2d_list.unique())

      _h1a = _con_mat['HBond_1_acc']
      if len(_h1a) > 0:
        _h1a_df = _rec_df[_rec_df['index'].isin(_h1a)]
        _h1a_list = _h1a_df.resname +":"+_h1a_df.resid.astype(str)
        _h1a = list(_h1a_list.unique())

      _h2a = _con_mat['HBond_2_acc']
      if len(_h2a) > 0:
        _h2a_df = _lig_df[_lig_df['index'].isin(_h2a)]
        _h2a_list = _h2a_df.resname +":"+_h2a_df.resid.astype(str)
        _h2a = list(_h2a_list.unique())

      _con_mat['Contact_1'] = _c1
      _con_mat['Contact_2'] = _c2
      _con_mat['HBond_1_don'] = _h1d
      _con_mat['HBond_2_don'] = _h2d
      _con_mat['HBond_1_acc'] = _h1a
      _con_mat['HBond_2_acc'] = _h2a

    return _con_mat


  def setup(self, *args, **kwargs):
    self.update_attributes(self, kwargs)

  def boot(self, *args, **kwargs):
    self.log_debug('VMDPYTHON_01: Boot method directly controlled by docking plugin.')
    return self

  def run(self, *args, **kwargs):
    self.log_debug('VMDPYTHON_02: Run method directly controlled by docking plugin.')
    return self

  def shutdown(self, *args, **kwargs):
    self.log_debug('VMDPYTHON_03: Shutdown method directly controlled by docking plugin.')
    return self

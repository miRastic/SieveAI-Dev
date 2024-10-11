
from ..plug import StepManager, DictConfig
from ..managers import Structures
from ..managers.plugin import PluginManager
from .base import PluginBase

from Bio.PDB import PDBParser
from Bio.PDB.PDBExceptions import PDBConstructionWarning
import warnings as WARNINGS

# Python binding for AutoDock VINA
from vina import Vina as VinaPy

"""
ToDo:
  Clean PDB files
  Fix alternate occupancy along with residue name for correct PDBQT coordinates
  * https://www.cgl.ucsf.edu/chimerax/docs/user/commands/altlocs.html
  * alt list; alt clean;

"""

class Vina(PluginBase):
  is_ready = False
  plugin_name = "AutoDock VINA"
  plugin_uid = "Vina123"
  process = ['docking']
  url = "https://autodock-vina.readthedocs.io/en/latest/docking_python.html"

  Vina_config = None

  _max_conformers = 3

  path_vina_exe = None

  def __init__(self, *args, **kwargs):
    WARNINGS.simplefilter('ignore', PDBConstructionWarning)
    super().__init__(**kwargs)

  def boot(self, *args, **kwargs) -> None:
    self.update_attributes(self, kwargs)

    self.path_plugin_res = (self.path_base / 'docking' / self.plugin_uid).validate().rel_path()
    self.path_pkl_molecules = (self.path_base / 'docking' / self.plugin_uid).with_suffix('.Structures.sob').rel_path()
    self.path_pkl_progress = (self.path_base / 'docking' / self.plugin_uid).with_suffix('.config.sob').rel_path()
    self.path_excel_results = (self.path_base / self.plugin_uid ).with_suffix('.Results.xlsx').rel_path()

    self.path_vina_exe = 'vina' # self.which('vina')

    self.require('re', 'RegEx')
    self.re_contacts = self.RegEx.compile(f"(\d+) contacts")

    self._restore_progress()

    self._set_defualt_config()

    self._steps_map_methods = {
      "init": self._prepare_molecules,
      "config": self._write_receptor_vina_config,
      "dock": self._run_docking,
      # "dock": self._run_api_docking,
      "analyse": self._run_analysis,
      "final": self._finalise_complex,
    }

    self._step_sequence = tuple(self._steps_map_methods.keys())

    if not self.path_pkl_molecules.exists():
      self.log_debug('Running for the first time.')
      self.Receptors = Structures(self.SETTINGS.user.path_receptors, ['protein', 'dna', 'rna'])
      self.Ligands = Structures(self.SETTINGS.user.path_ligands, 'compound')
      self.log_debug('Storing Molecules')
      self._update_progress()

    if not self.path_pkl_progress.exists():
      self.Complexes = self.ObjDict()

  def _restore_progress(self, *args, **kwargs):
    if self.path_pkl_progress.exists():
      _ci = self.unpickle(self.path_pkl_progress)
      self.Complexes = _ci

    if self.path_pkl_molecules.exists():
      self.Receptors, self.Ligands = self.unpickle(self.path_pkl_molecules)

  def _update_progress(self, *args, **kwargs):
    if hasattr(self, 'Complexes'):
      self.pickle(self.path_pkl_progress, self.Complexes)

    if hasattr(self, 'Receptors') and hasattr(self, 'Ligands'):
      self.pickle(self.path_pkl_molecules, (self.Receptors, self.Ligands))

  def _set_defualt_config(self):

    self.Vina_config = DictConfig()

    self.Vina_config.default = {
        "exhaustiveness": 16,
        "verbosity": 2,
        "center_x": None,
        "center_y": None,
        "center_z": None,
        "size_x": None,
        "size_y": None,
        "size_z": None,
        "out": None,
        "cpu": None,
        "log": None,
        "seed": 41103333,
        "num_modes": 10,
      }

    self.Vina_config.other.spacing = 1
    self.Vina_config.other.residues = []

    self.Vina_config.energy_range = 3

    self.Vina_config.allowed_keys = ["flex", "receptor", "ligand",
                  "center_x", "center_y", "center_z",
                  "size_x", "size_y", "size_z",
                  "out", "log",
                  "cpu", "verbosity", # "seed",
                  "exhaustiveness", "num_modes", "energy_range"]

  def _run_api_docking(self, cuid):
    _vna = VinaPy(sf_name='vina')
    _cuid_c = self.Complexes[cuid]
    _vna.set_receptor(str(_cuid_c.path_receptor))

    _vna.set_ligand_from_file(str(_cuid_c.path_ligand))
    _vna.compute_vina_maps(center=_cuid_c.center, box_size=_cuid_c.box_size)

    # Score the current pose
    energy = _vna.score()
    print('Score before minimization: %.3f (kcal/mol)' % energy[0])

    # Minimized locally the current pose
    energy_minimized = _vna.optimize()
    print('Score after minimization : %.3f (kcal/mol)' % energy_minimized[0])
    _vna.write_pose(str(_cuid_c.path_ligand).with_suffix('.min.pdbqt'), overwrite=True)

    # Dock the ligand
    _vna.dock(exhaustiveness=32, n_poses=20)
    _vna.write_poses(str(_cuid_c.path_out), n_poses=5, overwrite=True)

  def _run_docking(self, cuid) -> None:
    """Runs vina command."""
    _cuid_c = self.Complexes[cuid]

    if _cuid_c.path_out.exists():
      self.log_debug(f'Vina result for {cuid} exists. Returning...')
      return

    _config = {
            # "--cpu": 1,
            "--receptor": _cuid_c.path_receptor.resolve(),
            "--ligand": _cuid_c.path_ligand.resolve(),
            "--config": _cuid_c.path_vina_config.resolve(),
            "--out": _cuid_c.path_out.resolve(),
            # "--verbosity": self.Vina_config.default.get('verbosity', 2),
            "cwd": _cuid_c.path_docking.resolve(),
            # ">": _cuid_c.path_score.resolve() # from command line to file
          }
    _result = self.cmd_run(self.path_vina_exe, **_config)
    _cuid_c.path_score.write_text(_result)

  _score_headers = ["mode", "affinity", "rmsd_lb", "rmsd_ub"]

  def _run_analysis(self, cuid):
    _cuid_c = self.Complexes[cuid]

    _cuid_c.path_cxc_cmd = (_cuid_c.path_docking / 'analysis.cxc').rel_path()

    if not _cuid_c.path_score.exists():
      return

    _score = list(_cuid_c.path_score.readlines())
    _score_flag = False
    _score_records = []
    for _res_line in _score:
      if _score_flag and _res_line.startswith(" "):
          _record = str(_res_line).split()
          _record = [r.strip() for r in _record]
          _score_records.append(_record)

      if not _score_flag and _res_line.startswith("-----+------------+----------+----------"):
        _score_flag = True

    _df_score = self.DF(_score_records, columns=self._score_headers)

    _models = _df_score['mode'].tolist()
    _CX =  self.SETTINGS.plugin_refs.analysis.chimerax()
    _file_template_cxc_contacts = 'CXC-Result-Model-%s.contacts.txt'
    _file_template_cxc_hbonds = 'CXC-Result-Model-%s.hbonds.txt'

    if _cuid_c.path_cxc_cmd.exists():
      self.log_debug(f'ChimeraX analysis file for {cuid} exists, skipping CXC analysis...')
    else:
      _complex_commads = [
        f"close;"
        f"set bgColor white; open {_cuid_c.path_receptor.resolve()}; wait; hide surfaces; hide atoms; show cartoons; wait;"
        "addh;",
        "~sel;",
        "wait;",
        f"open {_cuid_c.path_out.resolve()}; wait;",
      ]

      for _model_id in _models:
        _path_contacts = (_cuid_c.path_docking / (_file_template_cxc_contacts % _model_id)).resolve()

        if _path_contacts.exists(): continue

        _complex_commads.extend([
          f"# MODEL-NO-{_model_id}",
          "hide #!2.1-%s target m;" % (len(_models)),
          f"show #!2.{_model_id} models;",
          f"view;",
          f"sel #!2.{_model_id};", # Select the model
          f"contacts (#1 & ~hbonds) restrict sel radius 0.05 log t saveFile {_path_contacts};",
          f"wait;",
          f"hb #1 restrict sel reveal t show t select t radius 0.05 log t saveFile {(_cuid_c.path_docking / (_file_template_cxc_hbonds % _model_id)).resolve()};",
          f"wait;",
          "label sel residues text {0.name}-{0.number} height 1.5 offset -2,0.25,0.25 bgColor #00000099 color white;",
          f"~sel;",
          # f"save {self.path_analysis}/{_comp}--{_model_id}.complex.png width 1200 height 838 supersample 4 transparentBackground true;",
          f"sel #!2.{_model_id};", # Select the model
          f"view sel;",
          f"~sel;",
          # f"save {self.path_analysis}/{_comp}--{_model_id}.ligand.png width 1200 height 838 supersample 4 transparentBackground true;",
          f"turn x 45;",
          # f"save {self.path_analysis}/{_comp}--{_model_id}.T45.ligand.png width 1200 height 838 supersample 4 transparentBackground true;",
          f"\n",
        ])

      _complex_commads.extend([
          f"exit;",
        ])

      _cuid_c.path_cxc_cmd.write_text("\n".join(_complex_commads))
      _CX.exe_cxc_file(_cuid_c.path_cxc_cmd.resolve())

    _summary = []
    for _model_id in _models:
      _contacts_df = _CX.parse_contacts((_cuid_c.path_docking / (_file_template_cxc_contacts % _model_id)).resolve())
      _hbonds_df = _CX.parse_hbonds((_cuid_c.path_docking / (_file_template_cxc_hbonds % _model_id)).resolve())

      self.Complexes[cuid][f'Model_{_model_id}'].contacts = _contacts_df
      self.Complexes[cuid][f'Model_{_model_id}'].hbonds = _hbonds_df

      _contacts, _hbonds = [], []
      NoneType = type(None)
      if not isinstance(_contacts_df, NoneType):
        _contacts = _contacts_df.copy()
        _contacts["residues"] =  _contacts["atom1__resname"].astype(str) + ":" + _contacts["atom1__resid"].astype(str)
        _contacts = _contacts["residues"].tolist()

      _len_contacts = len(_contacts)
      _contacts = ",".join(_contacts)

      if not isinstance(_hbonds_df, NoneType):
        _hbonds = _hbonds_df.copy()
        _hbonds["residues"] =  _hbonds["donor__resname"].astype(str) + ":" + _hbonds["donor__resid"].astype(str)
        _hbonds = _hbonds["residues"].tolist()

      _len_hbonds = len(_hbonds)
      _hbonds = ",".join(_hbonds)

      _summary.append({
        'mode': _model_id,
        'total_contacts': _len_contacts,
        'total_hbonds': _len_hbonds,
        'contacts': _contacts,
        'hbonds': _hbonds,
      })

    if len(_summary) > 0:
      _df_summary = self.DF(_summary)
      _df_score = self.PD.merge(_df_score, _df_summary, on='mode', how='outer')
      # _df_score.columns = ['Conformer ID', 'VINA Score', 'RMSD LB', 'RMSD UB', 'Total Contacts', 'Total Hbonds', 'Contacts', 'Hbonds']
      self.Complexes[cuid].vina_results = _df_score

  def _prepare_molecules(self, cuid):
    return cuid

  def _finalise_complex(self, cuid):
    return cuid

  def _process_complex(self, cuid) -> None:
    if not cuid in self.Complexes:
      return

    for _step in self.Complexes[cuid].step:
      if _step in self.Complexes[cuid].steps_completed:
        continue

      _step = self.Complexes[cuid].step._current

      if not self.Complexes[cuid].step.is_last:
        self.log_debug(f"{cuid}:: Step: {_step}")
      else:
        self.log_debug(f"{cuid}:: Last Step: {_step}")

      self._steps_map_methods[_step](cuid)
      self.Complexes[cuid].steps_completed.append(_step)
      self._update_progress()

  multiprocessing = True
  def _queue_complexes(self) -> None:
    self.log_debug(f"Receptors: {self.Receptors}")
    self.log_debug(f"Ligands: {self.Ligands}")

    if self.path_vina_exe is None:
      self.log_error(f'{self.path_vina_exe} executable is not found. Please provide the executable command or path to executable file.')
      return

    # Perform Docking
    self.init_multiprocessing()
    _combs = list(self.product([self.Receptors.keys(), self.Ligands.keys()], 1))
    for _rck, _ligk in self.PB(_combs, desc='Queue'):
      _rec = self.Receptors[_rck]
      _lig = self.Ligands[_ligk]

      _complex_uid = self.slug(f"{_rec.mol_id}--{_lig.mol_id}")

      if not _complex_uid in self.Complexes:
        self.Complexes[_complex_uid] = self.ObjDict()

        _complex_path = (self.path_plugin_res / _complex_uid).validate()

        # Convert mol_path to PDBQT using meeko/OpenBabel???

        _c_rec = _complex_path / f'REC.pdbqt'
        _c_lig = _complex_path / f'LIG.pdbqt'

        if not _rec.formats['.pdbqt'].mol_path.exists():
          self.log_debug(f'{_rec.mol_id} PDBQT does not exist.')
          continue

        if not _lig.formats['.pdbqt'].mol_path.exists():
          self.log_debug(f'{_lig.mol_id} PDBQT does not exist.')
          continue

        _rec.formats['.pdbqt'].mol_path.copy(_c_rec.resolve())
        _lig.formats['.pdbqt'].mol_path.copy(_c_lig.resolve())

        self.Complexes[_complex_uid].update({
            "step": StepManager(self._step_sequence),
            "steps_completed": [],
            "uid": _complex_uid,
            "rec_uid": _rec.mol_id,
            "lig_uid": _lig.mol_id,
            "path_receptor": _c_rec,
            "path_ligand": _c_lig,
            "path_docking": _complex_path,
            "path_out": _complex_path / f'{_complex_uid}.out.pdbqt',
            "path_score": _complex_path / f'{_complex_uid}.vina.txt',
            "path_vina_config": _complex_path / f"{_complex_uid}.vina.config"
          })

        self.log_debug(f'{_complex_uid}:: Queued.')

      if self.multiprocessing:
        self.queue_task(self._process_complex, _complex_uid)
      else:
        self._process_complex(_complex_uid)

  def _rank_conformers(self, _all_res):
    _ranking_columns = {
        'affinity': True,
        'total_contacts': False,
        'total_hbonds': False,
      }

    _all_res = _all_res.reset_index(drop=True)

    _ranking_cols = []
    for _rc, _rval in _ranking_columns.items():
      _rc_rank_col = f"{_rc}__RANK"
      _ranking_cols.append(_rc_rank_col)
      _all_res[_rc] = self.PD.to_numeric(_all_res[_rc], errors='coerce')
      _all_res[_rc] = _all_res[_rc].fillna(_all_res[_rc].mean())
      _all_res[_rc_rank_col] = _all_res[_rc].rank(ascending=_rval)

    _all_res['Final_Score'] = _all_res[_ranking_cols].sum(axis='columns')
    _all_res = _all_res.sort_values('Final_Score')

    _all_res = _all_res.drop(columns=_ranking_cols)
    _all_res[list(_ranking_columns.keys())] = _all_res[list(_ranking_columns.keys())].round(4)

    _reindexed_score = _all_res.Final_Score.reset_index(drop=True)
    _all_res['Final_Rank'] = _reindexed_score.index + 1

    _grouper = 'Complex UID'
    _score_col = 'Final Score'

    _all_res.columns = ['Conformer ID', 'VINA Score', 'RMSD LB', 'RMSD UB', 'Total Contacts', 'Total Hbonds', 'Contacts', 'Hbonds', 'Receptor ID', 'Ligand ID', _grouper, _score_col, 'Final Rank']

    _top_res = _all_res.loc[_all_res.groupby(_grouper)[_score_col].idxmin()].copy()

    _top_res = _top_res.reset_index(drop=True)
    _top_res = _top_res[['Final Rank', _grouper, 'Receptor ID', 'Ligand ID', 'Conformer ID', 'VINA Score', 'Total Contacts', 'Total Hbonds', 'Contacts', 'Hbonds']].copy()

    _top_res['Final Rank'] = _top_res.index + 1

    # Top Results with Ranking
    _top_res = _top_res.sort_values('Final Rank')

    return _all_res, _top_res

  _df_results = None
  def _tabulate_results(self, *args, **kwargs):
    while self.queue_running > 0:
      self.log_debug()
      self.time_sleep(60)

    self.require('pandas', 'PD')

    # Combine all the interactions
    _score_tables = []
    for _idx in self.Complexes._keys:
      _cmplx = self.Complexes[_idx]
      if not all([isinstance(_cmplx, (dict)), 'vina_results' in _cmplx]):
        continue

      _s = _cmplx.vina_results
      _s['Receptor ID'] = _cmplx.rec_uid
      _s['Ligand ID'] = _cmplx.lig_uid
      _s['Complex_UID'] = _cmplx.uid
      _score_tables.append(_s)

    if not len(_score_tables) > 0:
      self.log_debug('No results were found to be concatenated.')
      return

    _score_tables = self.PD.concat(_score_tables)

    # Save conformers and ranks as excel
    self._df_results, _top_ranked = self._rank_conformers(_score_tables)

    # self.pd_excel(self.path_excel_results, _score_tables, sheet_name=f"Raw-Results")
    self.pd_excel(self.path_excel_results, self._df_results, sheet_name=f"{self.plugin_uid}-All-Ranked")
    self.pd_excel(self.path_excel_results, _top_ranked, sheet_name=f"{self.plugin_uid}-Top-Ranked")

  def _write_receptor_vina_config(self, cuid):
    if not cuid in self.Complexes:
      return

    _complx = self.Complexes[cuid]
    _check = ['path_vina_config' in _complx, _complx.path_vina_config.exists()]

    if all(_check) and _complx.path_vina_config.size > 0:
      self.log_info(f'{cuid} vina config file already exists. Skipping...')
      return

    _config_path = self.Complexes[cuid].path_vina_config

    _mol_obj = self.Receptors[_complx.rec_uid]

    _Parser = PDBParser(get_header=False)
    _structure = _Parser.get_structure(_mol_obj.mol_id, _mol_obj.mol_path)

    _coordinates = []

    # If config settings has specific residues for site specific docking then prepare grid around specific residues
    if self.Vina_config.other.get("residues") and len(self.Vina_config.other.get("residues")):
      for _chains in _structure.get_chains():
        for _chain in _chains:
          _chain_vars = vars(_chain)
          if _chain_vars.get("resname") in self.Vina_config.other.get("residues"):
            _coordinates.extend([[k for k in res.get_coord()] for res in _chain])
    else:
      _coordinates = [_atom.get_coord() for _atom in _structure.get_atoms()]

    # Calculate center, size, and distance
    _coord_x, _coord_y, _coord_z = zip(*_coordinates) if _coordinates else ([], [], [])

    _center = (sum(_coord_x) / len(_coord_x), sum(_coord_y) / len(_coord_y), sum(_coord_z) / len(_coord_z))

    _size = (max(_coord_x) - min(_coord_x), max(_coord_y) - min(_coord_y), max(_coord_z) - min(_coord_z))

    # Prepare VINA config
    _center_x, _center_y, _center_z = (round(_coord, 4) for _coord in _center)
    _size_x, _size_y, _size_z = (min(int(dim), 126) for dim in _size)

    _spacing = float(self.Vina_config.other.get("spacing", 1))

    _vina_config = {
        **self.Vina_config.default,
        "center_x": _center_x,
        "center_y": _center_y,
        "center_z": _center_z,
        "size_x": _size_x + _spacing,
        "size_y": _size_y + _spacing,
        "size_z": _size_z + _spacing,
      }

    self.Complexes[cuid].center = [_center_x, _center_y, _center_z]
    self.Complexes[cuid].box_size = [_size_x + _spacing, _size_y + _spacing, _size_z + _spacing]

    _vina_config = {_k: _vina_config[_k] for _k in _vina_config if _k in self.Vina_config.allowed_keys}

    _vina_config_lines = [f"{config_key} = {_vina_config[config_key]}" for config_key in _vina_config.keys() if _vina_config[config_key] is not None]

    _vina_config_lines = "\n".join(_vina_config_lines + ["\n"])

    _config_path.write(_vina_config_lines)


  def run(self, *args, **kwargs) -> None:
    # Setting molecular formats
    _mgltools = PluginManager.share_plugin('mgltools')()
    self.Receptors.set_format('pdbqt', converter=_mgltools.prepare_receptor)

    _openBabel = PluginManager.share_plugin('openbabel')()
    self.Ligands.set_format('pdbqt', converter=_openBabel.convert)
    self._queue_complexes()
    self._update_progress()

    if self.multiprocessing:
      self.process_queue()
      self.queue_final_callback(self._tabulate_results)
    else:
      self._tabulate_results()

  def shutdown(self, *args, **kwargs) -> None:
    ...
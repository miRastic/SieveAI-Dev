from __future__ import annotations

from ..sieveaibase import StepManager, DictConfig
from ..managers import Structures
from ..process.docking import PluginDockingBase

class HDockLite(PluginDockingBase):
  is_ready = False
  plugin_name = "HDockLite (v Unknown)"
  plugin_uid = "HDockLite"
  plugin_version = "1.0"
  assignments = ['docking']
  current_assignment = None
  dependencies = ['vmdpython', 'cir']
  url = "http://hdock.phys.hust.edu.cn/"

  _max_conformers = 10

  _hdock_exe = None
  _hdock_exe_name = 'hdock'
  _hdock_exe_name_pl = 'hdockpl'

  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)

    self.Receptors = None
    self.Ligands = None

    self.path_plugin_docking = self.SETTINGS.plugin_data[self.plugin_uid].path_plugin_docking = (self.path_sieveai_docking / self.plugin_uid).validate().rel_path()

    self.path_excel_results = self._get_result_excel_path()
    self._restore_progress()

    self._steps_map_methods = {
      "init": self._run_preprocess_check,
      "dock": self._run_hdock_main,
      "extract": self._run_hdock_pl,
      "analyse": self._run_analysis,
      "completed": self._finalise_complex,
    }

    self._step_sequence = tuple(self._steps_map_methods.keys())
    self.re_remarks = self.re_compile(r'REMARK\s(\w+):\s+(.*)$')

  def setup(self, *args, **kwargs):
    self.update_attributes(self, kwargs)

  def _init_molecules(self, *args, **kwargs):
    self.setup(*args, **kwargs)
    self.Receptors = Structures(self.SETTINGS.user.path_receptors, '*.pdb', 'macromolecule')
    self.Ligands = Structures(self.SETTINGS.user.path_ligands, '*.pdb', 'macromolecule')

  def _run_hdock_main(self, cuid) -> None:
    """Runs hdock and hdockpl to perform docking and later extact the complexes.
    """
    _cmplx = self.Complexes[cuid]
    if (_cmplx.path_docking / f"{cuid}.out").exists():
      self.log_debug(f'HDOCKLITE_05: {cuid} already docked.')
    else:
      _log = self.cmd_run(self._hdock_exe_name, _cmplx.path_receptor.name, _cmplx.path_ligand.name, cwd=_cmplx.path_docking, **{
        '-out': f"{cuid}.out",
      })
      _cmplx.path_log.write(str(_log))

  def _run_hdock_pl(self, cuid):
    """Runs hdock and hdockpl to perform docking and later extact the complexes.
    """
    _cmplx = self.Complexes[cuid]
    *_models, = list(_cmplx.path_docking.search('model*'))
    if len(_models) > 0:
      self.log_debug(f'HDOCKLITE_06: {cuid} already splitted.')
    else:
      _log = self.cmd_run(self._hdock_exe_name_pl, f"{cuid}.out", "complex.pdb", "-nmax", self._max_conformers, "-complex", "-chid", "-models", cwd=_cmplx.path_docking)

      _cmplx.path_log.write(str(_log))

  def _fn_sort_model(self, _model_path=""):
    _number = self.digit_only(self.filename(_model_path))
    return int(_number)

  def _run_analysis(self, cuid):
    _VPY = self.SETTINGS.PLUGIN_REFS.vmdpython()

    *_models, = list(self.Complexes[cuid].path_docking.search('model*'))
    _models.sort(key=self._fn_sort_model)

    _model_results = []
    for _model in _models:
      _vmd_id = _VPY.parse_molecule(str(_model))
      _rec_obj = _VPY.get_atom_sel('chain A', _vmd_id)
      _lig_obj = _VPY.get_atom_sel('chain B', _vmd_id)

      _lines = list(_model.readlines(num_lines=5))
      _remarks = dict([_r[0] for _r in map(self.re_remarks.findall, _lines)])
      _remarks['Complex_uid'] = cuid
      _interactions = _VPY.get_interactions(_rec_obj, _lig_obj)
      _remarks.update(_interactions)
      _model_results.append(_remarks)

    self.log_debug(f'{cuid}:: Conformer Results Generated')

    _df_conformer_scores = self.DF(_model_results)
    _df_conformer_scores['plugin'] = self.plugin_uid
    self.Complexes[cuid].conformer_scores = _df_conformer_scores

  def _run_preprocess_check(self, cuid):
    return cuid

  def _finalise_complex(self, cuid):
    return cuid

  def _process_complex(self, cuid):
    if cuid in self.Complexes:
      for _step in self.Complexes[cuid].step:
        if _step in self.Complexes[cuid].steps_completed:
          continue

        _step = self.Complexes[cuid].step._current

        if self.Complexes[cuid].step.is_last:
          self.log_debug(f"{cuid}:: Last Step: {_step}")
        else:
          self.log_debug(f"{cuid}:: Step: {_step}")

        self._steps_map_methods[_step](cuid)
        self.Complexes[cuid].steps_completed.append(_step)

  def _queue_complexes(self):
    # Pre-process or cleaning of molecules
    # Create Directories and Copy Molecules
    # Perform docking and extraction of conformers
    self.log_debug(f"HDOCKLITE_02: Receptors = {self.Receptors}")
    self.log_debug(f"HDOCKLITE_03: Ligands = {self.Ligands}")

    self._hdock_exe = self.which(self._hdock_exe_name)

    if not self._hdock_exe:
      self.log_error(f'HDOCKLITE_04: {self._hdock_exe_name} executable is not found. Please provide the executable command or path to executable file.')
      return

    # Perform Docking
    self.SETTINGS.user.multiprocessing and self.init_multiprocessing()

    _combs = list(self.product(self.Receptors.keys(), self.Ligands.keys()))

    for _rck, _ligk in _combs:
      _rec = self.Receptors[_rck]
      _lig = self.Ligands[_ligk]

      _complex_uid = self.slug(f"{_rec.mol_id}--{_lig.mol_id}")

      if not _complex_uid in self.Complexes:
        self.Complexes[_complex_uid] = DictConfig()

        _complex_path = (self.path_plugin_docking / _complex_uid).validate()

        # Copy _path
        _c_rec = _complex_path / f'REC{_rec.mol_path.suffix}'
        _c_lig = _complex_path / f'LIG{_lig.mol_path.suffix}'

        _rec.mol_path.copy(_c_rec)
        _lig.mol_path.copy(_c_lig)

        self.Complexes[_complex_uid].update({
            "step": StepManager(self._step_sequence),
            "steps_completed": [],
            "uid": _complex_uid,
            "rec_uid": _rec.mol_id,
            "lig_uid": _lig.mol_id,
            "path_receptor": _c_rec,
            "path_ligand": _c_lig,
            "path_docking": _complex_path,
            "path_log": _complex_path / f'{_complex_uid}.log',
          })

        self.log_debug(f'{_complex_uid}:: Queued.')

      if self.SETTINGS.user.multiprocessing:
        self.queue_task(self._process_complex, _complex_uid)
      else:
        self._process_complex(_complex_uid)

  def _manage_queue(self, *args, **kwargs):
    self._queue_complexes()
    self._update_progress()
    if self.SETTINGS.user.multiprocessing:
      self.process_queue()
      self.queue_final_callback(self._tabulate_results)
    else:
      self._tabulate_results()

  def _rank_conformers(self, _all_res):
    _ranking_columns = {
        'Score': True,
        # 'RMSD': True,
        'distance': True,
        'SASA_1': True,
        'SASA_2': True,
        'HBond_total': False,
        'Contact_Total': False,
      }

    _all_result_order = ['Rank', 'Number', 'rec_uid', 'lig_uid', 'Score', 'HBond_total', 'Contact_Total', 'SASA_1', 'SASA_2', 'Contact_1', 'Contact_2', 'HBond_1_don', 'HBond_2_don', ]

    _top_result_order = ['Rank', 'Number', 'rec_uid', 'lig_uid', 'Score', 'HBond_total', 'Contact_Total', 'SASA_1', 'SASA_2', 'Contact_1', 'Contact_2', 'HBond_1_don', 'HBond_2_don', ]

    _column_rename_map = {
      'Complex_uid': 'Complex ID',
      'rec_uid': 'Receptor ID',
      'lig_uid': 'Ligand ID',
      'plugin': 'Plugin Name',

      'Rank': 'Composite Rank', # Deprecated
      'Composite_Rank': 'Composite Rank',
      'Composite_Score': 'Composite Score',

      'Number': 'Conformer ID',
      'Ligand': 'Ligand_File_Name',
      'Contact': 'Contact_UNKNOWN',
      'Score': 'HDock Score',
      'RMSD': 'RMSD',

      'distance': 'Distance',

      'SASA_1': 'SASA Receptor',
      'SASA_2': 'SASA Ligand',

      'Contact_1': 'Contact Res Receptor',
      'Contact_2': 'Contact Res Ligand',
      'HBond_1_don': 'HBond Donor Receptor Res',
      'HBond_2_acc': 'HBond Acceptor Ligand Res',
      'HBond_12_proton': 'Receptor to Ligand HBond Proton',
      'HBond_2_don': 'HBond Donor Ligand Res',
      'HBond_1_acc': 'HBond Acceptor Receptor Res',
      'HBond_21_proton': 'Ligand to Receptor HBond Proton',

      'HBond_total': 'Total HBonds',
      'Contact_Total': 'Total Contacts',
    }

    _ranker = self.SETTINGS.PLUGIN_REFS.CompositeIndexRanker() # CIR
    _all_res, _top_res = _ranker.rank_conformers(
          _all_res, _ranking_columns,
            grouper = 'Complex_uid'
        )

    _all_res = _all_res[_all_result_order]
    _top_res = _top_res[_top_result_order]

    _all_res.rename(columns=_column_rename_map, inplace=True)
    _top_res.rename(columns=_column_rename_map, inplace=True)

    return _all_res, _top_res

  _df_results = None
  _df_top_ranked = None
  def _tabulate_results(self, *args, **kwargs):
    self.require('pandas', 'PD')

    # Combine all the interactions
    _score_table = None
    for _idx, _cmplx in self.Complexes.items():
      if not isinstance(_cmplx, (dict)) or not 'conformer_scores' in _cmplx:
        continue

      if _score_table is None:
        _score_table = _cmplx.conformer_scores
      else:
        _score_table = self.PD.concat([_score_table, _cmplx.conformer_scores])

    _score_table['HBond_total'] = (_score_table.HBond_1_don.apply(lambda _x: len(set(_x))) + _score_table.HBond_2_don.apply(lambda _x: len(set(_x))))
    _score_table['Contact_Total'] = (_score_table.Contact_1.apply(lambda _x: len(set(_x))) + _score_table.Contact_2.apply(lambda _x: len(set(_x))))

    _score_table[['rec_uid', 'lig_uid']] = _score_table.apply(lambda _r: _r.Complex_uid.split('--'), result_type='expand', axis='columns')

    # Save conformers and ranks as excel
    try:
      self._df_results, self._df_top_ranked = self._rank_conformers(_score_table)
      self.pd_excel(self.path_excel_results, self._df_results, sheet_name=f"{self.plugin_uid}-All-Ranked")
      self.pd_excel(self.path_excel_results, self._df_top_ranked, sheet_name=f"{self.plugin_uid}-Top-Ranked")
    except Exception as _e:
      self.log_error(f"HDOCKLITE_01: {_e}")
      self.error_traceback(_e)

  def boot(self, *args, **kwargs) -> HDockLite:
    self._init_molecules(**kwargs)
    return self

  def run(self, *args, **kwargs) -> HDockLite:
    self._manage_queue(**kwargs)
    return self

  def shutdown(self, *args, **kwargs) -> HDockLite:
    self._update_progress()
    self.post_docking()
    return self

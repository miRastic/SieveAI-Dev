
from ..plug import StepManager
from ..managers import Structures
from .base import PluginBase

class HDockLite(PluginBase):
  is_ready = False
  plugin_name = "HDockLite (v Unknown)"
  plugin_uid = "HDockLite"
  process = ['docking']
  url = "http://hdock.phys.hust.edu.cn/"

  _max_conformers = 10

  _hdock_exe = None
  _hdock_exe_name = 'hdock'
  _hdock_exe_name_pl = 'hdockpl'

  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)
    self.Complexes = self.ObjDict()

    self.Receptors = None
    self.Ligands = None

    self.path_plugin_res = (self.path_base / 'docking' / self.plugin_uid).validate()
    self.path_update = (self.path_base / 'docking' / self.plugin_uid).with_suffix('.config.sob')
    self.path_excel_results = (self.path_base / self.plugin_uid ).with_suffix('.Results.xlsx')
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

  def boot(self, *args, **kwargs):
    self.setup(*args, **kwargs)
    self.Receptors = Structures(self.SETTINGS.user.path_receptors, '*.pdb', 'macromolecule')
    self.Ligands = Structures(self.SETTINGS.user.path_ligands, '*.pdb', 'macromolecule')

  def _restore_progress(self, *args, **kwargs):
    if self.path_update.exists():
      _ci = self.unpickle(self.path_update)
      self.Complexes = _ci

  def _update_progress(self, *args, **kwargs):
    self.pickle(self.path_update, self.Complexes)

  def _run_hdock_main(self, cuid) -> None:
    """Runs hdock and hdockpl to perform docking and later extact the complexes.
    """
    _cmplx = self.Complexes[cuid]
    _log = self.cmd_run(self._hdock_exe_name, _cmplx.path_receptor.name, _cmplx.path_ligand.name, cwd=_cmplx.path_docking, **{
      '-out': f"{cuid}.out",
    })

    _cmplx.path_log.write(str(_log))

  def _run_hdock_pl(self, cuid):
    """Runs hdock and hdockpl to perform docking and later extact the complexes.
    """
    _log = self.cmd_run(self._hdock_exe_name_pl, f"{cuid}.out", "complex.pdb", "-nmax", self._max_conformers, "-complex", "-chid", "-models", cwd=self.Complexes[cuid].path_docking)

    self.Complexes[cuid].path_log.write(str(_log))

  def _fn_sort_model(self, _model_path=""):
    _number = self.digit_only(self.filename(_model_path))
    return int(_number)

  def _run_analysis(self, cuid):
    _VPY = self.SETTINGS.plugin_refs.analysis.vmdpython()

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
        self._update_progress()

  _is_multiprocess = True

  def _queue_complexes(self):
    # Pre-process or cleaning of molecules
    # Create Directories and Copy Molecules
    # Perform docking and extraction of conformers
    self.debug(f"Receptors: {self.Receptors}")
    self.debug(f"Ligands: {self.Ligands}")

    self._hdock_exe = self.which(self._hdock_exe_name)

    if not self._hdock_exe:
      self.log_error(f'{self._hdock_exe_name} executable is not found. Please provide the executable command or path to executable file.')
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

      if self._is_multiprocess:
        self.queue_task(self._process_complex, _complex_uid)
      else:
        self._process_complex(_complex_uid)

  def run(self, *args, **kwargs):
    self._queue_complexes()
    self._update_progress()
    self.process_queue()
    self.queue_final_callback(self._tabulate_results)

  def _rank_conformers(self, _all_res):
    _ranking_columns = {
        'Score': True,
        'RMSD': True,
        'distance': True,
        'SASA_1': True,
        'SASA_2': True,
        'HBond_total': False,
        'Contact_Total': False,
      }

    _all_res = _all_res.reset_index(drop=True)
    _all_res['HBond_total'] = (_all_res.HBond_1_don.apply(lambda _x: len(set(_x))) + _all_res.HBond_2_don.apply(lambda _x: len(set(_x))))
    _all_res['Contact_Total'] = (_all_res.Contact_1.apply(lambda _x: len(set(_x))) + _all_res.Contact_2.apply(lambda _x: len(set(_x))))

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

    _top_res = _all_res.loc[_all_res.groupby('Complex_uid')['Final_Score'].idxmin()].copy()
    _top_res = _top_res.reset_index(drop=True)
    _top_res = _top_res[['Final_Rank', 'Complex_uid', 'Number',
                         'Ligand', 'Score', 'RMSD', 'distance',
                         'SASA_1', 'SASA_2', 'HBond_total',
                         'Contact_Total',]].copy()

    # Top Results with Ranking
    _top_res = _top_res.sort_values('Final_Rank')

    return _all_res, _top_res

  _df_results = None
  _df_top_ranked = None
  def _tabulate_results(self, *args, **kwargs):
    while self.queue_running > 0:
      self.log_debug()
      self.time_sleep(60)

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

    print(_score_table)
    # Save conformers and ranks as excel
    try:
      self._df_results, self._df_top_ranked = self._rank_conformers(_score_table)
      self.pd_excel(self.path_excel_results, self._df_results, sheet_name=f"{self.plugin_uid}-All-Ranked")
      self.pd_excel(self.path_excel_results, self._df_top_ranked, sheet_name=f"{self.plugin_uid}-Top-Ranked")
    except Exception as _e:
      self.log_error(f"HDOCKLITE_01: {_e}")
      self.error_traceback(_e)
  def shutdown(self, *args, **kwargs):
    # Prepare HTML server for visualisation of results
    pass

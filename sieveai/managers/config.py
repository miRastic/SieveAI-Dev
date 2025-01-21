from .base import ManagerBase
from collections.abc import Mapping
from ..sieveaibase import EntityPath, DictConfig

class ConfigManager(ManagerBase):
  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)
    self._init_config()

  def __set_defaults(self):
    _user_vars = {
      'path_base': None,

      'dir_receptors': 'receptors',
      'dir_ligands': 'ligands',
      'dir_docking': 'docking',
      'dir_analysis': 'analysis',
      'dir_results': 'results',
      'dir_plots': 'plots',

      'path_receptors': None,
      'path_ligands': None,
      'path_docking': None,
      'path_results': None,
      'path_plots': None,
      'path_analysis': None,

      'file_toml_workflow': 'sieveai.workflow.toml',
      'file_sob_progress': 'sieveai.progress.sob',

      'path_toml_workflow': None,
      'path_sob_progress': None,

      'multiprocessing': False,

      'report_flag': True,
      'report_interval': 90,
      'report_interval_unit': 'seconds',
      'exit_interval': 1,
      'exit_interval_unit': 'hours',
    }

    # User Settings with String/EntityPath Only
    self.SETTINGS.user.update(_user_vars)

    # User workflow default settings (Will override plugin_list)
    self.SETTINGS.user.workflow_order = ['sync', 'docking', 'analysis', 'results']
    self.SETTINGS.user.workflow.sync = ['structuresync']
    self.SETTINGS.user.workflow.docking = ['vina'] # , 'hdocklite'
    self.SETTINGS.user.workflow.analysis = ['chimerax'] # , 'vmdpython', 'plip', 'freesasa'

    # Other settings to be stored in compressed format
    self.SETTINGS.PLUGIN_REFS = DictConfig()

    self.SETTINGS.plugin_data = DictConfig()

  def __process_config(self) -> None:
    self.path_base = EntityPath(self.path_base)

    if self.SETTINGS.user.path_receptors is None:
      self.SETTINGS.user.path_receptors = (self.path_base / self.SETTINGS.user.dir_receptors)

    if self.SETTINGS.user.path_ligands is None:
      self.SETTINGS.user.path_ligands = (self.path_base / self.SETTINGS.user.dir_ligands)

    if self.SETTINGS.user.path_docking is None:
      self.SETTINGS.user.path_docking = (self.path_base / self.SETTINGS.user.dir_docking)

    if self.SETTINGS.user.path_analysis is None:
      self.SETTINGS.user.path_analysis = (self.path_base / self.SETTINGS.user.dir_analysis)

    if self.SETTINGS.user.path_results is None:
      self.SETTINGS.user.path_results = (self.path_base / self.SETTINGS.user.dir_results)

    if self.SETTINGS.user.path_sob_progress is None:
      self.SETTINGS.user.path_sob_progress = (self.path_base / self.SETTINGS.user.file_sob_progress)

    if self.SETTINGS.user.path_toml_workflow is None:
      self.SETTINGS.user.path_toml_workflow = (self.path_base / self.SETTINGS.user.file_toml_workflow)

  require_config_review = False

  def _val_casting(self, _v1, _v2):
    if isinstance(_v1, (Mapping)):
      for _k, _v in _v1.items():
        _v2[_k] = self._val_casting(_v, _v2[_k]) if _k in _v2 else None
      return _v2
    else:
      return type(_v1)(_v2)

  def _map_user_config_data_type(self, _toml_config):
    _updated_toml = self._val_casting(self.SETTINGS, _toml_config)
    _d2 = _updated_toml.get('user', {})

    self.SETTINGS.user.update((_k1, _d2[_k1]) for _k1 in self.SETTINGS.user.keys() & _d2.keys() if _d2[_k1] is not None)

  def _sync_user_config(self):
    if self.SETTINGS.user.path_toml_workflow.exists() and self.SETTINGS.user.path_toml_workflow.size > 0:
      _u_config = self.read_toml(self.SETTINGS.user.path_toml_workflow)

      _original_config_toml = self.convert_to_toml_obj({'user': self.SETTINGS.user})
      _u_config_toml = self.convert_to_toml_obj(_u_config)

      if not (_original_config_toml == _u_config_toml):
        self._map_user_config_data_type(_u_config)

    else:
      self.write_toml(self.SETTINGS.user.path_toml_workflow, {'user': self.SETTINGS.user})
      self.log_info('No user configuration was found. We have generated a user configuration. If required update it and rerun the program.')
      self.require_config_review = True

  def _init_config(self, *args, **kwargs):
    self.__set_defaults()
    self.__process_config()

    self.restore_progress()
    self._sync_user_config()

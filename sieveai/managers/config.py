from .base import ManagerBase
from collections.abc import Mapping
from ..plug import EntityPath

class ConfigManager(ManagerBase):
  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)
    self._init_config()

  def __set_defaults(self):

    _user_vars = {
      'path_base': None,

      'path_receptors': None,
      'path_ligands': None,
      'path_docking': None,
      'path_results': None,
      'path_plots': None,

      'dir_receptors': 'receptors',
      'dir_ligands': 'ligands',
      'dir_docking': 'docking',
      'dir_results': 'results',
      'dir_plots': 'plots',

      'file_user_config': 'config.user.toml',
      'file_sob': 'settings.sob',

      'path_user_toml': None,
      'path_sob': None,
    }

    # User Settings with String/EntityPath Only
    self.SETTINGS.user.update(_user_vars)
    self.SETTINGS.user.plugin_list.docking = ['hdocklite']
    self.SETTINGS.user.plugin_list.analysis = ['vmdpython', 'chimerax']

    # Other settings to be stored in compressed format
    self.SETTINGS.plugin_refs.docking = self.ObjDict()
    self.SETTINGS.plugin_refs.analysis = self.ObjDict()
    self.SETTINGS.plugin_data = self.ObjDict()

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

    if self.SETTINGS.user.path_sob is None:
      self.SETTINGS.user.path_sob = (self.path_base / self.SETTINGS.user.file_sob)

    if self.SETTINGS.user.path_user_toml is None:
      self.SETTINGS.user.path_user_toml = (self.path_base / self.SETTINGS.user.file_user_config)

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

  def reset_user_config(self):
    # Update non-existing keys in user config
    ...

  def _sync_user_config(self):
    if self.SETTINGS.user.path_user_toml.exists() and self.SETTINGS.user.path_user_toml.size > 0:
      _u_config = self.read_toml(self.SETTINGS.user.path_user_toml)

      _original_config_toml = self.convert_to_toml_obj({'user': self.SETTINGS.user})
      _u_config_toml = self.convert_to_toml_obj(_u_config)

      if not (_original_config_toml == _u_config_toml):
        self._map_user_config_data_type(_u_config)

    else:
      self.write_toml(self.SETTINGS.user.path_user_toml, {'user': self.SETTINGS.user})
      self.log_info('No user configuration was found. We have generated a user configuration. If required update it and rerun the program.')
      self.require_config_review = True

  def _init_config(self, *args, **kwargs):
    self.__set_defaults()
    self.__process_config()

    if self.SETTINGS.user.path_sob.exists() and self.SETTINGS.user.path_sob.size > 0:
      _s = self.unpickle(self.SETTINGS.user.path_sob)

      self.SETTINGS.update(_s)

    self._sync_user_config()

    self._write_config()

  def _write_config(self, *args, **kwargs):
    self.pickle(self.SETTINGS.user.path_sob, self.SETTINGS)

from .config import ConfigManager

class Manager(ConfigManager):
  ref_processes = None

  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)
    if not self.SETTINGS.user.path_base:
      self.SETTINGS.user.path_base = self.path_base

  # Manage commandline operations
  def _update_cli_args(self):
    # key: (['arg_k1', 'arg_k2'], nargs, default, help, {})
    _version_info = f"TEST (build-TEST)"
    _cli_settings = {
      "debug": (['--debug'], None, 0, 'silent/verbose/debug mode from 0, 1, 2, and 3.', {}),
      "path_base": (['-b'], None, self.OS.getcwd(), 'Provide base directory to run the process.', {}),
      "dir_receptors": (['-r'], None, 'receptors', 'Directory name containing receptors.', {}),
      "dir_ligands": (['-l'], None, 'ligands', 'Directory name containing ligands.', {}),
      # "docking_programs": (['-d'], "*", ['vina'], 'One or more Docking Programs eg: vina, hdocklite, auto.', {}),
    }

    _params = self.get_cli_args(_cli_settings, version=_version_info)

    print("{}\n{}\n{}".format("=" * len(_version_info), _version_info, "=" * len(_version_info)))
    self.SETTINGS.user.update(_params)

  def get_settings(self, obj_key=None, sep='.'):
    if isinstance(obj_key, (str)):
      return self.get_deep_key(self.SETTINGS, obj_key, sep=sep)
    else:
      return self.SETTINGS

  def handle_docking(self, *args, **kwargs):
    from ..process.master import Master
    self.SETTINGS.user.update(kwargs)

    if self.SETTINGS.user.path_base:
      self.path_base = self.SETTINGS.user.path_base

    self.log_debug(f'MANAGER_01: Current base path is {self.path_base}')

    # pass settings to Dock
    self.ref_processes = Master(path_base=self.path_base, SETTINGS=self.SETTINGS)

    self.log_debug(f'MANAGER_02: Starting Master process.')
    self.ref_processes.process()

  def get_process_status(self, *args, **kwargs):
    _status = {
      "queue": self.queue_task_status
    }
    for _idx, _item in self.SETTINGS.plugin_data.items():
      if str(_idx).startswith('_'): continue
      _status[_idx] = _item.status

    return _status

  def cli_dock(self):
    self._update_cli_args()
    if self.require_config_review:
      self.log_info('We have generated a default configuration file for you.')
      self.log_info('Continue with default configuration or do you want to modify the configuration?')
      input()
      return None
    self.handle_docking()

  # Manage web operation
  def _update_web_args(self):
    ...

  def web_dock(self):
    self._update_web_args()
    self.handle_docking()

  def web_server(self, *args, **kwargs):
    from .web import SieveAIAPI
    _wm = SieveAIAPI(*args, **kwargs)
    _wm.run_server()
    return _wm

from .config import ConfigManager
from .plugin import PluginManager

class Manager(ConfigManager, PluginManager):
  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)

  # Manage commandline operations
  def _update_cli_args(self):
    # key: (['arg_k1', 'arg_k2'], nargs, default, help, {})
    _version_info = f"TEST (build-TEST)"
    _cli_settings = {
      "debug": (['--debug'], None, 0, 'silent/verbose/debug mode from 0, 1, 2, and 3.', {}),
      "path_base": (['-b'], "*", [self.OS.getcwd()], 'Provide base directory to run the process.', {}),
      "dir_receptors": (['-r'], None, 'receptors', 'Directory name containing receptors.', {}),
      "dir_ligands": (['-l'], None, 'ligands', 'Directory name containing ligands.', {}),
      "docking_programs": (['-d'], "*", ['vina'], 'One or more Docking Programs eg: vina, hdock, auto.', {}),
    }

    _params = self.get_cli_args(_cli_settings, version=_version_info)

    print("{}\n{}\n{}".format("=" * len(_version_info), _version_info, "=" * len(_version_info)))
    self.settings.base.update(_params)

  def manage_exe_plugins(self, *args, **kwargs):
    _plugin_type = args[0] if len(args) > 0 else kwargs.get("plugin_type", "docking")

    if not isinstance(self.settings.exe.plugins[_plugin_type], (list)):
      self.settings.exe.plugins[_plugin_type] = []

    for _dp in self.settings.exe.programs[_plugin_type] or []:
      self.settings.exe.plugins[_plugin_type].append(self.get_plugin(_dp))

  def handle_docking(self, *args, **kwargs):
    from ..core.dock import Dock
    self.settings.base.update(kwargs or {})

    if self.settings.base.path_base:
      self.path_base = self.settings.base.path_base

    if self.settings.base.docking_programs and len(self.settings.base.docking_programs) > 0:
      self.settings.exe.programs.docking = self.settings.base.docking_programs

    self.manage_exe_plugins('docking')

    _dock = Dock(path_base=self.path_base, settings=self.settings) # pass settings to Dock
    _dock.process()

  def handle_rescoring(self, *args, **kwargs):
    from ..core.rescore import Rescore
    self.settings.update(kwargs or {})

    if self.settings.base.path_base:
      self.path_base = self.settings.base.path_base

    if self.settings.base.rescoring_programs and len(self.settings.base.rescoring_programs) > 0:
      self.settings.exe.programs.rescoring = self.settings.base.rescoring_programs

    self.manage_exe_plugins('rescoring')

    _rescore = Rescore(path_base=self.path_base, settings=self.settings)
    _rescore.process()

  def cli_dock(self):
    self._update_cli_args()
    self.handle_docking()

  def cli_rescore(self):
    self._update_cli_args()
    self.handle_rescoring()

  # Manage web operation

  def _update_web_args(self):
    ...

  def web_dock(self):
    self._update_web_args()
    self.handle_docking()

  def web_rescore(self):
    self._update_web_args()
    self.handle_rescoring()
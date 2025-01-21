from UtilityLib import ProjectManager

class OnceManager(ProjectManager):
  master_config_path = None
  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)

  def check(self, mcp, *args, **kwargs):
    self.master_config_path = mcp
    self._check_third_party_pkgs(**kwargs)
    self._test_installation()

  def recheck_exe(self, *args, **kwargs):
    self.check(*args, **kwargs)

  def _check_third_party_pkgs(self, *args, **kwargs):
    _test_packages = ('vina', 'chimerax', 'hdock', 'prepare_receptor', 'sieveai', 'mk_prepare_receptor')
    _exe_map = {
      'version': kwargs.get('version', '0.1.dev')
    }
    for _tp in _test_packages:
      _exe_path = self.cmd_which(_tp)
      if not _exe_path:
        self.log_debug(f'{_tp} requires your attentions as it is not available to be used.')
        # Retry with alterate approach...
      else:
        _exe_map[_tp] = self.cmd_which(_tp)
    self.write_toml(self.master_config_path, {'EXE_PATHS': _exe_map})

  def _test_installation(self):
    # Avail config from user for different packages and provide UI option to let them add those packages
    # Allow users to modify code through WebUI editor
    ...

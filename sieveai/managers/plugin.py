import importlib as ImportLib

class PluginManager:
  def __init__(self, *args, **kwargs):
    pass

  @staticmethod
  def get_plugin_refs(self, *args, **kwargs):
    _plugin_map = kwargs.get('plugin_map',  args[1] if len(args) > 1 and isinstance(args[0], dict) else {})
    _plugin_refs = {}
    for _pc, _pn in _plugin_map.items():
      _pref = PluginManager.share_plugin(self, _pc)
      _plugin_refs[_pc] = _pref

      # When plugins are referred by the filename or referred with lower class
      _plugin_refs[_pc.lower()] = _pref
      _plugin_refs[_pn] = _pref
      _plugin_refs[_pn.lower()] = _pref

    return _plugin_refs

  @staticmethod
  def share_plugin(self, _plugin_name):
    """
    @ToDo: Implement import from file or different path
    """
    _plugin_file = PluginManager.plugin_map.get(_plugin_name)
    _plugin_ref = ImportLib.import_module("..plugins.%s" % _plugin_file, package=__package__)
    return getattr(_plugin_ref, _plugin_name)

import importlib as ImportLib

class PluginManager:
  plugin_map = {
    'vina': 'Vina',
    'chimerax': 'ChimeraX',
    'hdocklite': 'HDockLite',
    'openbabel': 'OpenBabel',
    'vmdpython': 'VMDPython',
    'annapurna': 'AnnapuRNA',
    'mgltools': 'MGLTools',
    'structuresync': 'StructureSync',
  }
  def __init__(self, *args, **kwargs):
    pass

  @staticmethod
  def share_plugin(_plugin_name):
    _plugin_refs = ImportLib.import_module("..plugins.%s" % _plugin_name, package=__package__)
    _plugin_obj = getattr(_plugin_refs, PluginManager.plugin_map.get(_plugin_name) or _plugin_name.title())
    return _plugin_obj

  def get_plugin(self, _plugin_name):
    return PluginManager.share_plugin(_plugin_name)

  # Detect plugins automatically

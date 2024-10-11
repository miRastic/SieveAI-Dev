from ..plug import SieveAIBase
from ..managers.plugin import PluginManager

class CoreBase(SieveAIBase):
  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)

  def get_plugin(self, _plugin_name):
    return PluginManager.share_plugin(_plugin_name)

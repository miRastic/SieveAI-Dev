
from ..process.dynamics import PluginDynamicsBase
from ..process.analysis import PluginAnalysisBase

class OpenMM(PluginAnalysisBase, PluginDynamicsBase):
  is_ready = False
  plugin_name = "OpenMM"
  plugin_uid = "OpenMM"
  plugin_version = "1.0"

  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)

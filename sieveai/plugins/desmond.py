# Desmond Projects
from ..process.dynamics import PluginDynamicsBase
from ..process.analysis import PluginAnalysisBase

class Desmond(PluginAnalysisBase, PluginDynamicsBase):
  is_ready = False
  plugin_name = "Desmond"
  plugin_uid = "Desmond"
  plugin_version = "1.0"

  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)

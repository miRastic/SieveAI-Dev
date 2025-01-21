# gmx_MMPBSA
from ..process.dynamics import PluginDynamicsBase
from ..process.analysis import PluginAnalysisBase

class gmx_MMPBSA(PluginAnalysisBase, PluginDynamicsBase):
  is_ready = False
  plugin_name = "gmx_MMPBSA"
  plugin_uid = "gmx_MMPBSA"
  plugin_version = "1.0"

  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)

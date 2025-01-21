# GROMACS
from ..process.dynamics import PluginDynamicsBase
from ..process.analysis import PluginAnalysisBase

class GMX(PluginAnalysisBase, PluginDynamicsBase):
  is_ready = False
  plugin_name = "GROMACS"
  plugin_uid = "gmx"
  plugin_version = "1.0"

  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)

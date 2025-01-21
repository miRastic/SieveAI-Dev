
from ..process.docking import PluginDockingBase

class PatchDockWeb(PluginDockingBase):
  is_ready = False
  plugin_name = "PatchDockWeb"
  plugin_uid = "PatchDockWeb"
  plugin_version = "1.0"
  assignments = ['docking']
  current_assignment = None
  url = "https://bioinfo3d.cs.tau.ac.il/PatchDock/"
  Receptors = None
  Ligands = None

  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)

  def setup(self, *args, **kwargs):
    self.update_attributes(self, kwargs)

  def boot(self, *args, **kwargs):
    self.setup(*args, **kwargs)

  def _prepare_receptor(self, _rec_id):
    ...

  def run(self, *args, **kwargs):
    ...

  def shutdown(self, *args, **kwargs):
    ...

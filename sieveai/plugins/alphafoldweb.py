from ..process.docking import PluginDockingBase

class AlphaFoldWeb(PluginDockingBase):
  is_ready = False
  plugin_name = "AlphaFold"
  plugin_uid = "AlphaFold"
  plugin_version = "1.0"
  assignments = ['docking']
  current_assignment = None
  url = "https://alphafoldserver.com"

  Receptors = None
  Ligands = None

  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)

  def setup(self, *args, **kwargs):
    self.update_attributes(self, kwargs)

  def boot(self, *args, **kwargs):
    self.setup(*args, **kwargs)

  def run(self, *args, **kwargs):
    ...

  def shutdown(self, *args, **kwargs):
    ...

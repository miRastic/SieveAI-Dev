
from ..process.docking import PluginDockingBase

class HDockWeb(PluginDockingBase):
  is_ready = False
  plugin_name = "HDockWeb (v Unknown)"
  plugin_uid = "HDockWeb"
  plugin_version = "3.1"
  assignments = ['docking']
  current_assignment = None
  url = "http://hdock.phys.hust.edu.cn/"

  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)

  def setup(self, *args, **kwargs):
    self.update_attributes(self, kwargs)

  def boot(self, *args, **kwargs): pass

  def _restore_progress(self, *args, **kwargs): pass

  def run(self, *args, **kwargs): pass

  def shutdown(self, *args, **kwargs): pass

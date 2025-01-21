from ..process.analysis import PluginAnalysisBase

class FreeSASA(PluginAnalysisBase):
  is_ready = False
  plugin_name = "FreeSASA"
  plugin_uid = "FreeSASA"
  plugin_version = "1.0"
  assignments = ['analysis']
  current_assignment = None
  url = "https://freesasa.github.io/"

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

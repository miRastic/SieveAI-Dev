
from .base import PluginBase

class AlphaFoldWeb(PluginBase):
  is_ready = False
  plugin_name = "AlphaFold"
  process = ['analysis']
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

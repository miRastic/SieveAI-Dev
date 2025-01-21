from .base import PluginBase

class PluginDynamicsBase(PluginBase):
  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)
    self.path_sieveai_dynamics = self.path_base / 'dynamics'

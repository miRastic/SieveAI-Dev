from .base import PluginBase

class PluginAnalysisBase(PluginBase):
  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)

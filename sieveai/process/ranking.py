from .base import PluginBase

class PluginRankingBase(PluginBase):
  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)

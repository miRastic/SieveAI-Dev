from .base import PluginBase

class PluginRescoringBase(PluginBase):
  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)

from .base import PluginBase

class PluginConverterBase(PluginBase):
  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)

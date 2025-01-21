from ..process.base import PluginBase

class CloudData(PluginBase):
  # Retrieve Public DataSet, Already Processed Data, Demo DataSet
  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)

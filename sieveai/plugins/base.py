from ..plug import SieveAIBase

class PluginBase(SieveAIBase):
  is_ready = False
  plugin_name = "Base"
  url = None

  def __init__(self, *args, **kwargs):
    self.path_base = None
    super().__init__(**kwargs)

  def installation_instructions(self, *args, **kwargs):
    ...

  def get_status(self, cuid=None):
    _status = None

    if not hasattr(self, 'Complexes'):
      return

    if not cuid is None and cuid in self.Complexes:
      _status = self.Complexes[cuid].step.current
    else:
      _status = []
      for _idx, _item in self.Complexes.items():
        if not isinstance(_item, (dict)):
          continue

        _status.append((_idx, _item.step.current))

    return _status

  @property
  def status(self):
    return self.get_status()

from ..sieveaibase import DictConfig

class Atom(DictConfig):
  def __init__(self, *args, **kwargs):
    self.update(kwargs)

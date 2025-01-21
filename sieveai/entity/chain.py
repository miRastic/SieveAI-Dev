from ..sieveaibase import DictConfig

class Chain(DictConfig):
  def __init__(self, *args, **kwargs):
    self.update(kwargs)

class Chains(DictConfig):
  def __init__(self, *args, **kwargs):
    self.update(kwargs)

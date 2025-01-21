from ..sieveaibase import DictConfig

class Residue(DictConfig):
  def __init__(self, *args, **kwargs):
    self.update(kwargs)

class Residues(DictConfig):
  def __init__(self, *args, **kwargs):
    self.update(kwargs)

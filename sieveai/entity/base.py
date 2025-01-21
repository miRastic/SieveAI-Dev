from ..sieveaibase import DictConfig

class MoleculeBase(DictConfig):
  def __init__(self, *args, **kwargs):
    kwargs['formats'] = DictConfig()
    self.update(kwargs)

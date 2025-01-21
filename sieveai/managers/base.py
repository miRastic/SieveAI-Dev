from ..sieveaibase import DictConfig, SieveAIBase

class ManagerBase(SieveAIBase):
  name = 'SieveAI'
  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)

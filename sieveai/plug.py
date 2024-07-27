
from UtilityLib.lib.entity import EntityPath
from UtilityLib.lib.obj import ObjDict as DictConfig
from UtilityLib.lib.step import StepManager

from UtilityLib import ProjectManager

from .__metadata__ import __version__, __build__

class SieveAIBase(ProjectManager):
  name = 'SieveAI'
  version = __version__
  ObjDict = DictConfig
  SETTINGS = DictConfig()
  path_base = None
  multiprocessing = True

  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)

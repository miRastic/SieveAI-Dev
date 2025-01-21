# Quick Test
```python
# import sys as SYS
# SYS.path.append("/home/vishalkumarsahu/UtilityLib")
# SYS.path.append("/home/vishalkumarsahu/SieveAI-Dev")

from UtilityLib.lib.schedule import ScheduleManager
from sieveai.managers.manager import Manager

from UtilityLib.lib.schedule import ScheduleManager
from sieveai.managers.manager import Manager

def _man_cb(self, *args, **kwargs):
    self.get_file(f"https://example.com/SieveAI-Job-({self.time}):{_done}-{_total}")

_manager = Manager(path_base="/mnt/DataDrive/MDD/T0096--DevWork/SieveAI/Docking-Test-2/Protein-Ligand-2", log_level='debug', Report_CallBack=_man_cb, Report_Interval=(6,), Report_Check_Interval=(30, 'seconds'))
_manager.handle_process()

```
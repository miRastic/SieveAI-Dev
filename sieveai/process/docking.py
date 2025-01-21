from .base import PluginBase
from ..sieveaibase import DictConfig

class PluginDockingBase(PluginBase):
  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)
    self.path_sieveai_docking = (self.path_base / 'docking').validate()
    self.path_sieveai_analysis = (self.path_base / 'analysis').validate()

    self.path_plugin_docking = self.SETTINGS.plugin_data[self.plugin_uid].path_plugin_docking = (self.path_sieveai_docking / self.plugin_uid).validate()
    self.path_plugin_analysis = self.SETTINGS.plugin_data[self.plugin_uid].path_plugin_analysis = (self.path_sieveai_analysis / self.plugin_uid).validate()

  def _restore_progress(self, *args, **kwargs):
    _plugin_data_ref = self.SETTINGS.plugin_data[self.plugin_uid]
    if 'Complexes' in _plugin_data_ref:
      self.Complexes = _plugin_data_ref.Complexes
    else:
      self.Complexes = DictConfig()

    if 'Receptors' in _plugin_data_ref:
      self.Receptors = _plugin_data_ref.Receptors
    else:
      self.Receptors = DictConfig()

    if 'Ligands' in _plugin_data_ref:
      self.Ligands = _plugin_data_ref.Ligands
    else:
      self.Ligands = DictConfig()

  def _update_progress(self, *args, **kwargs):
    if hasattr(self, "Complexes"):
      self.SETTINGS.plugin_data[self.plugin_uid].Complexes = self.Complexes

    if hasattr(self, "Receptors"):
      self.SETTINGS.plugin_data[self.plugin_uid].Receptors = self.Receptors

    if hasattr(self, "Ligands"):
      self.SETTINGS.plugin_data[self.plugin_uid].Ligands = self.Ligands

    self.save_progress()

  def post_docking(self, *args, **kwargs):
    _compressed_path = (self.path_sieveai_docking / self.plugin_uid).with_suffix('.tar.gz')

    if (_compressed_path.exists()):
      self.backup(_compressed_path)

    # Individually compressed file and backup
    # self.tgz(self.path_sieveai_docking / self.plugin_uid)

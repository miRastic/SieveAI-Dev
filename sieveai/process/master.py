from .base import CoreBase

class Master(CoreBase):
  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)

  def process(self, *args, **kwargs):
    self.update_attributes(self, kwargs)

    print('Process starting')

    if self.SETTINGS.user.path_base:
      self.path_base = self.SETTINGS.user.path_base

    for _wf_step in self.PB(list(self.iterate(self.SETTINGS.user.workflow_order))):
      _msg = f"Starting workflow {_wf_step.upper()}"
      self.log_info("="*len(_msg))
      self.log_info(_msg)
      self.log_info("="*len(_msg))
      for _plugin_uid in self.iterate(self.SETTINGS.user.workflow[_wf_step]):
        if not isinstance(self.SETTINGS.plugin_refs[_wf_step], (dict)):
          self.SETTINGS.plugin_refs[_wf_step] = self.ObjDict()

        # Handle if plugin is not found.
        self.SETTINGS.plugin_refs[_wf_step][_plugin_uid] = self.get_plugin(_plugin_uid)

        self.SETTINGS.plugin_data[_plugin_uid] = self.SETTINGS.plugin_refs[_wf_step][_plugin_uid](path_base=self.path_base, SETTINGS=self.SETTINGS)

        self.log_info(f"Booting {_wf_step.upper()}:{_plugin_uid}...")
        self.SETTINGS.plugin_data[_plugin_uid].boot()
        self.SETTINGS.plugin_data[_plugin_uid].run()
        self.SETTINGS.plugin_data[_plugin_uid].shutdown()
        # self.log_error(f"MASTER_01: Workflow step {_wf_step} has no plugin or you might not want this step to do anything.")
        # self.log_error("MASTER_02: No workflow steps are found. Ignore if you want to run it without any workflow step.")

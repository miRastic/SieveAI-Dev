from ..process.converter import PluginConverterBase

class OpenBabel(PluginConverterBase):
  is_ready = False
  plugin_name = "OpenBabel"
  plugin_uid = "OpenBabel"
  plugin_version = "1.0"
  assignments = ['conversion']
  current_assignment = None
  url = "https://github.com/openbabel/openbabel"

  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)

  def setup(self, *args, **kwargs):
    self.update_attributes(self, kwargs)

  def py_convert_string(self, *args, **kwargs):
    from openbabel import openbabel as OBabel
    _source_text = args[0] if len(args) > 0 else kwargs.get('path_source')
    _path_target = args[0] if len(args) > 0 else kwargs.get('path_target')

    _format_to = args[1] if len(args) > 1 else kwargs.get('format_to')
    _format_from = args[2] if len(args) > 2 else kwargs.get('format_from')
    _addh = args[3] if len(args) > 3 else kwargs.get('addh', False)

    # Check if to and from formats are valid for OpenBabel
    _obc = OBabel.OBConversion()
    _obc.SetInAndOutFormats(_format_from, _format_to)

    _mol = OBabel.OBMol()
    # Open Babel will uncompress .gz files automatically
    _obc.ReadString(_mol, _source_text)

    # Optionally add hydrogens
    if _addh:
      _mol.AddHydrogens()

    _obc.WriteFile(_mol, _path_target)

  def py_convert(self, *args, **kwargs):
    from openbabel import openbabel as OBabel
    _path_source = kwargs.get('path_source', args[0] if len(args) > 0 else None)
    _path_target = kwargs.get('path_target', args[1] if len(args) > 1 else None)

    _format_to = kwargs.get('format_to', args[2] if len(args) > 2 else _path_source.suffix)
    _format_from = kwargs.get('format_from', args[3] if len(args) > 3 else _path_target.suffix)

    _addh = kwargs.get('addh', args[4] if len(args) > 4 else False)

    # Check if to and from formats are valid for OpenBabel
    _obc = OBabel.OBConversion()
    _obc.SetInAndOutFormats(_format_from, _format_to)

    _mol = OBabel.OBMol()
    # Open Babel will uncompress .gz files automatically
    _obc.ReadFile(_mol, str(_path_source))

    # Optionally add hydrogens
    if _addh:
      _mol.AddHydrogens()

    _obc.WriteFile(_mol, str(_path_target))

  def bulk_convert(self, *args, **kwargs):
    # Use multiprocess
    pass

  def convert(self, *args, **kwargs):
    _path_source = kwargs.get('path_source', args[0] if len(args) > 0 else None)
    _path_target = kwargs.get('path_target', args[1] if len(args) > 1 else None)

    # _command = f"""obabel -i{_file_ext} {_mol_path} -o{_ext_to} -O {_converted_path} """
    _res = self.cmd_run("obabel",
                             str(_path_source),
                             "-O", str(_path_target),
                             "-h", "--quiet")
    return _res

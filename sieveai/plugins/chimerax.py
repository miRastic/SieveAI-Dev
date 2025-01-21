from ..process.analysis import PluginAnalysisBase
from ..process.converter import PluginConverterBase
from ..sieveaibase import EntityPath

class ChimeraX(PluginAnalysisBase, PluginConverterBase):
  is_ready = False
  plugin_name = "ChimeraX"
  plugin_uid = "ChimeraX"
  assignments = ['analysis', 'conversion', 'sync']
  current_assignment = None
  url = "https://www.cgl.ucsf.edu/chimerax/docs/user/index.html"

  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)
    self.require('requests', 'REQUESTS')
    self.require('json', 'JSON')
    self.require('pandas', 'PD')
    self.require('re', 'RegEx')
    self.re_contacts = self.RegEx.compile(f"(\d+) contacts")
    self.re_hbonds = self.RegEx.compile(f"(\d+) H-bonds")

    self._set_default_vars()

  def _set_default_vars(self):
    self.suffix_jpeg_contacts = "--contacts.jpeg"
    self.suffix_jpeg_hbonds = "--hbonds.jpeg"
    self.suffix_jpeg_full = "--full.jpeg"

  def start_remote(self, *args, **kwargs) -> None:
    _start_chimerax = "chimerax --cmd 'remotecontrol rest start port 45385 json 1' &"
    self.OS.system(_start_chimerax)

  def request(self, *args, **kwargs):
    """
    Example: .request(params={"command": "surface #1; measure volume #1;"})

    """
    _url = kwargs.get("url", args[0] if len(args) > 0 else "http://127.0.0.1:45385/run")
    _params = kwargs.get("params", args[1] if len(args) > 1 else {})
    _return_type = kwargs.get("return_type", args[2] if len(args) > 2 else "json")
    _method = kwargs.get("method", args[3] if len(args) > 3 else 'get')

    if not _url:
      return None

    if _method == 'post':
      _r = self.REQUESTS.post(url=_url, data=self.JSON.dumps(_params))
    else:
      _r = self.REQUESTS.get(url=_url, params=_params)

    # Return other requests
    if _r.status_code == 200 and _return_type == 'json':
      _r = _r.json()

    return _r

  def exe_cxc_file(self, file_path=None):
    if file_path is None:
      return

    _res = self.cmd_run(*["chimerax",
      "--cmd", f"open {file_path}",
      "--silent",
      "--offscreen",
    ])
    return _res

  def _parse_hbond_line(self, line):
    _result = None
    if "#" in line:
      pass
    elif "/" in line:
      # Since Model ID is 1 and only Chain ID is given so appending to keep the syntax intact
      line = str(line).replace("/", "Structure #1/")
    else:
      raise Exception("Unknown type of col separators.")

    cols = line.split("#")

    if len(cols):
      try:
        # Use Second Column to get Donor
        donor = tuple(cols[1].split()[:4])
        # Use Third Column to get acceptor
        acceptor = tuple(cols[2].split()[:4])
        # Use fourth colun to get Hydrogen and HBond length
        hydrogen = tuple(cols[3].split()[:4])
        _dis_da, _dis_dha = tuple(cols[3].split()[-2:])
        _result = {
          "donor": donor,
          "acceptor": acceptor,
          "hydrogen": hydrogen,
          "distance_DA": _dis_da,
          "distance_DHA": _dis_dha
        }
      except:
        ...

    return _result

  def _parse_hbonds_file(self, file_path):
    _hb_attribs = []
    file_path = EntityPath(file_path)
    if file_path.exists():
      _res_line_flag = False
      key_term = 'H-bonds'
      for line in file_path.readlines():
        line = line.strip()
        # print(_res_line_flag, search_regex.search(line))
        if _res_line_flag and not line.startswith(key_term) and "#" in line:
          _res = self._parse_hbond_line(line)
          if _res:
            _hb_attribs.append(_res)
        if not _res_line_flag and self.re_hbonds.search(line):
          _res_line_flag = True
          if not int(self.re_hbonds.search(line).group(1)) > 0:
            return _hb_attribs

    return _hb_attribs

  def _parse_contacts_line(self, line):
    _result = None
    if "#" in line:
      pass
    elif "/" in line:
      # Since Model ID is 1 and only Chain ID is given so appending to keep the syntax intact
      line = str(line).replace("/", "Structure #1/")
    else:
      self.log_error("ChimeraX: Unknown type of col separators.")

    _cols = line.split("#")
    # print(cols); self.log_error("Unknown type of col separators.")

    if len(_cols):
      # Use Second Column to get Atom1
      _atom1 = tuple(_cols[1].split()[:4])
      # Use Third Column to get Atom2
      _atom2 = tuple(_cols[2].split()[:4])
      # Use fourth colun to get Hydrogen and HBond length
      _overlap = _cols[2].split()[-2]
      _distance = _cols[2].split()[-1]
      _result = {
        "atom1": _atom1,
        "atom2": _atom2,
        "overlap": _overlap,
        "distance": _distance
      }

    return _result

  def _parse_contacts_file(self, file_path):
    file_path = EntityPath(file_path)

    _contact_attrib = []
    if file_path.exists():
      _res_line_flag = False

      for line in file_path.readlines():
        line = line.strip()
        if _res_line_flag and not len({"atom1", "atom2"} & set(line.split())):
          _res = self._parse_contacts_line(line)
          if _res:
            _contact_attrib.append(_res)
        if not _res_line_flag and self.re_contacts.search(line):
          _res_line_flag = True
          if not int(self.re_contacts.search(line).group(1)) > 0:
            return _contact_attrib

    return _contact_attrib

  _atom_identity_keys = ("model_id", "sub_model_id", "chain", "resname", "resid", "atom", "atom_type")
  def _parse_atom_identity(self, atom_details: tuple = ()):
    if atom_details and type(atom_details) is tuple and len(atom_details) == 4:
      atom_details_model = atom_details[0].split("/")[0]
      atom_details_chain = atom_details[0].split("/")[1]
      atom_details_resname = atom_details[1]
      atom_details_resid = atom_details[2]
      atom_details_atom = atom_details[3]

      model_id = atom_details_model
      sub_model_id = None
      if "." in atom_details_model:
        model_id = atom_details_model.split(".")[0]
        sub_model_id = atom_details_model.split(".")[1]

      __result = {
        "model_id": model_id,
        "sub_model_id": sub_model_id,
        "chain": atom_details_chain,
        "resname": atom_details_resname,
        "resid": atom_details_resid,
        "atom": atom_details_atom,
        "atom_type": None,
      }

      return __result.values()
    else:
      raise Exception(f"Problem in atom records {atom_details}")

  def parse_contacts(self, file_path):
    _contacts = self.DF(self._parse_contacts_file(file_path))

    if not _contacts.shape[0]:
        return None

    for _atomN in ['atom1', 'atom2']:
      _atomN_cols = [f"{_atomN}__{_c}" for _c in self._atom_identity_keys]

      _contacts[_atomN_cols] = _contacts.apply(lambda _x: self._parse_atom_identity(_x[_atomN]), result_type='expand', axis='columns')

      if _atomN in _contacts.columns:
        _contacts.drop([_atomN], axis=1, inplace=True)

    return _contacts

  def parse_hbonds(self, file_path):
    _hbonds = self.DF(self._parse_hbonds_file(file_path))

    if not _hbonds.shape[0]:
      return None

    for _atomN in ['donor', 'acceptor', 'hydrogen']:
      _atomN_cols = [f"{_atomN}__{_c}" for _c in self._atom_identity_keys]

      _hbonds[_atomN_cols] = _hbonds.apply(lambda _x: self._parse_atom_identity(_x[_atomN]), result_type='expand', axis='columns')

      if _atomN in _hbonds.columns:
        _hbonds.drop([_atomN], axis=1, inplace=True)

    return _hbonds



  def setup(self, *args, **kwargs):
    self.update_attributes(self, kwargs)

  def boot(self, *args, **kwargs):
    self.log_debug('CHIMERAX_01: Boot method directly controlled by the referring plugin.')
    return self

  def run(self, *args, **kwargs):
    self.log_debug('CHIMERAX_02: Run method directly controlled by the referring plugin.')
    return self

  def shutdown(self, *args, **kwargs):
    self.log_debug('CHIMERAX_03: Shutdown method directly controlled by the referring plugin.')
    return self


  # RESUABLE STRINGS AND COMMANDS

  def get_cmd_contacts(self, *args, **kwargs):
    _model_id = kwargs.get('model_id', args[0] if len(args) > 0 else 2)
    return f"contacts #{_model_id} restrict cross reveal t radius 0.05 dashes 25 sel t; sel sel & protein; label sel bgColor #00000099 color white; label height 0.7;"

  def get_cmd_hbonds(self, *args, **kwargs):
    _model_id = kwargs.get('model_id', args[0] if len(args) > 0 else 2)
    return f"hbonds #{_model_id} restrict cross reveal t dashes 25 sel t showDist true; sel sel & protein; label sel bgColor #00000099 color white; label height 0.7; color #{_model_id} #e01b24ff models;"

  def get_html_head(self, *args, **kwargs):
    return """
<h1>Docking Analysis</h1>
<p></p>
<a href="cxcmd:set bg white; graphics silhouettes f; lighting depthCue t;" style="color: darkred;">Set Graphics</a>

<p></p>
<a href="cxcmd:close;" style="color: darkred;">Close All</a>
"""

  def get_contact_calc_html(self, *args, **kwargs):
    _contacts_count = kwargs.get('contact_count', args[0] if len(args) > 0 else 'NA')
    _contacts_img_path = kwargs.get('contacts_img_path', args[1] if len(args) > 1 else 'contacts' + self.suffix_jpeg_contacts)

    return f"""
  <lh>Contacts [{_contacts_count}]</lh>
  <li><input type='checkbox' /><a href="cxcmd:close #1.1; ~label; {self.get_cmd_contacts()} view sel; zoom 0.9;">Calculate & Label</a></li>
  <li><input type='checkbox' /><a href="cxcmd:~sel; save {_contacts_img_path}; ">Save</a></li>
"""

  def get_hbonds_calc_html(self, *args, **kwargs):
    _hbonds_count = kwargs.get('hbond_count', args[0] if len(args) > 0 else 'NA')
    _hbonds_img_path = kwargs.get('hbonds_img_path', args[1] if len(args) > 1 else 'hbonds' + self.suffix_jpeg_hbonds)

    return f"""
  <lh>H-Bonds [{_hbonds_count}]</lh>
  <li><input type='checkbox' /><a href="cxcmd:close #1.1; ~label; {self.get_cmd_hbonds()} view sel; zoom 0.9;">Calculate & Label</a></li>
  <li><input type='checkbox' /><a href="cxcmd:~sel; save {_hbonds_img_path}; ">Save</a></li>
"""

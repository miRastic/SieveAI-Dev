__build__ = "20241024"

try:
  from importlib.metadata import distribution as _DIST
  _DIST_INFO = _DIST(__package__ or __name__)
  _DIST_META = dict(_DIST_INFO.metadata)
  __version__ = _DIST_META['Version']
  __description__ = _DIST_META['Summary']
  __name__ = _DIST_META['Name']
except Exception as _e: # for Dev
  __version__ = "0.8.Dev"
  __description__ = "Dev"
  __name__ = __package__

import os
# Minescript strips environment variables — restore critical ones before any imports
if "PATH" not in os.environ:
	os.environ["PATH"] = ""

# parso/jedi need a home directory for caching; Minescript strips USERPROFILE etc.
if "USERPROFILE" not in os.environ:
	_home = os.path.expanduser("~") if os.name == "nt" else "/tmp"
	# expanduser may itself fail if env is totally empty, fall back to a safe default
	if _home == "~" or not _home:
		_home = os.path.join(os.environ.get("SystemDrive", "C:"), os.sep, "Users", "Default")
	os.environ["USERPROFILE"] = _home
	os.environ["HOMEPATH"] = _home
	os.environ.setdefault("HOMEDRIVE", os.environ.get("SystemDrive", "C:"))
	os.environ.setdefault("HOME", _home)

from lib.ui import FluxusApp


if __name__ == "__main__":
	app = FluxusApp()
	app.run()
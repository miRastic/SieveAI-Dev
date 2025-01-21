# <a name="dependencies"></a>SieveAI Setup: Dependencies and Requirements

## Python (version >= 3.10)
- [Download](https://www.python.org/downloads/) and install Python and setup PIP package manager

## ChimeraX (version >= 1.7)
- Step 1: Download Chimerax from [download page](https://www.rbvi.ucsf.edu/chimerax/download.html)
- Step 2: Install ChimeraX
  - Ubuntu: Download .deb file and install using `sudo apt-get install ./ucsf-chimerax_<VERSION>.deb`
  - Windows: Download .exe file and install normally
- Step 3: Add ChimeraX installation bin directory to PATH/Path environmental variables.
- Step 4: Confirm ChimeraX availble through commandline chimerax

## AutoDockVINA (version >= 1.2.3)
  * Step 1: Navigate to [vina binary on GitHub](https://github.com/ccsb-scripps/AutoDock-Vina/releases/tag/v1.2.3)
  * Ubuntu 20 LTS
    - Step 2: Download `vina_1.2.3_linux_x86_64` (for Linux)
    - Step 3: Rename downloaded file to `vina` and move to `/opt/AutoDock/` in Ubuntu
    - Step 4: Add `/opt/AutoDock/` to `PATH` [see help](https://askubuntu.com/q/60218).
  * Windows
    - Step 2: Download `vina_1.2.3_windows_x86_64.exe` (for windows)
    - Step 3: Rename downloaded file to `vina` and move it to `C:\Program Files\AutoDockVINA`.
    - Step 4: Add directory to environmental variables. [see help](https://stackoverflow.com/a/9546345)
  * Step 5: Test `vina` command output in terminal.

## AutoDock Tools/MGL Tools (version ~1.5.7)
  - Step 1: Download [ADFR Suit for Linux/Windows](https://ccsb.scripps.edu/adfr/downloads/) and install as per given instructions
  - Step 2: Add the installation path to `PATH` (Ubuntu) or `path` environmental variables (Windows).
  - Step 3: Make sure that `vina`, `prepare_ligand`, `mk_prepare_ligand` and `prepare_receptor` commands available through commandline

## OpenBabel (version ~3)
  - Ubuntu 20 LTS
    * STEP 1: `sudo apt-get install openbabel`
  - Windows
    * Get OpenBabel download from [here](https://openbabel.org/docs/dev/Installation/install.html)
  - Add `obabel` path to environment PATH variables
  - Confirm `obabel` is available through commandline

## FreeSASA (Optional)
  * Follow instructions at https://freesasa.github.io/
  * Download https://freesasa.github.io/freesasa-2.0.3.tar.gz and extract
  * Install using `make` (Refer provider's installation guide)
```
./configure
make
sudo make install
freesasa -h
```

# <a name="installation"></a>SieveAI Installation

* Release from Pypi repository: `pip install sieveai`
* Latest update from github: `pip install git+https://github.com/VishalKumarSahu/SieveAI`

> Copyright
&copy; 2023: Dr. Soumya Basu, Vishal Kumar Sahu, ...

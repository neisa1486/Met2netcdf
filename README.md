# Antarctic Meteorological Data Converter

This project retrieves meteorological observation data from the **British Antarctic Survey (BAS) READER dataset** and converts raw `.dat` files into monthly NetCDF files with metadata following CF conventions.


## Repository Structure

```text
project/

├── src/
│   └── main.py
│
├── config/
│   └── config.yaml
│
├── environment.yaml
│
├── .gitignore
│
└── README.md
```

Generated output files are stored locally in the `data/` folder.

Generated data files are excluded from version control.

---

## Environment Setup

The project uses Conda for dependency management.

Create the environment from the provided file:

```bash
conda env create -f environment.yaml
```

Activate the environment:

```bash
conda activate bas-reader-netcdf
```

The `environment.yaml` file contains all required dependencies for running the project.

---

## Configuration

The program is configured through `config/config.yaml`.
The `metadata` section in `config.yaml` defines station metadata, global dataset attributes, and variable-specific attributes written to the NetCDF output files.

Before running the script, update the configuration file to define:

- **category** → Select which BAS dataset category to use  
  (`SURFACE`, `AWS`, `UPPER_AIR`, `POLENET_AWS`)

- **base_url** → The URL where the source `.dat` files are located

- **files** → The station data files you want to process

- **output folder** → The local folder where generated NetCDF files will be stored

- **schedule settings** → Choose whether the script should run once or continuously

Example:

```yaml
input:
  category: "SURFACE"
  base_url: "https://legacy.bas.ac.uk/met/READER/ANTARCTIC_METEOROLOGICAL_DATA/SURFACE/"
  files:
    - "Asuka_surface.dat"

output:
  folder: "data/"

schedule:
  enabled: false
  interval_seconds: 30
```

If `schedule.enabled` is set to `false`, the script runs once.

If `schedule.enabled` is set to `true`, the script continuously checks for updated source files at the specified interval.

## Running the Program

Run the script with:

```bash
python src/main.py
```

The script will:

1. Check whether the remote source file has changed  
2. Download the `.dat` file  
3. Parse meteorological observations  
4. Convert observations into a pandas DataFrame  
5. Group data by year and month  
6. Convert monthly data into NetCDF files  
7. Save the output locally  

---


## Output

The program creates monthly NetCDF files organized as:

```text
data/<category>/<station>/<year>/
```

Example:

```text
data/SURFACE/Adelaide/1990/Adelaide_1990_01.nc
```

Generated data files are local output and should not be stored in the Git repository.

---

## Input Data Source

Data is provided by the **British Antarctic Survey READER Project**.


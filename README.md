# Antarctic Meteorological Data Converter

This project retrieves meteorological observation data from the **British Antarctic Survey (BAS) READER dataset** and converts raw observation files into monthly NetCDF files with metadata following the **CF-1.11** and **ACDD-1.3** conventions.

---

## Repository Structure

```text
/

├── config/
│   └── config.yaml
│
├── src/
│   ├── main.py
│   ├── downloader.py
│   ├── parser.py
│   ├── netcdf_writer.py
│   ├── metadata.py
│   ├── scheduler.py
│   └── utils.py
│
├── data/                 # Generated NetCDF files
│
├── environment.yaml
├── .gitignore
└── README.md
```

Generated NetCDF files are written to the `data/` directory and are excluded from version control.

---

## Environment Setup

The project uses Conda for dependency management.

Create the environment:

```bash
conda env create -f environment.yaml
```

Activate the environment:

```bash
conda activate MET
```

The `environment.yaml` file contains all required dependencies.

---

## Configuration

Project settings are defined in `config/config.yaml`.

The configuration specifies:

- dataset category
- source URL
- station files to process
- output directory
- scheduling options
- metadata written to the NetCDF files

Example:

```yaml
input:
  category: SURFACE
  base_url: https://legacy.bas.ac.uk/met/READER/ANTARCTIC_METEOROLOGICAL_DATA/SURFACE/
  files:
    - Amundsen_Scott_surface.dat

output:
  folder: data/

schedule:
  enabled: false
  interval_seconds: 30
```

If `schedule.enabled` is `false`, the program runs once.

If `true`, it periodically checks the source files for updates and regenerates affected NetCDF files.

---

## Running the Program

Run:

```bash
python src/main.py
```

The program will:

1. Check whether the source data has changed
2. Download the observation file if needed
3. Parse the observations into a pandas DataFrame
4. Group the data into monthly datasets
5. Create or update monthly CF-compliant NetCDF files
6. Save the files to the configured output directory

---

## Output

Monthly NetCDF files are written to:

```text
data/<category>/<station>/<year>/
```

Example:

```text
data/SURFACE/Amundsen_Scott/2026/Amundsen_Scott_2026_07.nc
```

Each NetCDF file contains:

- monthly observations
- station metadata
- CF-1.11 compliant metadata
- recommended ACDD-1.3 discovery metadata

Generated files are local output and are not intended to be committed to the repository.

---

## Standards

The generated NetCDF files are designed to follow:

- CF Conventions 1.11
- ACDD 1.3

The files have been validated using the IOOS Compliance Checker.

---

## Input Data Source

Observation data are provided by the **British Antarctic Survey (BAS) READER Project**.


import os
import json
import time
import yaml
import pandas as pd
import xarray as xr
import requests
from urllib.parse import urljoin
from io import StringIO


# =========================
# LOADING CONFIG FILE
# =========================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.yaml")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

OUTPUT_DIR = os.path.join(BASE_DIR, config["output"]["folder"])
os.makedirs(OUTPUT_DIR, exist_ok=True)

STATE_FILE = os.path.join(BASE_DIR, config["state"]["file"])

# =========================
# STATE - Tracks remote source file changes to avoid unnecessary processing
# =========================

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


# =========================
# GET FILE URLS FROM CONFIG
# =========================

def get_dat_files():
    base_url = config["input"]["base_url"]
    files = config["input"]["files"]
    return [urljoin(base_url, filename) for filename in files]


# =========================
# READING THE .dat FILES 
# =========================

def read_dat_file(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    text = response.text
    lines = text.splitlines()
    station_name = lines[0].strip()
    parts = lines[2].split()
    latitude = float(parts[1])
    longitude = float(parts[3])
    height = float(parts[5].replace("m", ""))

    columns = [
        "year",
        "month",
        "day",
        "hour",
        "minute",
        "sea_pressure",
        "station_pressure",
        "temperature",
        "wind_speed",
        "wind_direction"]

    df = pd.read_csv(
        StringIO(text),
        sep=r"\s+",
        skiprows=7,
        names=columns,
        na_values=-999)

    df["time"] = pd.to_datetime(
        df[["year", "month", "day", "hour", "minute"]])

    df = df.set_index("time")
    df = df.drop(columns=["year", "month", "day", "hour", "minute"])

    return df, station_name, latitude, longitude, height

# =========================
# APPLY METADATA
# =========================

def apply_metadata(ds, station_name, latitude, longitude, height):
    station_meta = config["metadata"]["station"]
    global_meta = config["metadata"]["global"]
    variable_meta = config["metadata"]["variables"]

    # -------------------------
    # Coordinate variables
    # -------------------------
    ds["latitude"] = latitude
    ds["longitude"] = longitude
    ds["height"] = height

    ds["latitude"].attrs = {
        "standard_name": station_meta["latitude"]["standard_name"],
        "long_name": station_meta["latitude"]["long_name"],
        "units": station_meta["latitude"]["units"]}

    ds["longitude"].attrs = {
        "standard_name": station_meta["longitude"]["standard_name"],
        "long_name": station_meta["longitude"]["long_name"],
        "units": station_meta["longitude"]["units"]}

    ds["height"].attrs = {
        "standard_name": station_meta["height"]["standard_name"],
        "long_name": station_meta["height"]["long_name"],
        "units": station_meta["height"]["units"],
        "positive": station_meta["height"]["positive"],
        "axis": station_meta["height"]["axis"]}

    ds["time"].attrs = {
        "standard_name": "time",
        "long_name": "time"}

    # -------------------------
    # Variable metadata - only applies if the variable exists in the dataset
    # -------------------------
    for var in variable_meta:
        if var in ds:
            ds[var].attrs = variable_meta[var]

    # -------------------------
    # Global metadata - only applies if the value is not empty, and formats the value with the station name if it's a string
    # -------------------------
    for key, value in global_meta.items():
        if value != "":
            if isinstance(value, str):
                value = value.format(station_name=station_name)
            ds.attrs[key] = value

    # -------------------------
    # Dataset-specific metadata
    # -------------------------

    ds.attrs["geospatial_lat_min"] = float(latitude)
    ds.attrs["geospatial_lat_max"] = float(latitude)
    ds.attrs["geospatial_lon_min"] = float(longitude)
    ds.attrs["geospatial_lon_max"] = float(longitude)

    ds.attrs["geospatial_bounds"] = f"POINT ({longitude} {latitude})"
    ds.attrs["geospatial_vertical_min"] = float(height)
    ds.attrs["geospatial_vertical_max"] = float(height)
    ds.attrs["geospatial_vertical_positive"] = station_meta["height"]["positive"]

    start_time = pd.to_datetime(ds.time.values[0])
    end_time = pd.to_datetime(ds.time.values[-1])
    ds.attrs["time_coverage_start"] = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    ds.attrs["time_coverage_end"] = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    ds.attrs["date_created"] = pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")

    return ds


# =========================
# SAVE MONTHLY NETCDF
# =========================

def save_monthly_netcdf(df, station_name, latitude, longitude, height, category):
    grouped = df.groupby([df.index.year, df.index.month])

    for (year, month), group in grouped:
        if group.empty:
            continue

        ds = xr.Dataset.from_dataframe(group)
        ds = apply_metadata(ds, station_name, latitude, longitude, height)

        safe_station_name = station_name.replace(" ", "_")

        category_folder = os.path.join(OUTPUT_DIR, category)
        station_folder = os.path.join(category_folder, safe_station_name)
        year_folder = os.path.join(station_folder, str(year))

        os.makedirs(year_folder, exist_ok=True)

        filename = f"{safe_station_name}_{year}_{month:02d}.nc"
        output_path = os.path.join(year_folder, filename)

        #Encoding settings for NetCDF4 output
        encoding = {}
        for var in ds.data_vars:
            encoding[var] = {"_FillValue": -999.0}
        
        encoding["time"] = {
            "dtype": "int32"}

        #Saving NetCDF file with specified encoding
        ds.to_netcdf(output_path, encoding=encoding)
        ds.close()
        print(f"Saved {output_path}")

# =========================
# RUN ONCE - Processes source files and creates or updates monthly NetCDF files when remote data has changed
# =========================

def run_once():
    state = load_state()
    dat_files = get_dat_files()
    category = config["input"]["category"]

    for url in dat_files:
        try:
            response = requests.head(url, timeout=30)
            last_modified = response.headers.get("Last-Modified", "")

            if state.get(url) == last_modified:
                print(f"Skipping unchanged file: {url}")
                continue

            print(f"Processing {url}")
            df, station_name, latitude, longitude, height = read_dat_file(url)
            save_monthly_netcdf(df, station_name, latitude, longitude, height, category)

            state[url] = last_modified

        except Exception as e:
            print(f"Failed for {url}: {e}")

    save_state(state)



# =========================
# RUN FOREVER
# =========================

def run_forever():
    interval = config["schedule"]["interval_seconds"]

    while True:
        print("Starting new run...")
        run_once()
        print(f"Sleeping for {interval} seconds...")
        time.sleep(interval)


# =========================
# MAIN
# =========================

if __name__ == "__main__":
    if config["schedule"]["enabled"]:
        run_forever()
    else:
        run_once()

"""
RF-EMF Urban Exposure Mapping Scripts
=====================================

This script generates standard RF-EMF exposure maps from an anonymized multi-band measurement dataset.

Main features:
- Reads RF-EMF measurement data from Excel
- Converts geographic coordinates from WGS84 (EPSG:4326) to Web Mercator (EPSG:3857)
- Performs spatial interpolation for each RF band
- Generates exposure heatmaps with:
    * hotspot countour based on the 85th percentile
    * measurement points
    * study area boundary
    * geographic coordinates
    * north arrow
    * 100m scale bar
    * colorbar in unit V/m

Expected columns:
     lat, lon, LTE800, GSM900, LTE1800, UMTS2100, LTE2600, 5G_3500

Author: Ejona Zeneli
License: MIT
"""

from pathlib import Path

import contextily as ctx
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Point, Polygon
from pyproj import Transformer
from scipy.interpolate import griddata
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter

#-------------------------------------------------------------------------
# Configuration
#-------------------------------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_DIR / "data" / "anonymized_dataset.xlsx"
OUTPUT_DIR = PROJECT_DIR / "outputs" / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

bands = ["LTE800", "GSM900", "LTE1800", "UMTS2100", "LTE2600", "5G_3500"]

grid_res = 400
heat_alpha = 0.72
cmap_name = "jet"
SCALEBAR_LENGTH_M = 100

# -------------------------------------------------------------------------
# Utility Functions
# -------------------------------------------------------------------------

# =========================================================================
# READ DATA
# =========================================================================

df = pd.read_excel(INPUT_FILE)
df.columns = df.columns.astype(str).str.strip()

required_cols = ["lat", "lon"] + bands
missing = [c for c in required_cols if c not in df.columns]

if missing:
    raise ValueError(f"Mungojne keto kolona ne Excel: {missing}")

for col in required_cols:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=required_cols).copy()

print("Kontroll koordinatash:")
print(df[["lat", "lon"]].describe())


# ============================================================
# COORDINATE TRANSFORMATION
# ============================================================

to_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
to_4326 = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

df["x"], df["y"] = to_3857.transform(df["lon"].values, df["lat"].values)


# ============================================================
# STUDY AREA POLYGON
# ============================================================

points_geom = [Point(xy) for xy in zip(df["x"], df["y"])]
study_polygon = Polygon([[p.x, p.y] for p in points_geom]).convex_hull

poly_x, poly_y = study_polygon.exterior.xy

minx, miny, maxx, maxy = study_polygon.bounds

pad_x = (maxx - minx) * 0.04
pad_y = (maxy - miny) * 0.04

minx -= pad_x
maxx += pad_x
miny -= pad_y
maxy += pad_y

extent = (minx, maxx, miny, maxy)


# ============================================================
# GRID + MASK
# ============================================================

grid_x, grid_y = np.meshgrid(
    np.linspace(minx, maxx, grid_res),
    np.linspace(miny, maxy, grid_res)
)

mask = np.zeros_like(grid_x, dtype=bool)

for i in range(grid_x.shape[0]):
    for j in range(grid_x.shape[1]):
        mask[i, j] = study_polygon.contains(Point(grid_x[i, j], grid_y[i, j]))


# ============================================================
# FORMATTERS
# ============================================================

def lon_formatter(x, pos):
    lon, lat = to_4326.transform(x, miny)
    return f"{lon:.4f}°E"


def lat_formatter(y, pos):
    lon, lat = to_4326.transform(minx, y)
    return f"{lat:.4f}°N"


# ============================================================
# CARTOGRAPHIC ELEMENTS
# ============================================================

def add_scalebar(ax, length_m=100):
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    x0 = xlim[0] + 0.08 * (xlim[1] - xlim[0])
    y0 = ylim[0] + 0.075 * (ylim[1] - ylim[0])
    x1 = x0 + length_m

    box_x0 = x0 - 18
    box_x1 = x1 + 18
    box_y0 = y0 - 22
    box_y1 = y0 + 32

    ax.add_patch(
        plt.Rectangle(
            (box_x0, box_y0),
            box_x1 - box_x0,
            box_y1 - box_y0,
            facecolor="white",
            edgecolor="black",
            linewidth=0.8,
            alpha=0.85,
            zorder=20
        )
    )

    ax.plot([x0, x1], [y0, y0], color="black", linewidth=4, zorder=21)
    ax.plot([x0, x0], [y0 - 6, y0 + 6], color="black", linewidth=2, zorder=21)
    ax.plot([x1, x1], [y0 - 6, y0 + 6], color="black", linewidth=2, zorder=21)

    ax.text(
        (x0 + x1) / 2,
        y0 + 10,
        f"{length_m} m",
        ha="center",
        va="bottom",
        fontsize=11,
        fontweight="bold",
        color="black",
        zorder=22
    )


def add_north_arrow(ax):
    ax.annotate(
        "N",
        xy=(0.925, 0.88),
        xytext=(0.925, 0.76),
        xycoords="axes fraction",
        textcoords="axes fraction",
        ha="center",
        va="center",
        fontsize=16,
        fontweight="bold",
        arrowprops=dict(
            facecolor="black",
            edgecolor="black",
            width=4,
            headwidth=13
        ),
        bbox=dict(
            facecolor="white",
            edgecolor="black",
            boxstyle="square,pad=0.25",
            alpha=0.85
        ),
        zorder=30
    )


# ============================================================
# LEGEND
# ============================================================

legend_elements = [
    Line2D([0], [0], color="blue", lw=3, label="Study area boundary"),
    Line2D(
        [0], [0],
        marker="o",
        color="royalblue",
        markerfacecolor="white",
        markersize=7,
        linestyle="None",
        markeredgewidth=1.5,
        label="Measurement points"
    ),
    Line2D([0], [0], color="cyan", lw=2.0, label="Hotspot threshold\n85th percentile")
]


# ============================================================
# CREATE INDIVIDUAL MAPS
# ============================================================

for band in bands:

    z = df[band].values

    print(f"\n{band}")
    print("Min:", np.nanmin(z))
    print("Max:", np.nanmax(z))
    print("Mean:", np.nanmean(z))

    grid_z_linear = griddata(
        points=(df["x"].values, df["y"].values),
        values=z,
        xi=(grid_x, grid_y),
        method="linear"
    )

    grid_z_nearest = griddata(
        points=(df["x"].values, df["y"].values),
        values=z,
        xi=(grid_x, grid_y),
        method="nearest"
    )

    grid_z = np.where(np.isnan(grid_z_linear), grid_z_nearest, grid_z_linear)
    grid_z_masked = np.ma.array(grid_z, mask=~mask)

    fig, ax = plt.subplots(figsize=(14, 10))

    fig.subplots_adjust(
        left=0.09,
        right=0.88,
        top=0.91,
        bottom=0.10
    )

    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)

    # --------------------------------------------------------
    # BETTER BASEMAP
    # --------------------------------------------------------
    try:
        ctx.add_basemap(
            ax,
            crs="EPSG:3857",
            source=ctx.providers.Esri.WorldImagery,
            zoom=18,
            attribution_size=6
        )
    except Exception as e:
        print(f"Satellite basemap nuk u ngarkua: {e}")
        try:
            ctx.add_basemap(
                ax,
                crs="EPSG:3857",
                source=ctx.providers.OpenStreetMap.Mapnik,
                zoom=17,
                attribution_size=6
            )
        except Exception as e2:
            print(f"OSM basemap nuk u ngarkua: {e2}")

    # --------------------------------------------------------
    # HEATMAP
    # --------------------------------------------------------
    im = ax.imshow(
        grid_z_masked,
        extent=extent,
        origin="lower",
        cmap=cmap_name,
        alpha=heat_alpha,
        zorder=2,
        interpolation="bilinear"
    )

    # --------------------------------------------------------
    # STUDY AREA BOUNDARY
    # --------------------------------------------------------
    ax.plot(
        poly_x,
        poly_y,
        color="blue",
        linewidth=3.2,
        zorder=5
    )

    # --------------------------------------------------------
    # MEASUREMENT POINTS
    # --------------------------------------------------------
    ax.scatter(
        df["x"],
        df["y"],
        s=42,
        facecolors="white",
        edgecolors="royalblue",
        linewidths=1.5,
        alpha=0.95,
        zorder=7
    )

    # --------------------------------------------------------
    # HOTSPOT CONTOUR
    # --------------------------------------------------------
    hotspot_thr = np.nanpercentile(z, 85)

    try:
        ax.contour(
            grid_x,
            grid_y,
            grid_z_masked,
            levels=[hotspot_thr],
            colors=["cyan"],
            linewidths=2.0,
            zorder=8
        )
    except Exception:
        pass

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------
    ax.set_title(
        f"{band} - Interpolated electric field exposure (V/m)",
        fontsize=18,
        fontweight="bold",
        pad=14
    )

    # --------------------------------------------------------
    # AXES COORDINATES
    # --------------------------------------------------------
    ax.xaxis.set_major_formatter(FuncFormatter(lon_formatter))
    ax.yaxis.set_major_formatter(FuncFormatter(lat_formatter))

    ax.tick_params(axis="both", labelsize=10, direction="out")

    ax.set_xlabel("Longitude", fontsize=12)
    ax.set_ylabel("Latitude", fontsize=12)

    # --------------------------------------------------------
    # COLORBAR
    # --------------------------------------------------------
    cbar = fig.colorbar(
        im,
        ax=ax,
        fraction=0.035,
        pad=0.025
    )

    cbar.set_label(
        "Electric field strength, E (V/m)",
        fontsize=12
    )

    cbar.ax.tick_params(labelsize=10)

    # --------------------------------------------------------
    # SCALEBAR + NORTH ARROW
    # --------------------------------------------------------
    add_scalebar(ax, SCALEBAR_LENGTH_M)
    add_north_arrow(ax)

    # --------------------------------------------------------
    # LEGEND OUTSIDE MAP, NO OVERLAP
    # --------------------------------------------------------
    ax.legend(
        handles=legend_elements,
        loc="upper center",
        bbox_to_anchor=(0.50, -0.10),
        ncol=3,
        fontsize=10,
        frameon=True,
        facecolor="white",
        edgecolor="gray"
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------
    output_file = os.path.join(
        OUTPUT_DIR,
        f"{band}_bands.png"
    )

    plt.savefig(
        output_file,
        dpi=300,
        facecolor="white",
        bbox_inches="tight",
        pad_inches=0.25
    )

    plt.close(fig)

    print(f"Saved: {output_file}")


print("\nDONE")
print("Figurat u ruajten ketu:")
print(OUTPUT_DIR)



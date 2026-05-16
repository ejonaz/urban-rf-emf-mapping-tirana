# Urban RF-EMF Mapping - Tirana

This repository contains Python scripts and an anonymized dataset for multi-band RF-EMF exposure mapping in urban areas of Tirana.

### Repository contents

'''text
urban-rf-emf-mapping-tirana/
     scripts/
         rf_emf_mapping_journal.py
     data/
         anonymized_dataset.xlsx
     outputs/
         figures/
     README.md
     requirements.txt
     LICENSE
'''

### Main features

The script generates journal-standard RF-EMF exposure maps with:

- measurements points and study area boundary.
- geographic coordinates on map borders;
- north arrow;
- 100 m distance spatial scale bar;
- colorbar with electric field values in V/m;
- hotspot contour based on the 85th percentile;
- multi-band exposure visualization;
- spatial interpolation of measured RF-EMF values;

### Measurement equipment

Measurements were collected using the NARDA SRM-3600 spectrum analyzer.

### Frequency bands

The dataset includes the following RF bands:

- 5G_3500
- LTE2600
- UMTS2100
- LTE1800
- GSM900
- LTE800

### Input dataset

Expected input file:

'''text
data/anonymized_dataset.xlsx
''''

Expected columns:

'''text
lat, lon, 5G_3500, LTE2600, UMTS2100, LTE1800, GSM900, LTE800

Electrical field values are expressed in V/m.

### Installation

Install dependencies with:

'''bash
pip install -r requirements.txt
'''

### Usage

Run the script from the repository root:

'''bash
python scripts/rm-emf_mapping_journal.py
'''

Output figures will be saved in:

'''text
outputs/figures/

### Data availability

An anonymized dataset is provided for reproducibility purposes. Coordinates are reounded to reduce spatial sensitivity while preserving the structure required for GIS-based analysis.

### License

This project is distributed under the MIT License.






















# Data Dictionary — Predicting Irrigation Need (S6E4)

All files are in `data/`. The dataset has an Indian agricultural context (seasons, crops, and regions reflect the Indian subcontinent).

---

## Files

| File | Rows | Description |
|---|---|---|
| `train.csv` | 630,000 | Labelled training data (IDs 0–629,999) |
| `test.csv` | 270,000 | Unlabelled test data (IDs 630,000–899,999) |
| `sample_submission.csv` | 270,000 | Submission template |

---

## Columns

### Identifier

| Column | Type | Description |
|---|---|---|
| `id` | int | Unique row identifier. Train: 0–629,999. Test: 630,000–899,999. |

---

### Soil Features

| Column | Type | Range | Description |
|---|---|---|---|
| `Soil_Type` | categorical | Clay, Loamy, Sandy, Silt | Texture class of the soil. Affects water retention: Clay > Silt > Loamy > Sandy. |
| `Soil_pH` | float | 4.80 – 8.20 | Acidity/alkalinity of the soil. Neutral is ~7.0; most crops prefer 5.5–7.5. |
| `Soil_Moisture` | float | 8.00 – 65.00 | Current moisture content of the soil (%). Higher values indicate less need for irrigation. |
| `Organic_Carbon` | float | 0.30 – 1.60 | Organic carbon content (%). Higher values improve water-holding capacity. |
| `Electrical_Conductivity` | float | 0.10 – 3.50 | Soil salinity proxy (dS/m). High values can stress crops and affect water uptake. |

---

### Weather Features

| Column | Type | Range | Description |
|---|---|---|---|
| `Temperature_C` | float | 12.00 – 42.00 | Ambient air temperature (°C). Higher temperatures increase evapotranspiration and irrigation demand. |
| `Humidity` | float | 25.00 – 95.00 | Relative humidity (%). Higher humidity reduces evaporation and irrigation need. |
| `Rainfall_mm` | float | 0.38 – 2,499.69 | Cumulative rainfall (mm). Strong negative driver of irrigation need. |
| `Sunlight_Hours` | float | 4.00 – 11.00 | Daily sunlight exposure (hours). More sun increases water loss via evapotranspiration. |
| `Wind_Speed_kmh` | float | 0.50 – 20.00 | Wind speed (km/h). Higher wind accelerates soil moisture loss. |

---

### Crop Features

| Column | Type | Values | Description |
|---|---|---|---|
| `Crop_Type` | categorical | Cotton, Maize, Potato, Rice, Sugarcane, Wheat | Type of crop grown. Different crops have different water requirements (e.g. Rice is high, Wheat is moderate). |
| `Crop_Growth_Stage` | categorical | Sowing, Vegetative, Flowering, Harvest | Current growth stage. Water demand peaks at Flowering and is lowest at Harvest. |
| `Season` | categorical | Kharif, Rabi, Zaid | Indian agricultural season. Kharif = monsoon (Jun–Oct), Rabi = winter (Nov–Apr), Zaid = summer (Apr–Jun). |

---

### Farm Management Features

| Column | Type | Values / Range | Description |
|---|---|---|---|
| `Irrigation_Type` | categorical | Canal, Drip, Rainfed, Sprinkler | Method of irrigation currently in use. Rainfed fields rely solely on rainfall. This is a predictor, not the target. |
| `Water_Source` | categorical | Groundwater, Rainwater, Reservoir, River | Source of water available for irrigation. |
| `Field_Area_hectare` | float | 0.30 – 15.00 | Size of the field (hectares). Larger fields may have more variable soil/moisture conditions. |
| `Mulching_Used` | binary | No, Yes | Whether mulching is applied. Mulching retains soil moisture and reduces irrigation frequency. |
| `Previous_Irrigation_mm` | float | 0.02 – 120.00 | Amount of irrigation applied in the previous cycle (mm). |
| `Region` | categorical | Central, East, North, South, West | Geographic region of the farm within India. Captures climate and agro-ecological variation. |

---

### Target Variable

| Column | Type | Values | Description |
|---|---|---|---|
| `Irrigation_Need` | categorical | Low, Medium, High | The level of irrigation required for the field. **Present in train only.** |

**Class distribution (train):**

| Class | Count | Share | Notes |
|---|---|---|---|
| Low | 369,917 | 58.7% | Field has sufficient moisture / rainfall |
| Medium | 239,074 | 37.9% | Moderate supplemental irrigation needed |
| High | 21,009 | 3.3% | Significant irrigation required — minority class |

The dataset is imbalanced: `High` is ~18× rarer than `Low`. Consider class-weighted models or oversampling strategies when targeting recall on the `High` class.

---

## Notes

- Data is **synthetically generated** by Kaggle from a real-world irrigation dataset, so it is clean with no missing values.
- The `Irrigation_Type` column (Drip, Sprinkler, Canal, Rainfed) describes the *current* irrigation method — it is a feature, not the label being predicted.
- Season names reflect the Indian crop calendar: Kharif crops (Rice, Cotton, Sugarcane) are grown in the monsoon, Rabi crops (Wheat, Potato) in winter, and Zaid crops in summer.

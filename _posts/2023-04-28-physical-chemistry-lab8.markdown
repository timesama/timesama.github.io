---
layout: post
title:  "Determination of Molar Mass from freezing point"
link_to_notebook: https://github.com/timesama/bgu-physical-chemistry-lab8/blob/main/bgu-physical-chemistry-lab8.ipynb
---

# Determination of Molar Mass from freezing point

The aim of the experiment if to calculate Molar Mass of compound (urine) after determination of its freezing point ($T_{fr}$) and to determine Vant-Hoff constant ($i$) for compounds under study. The $T_{fr}$ is measured with kryoscopy method, when solution is being cooled down with thermostate, and solution's tempreature is being measured with thermocouple. When $T_{fr}$ is achieved, usually over-freezing is observed in the time-temperature curve. The plateau after over-freeze corresponds to real freezing temperature of the solution. 

Throughout the experiment several referenced solutions are measured: distilled water and KCl. The $T_{fr} (water)$ is taken as calibration point for equipment, whereas KCl serves as checkpoint for the experiment, since theoretically $i(KCl)$ is approximately 2. Finally, solutions of urine with two different concentrations are measured. Given the high dilution of solutions, the equations suitable for ideal solutions are applicable as it will be shown further. It allows to say that $T_{fr}$ changes linearly with concentration ($m$).


## Import libraries


```python
import numpy as np # math
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit # fitting custom function
from matplotlib.dates import datestr2num 
from tabulate import tabulate
```

## Get seconds from time


```python
def get_sec(time_str):
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)
```

## Find the plateau (index) from the raw data

The plateau is determined as line, where temperature doesn't change more than by 0.5


```python
def find_plateau_index(y, threshold):
    for i in reversed(range(len(y))):
        if y[i] - threshold <= y[i-1] <= y[i] + threshold:
            last_index = i
        else:
            break
    return last_index
```

## Define compounds
compounds["short name of the experiment"] = { "filename": "filename.txt",
                     "title": "Title would appear on the plot", 
                     "plot_fmt": "colour of the plateau",
                     "plot_pos_x": 0,  Poistion of plot in general figure
                     "plot_pos_y": 0,
                     "calculate_molar_mass": False } Flag to (not) calculate molar mass

```python
compounds = {}
compounds["water_stir"] = { "filename": "2405_water_stir.txt",
                     "title": "Water stir", 
                     "plot_fmt": "r",
                     "plot_pos_x": 0, 
                     "plot_pos_y": 0,
                     "calculate_molar_mass": False }

compounds["water_no_stir"] = { "filename": "2405_water_nostir.txt",
                    "title": "Water no stir", 
                    "plot_fmt": "r",
                    "plot_pos_x": 0, 
                    "plot_pos_y": 1,
                    "calculate_molar_mass": False }

compounds["kcl"] =   { "filename": "2405_kcl.txt",
                     "title": "KCl", 
                     "plot_fmt": "g",
                     "plot_pos_x": 1, 
                     "plot_pos_y": 0,
                     "mass_solid": 1.0010,
                     "mass_water": 50.0023,
                     "calculate_molar_mass": True }

compounds["urea1"] = { "filename": "2405_urea1.txt",
                     "title": "Urea Concentrated", 
                     "plot_fmt": "b",
                     "plot_pos_x": 1, 
                     "plot_pos_y": 1,
                     "mass_solid": 1.0011,
                     "mass_water": 50.0078,
                     "calculate_molar_mass": True }

compounds["urea2"] = { "filename": "2405_urea05.txt",
                     "title": "Urea Diluted", 
                     "plot_fmt": "y",
                     "plot_pos_x": 2, 
                     "plot_pos_y": 0,
                     "mass_solid": 0.4999,
                     "mass_water": 50.0039,
                     "calculate_molar_mass": True }
```

## Read files, extract time and temperature values, find plateau 


```python
for type, info in compounds.items():
    time_abs, temperature = np.loadtxt(info["filename"], unpack=True, delimiter='\t', encoding = 'ascii', converters={0: get_sec})
    time_rel = time_abs - time_abs[0]
    idx = find_plateau_index(temperature, 0.05)

    compounds[type]["temperature"] = temperature
    compounds[type]["time_rel"] = time_rel
    compounds[type]["temperature_plateau"] = temperature[idx-1:]
    compounds[type]["time_rel_plateau"] = time_rel[idx-1:]
    compounds[type]["freezing_temperature"] = np.round_(np.mean(compounds[type]["temperature_plateau"]), decimals = 2, out = None)

temperature_water = (compounds["water_stir"]["freezing_temperature"] + compounds["water_no_stir"]["freezing_temperature"])/2
```

## Constants from the literature


```python
Molar_mass_kcl = 74.55
Molar_mass_urea = 60.06
Kf_water = 1.855
```

Molar masses can be googled or easily calculated with help of periodic table.
$K_f(water)$ is kryoscopic water constant, also known from temperature.

## Molar mass calculation


```python
def find_molar_mass(temperature_water, temperature_solution, Kf, mass_water, mass_solid):
    Molar_mass = mass_solid * Kf * 1000 / ((temperature_water-temperature_solution) * mass_water)
    return Molar_mass

for type, info in compounds.items():
    if not info["calculate_molar_mass"]:
        continue

    temperature_solution = compounds[type]["freezing_temperature"]
    mass_solid = compounds[type]["mass_solid"]
    mass_water = compounds[type]["mass_water"]
    molar_mass = find_molar_mass(temperature_water, temperature_solution, Kf_water, mass_water, mass_solid)
    compounds[type]["mass"] = molar_mass
```

Molar mass is determined by the equation

$M = \frac{mass_{compound} \cdot K_f(water) \cdot 1000 }{ \Delta T_{fr} \cdot mass_{water}}$

where $\Delta T_{fr}=T_{fr}(water)-T_{fr}(solution)$

## Determination of Vant-Hoff constant


```python
mass_urea_avg = (compounds["urea1"]["mass"] + compounds["urea2"]["mass"])/2
mass_kcl_avg = compounds["kcl"]["mass"]
vanthoff_kcl = Molar_mass_kcl / mass_kcl_avg
vanthoff_urea = Molar_mass_urea /mass_urea_avg
```

In order to determine Vant-Hoff constant, we need to divide expected molar mass to experimentally obtained molar mass. 

## Resulting table


```python
table = [['Name', 'Molar mass exp', 'Molar mass lit', 'Vant Hoff'], 
         ['Urea', mass_urea_avg, Molar_mass_urea, vanthoff_urea],
         ['KCl', compounds["kcl"]["mass"], Molar_mass_kcl, vanthoff_kcl]]
print(tabulate(table, headers='firstrow', tablefmt='fancy_grid'))
```

    ╒════════╤══════════════════╤══════════════════╤═════════════╕
    │ Name   │   Molar mass exp │   Molar mass lit │   Vant Hoff │
    ╞════════╪══════════════════╪══════════════════╪═════════════╡
    │ Urea   │          77.308  │            60.06 │    0.776893 │
    ├────────┼──────────────────┼──────────────────┼─────────────┤
    │ KCl    │          41.2615 │            74.55 │    1.80677  │
    ╘════════╧══════════════════╧══════════════════╧═════════════╛
    

## Plot figure


```python
figure_title = 'The freezing curves for compounds under study'
fig, axs = plt.subplots(3, 2)
for type, info in compounds.items():
     data = compounds[type]
     ax = axs[info["plot_pos_x"], info["plot_pos_y"]]

     ax.plot(data["time_rel"], data["temperature"], data["time_rel_plateau"],  data["temperature_plateau"], info["plot_fmt"])
     ax.set_title(f'{info["title"]} $T_{{fr}}$ = {data["freezing_temperature"]}')

     ax.set(xlabel='Time, sec', ylabel='Temperature, C')
fig.suptitle(figure_title, fontsize=16)
fig.canvas.manager.set_window_title(figure_title)
fig.delaxes(axs[2][1])
fig.tight_layout()
plt.show()
```

![png](/assets/bgu-physical-chemistry-lab8_files/bgu-physical-chemistry-lab8_25_0.png)

<a href="{{ page.link_to_notebook }}">Link to Jupyter Notebook</a>

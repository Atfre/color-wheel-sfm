# 🎨 Color Wheel Script

A Color Wheel tool for Source Filmmaker built using **Python**.

This script lets the user modify different aspects of SFM's lights, introducing a color wheel for easy color picking, sliders for different properties and divided by sections, and an option to see and copy the HEX code of the currently selected color.

## ✨ Features

- Interactive color wheel
- RGB brightness vertical slider
- Preview that compensates SFM's light desaturation
- Automatically changes the color of the light
- HEX Code and a button to copy it (Idea by: Dani3D)
- Sections with more properties
- Modifies different aspects of the lights
  - Intensity
  - Radius
  - Field of View
  - Shadows
  - Distance
  - Attenuation
  - Volumetrics
  - UberLights

---

## 📂 Structure

```
color_wheel.py
```

---

## 📦 Installation

- **(1) Locate your SFM usermod scripts folder**
```
SteamLibrary/steamapps/common/SourceFilmmaker/game/usermod/scripts/sfm/animset/tools/
```
- **(2) Place the script**
```
color_wheel.py
```
- **(3) Run the script in SFM**
  - Open Source Filmmaker
  - Spawn a light
  - Right click on the light
  - Go to the "rig" section
  - Run the "color_wheel" script

# 🎨 Color Wheel Script [BETA]

A Color Wheel tool for Source Filmmaker built using **Python**.
This script allows users to select a color for SFM lights, featuring RGB values (0–1 range) and a SFM desaturation preview compensation for more accurate color matching.

Since I couldn't find a way of directly modifying light color properties in SFM, this tool provides a practical and efficient solution by offering better visual control and precise RGB value copying. If I find a solution to this problem, I'll update the file.

## ✨ Features

- Interactive color wheel
- RGB values (0–1 range)
- Copy RGB values buttons
- Preview compensates SFM's light desaturation
- Attachable to any place inside SFM's interface

---

## 📂 Structure

```
color_wheel.py
```

---

## 📦 Installation

- **(1) Locate your SFM usermod scripts folder**
```
SteamLibrary/steamapps/common/SourceFilmmaker/game/usermod/scripts/sfm/mainmenu/
```
- **(2) Create a folder (optional)**
```
...mainmenu/aftre/
```
- **(3) Place the script**
```
color_wheel.py
```
- **(4) Run the script in SFM**
  - Open Source Filmmaker
  - Go to the top menu
  - Click on "scripts"
  - Run the script

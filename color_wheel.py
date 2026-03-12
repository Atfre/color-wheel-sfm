## Color Wheel
##
## A simple color wheel widget for picking colors and copying RGB values.
##
## Unfortunately I couldn't find a way to directly modify the color values from lights in SFM
## but I had the idea to make a color wheel to havea preview of the color I wish and copy its
## values to put it directly in the sliders. If someone finds a better way to do this, feel free
## to use this code as a base or if I find myself the way, I'll directly edit this file.
##
## Author: Aftre

import math
import sfm
import sfmUtils
import vs
import sfmApp
from PySide import QtGui, QtCore, shiboken

ProductName = "Color Wheel"
InternalName = "color_wheel"

# Color Wheel
class COLORWheel(QtGui.QWidget):
    colorChanged = QtCore.Signal(QtGui.QColor)

    def __init__(self):
        super(COLORWheel, self).__init__()
        self.setMinimumSize(240, 240)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        size = min(self.width(), self.height())
        radius = size/2 - 4
        center = QtCore.QPoint(self.width()/2, self.height()/2)

        image = QtGui.QImage(
            self.width(),
            self.height(),
            QtGui.QImage.Format_RGB32
        )

        for x in range(self.width()):
            for y in range(self.height()):
                dx = x - center.x()
                dy = y - center.y()
                dist = math.sqrt(dx*dx + dy*dy)

                if dist <= radius:
                    angle = math.degrees(math.atan2(dy, dx))
                    if angle < 0: angle += 360
                    sat = dist / radius
                    color = QtGui.QColor()
                    color.setHsv(int(angle), int(sat*255), 255)
                    image.setPixel(x, y, color.rgb())
                else:
                    image.setPixel(x, y, QtGui.QColor(40,40,40).rgb())
        painter.drawImage(0,0,image)

    def mousePressEvent(self, event):
        self.pick(event)

    def mouseMoveEvent(self, event):
        self.pick(event)

    def pick(self, event):
        cx = self.width()/2
        cy = self.height()/2
        dx = event.x() - cx
        dy = event.y() - cy
        radius = min(self.width(), self.height())/2 - 4
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > radius:
            return
        angle = math.degrees(math.atan2(dy, dx))
        if angle < 0:
            angle += 360
        sat = dist / radius
        color = QtGui.QColor()
        color.setHsv(int(angle), int(sat*255), 255)
        self.colorChanged.emit(color)

# UI
class ColorWheelTab(QtGui.QWidget):
    def __init__(self):
        super(ColorWheelTab, self).__init__()
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.setSpacing(8)
        mainLayout.setContentsMargins(10,10,10,10)
        self.setLayout(mainLayout)

        title = QtGui.QLabel("Color Wheel")
        title.setStyleSheet("font-size:16px; font-weight:bold;")
        mainLayout.addWidget(title)
        mainLayout.addWidget(QtGui.QLabel("Script made by: Aftre"))

        self.wheel = COLORWheel()
        self.wheel.colorChanged.connect(self.updatePreview)
        mainLayout.addWidget(self.wheel)

        self.preview = QtGui.QLabel()
        self.preview.setFixedHeight(36)
        self.preview.setAutoFillBackground(True)
        mainLayout.addWidget(self.preview)

        self.rgbLabel = QtGui.QLabel()
        mainLayout.addWidget(self.rgbLabel)

        self.rLabel = QtGui.QLabel()
        self.gLabel = QtGui.QLabel()
        self.bLabel = QtGui.QLabel()
        mainLayout.addWidget(self.rLabel)
        mainLayout.addWidget(self.gLabel)
        mainLayout.addWidget(self.bLabel)

        btnLayout = QtGui.QHBoxLayout()
        self.copyR = QtGui.QPushButton("Copy R")
        self.copyG = QtGui.QPushButton("Copy G")
        self.copyB = QtGui.QPushButton("Copy B")
        self.copyR.clicked.connect(lambda: self.copyChannel('R'))
        self.copyG.clicked.connect(lambda: self.copyChannel('G'))
        self.copyB.clicked.connect(lambda: self.copyChannel('B'))
        btnLayout.addWidget(self.copyR)
        btnLayout.addWidget(self.copyG)
        btnLayout.addWidget(self.copyB)
        mainLayout.addLayout(btnLayout)

        self.currentColor = QtGui.QColor(255,255,255)
        self.updatePreview(self.currentColor)

    # SFM's light desaturation - simulation
    def simulateSFMDesaturation(self, color):
        r = color.red()
        g = color.green()
        b = color.blue()

        h,s,v,a = color.getHsv()

        # Desaturation (20%)
        s=int(s*0.80)

        adjusted = QtGui.QColor()
        adjusted.setHsv(h,s,v)

        return adjusted

    def updatePreview(self, color):
        self.currentColor = color

        adjustedColor = self.simulateSFMDesaturation(color)

        palette = self.preview.palette()
        palette.setColor(QtGui.QPalette.Window, adjustedColor)
        self.preview.setPalette(palette)

        r = color.red()/255.0
        g = color.green()/255.0
        b = color.blue()/255.0

        self.rgbLabel.setText("RGB: %.3f | %.3f | %.3f" % (r,g,b))
        self.rLabel.setText("R: %.3f" % r)
        self.gLabel.setText("G: %.3f" % g)
        self.bLabel.setText("B: %.3f" % b)

    def copyChannel(self, channel):
        r = self.currentColor.red()/255.0
        g = self.currentColor.green()/255.0
        b = self.currentColor.blue()/255.0
        val = {'R':r,'G':g,'B':b}[channel]
        QtGui.QApplication.clipboard().setText("%.3f" % val)
        print("Copied %s: %.3f" % (channel, val))

# Attach window to SFM's Interface (meow)
def CreateScriptWindow():
    widget = ColorWheelTab()
    pointer = shiboken.getCppPointer(widget)
    sfmApp.RegisterTabWindow(
        InternalName,
        ProductName,
        pointer[0]
    )
    globals()[InternalName] = widget

def DestroyScriptWindow():
    existing = globals().get(InternalName)
    if existing is not None:
        existing.close()
        existing.deleteLater()
        globals()[InternalName] = None

try:
    if globals().get(InternalName) is None:
        CreateScriptWindow()
    else:
        DestroyScriptWindow()
        CreateScriptWindow()
    sfmApp.ShowTabWindow(InternalName)
    
except Exception as e:
    print(e)
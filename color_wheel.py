# Color Wheel
#
# A color wheel tool that lets the user modify the color of SFM lights with a color wheel, modify
# the intensity/brightness of the light and copy the HEX Code.
#
# Author: Aftre / Discord: aftre
#
# This script is based off msu355 and an0nymooose's scripts for a few solutions and fixes.

import math
import sfm
import sfmUtils
import vs
import sfmApp
import vsUtils
from vs import g_pDataModel as dm
from PySide import QtGui, QtCore

ProductName = "Color Wheel"
InternalName = "color_wheel"

#  Color application
def getChannel(animSet, controlName):
    try:
        rootGroup = animSet.GetRootControlGroup()
        if rootGroup is None:
            return None

        ctrl = rootGroup.FindControlByName(controlName, True)
        if ctrl is None:
            return None

        return ctrl.channel

    except Exception as e:
        return None


def setChannelAllKeys(channel, value):
    try:
        layer = channel.log.GetLayer(0)
        count = layer.GetKeyCount()

        if count == 0:
            # If there's no keys, then inserts one affecting the whole timeline
            channel.log.InsertKey(vs.DmeTime_t(0), value, 3)
            layer.values[0] = value
        else:
            # Overwrite every existing key with the new color value
            for i in range(count):
                layer.values[i] = value

        return True

    except Exception as e:
        return False


def applyLightColor(animSet, r, g, b):
    if animSet is None:
        return

    chR = getChannel(animSet, "color_red")
    chG = getChannel(animSet, "color_green")
    chB = getChannel(animSet, "color_blue")

    if not chR or not chG or not chB:
        return

    dm.StartUndo("ColorWheel", "ColorWheel", 0)
    setChannelAllKeys(chR, r)
    setChannelAllKeys(chG, g)
    setChannelAllKeys(chB, b)
    dm.FinishUndo()

    # Refresh viewport
    sfmApp.SetHeadTimeInFrames(sfmApp.GetHeadTimeInFrames())

#  Color Wheel thing
class COLORWheel(QtGui.QWidget):
    colorChanged = QtCore.Signal(QtGui.QColor)

    def __init__(self):
        super(COLORWheel, self).__init__()
        self.setMinimumSize(240, 240)
        self.setMaximumSize(240, 240)

        self._radius      = 116
        self._selectorPos = QtCore.QPoint(120, 120)
        self._cachedWheel = None
        self._generateWheel()

        # System to avoid lagging SFM
        self._applyTimer   = QtCore.QTimer(self)
        self._applyTimer.setSingleShot(True)
        self._applyTimer.setInterval(40)
        self._pendingColor = None
        self._applyTimer.timeout.connect(self._emitPending)

    def _generateWheel(self):
        size = self._radius * 2
        image = QtGui.QImage(size, size, QtGui.QImage.Format_RGB32)
        cx = cy = self._radius

        for y in range(size):
            for x in range(size):
                dx = x - cx
                dy = y - cy
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= self._radius:
                    # Blender layout
                    angle = math.degrees(math.atan2(-dx, dy))
                    if angle < 0:
                        angle += 360
                    sat = dist / self._radius
                    c = QtGui.QColor()
                    # 90% desaturation to make it similar to SFMs desaturated colors
                    c.setHsv(int(angle), int(sat * 255 * 0.90), 255)
                    image.setPixel(x, y, c.rgb())
                else:
                    image.setPixel(x, y, QtGui.QColor(40, 40, 40).rgb())

        self._cachedWheel = QtGui.QPixmap.fromImage(image)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        ox = (self.width()  - self._radius * 2) / 2
        oy = (self.height() - self._radius * 2) / 2
        painter.drawPixmap(ox, oy, self._cachedWheel)

        sx = self._selectorPos.x()
        sy = self._selectorPos.y()
        painter.setPen(QtGui.QPen(QtCore.Qt.white, 2))
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawEllipse(QtCore.QPoint(sx, sy), 7, 7)
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 1))
        painter.drawEllipse(QtCore.QPoint(sx, sy), 9, 9)

    def mousePressEvent(self, event):
        self._pick(event.pos())

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton:
            self._pick(event.pos())

    def _pick(self, pos):
        cx = self.width()  / 2
        cy = self.height() / 2
        dx = pos.x() - cx
        dy = pos.y() - cy
        dist = math.sqrt(dx * dx + dy * dy)

        if dist > self._radius:
            angle = math.atan2(dy, dx)
            dx = math.cos(angle) * self._radius
            dy = math.sin(angle) * self._radius
            dist = self._radius

        self._selectorPos = QtCore.QPoint(int(cx + dx), int(cy + dy))
        self.update()

        # Blender layout
        angle_deg = math.degrees(math.atan2(-dx, dy))
        if angle_deg < 0:
            angle_deg += 360
        sat = min(dist / self._radius, 1.0)

        color = QtGui.QColor()
        color.setHsv(int(angle_deg), int(sat * 255), 255)

        self._pendingColor = color
        if not self._applyTimer.isActive():
            self._applyTimer.start()

    def _emitPending(self):
        if self._pendingColor is not None:
            self.colorChanged.emit(self._pendingColor)
            self._pendingColor = None

# Vertical gradient brightness slider
class BrightnessSlider(QtGui.QWidget):
    valueChanged = QtCore.Signal(float)

    def __init__(self, parent=None):
        super(BrightnessSlider, self).__init__(parent)
        self.setFixedWidth(20)
        self.setMinimumHeight(240)
        self._value = 1.0
        self._dragging = False

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        gradient = QtGui.QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QtGui.QColor(255, 255, 255))
        gradient.setColorAt(1.0, QtGui.QColor(0, 0, 0))
        painter.fillRect(self.rect(), QtGui.QBrush(gradient))

        y = int((1.0 - self._value) * self.height())
        painter.setPen(QtGui.QPen(QtCore.Qt.white, 2))
        painter.drawLine(0, y, self.width(), y)
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 1))
        painter.drawLine(0, y + 2, self.width(), y + 2)

    def mousePressEvent(self, event):
        self._dragging = True
        self._updateValue(event.pos().y())

    def mouseMoveEvent(self, event):
        if self._dragging:
            self._updateValue(event.pos().y())

    def mouseReleaseEvent(self, event):
        self._dragging = False

    def _updateValue(self, y):
        self._value = 1.0 - max(0.0, min(1.0, float(y) / self.height()))
        self.update()
        self.valueChanged.emit(self._value)

    def getValue(self):
        return self._value

# Window Code meow
class ColorWheelWindow(QtGui.QWidget):
    def __init__(self, animSet):
        super(ColorWheelWindow, self).__init__()

        self.targetAnimSet = animSet
        self.setWindowTitle(ProductName)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
        self.setFixedWidth(300)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.setSpacing(8)
        mainLayout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(mainLayout)

        # Window Title
        title = QtGui.QLabel("Color Wheel")
        title.setStyleSheet("font-size:16px; font-weight:bold;")
        mainLayout.addWidget(title)

        # Show which light is selected or affected by the script
        lightName = animSet.GetName() if animSet else "Meow"
        self.targetLabel = QtGui.QLabel("Selected Light: %s" % lightName)
        self.targetLabel.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        mainLayout.addWidget(self.targetLabel)

        wheelRow = QtGui.QHBoxLayout()
        wheelRow.setSpacing(6)

        self.wheel = COLORWheel()
        self.wheel.colorChanged.connect(self.onColorChanged)
        wheelRow.addWidget(self.wheel)

        # Intensity (Brightness) vertical slider
        self.brightnessSlider = BrightnessSlider()
        self.brightnessSlider.valueChanged.connect(self.onBrightnessChanged)
        wheelRow.addWidget(self.brightnessSlider, alignment=QtCore.Qt.AlignVCenter)

        mainLayout.addLayout(wheelRow)

        # HEX code display and copy button
        hexRow = QtGui.QHBoxLayout()
        self.hexLabel = QtGui.QLabel("#FFFFFF")
        self.hexLabel.setStyleSheet("font-size: 13px;")
        self.copyHexBtn = QtGui.QPushButton("Copy HEX")
        self.copyHexBtn.clicked.connect(self.copyHex)
        hexRow.addWidget(self.hexLabel)
        hexRow.addWidget(self.copyHexBtn)
        mainLayout.addLayout(hexRow)

        self.currentColor    = QtGui.QColor(255, 255, 255)
        self.currentR        = 1.0
        self.currentG        = 1.0
        self.currentB        = 1.0
        self.brightnessScale = 1.0

    def onColorChanged(self, color):
        self.currentColor = color
        self.currentR = color.red()   / 255.0
        self.currentG = color.green() / 255.0
        self.currentB = color.blue()  / 255.0
        self.hexLabel.setText("#%02X%02X%02X" % (color.red(), color.green(), color.blue()))
        self._applyToLight()

    def onBrightnessChanged(self, value):
        self.brightnessScale = value
        self._applyToLight()

    def copyHex(self):
        QtGui.QApplication.clipboard().setText(self.hexLabel.text())

    def _applyToLight(self):
        r = min(self.currentR * self.brightnessScale, 1.0)
        g = min(self.currentG * self.brightnessScale, 1.0)
        b = min(self.currentB * self.brightnessScale, 1.0)
        applyLightColor(self.targetAnimSet, r, g, b)

try:
    currentAnimSet = sfm.GetCurrentAnimationSet()

    existing = globals().get(InternalName)
    if existing is not None:
        existing.close()

    tool = ColorWheelWindow(currentAnimSet)
    globals()[InternalName] = tool
    tool.show()

except Exception as e:
    print("[Color Wheel] Failed to launch: %s" % e)

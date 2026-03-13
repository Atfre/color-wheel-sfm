# Color Wheel
#
# A color wheel widget that lets the user modify the color of SFM lights with a color wheel, copy its
# RGB values and modify the intensity/brightness of the light.
#
# Author: Aftre

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
            print("[Color Wheel] rootGroup is equal none")
            return None

        ctrl = rootGroup.FindControlByName(controlName, True)
        if ctrl is None:
            print("[Color Wheel] Control not found: %s" % controlName)
            return None

        return ctrl.channel

    except Exception as e:
        print("[Color Wheel] getChannel error: %s" % e)
        return None


def setChannelAllKeys(channel, value):
    try:
        layer = channel.log.GetLayer(0)
        count = layer.GetKeyCount()

        if count == 0:
            # If there's no keys, then inserts one affecting the whole timeline
            channel.log.InsertKey(vs.DmeTime_t(0), value, 3)
            layer.values[0] = value
            print("[Color Wheel] No keys found, inserted one at 0")
        else:
            # Overwrite every existing key with the new color value
            for i in range(count):
                layer.values[i] = value

        return True

    except Exception as e:
        print("[Color Wheel] setChannelAllKeys error: %s" % e)
        return False


def applyLightColor(animSet, r, g, b):
    if animSet is None:
        print("[Color Wheel] No AnimationSet targeted.")
        return

    chR = getChannel(animSet, "color_red")
    chG = getChannel(animSet, "color_green")
    chB = getChannel(animSet, "color_blue")

    if not chR or not chG or not chB:
        print("[Color Wheel] Couldnt get the color channels.")
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
                    angle = math.degrees(math.atan2(dy, dx))
                    if angle < 0:
                        angle += 360
                    sat = dist / self._radius
                    c = QtGui.QColor()
                    c.setHsv(int(angle), int(sat * 255), 255)
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

        angle_deg = math.degrees(math.atan2(dy, dx))
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

# Window Code meow
class ColorWheelWindow(QtGui.QWidget):
    def __init__(self, animSet):
        super(ColorWheelWindow, self).__init__()

        self.targetAnimSet = animSet
        self.setWindowTitle(ProductName)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
        self.setFixedWidth(280)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.setSpacing(8)
        mainLayout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(mainLayout)

        # Window Title
        title = QtGui.QLabel("Color Wheel")
        title.setStyleSheet("font-size:16px; font-weight:bold;")
        mainLayout.addWidget(title)

        # Show which light is selected or affected by the script
        lightName = animSet.GetName() if animSet else "None"
        self.targetLabel = QtGui.QLabel("Selected Light: %s" % lightName)
        self.targetLabel.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        mainLayout.addWidget(self.targetLabel)

        # Color Wheel
        self.wheel = COLORWheel()
        self.wheel.colorChanged.connect(self.onColorChanged)
        mainLayout.addWidget(self.wheel, alignment=QtCore.Qt.AlignHCenter)

        # Color preview with desaturation, matching SFM's color system
        self.preview = QtGui.QLabel()
        self.preview.setFixedHeight(60)
        self.preview.setMinimumWidth(240)
        self.preview.setAlignment(QtCore.Qt.AlignCenter)
        self.preview.setToolTip("Preview of how SFM will display the color (20% desaturated)")
        mainLayout.addWidget(self.preview, alignment=QtCore.Qt.AlignHCenter)

        # RGB
        self.rgbLabel = QtGui.QLabel()
        mainLayout.addWidget(self.rgbLabel)

        # Intensity slider
        intensityLabel = QtGui.QLabel("Intensity (Brightness)")
        intensityLabel.setStyleSheet("margin-top:4px;")
        mainLayout.addWidget(intensityLabel)

        intensityRow = QtGui.QHBoxLayout()
        self.brightnessSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.brightnessSlider.setMinimum(0)
        self.brightnessSlider.setMaximum(100)
        self.brightnessSlider.setValue(100)
        self.brightnessSlider.setTickInterval(10)
        self.brightnessSlider.valueChanged.connect(self.onBrightnessChanged)
        self.brightnessValueLabel = QtGui.QLabel("1.00")
        self.brightnessValueLabel.setFixedWidth(36)
        intensityRow.addWidget(self.brightnessSlider)
        intensityRow.addWidget(self.brightnessValueLabel)
        mainLayout.addLayout(intensityRow)

        # Copy RGB buttons
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

        self.currentColor    = QtGui.QColor(255, 255, 255)
        self.currentR        = 1.0
        self.currentG        = 1.0
        self.currentB        = 1.0
        self.brightnessScale = 1.0
        self.updatePreview(self.currentColor)

    def simulateSFMDesaturation(self, color, brightnessScale):
        h, s, v, a = color.getHsv()
        s = int(s * 0.80)
        v = int(v * brightnessScale)
        adjusted = QtGui.QColor()
        adjusted.setHsv(h, s, v)
        return adjusted

    def onColorChanged(self, color):
        self.updatePreview(color)
        self._applyToLight()

    def onBrightnessChanged(self, sliderValue):
        self.brightnessScale = sliderValue / 100.0
        self.brightnessValueLabel.setText("%.2f" % self.brightnessScale)
        self.updatePreview(self.currentColor)
        self._applyToLight()

    def updatePreview(self, color):
        self.currentColor = color

        adjusted = self.simulateSFMDesaturation(color, self.brightnessScale)
        self.preview.setStyleSheet(
            "background-color: rgb(%d, %d, %d); border: 2px solid #555555; border-radius: 4px;"
            % (adjusted.red(), adjusted.green(), adjusted.blue())
        )

        r = color.red()   / 255.0
        g = color.green() / 255.0
        b = color.blue()  / 255.0

        self.currentR = r
        self.currentG = g
        self.currentB = b

        self.rgbLabel.setText("R: %.3f | G: %.3f | B: %.3f" % (r, g, b))

    def _applyToLight(self):
        r = min(self.currentR * self.brightnessScale, 1.0)
        g = min(self.currentG * self.brightnessScale, 1.0)
        b = min(self.currentB * self.brightnessScale, 1.0)
        applyLightColor(self.targetAnimSet, r, g, b)

    def copyChannel(self, channel):
        val = {'R': self.currentR, 'G': self.currentG, 'B': self.currentB}[channel]
        QtGui.QApplication.clipboard().setText("%.3f" % val)
        print("Copied %s: %.3f" % (channel, val))

try:
    currentAnimSet = sfm.GetCurrentAnimationSet()
    print("[Color Wheel] Targeting: %s" % currentAnimSet.GetName())

    existing = globals().get(InternalName)
    if existing is not None:
        existing.close()

    tool = ColorWheelWindow(currentAnimSet)
    globals()[InternalName] = tool
    tool.show()

except Exception as e:
    print("[Color Wheel] Failed to launch: %s" % e)

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QBrush, QPen


class ToggleButton(QWidget):
    toggled = pyqtSignal(bool)  # Custom signal

    def __init__(self, parent=None, width=60, height=30, bg_color="#777", circle_color="#DDD", active_color="#00BCff"):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.bg_color = QColor(bg_color)
        self.circle_color = QColor(circle_color)
        self.active_color = QColor(active_color)
        self._checked = False
        self._circle_position = 3

        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self.toggled.emit(self._checked)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        rect = self.rect()
        bg = self.active_color if self._checked else self.bg_color
        painter.setBrush(QBrush(bg))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)

        # Circle
        margin = 3
        diameter = rect.height() - 2 * margin
        x = rect.width() - diameter - margin if self._checked else margin
        painter.setBrush(QBrush(self.circle_color))
        painter.drawEllipse(x, margin, diameter, diameter)

    def isChecked(self):
        return self._checked

    def setChecked(self, state):
        self._checked = state
        self.update()

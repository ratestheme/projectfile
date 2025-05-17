
import sys
import os
import json
import tempfile
import threading
import time
import subprocess
import ctypes
import re
import urllib.request
from ctypes import windll
import requests
import psutil
import winreg

from PyQt5.QtCore import (
    Qt, QSize, QTimer, QRect,QFileInfo, QPoint, QRectF, QPointF, pyqtSignal, QThread, QObject
)
from PyQt5.QtGui import (
    QColor, QPalette, QPainter, QBrush, QPen, QFont, QPixmap,
    QConicalGradient, QRadialGradient, QCursor
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QLabel, QVBoxLayout,
    QHBoxLayout, QSlider, QFrame, QScrollArea, QGridLayout, QGroupBox,
    QCheckBox, QMessageBox, QDialog, QTextEdit, QDialogButtonBox,
    QFileDialog, QFileIconProvider, QLineEdit, QProgressBar, QStyleFactory,
    QStackedWidget, QSizePolicy, QStyle, QGraphicsDropShadowEffect
)
from PyQt5 import uic






# Add early in main()
if hasattr(sys, '_MEIPASS'):
    ctypes.windll.kernel32.SetDllDirectoryW(None)  # Disable DLL hijacking




import uuid
import requests
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt





class CircularProgressBar(QWidget):
    def __init__(self, size=150, thickness=10, parent=None):
        super().__init__(parent)
        self.value = 0
        self.size = size
        self.thickness = thickness
        self.setMinimumSize(self.size, self.size)
        self.setFixedSize(self.size, self.size)  # Fixed size for the circle
        # Colors for the background ring, progress arc, and text
        self.bg_color = QColor(230, 230, 230)
        self.progress_color = QColor(0, 122, 255)
        self.text_color = QColor(50, 50, 50)

    def setValue(self, val):
        """Update the progress value (0-100) and repaint."""
        self.value = val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background circle
        pen = QPen(self.bg_color, self.thickness)
        painter.setPen(pen)
        painter.drawEllipse(self.rect().adjusted(5, 5, -5, -5))

        # Draw progress arc
        pen.setColor(self.progress_color)
        painter.setPen(pen)
        span_angle = -int(360 * 16 * (self.value / 100))
        painter.drawArc(self.rect().adjusted(5, 5, -5, -5), 90 * 16, span_angle)

        # Draw percentage text
        painter.setFont(QFont("Arial", 16, QFont.Bold))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(self.rect(), Qt.AlignCenter, f"{self.value}%")

        # Draw status text
        painter.setFont(QFont("Arial", 10))
        painter.drawText(self.rect().adjusted(0, 30, 0, 0), Qt.AlignCenter, "System Optimization")

class ProgressSignal(QObject):
    progress_updated = pyqtSignal(int)
    message_updated = pyqtSignal(str)  # For status messages

class PercentageOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.progress = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.font = QFont("Arial", 24, QFont.Bold)
        self.text_color = QColor(255, 255, 255)
        self.progress_color = QColor(76, 175, 80)
        
        # Progress bar metrics
        self.bar_width = 200
        self.bar_height = 10
        self.bar_radius = 5
        
        self.hide()

    def start_animation(self):
        self.progress = 0
        self.timer.start(50)  # Update every 50ms
        self.show()

    def update_progress(self):
        if self.progress < 100:
            self.progress += 1
            self.update()
        else:
            self.timer.stop()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw rounded black background
        bg_rect = QRectF(0, 0, self.width(), self.height())
        painter.setBrush(QColor(0, 0, 0, 150))  # Black with transparency
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(bg_rect, 40, 40)  # Rounded corners with radius 15
        
        
        # Calculate center position
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        # Draw progress bar background
        bar_bg_rect = QRectF(
            center_x - self.bar_width / 2,
            center_y + 30,
            self.bar_width,
            self.bar_height
        )
        painter.setBrush(QColor(255, 255, 255, 50))
        painter.drawRoundedRect(bar_bg_rect, self.bar_radius, self.bar_radius)
        
        # Draw progress bar fill
        fill_width = (self.progress / 100) * self.bar_width
        fill_rect = QRectF(
            center_x - self.bar_width / 2,
            center_y + 30,
            fill_width,
            self.bar_height
        )
        painter.setBrush(self.progress_color)
        painter.drawRoundedRect(fill_rect, self.bar_radius, self.bar_radius)
        
        # Draw percentage text
        painter.setFont(self.font)
        painter.setPen(self.text_color)
        painter.drawText(
            QRectF(0, center_y - 50, self.width(), 50),
            Qt.AlignCenter,
            f"Optimizing... {self.progress}%"
        )    

class ToggleButton(QWidget):
    toggled = pyqtSignal(bool)
    def __init__(self, parent=None, width=70, height=34, bg_color="#cccccc", 
                 circle_color="#ffffff", active_color=None):
        super().__init__(parent)
        self.active_color = active_color if active_color else QColor(118, 200, 255)
        self.setFixedSize(width, height)
        self.bg_color = QColor(bg_color)
        self.circle_color = QColor(circle_color)
        self.active_color = QColor(active_color)
        self._checked = False
        self.setCursor(Qt.PointingHandCursor)

    def update_colors(self, active_color):
        self.active_color = QColor(active_color)
        self.update()

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self.toggled.emit(self._checked)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        
        # Background
        bg = self.active_color if self._checked else self.bg_color
        painter.setBrush(QBrush(bg))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)
        
        # Circle
        margin = 4
        diameter = rect.height() - 2 * margin
        x = rect.width() - diameter - margin if self._checked else margin
        painter.setBrush(QBrush(self.circle_color))
        painter.drawEllipse(x, margin, diameter, diameter)

    def isChecked(self):
        return self._checked

    def setChecked(self, state):
        self._checked = state
        self.update()
    


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.current_hue = 190  # Default blue hue
        
        
        # GitHub raw URLs
        self.ui_url = "https://raw.githubusercontent.com/ratestheme/project-1/main/interface.ui"

        
        # Create temp directory
        self.temp_dir = tempfile.mkdtemp(prefix="gaming_tweaks_")
        
        # Download required files
        if not self.download_required_files():
            sys.exit(1)
        
           
        self.setup_ui()
        self.setFixedSize(1015, 640)                                         
        self.setWindowFlags(Qt.FramelessWindowHint)                            
        self.setStyleSheet("background-color: #f4f2f3; border-radius: 10px; color: black;")
        self.header.setStyleSheet("background-color: transparent; color: black;")
        self.sidemenu.setStyleSheet("QFrame { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #7fddfa, stop: 1 #8ff9eb); border-radius: 10px; }")
        self.stackedWidget.setStyleSheet("background-color: transparent; color: black;")
        self.label.setStyleSheet("color: #80daf6; font-size: 20px; font-weight: bold;")
        self.dark_mode = False
        self.setup_main_toggle()
        self.connect_menu_buttons()
        self.setup_menu_button()
        self.init_toggles()
        self.define_toggle_functions()
        self.stackedWidget.setCurrentIndex(0)

        self.settings_panel = None
        self.device_id = ""  # This should be populated from loginform
        
        self.silent_mode = False  

        self.default_config_path = os.path.join(os.path.dirname(__file__), "default_config.json")
        if not os.path.exists(self.default_config_path):
          self.create_default_config(self.default_config_path)

        self.light_scrollbar_style = """
    QScrollBar:vertical {
        background: #f1f1f1;
        width: 12px;
        border-radius: 6px;
    }
    QScrollBar::handle:vertical {
        background: #888;
        border-radius: 6px;
        min-height: 20px;
    }
    QScrollBar::handle:vertical:hover {
        background: #555;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }

    QScrollBar:horizontal {
        background: #f1f1f1;
        height: 12px;
        border-radius: 6px;
    }
    QScrollBar::handle:horizontal {
        background: #888;
        border-radius: 6px;
        min-width: 20px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #555;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: none;
    }
    """

        self.dark_scrollbar_style = """
    QScrollBar:vertical {
        background: #2e2f33;
        width: 12px;
        border-radius: 6px;
    }
    QScrollBar::handle:vertical {
        background: #666;
        border-radius: 6px;
        min-height: 20px;
    }
    QScrollBar::handle:vertical:hover {
        background: #aaa;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }

    QScrollBar:horizontal {
        background: #2e2f33;
        height: 12px;
        border-radius: 6px;
    }
    QScrollBar::handle:horizontal {
        background: #666;
        border-radius: 6px;
        min-width: 20px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #aaa;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: none;
    }
    """


        self.games = []
        self.service_config = {}
        self.load_games()
        self.load_service_config()
        self.setup_game_booster_ui()
        self.setup_one_click_page()
        
        self.setup_process_manager()
         

        self.optimization_timer = QTimer(self)
        self.optimization_timer.timeout.connect(self.apply_next_optimization)
       
        
    def verify_windows_signature(self):
        try:
            from ctypes import windll
            return windll.shell32.IsUserAnAdmin() != 0
        except:
            return False   
        
    

    

    def update_optimization_stats(self):
        total = len(self.toggles)
        enabled = sum(1 for toggle in self.toggles if toggle.isChecked())
        disabled = total - enabled
        
        # Calculate percentages
        enabled_pct = (enabled / total) * 100
        disabled_pct = (disabled / total) * 100
        
        # Update gauge
        self.progressBar.setValue(int(enabled_pct))
        
        # Update labels
        self.optimized_label.setText(f"OPTIMIZED\n{enabled_pct:.1f}%")
        self.not_optimized_label.setText(f"NOT OPTIMIZED\n{disabled_pct:.1f}%")

    def create_stats_container(self, text, color="#FFFFFF"):
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 16px;
            }}
        """)

        # Add drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 40))  # Light shadow
        container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        label = QLabel(text)
        label.setStyleSheet("""
            color: #333;
            font-weight: 600;
            font-size: 14px;
            qproperty-alignment: AlignCenter;
        """)
        
        layout.addWidget(label)
        return container, label

    def mousePressEvent(self, event):
        self.drag_pos = event.globalPos() if hasattr(self, 'drag_pos') else event.globalPos()
        
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if hasattr(self, 'drag_pos'):
                self.move(self.pos() + event.globalPos() - self.drag_pos)
                self.drag_pos = event.globalPos()
                event.accept()

    # Add these new methods to the MainWindow class
    def setup_process_manager(self):
        # Create the page widget and layout
        page_index = 11  # Assuming page 11 is index 11 (adjust if different)
        page = self.stackedWidget.widget(page_index)
        page.setLayout(QVBoxLayout())
        page.layout().setContentsMargins(20, 20, 20, 20)
        page.layout().setSpacing(15)

        # Title Label
        title = QLabel("Background Process Manager")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: grey;
                padding-bottom: 10px;
            }
        """)
        page.layout().addWidget(title)

        # Scroll Area
        self.process_scroll = QScrollArea()
        self.process_scroll.setWidgetResizable(True)
        self.process_scroll.setStyleSheet(self.light_scrollbar_style if not self.dark_mode else self.dark_scrollbar_style)
        
        # Container Widget
        container = QWidget()
        container.setLayout(QVBoxLayout())
        container.layout().setContentsMargins(5, 5, 5, 5)
        container.layout().setSpacing(8)
        
        # Header Frame
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: transparent; border: none;")
        header_frame.setLayout(QHBoxLayout())
        header_frame.layout().setContentsMargins(15, 8, 15, 8)
        
        pid_header = QLabel("PID")
        pid_header.setStyleSheet("font-weight: bold;")
        name_header = QLabel("Process Name")
        name_header.setStyleSheet("font-weight: bold;")
        action_header = QLabel("Actions")
        action_header.setStyleSheet("font-weight: bold;")
        
        header_frame.layout().addWidget(pid_header, 1)
        header_frame.layout().addWidget(name_header, 4)
        header_frame.layout().addWidget(action_header, 2)
        container.layout().addWidget(header_frame)

        # Process List
        self.process_list_layout = QVBoxLayout()
        self.process_list_layout.setSpacing(5)
        container.layout().addLayout(self.process_list_layout)
        
        self.process_scroll.setWidget(container)
        page.layout().addWidget(self.process_scroll)

        # Refresh Button
        refresh_btn = QPushButton("Refresh List")
        refresh_btn.setFixedHeight(35)
        refresh_btn.clicked.connect(self.refresh_process_list)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #ececec ; }
        """)
        page.layout().addWidget(refresh_btn)

        # Initial load
        self.refresh_process_list()

    def refresh_process_list(self):
        # Clear existing entries
        while self.process_list_layout.count():
            child = self.process_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Get running processes
        processes = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.pid == 0 or not proc.name():
                    continue
                processes.append((proc.pid, proc.name()))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Create process entries
        for pid, name in processes:
            frame = QFrame()
            frame.setStyleSheet("""
                QFrame {
                    background-color: transparent;
                    border-radius: 30px;
                    padding: 10px;
                    font-size: 14px;
                    font-weight: bold;
                    border: none;
                    
                }
            """)
            frame.setLayout(QHBoxLayout())
            frame.layout().setContentsMargins(15, 8, 15, 8)

            # PID Label
            pid_label = QLabel(str(pid))
            pid_label.setStyleSheet("color: #666666;")

            # Name Label with elided text
            name_label = QLabel(name)
            name_label.setStyleSheet("""
                QLabel {
                    color: #333333;
                    font-weight: bold;
                }
            """)
            # Add elided text functionality
            name_label.setMinimumWidth(150)
            name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            
            # End Task Button
            end_btn = QPushButton("End Task")
            end_btn.setFixedSize(90, 30)
            end_btn.clicked.connect(lambda _, p=pid: self.end_process(p))
            end_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ececec;
                    color: black;
                    border-radius: 13px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #b9b9b9; }
            """)

            frame.layout().addWidget(pid_label, 1)
            frame.layout().addWidget(name_label, 4)
            frame.layout().addWidget(end_btn, 2)
            self.process_list_layout.addWidget(frame)

        self.process_list_layout.addStretch()

    def end_process(self, pid):
        # Add user confirmation
        reply = QMessageBox.question(
            self, 'Confirmation',
            f"Are you sure you want to terminate process {pid}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return
        # Rest of the original code...
        try:
            process = psutil.Process(pid)
            process.terminate()
            time.sleep(0.5)
            if process.is_running():
                process.kill()
        except psutil.NoSuchProcess:
            QMessageBox.information(self, "Info", "Process already terminated")
        except Exception as e:
            # Try force kill with taskkill
            try:
                subprocess.run(f"taskkill /F /PID {pid}", shell=True, check=True)
            except subprocess.CalledProcessError:
                QMessageBox.critical(self, "Error", f"Failed to terminate process: {str(e)}")
        self.refresh_process_list()

    def show_message(self, title, message, is_error=False):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        
        # Style based on theme
        if self.dark_mode:
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #2a2a2a;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #404040;
                    color: white;
                    padding: 5px 15px;
                    border-radius: 4px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
            """)
        else:
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #f8f8f8;
                    color: #333333;
                }
                QPushButton {
                    background-color: #e0e0e0;
                    color: #333;
                    padding: 5px 15px;
                    border-radius: 4px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
            """)
        
        if is_error:
            msg.setIcon(QMessageBox.Critical)
        else:
            msg.setIcon(QMessageBox.Information)
        
        msg.exec_()

    def start_one_click_optimize(self):
        self.silent_mode = True
        # Exclude network-related toggles
        network_toggles = {75, 76, 95, 103, 20, 21, 14, 15, 48, 49, 50, 51}
        self.safe_optimizations = [i for i in range(104) if i not in network_toggles]
        
        # Reset progress
        self.current_step = 0
        self.progressBar.setValue(0)
        self.statusLabel.setText("Starting optimization...")
        self.fileLabel.setText("Preparing system")
        
        # Start the timer
        self.optimization_timer.start(50)  # 50ms update interval

    def apply_next_optimization(self):
        if self.current_step >= len(self.safe_optimizations):
            self.optimization_timer.stop()
            self.silent_mode = False
            self.statusLabel.setText("Optimization Complete!")
            self.fileLabel.setText("")
            self.progressBar.setValue(100)  # Set to 100% when done
            return
        
        toggle_idx = self.safe_optimizations[self.current_step]
        toggle = self.toggles[toggle_idx]
        
        # Update progress (0-100)
        progress = int((self.current_step / len(self.safe_optimizations)) * 100)
        self.progressBar.setValue(progress)
        
        # Update status text
        self.fileLabel.setText(f"Applying optimization {self.current_step + 1}/{len(self.safe_optimizations)}")
        
        # Apply the optimization if not already enabled
        if not toggle.isChecked():
            try:
                func_name = f"toggle_{toggle_idx + 1}_action"
                getattr(self, func_name)(True)
            except Exception as e:
                print(f"Error applying toggle {toggle_idx}: {str(e)}")
        
        self.current_step += 1

    def start_reset_to_default(self):
        self.silent_mode = True
        try:
            with open(self.default_config_path, "r") as f:
                default_states = json.load(f)
            self.safe_optimizations = [int(k) for k, v in default_states.items() if v]
        except:
            self.safe_optimizations = list(range(104))
        
        # Reset progress UI
        self.current_step = 0
        self.progressBar.setValue(0)
        self.statusLabel.setText("Resetting to default...")
        self.fileLabel.setText("")
        
        # Start reset process
        self.optimization_timer.start(50)

   

    
    
        

    def setup_one_click_page(self):
        # Create the page widget and layout
        page_index = 12  # Assuming page 11 is index 11 (adjust if different)
        page = self.stackedWidget.widget(page_index)
        main_layout = QVBoxLayout(page)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # --- Progress Container ---
        progress_container = QWidget()
        progress_container.setFixedSize(220, 220)  # Slightly larger to accommodate shadow
        container_layout = QGridLayout(progress_container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # --- Circular Progress Bar ---
        self.progressBar = CircularProgressBar(size=200, thickness=12)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setOffset(0)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.progressBar.setGraphicsEffect(shadow)

        # --- Optimize Button ---
        self.one_click_btn = QPushButton("Optimize")
        self.one_click_btn.setObjectName("optimize_button")
        self.one_click_btn.setCursor(Qt.PointingHandCursor)
        self.one_click_btn.setFixedSize(180, 180)

        # --- Progress Percentage Label ---
        self.percentageLabel = QLabel()
        self.percentageLabel.setAlignment(Qt.AlignCenter)
        self.percentageLabel.hide()
        self.percentageLabel.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #007BFF;
            background: transparent;
        """)

        # Add widgets to container
        container_layout.addWidget(self.progressBar, 0, 0, Qt.AlignCenter)
        container_layout.addWidget(self.one_click_btn, 0, 0, Qt.AlignCenter)
        container_layout.addWidget(self.percentageLabel, 0, 0, Qt.AlignCenter)

        main_layout.addWidget(progress_container, alignment=Qt.AlignHCenter)

        # --- Status Labels ---
        self.statusLabel = QLabel("Ready to start optimization")
        self.statusLabel.setAlignment(Qt.AlignCenter)
        self.statusLabel.setStyleSheet("font-size: 14px; color: #333;")
        main_layout.addWidget(self.statusLabel)

        self.fileLabel = QLabel("")
        self.fileLabel.setAlignment(Qt.AlignCenter)
        self.fileLabel.setStyleSheet("font-size: 12px; color: #666;")
        main_layout.addWidget(self.fileLabel)

        main_layout.addStretch(1)  # Push reset button to bottom

        # --- Reset Button ---
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setObjectName("reset_button")
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setFixedSize(80, 30)

        
        

        reset_layout = QHBoxLayout()
        reset_layout.addStretch()
        reset_layout.addWidget(self.reset_btn)

        main_layout.addLayout(reset_layout)

        # --- Styling ---
        page.setStyleSheet("""
            QWidget#OneClickPage {
                background-color: transparent;
                border-radius: 15px;
            }
            QLabel {
                color: #333333;
                font-size: 13px;
            }
            QPushButton#optimize_button {
                background-color: #80daf6;
                color: white;
                border-radius: 90px;
                min-width: 180px;
                min-height: 180px;
                font-size: 14px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton#optimize_button:hover {
                background-color: #0056b3;
            }
            QPushButton#optimize_button:disabled {
                background-color: #cccccc;
            }
            QPushButton#reset_button {
                background-color: #6c757d;
                color: white;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton#reset_button:hover {
                background-color: #5a6268;
            }
        """)

        # Connect signals
        self.one_click_btn.clicked.connect(self.start_one_click_optimize)
        self.reset_btn.clicked.connect(self.start_reset_to_default)



        # Add stats containers
        stats_container = QWidget()
        stats_layout = QHBoxLayout(stats_container)
        stats_layout.setContentsMargins(30, 30, 30, 30)
        stats_layout.setSpacing(15)

        # Optimized container
        self.optimized_container, self.optimized_label = self.create_stats_container(
            "OPTIMIZED\n0.0%",)
        # Not optimized container
        self.not_optimized_container, self.not_optimized_label = self.create_stats_container(
            "NOT OPTIMIZED\n100.0%",)

        stats_layout.addWidget(self.optimized_container)
        stats_layout.addWidget(self.not_optimized_container)

        # Add to main layout
        main_layout.addWidget(stats_container)

        # Connect toggle signals
        for toggle in self.toggles:
            toggle.toggled.connect(self.update_optimization_stats)

        # Initial update
        self.update_optimization_stats()

    def reset_next_optimization(self):
        if self.current_step >= len(self.safe_optimizations):
            self.optimization_timer.stop()
            self.silent_mode = False
            self.statusLabel.setText("Reset Complete!")
            self.fileLabel.setText("")
            self.progressBar.setValue(100)  # Full circle
            return
        
        # Update progress percentage
        progress = int((self.current_step / len(self.safe_optimizations)) * 100)
        self.progressBar.setValue(progress)
        
        # Original reset logic
        toggle_idx = self.safe_optimizations[self.current_step]
        try:
            with open(self.default_config_path, "r") as f:
                default_states = json.load(f)
            desired_state = bool(default_states.get(str(toggle_idx), False))
            
            toggle = self.toggles[toggle_idx]
            if toggle.isChecked() != desired_state:
                func_name = f"toggle_{toggle_idx + 1}_action"
                getattr(self, func_name)(desired_state)
        except Exception as e:
            print(f"Error resetting toggle {toggle_idx}: {str(e)}")
        
        self.current_step += 1
        self.fileLabel.setText(f"Resetting {self.current_step}/{len(self.safe_optimizations)}")

    def create_default_config(self, path):
        default_states = {}
        for idx in range(len(self.toggles)):
            try:
                # Use actual system check instead of current toggle state
                default_states[str(idx)] = self.check_initial_state(idx)
            except:
                default_states[str(idx)] = False
                
        with open(path, "w") as f:
            json.dump(default_states, f)

    def activate_beast_mode(self):
        # Define services that must stay enabled
        safe_services = {
            "WlanSvc", "AJRouter", "bthserv", "BluetoothUserService", "QWAVE",
            "NetTcpPortSharing", "NcdAutoSetup", "p2pimsvc", "p2psvc", "PNRPsvc",
            "RasMan", "RemoteAccess", "SSDPSRV", "WpnService", "iphlpsvc", "icssvc"
        }
        # Rest of the method remains the same
        for service_id in self.default_services:
            if service_id not in safe_services:
                self.service_config[service_id] = True
            else:
                self.service_config[service_id] = False
        self.save_service_config()
        self.refresh_service_checkboxes()

    def activate_balanced_mode(self):
        # Define a safer preset of commonly known services to stop
        common_services = {
            "wuauserv", "DiagTrack", "WdiServiceHost", "WerSvc",
            "Spooler", "SysMain", "WMPNetworkSvc", "lfsvc", "MapsBroker",
            "dmwappushservice", "fhsvc", "HomeGroupProvider", "HomeGroupListener"
        }
        safe_services = {"WlanSvc","AJRouter", "bthserv", "BluetoothUserService", "QWAVE", "NetTcpPortSharing", "NcdAutoSetup","p2pimsvc","p2psvc","PNRPsvc","RasMan","RemoteAccess", "SSDPSRV", "WpnService" }

        for service_id in self.default_services:
            if service_id in common_services and service_id not in safe_services:
                self.service_config[service_id] = True
            else:
                self.service_config[service_id] = False
        self.save_service_config()
        self.refresh_service_checkboxes()

    def refresh_service_checkboxes(self):
        for i in range(self.services_layout.count()):
            frame = self.services_layout.itemAt(i).widget()
            if frame and frame.layout():
                checkbox = frame.layout().itemAt(0).widget()
                if isinstance(checkbox, QCheckBox):
                    service_name = None
                    for key, value in self.default_services.items():
                        if value == checkbox.text():
                            service_name = key
                            break
                    if service_name and service_name in self.service_config:
                        checkbox.setChecked(self.service_config[service_name])
                
   
    def load_service_config(self):
        config_path = os.path.join(os.path.dirname(__file__), "service_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    self.service_config = json.load(f)
            except Exception as e:
                print(f"Error reading service config: {e}")
                self.service_config = {}
        else:
            self.service_config = {}
    
    def save_service_config(self):
        config_path = os.path.join(os.path.dirname(__file__), "service_config.json")
        try:
            with open(config_path, "w") as f:
                json.dump(self.service_config, f, indent=4)
        except Exception as e:
            print(f"Error saving service config: {e}")


    def load_games(self):
        try:
            games_path = os.path.join(os.path.dirname(__file__), "games.json")
            if os.path.exists(games_path):
                with open(games_path, "r") as f:
                    self.games = json.load(f)
        except Exception as e:
            print(f"Error loading games: {str(e)}")
            self.games = []

    def save_games(self):
        try:
            games_path = os.path.join(os.path.dirname(__file__), "games.json")
            with open(games_path, "w") as f:
                json.dump(self.games, f, indent=4)
        except Exception as e:
            print(f"Error saving games: {str(e)}")
        
    def setup_game_booster_ui(self):
        page_index = 13  # Verify your actual page index
        page = self.stackedWidget.widget(page_index)
        page.setLayout(QHBoxLayout())
        self.service_checkboxes = []
        # Left Panel - Game Management
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.StyledPanel)
        left_panel.setFrameShadow(QFrame.Raised)
        left_panel.setStyleSheet("border: none;")
        left_panel.setFixedWidth(330)
        left_panel.setLayout(QVBoxLayout())
        
        # Add Game Button
        self.add_game_btn = QPushButton("+")
        self.add_game_btn.setFixedSize(40, 40)
        self.add_game_btn.setCursor(Qt.PointingHandCursor)
        self.add_game_btn.setIconSize(QSize(20, 20))
        self.add_game_btn.setStyleSheet("""
            QPushButton {
                background: #80daf6;
                border-radius: 20px;
                color: white;
                padding: 10px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover { background: #65acc3; }
        """)
        self.add_game_btn.clicked.connect(self.add_game_dialog)
        left_panel.layout().addWidget(self.add_game_btn)
        
        # Games Grid
        self.games_scroll = QScrollArea()
        self.games_scroll.setWidgetResizable(True)
        

        games_container = QWidget()
        self.games_grid = QGridLayout(games_container)
        self.games_scroll.setWidget(games_container)
        left_panel.layout().addWidget(self.games_scroll)
        
        # Right Panel - Service Management
        right_panel = QFrame()
        right_panel.setFrameShape(QFrame.StyledPanel)
        right_panel.setFrameShadow(QFrame.Raised)
        right_panel.setStyleSheet("border: none;")
        right_panel.setLayout(QVBoxLayout())

        # Preset buttons
        preset_btn_layout = QHBoxLayout()

        self.beast_mode_btn = QPushButton("Beast Mode")
        self.beast_mode_btn.setStyleSheet("background: #80daf6; color: white; font-weight: bold; border-radius: 5px; padding: 6px;")
        self.beast_mode_btn.clicked.connect(self.activate_beast_mode)

        self.balanced_mode_btn = QPushButton("Balanced Mode")
        self.balanced_mode_btn.setStyleSheet("background: #80daf6; color: white; font-weight: bold; border-radius: 5px; padding: 6px;")
        self.balanced_mode_btn.clicked.connect(self.activate_balanced_mode)

        preset_btn_layout.addWidget(self.beast_mode_btn)
        preset_btn_layout.addWidget(self.balanced_mode_btn)

        right_panel.layout().addLayout(preset_btn_layout)

        # Service Controls
        service_group = QGroupBox("Services to Disable During Gaming")
        service_group.setFixedSize(420, 480)
        service_group.setLayout(QVBoxLayout())
        # Add radius to the service group box
        service_group.setStyleSheet("""
            QGroupBox {
            background-color: transparent;
            border: 1px solid #cccccc;
            border-radius: 10px;
            margin-top: 10px;
            font-weight: bold;
            font-size: 14px;
            color: grey;
            }
            QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            color: grey;
            padding: 0 5px;
            }
        """)
        self.services_scroll = QScrollArea()
        self.services_scroll.setWidgetResizable(True)
        services_container = QWidget()
        services_container.setStyleSheet("""
            QWidget {
                border-radius: 10px;
                background-color: transparent;
            }
        """)
        self.services_layout = QGridLayout(services_container)
        
        self.services_layout.setSpacing(10)
        self.services_layout.setContentsMargins(10, 10, 10, 10)
        self.services_scroll.setWidget(services_container)
        service_group.layout().addWidget(self.services_scroll)
        if self.dark_mode:
            self.games_scroll.setStyleSheet(self.dark_scrollbar_style)
            self.services_scroll.setStyleSheet(self.dark_scrollbar_style)
        else:
            self.games_scroll.setStyleSheet(self.light_scrollbar_style)
            self.services_scroll.setStyleSheet(self.light_scrollbar_style)
        
        # Default services to disable (customize as needed)
        self.default_services = {
            # Core Windows Services
            "wuauserv": "Windows Update",
            "BITS": "Background Intelligent Transfer",
            "DPS": "Diagnostic Policy Service",
            "DiagTrack": "Connected User Experiences",
            "WdiServiceHost": "Diagnostic System Host",
            
            # Graphics/Display Related
            "DisplayEnhancementService": "Display Enhancement",
            "FrameServer": "Camera Frame Server",
            "GraphicsPerfSvc": "Graphics Performance",
            
            # Networking
            "NcdAutoSetup": "Network Connected Devices Auto-Setup",
            "NetTcpPortSharing": "Net.Tcp Port Sharing",
            "p2pimsvc": "Peer Networking Identity Manager",
            "p2psvc": "Peer Networking Grouping",
            "PNRPsvc": "Peer Name Resolution Protocol",
            "QWAVE": "Quality Windows Audio Video Experience",
            "RasMan": "Remote Access Connection Manager",
            "RemoteAccess": "Routing and Remote Access",
            "SSDPSRV": "SSDP Discovery",
            "WpnService": "Windows Push Notifications",
            
            # Hardware Related
            "SensrSvc": "Sensor Monitoring Service",
            "SensorService": "Sensor Service",
            "TabletInputService": "Touch Keyboard & Handwriting",
            "UevAgentService": "User Experience Virtualization",
            "WbioSrvc": "Windows Biometric Service",
            
            # Media Services
            "WMPNetworkSvc": "Windows Media Player Network Sharing",
            "icssvc": "Windows Mobile Hotspot Service",
            "stisvc": "Windows Image Acquisition",
            
            # Security Services
            "wscsvc": "Windows Security Center",
            "SecurityHealthService": "Windows Security Health",
            "Sense": "Windows Defender Advanced Threat Protection",
            
            # Telemetry/Reporting
            "dmwappushservice": "Device Management Wireless Application",
            "lfsvc": "Geolocation Service",
            "MapsBroker": "Downloaded Maps Manager",
            "WerSvc": "Windows Error Reporting",
            
            # Virtualization
            "vmicguestinterface": "Hyper-V Guest Service Interface",
            "vmickvpexchange": "Hyper-V KVP Exchange",
            "vmicrdv": "Hyper-V Remote Desktop Virtualization",
            "vmicshutdown": "Hyper-V Guest Shutdown Service",
            
            # Legacy/Deprecated
            "Fax": "Fax Service",
            "fhsvc": "File History Service",
            "HomeGroupProvider": "HomeGroup Provider",
            "HomeGroupListener": "HomeGroup Listener",
            "SCardSvr": "Smart Card",
            "SCPolicySvc": "Smart Card Removal Policy",
            "wercplsupport": "Problem Reports Control Panel Support",
            
            # Xbox Services
            "XblAuthManager": "Xbox Live Auth Manager",
            "XblGameSave": "Xbox Live Game Save",
            "XboxNetApiSvc": "Xbox Live Networking",
            
            # Additional Performance Services
            "AJRouter": "AllJoyn Router",
            "CertPropSvc": "Certificate Propagation",
            "DsmSvc": "Device Setup Manager",
            "InstallService": "Microsoft Store Install Service",
            "MixedRealityOpenXRSvc": "Windows Mixed Reality OpenXR",
            "TrkWks": "Distributed Link Tracking Client",
            "WSearch": "Windows Search"
        }

        self.service_checkboxes = []
        self.checkbox_style_template = """
                QCheckBox {{
                    font-weight: bold;
                    font-size: 14px;
                    color: {text_color};
                    spacing: 8px;
                    padding: 4px;
                }}
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                    border: 2px solid {border_color};
                    border-radius: 4px;
                    background-color: {bg_color};
                }}
                QCheckBox::indicator:checked {{
                    background-color: {theme_color};
                    border: 2px solid {border_color};
                }}
                QCheckBox:hover {{
                    color: {hover_color};
                }}
            """
        
        # Populate service toggles
        for idx, (service_id, service_name) in enumerate(self.default_services.items()):
            frame = QFrame()
            frame.setFixedSize(340, 40)
            frame.setStyleSheet("background: transparent; border-radius: 5px;")
            frame.setLayout(QHBoxLayout())
            
        
            cb = QCheckBox(service_name)
            cb.setChecked(self.service_config.get(service_id, False))
            cb.stateChanged.connect(lambda state, s=service_id: self.update_service_config(s, state))
            self.service_checkboxes.append(cb)
                
            cb.setProperty("style_template", self.checkbox_style_template)
                
            self.update_checkbox_colors()
            
            frame.layout().addWidget(cb)
            self.services_layout.addWidget(frame, idx, 0)
        
        right_panel.layout().addWidget(service_group)
        
        # Add panels to main page
        page.layout().addWidget(left_panel)
        page.layout().addWidget(right_panel)
        self.update_game_buttons()

    def update_checkbox_colors(self):
        """Update all service checkboxes with current theme colors"""
        theme_color = QColor().fromHsv(self.current_hue, 150, 245)
        text_color = "black" if self.dark_mode else "grey"
        border_color = "#666666" if self.dark_mode else "#AAAAAA"
        bg_color = "#2A2A2A" if self.dark_mode else "#F0F0F0"
        hover_color = "#3AAFA9"  # Can be theme-based if needed

        for checkbox in self.service_checkboxes:
            style = checkbox.property("style_template").format(
                theme_color=theme_color.name(),
                text_color=text_color,
                border_color=border_color,
                bg_color=bg_color,
                hover_color=hover_color
            )
            checkbox.setStyleSheet(style)

    def update_service_config(self, service_id, state):
        self.service_config[service_id] = bool(state)
        self.save_service_config()

    def launch_game(self, path, button=None):
            if button and hasattr(button, 'loading_overlay'):
                button.loading_overlay.start_animation()
                QApplication.processEvents()

            self.stopped_services = []
            self.progress_signal = ProgressSignal()  # Create signal object
            self.progress_signal.progress_updated.connect(
                lambda p: setattr(button.loading_overlay, 'progress', p) if button and hasattr(button, 'loading_overlay') else None
            )
            self.progress_signal.progress_updated.connect(
                lambda p: button.loading_overlay.update() if button and hasattr(button, 'loading_overlay') else None
            )
            self.progress_signal.message_updated.connect(
                lambda msg: print(f"Progress: {msg}")
            )

            def update_progress():
                total_services = len(self.service_config)
                services_stopped = 0
                
                for service_id, should_stop in self.service_config.items():
                    if not should_stop:
                        continue
                        
                    try:
                        # Try normal stop
                        subprocess.run(
                            f"net stop {service_id}",
                            shell=True,
                            check=True,
                            creationflags=subprocess.CREATE_NO_WINDOW,
                            timeout=10
                        )
                    except subprocess.CalledProcessError:
                        try:
                            # Try force kill
                            service_info = subprocess.check_output(
                                f"sc queryex {service_id}",
                                shell=True,
                                creationflags=subprocess.CREATE_NO_WINDOW
                            ).decode(errors="ignore")
                            
                            if pid_match := re.search(r"PID\s*:\s*(\d+)", service_info):
                                pid = int(pid_match.group(1))
                                subprocess.run(
                                    f"taskkill /PID {pid} /F",
                                    shell=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW
                                )
                        except Exception as e:
                            # Silent fail for protected services
                            print(f"Could not stop {service_id}: {str(e)}")
                            continue
                            
                    services_stopped += 1
                    progress = int((services_stopped / total_services) * 50)
                    self.progress_signal.progress_updated.emit(progress)

                self.progress_signal.message_updated.emit("Launching game...")
                self.progress_signal.progress_updated.emit(75)  # Approximate mid-point
                time.sleep(2)  # Simulate game launch delay (replace with actual launch)
                self.game_launcher(path, button)  # Launch the game

            progress_thread = threading.Thread(target=update_progress)
            progress_thread.start()

    def game_launcher(self, path, button=None):
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            process = subprocess.Popen(
                path,
                startupinfo=startupinfo,
                creationflags=subprocess.HIGH_PRIORITY_CLASS | subprocess.CREATE_NEW_PROCESS_GROUP
            )

            def restore_services():
                while process.poll() is None:
                    QApplication.processEvents()
                for service_id in self.stopped_services:
                    try:
                        subprocess.run(
                            f"net start {service_id}",
                            shell=True,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                    except Exception as e:
                        print(f"Failed to start {service_id}: {str(e)}")
                if button and hasattr(button, 'loading_overlay'):
                    self.progress_signal.progress_updated.emit(100)
                    time.sleep(0.5)
                    button.loading_overlay.hide()

            threading.Thread(target=restore_services, daemon=True).start()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch game:\n{str(e)}")
            if button and hasattr(button, 'loading_overlay'):
                button.loading_overlay.hide()
            for service_id in self.stopped_services:
                try:
                    subprocess.run(f"net start {service_id}", shell=True)
                except:
                    pass
    
    def start_game_thread(self):
        game_thread = threading.Thread(target=self.game_launcher, args=(os.path, None))
        game_thread.start()

    def update_game_buttons(self):
        # Clear existing buttons
        for i in reversed(range(self.games_grid.count())): 
            widget = self.games_grid.itemAt(i).widget()
            if hasattr(widget, 'loading_overlay'):
                widget.loading_overlay.deleteLater()
            widget.deleteLater()
        
        # Add new buttons with fixed size
        for idx, game in enumerate(self.games):
            # Create a container widget for the game button and remove button
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(5)
            
            # Game button
            btn = QPushButton()
            btn.setFixedSize(280, 280)
            btn.setIcon(QFileIconProvider().icon(QFileInfo(game["path"])))
            btn.setIconSize(QSize(100, 100))
            btn.setStyleSheet("""
                QPushButton { 
                    border-radius: none;
                    background: transparent;
                    border: none;
                }
                QPushButton:hover { 
                    background: transparent;
                    border-color: none;
                }
            """)
            
            # Add loading overlay
            btn.loading_overlay = PercentageOverlay(btn)
            btn.loading_overlay.setGeometry(0, 0, btn.width(), btn.height())
            
            # Connect click signal with path and button reference
            btn.clicked.connect(lambda _, p=game["path"], b=btn: self.launch_game(p, b))
            
            # Remove button
            remove_btn = QPushButton("Remove")
            remove_btn.setFixedSize(280, 30)
            remove_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #aaa;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover { background: transparent; color: #ff4d4d; }
            """)
            remove_btn.clicked.connect(lambda _, idx=idx: self.remove_game(idx))
            
            # Add buttons to the container layout
            container_layout.addWidget(btn)
            container_layout.addWidget(remove_btn)
            
            self.games_grid.addWidget(container, idx // 1, idx % 1)

    def remove_game(self, idx):
        del self.games[idx]
        self.save_games()
        self.update_game_buttons()

    def add_game_dialog(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Executable Files (*.exe)")
        
        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                game_path = selected_files[0]
                game_name = os.path.basename(game_path)
                self.games.append({"name": game_name, "path": game_path})
                self.save_games()
                self.update_game_buttons()   
    
    def download_required_files(self):
        try:
            # Download UI file
            ui_content = requests.get(self.ui_url).content
            with open(os.path.join(self.temp_dir, "interface.ui"), "wb") as f:
                f.write(ui_content)
            
            return True
        except Exception as e:
            QMessageBox.critical(None, "Error", 
                #f"Failed to download required files:\n{str(e)}\n\n"
                f"Please check your internet connection and try again.")
            return False
    
    
    def setup_ui(self):
        try:
            ui_file = os.path.join(self.temp_dir, "interface.ui")
            uic.loadUi(ui_file, self)
        except Exception as e:
            QMessageBox.critical(None, "Error", 
                #f"Failed to load UI file:\n{str(e)}\n\n"
                #f"Please make sure the UI file exists at:\n{self.ui_url}")
                f"maintaining server, please come back later.")
            sys.exit(1)

            # Add BIOS warning label to BIOS pages
        for page_idx in [8, 9]:  # BIOS pages
            page = self.stackedWidget.widget(page_idx)
            if not page.layout():
                page.setLayout(QVBoxLayout())  # Set a default layout if none exists
            warning = QLabel(
                "⚠️ BIOS optimizations may require admin rights and system restart. "
                "Use with caution as incorrect settings may cause system instability."
            )
            warning.setStyleSheet("color: orange; font-weight: bold;")
            warning.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
            page.layout().insertWidget(0, warning)
    
    
    def setup_main_toggle(self):
        self.main_toggle = ToggleButton(self, width=70, height=34)
        header_layout = self.header.layout()
        toggle_container = QFrame()
        toggle_layout = QHBoxLayout(toggle_container)
        dark_mode_label = QLabel("Dark Mode:")
        dark_mode_label.setStyleSheet("font-size: 16px; color:grey; font-weight: bold;")
        toggle_layout.addWidget(dark_mode_label)
        toggle_layout.addWidget(self.main_toggle, alignment=Qt.AlignRight)
        toggle_layout.setContentsMargins(0, 0, 150, 0)
        toggle_layout.setSpacing(15)
        header_layout.insertWidget(1, toggle_container)
        self.main_toggle.toggled.connect(self.toggle_theme)
    
    def toggle_theme(self, state):
        self.dark_mode = state
        if state:
            self.setStyleSheet("background-color: #232429; color: white;")
            self.header.setStyleSheet("background-color: #2a2f34; color: white;")
            #self.sidemenu.setStyleSheet("QFrame { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #7fddfa, stop: 1 #8ff9eb); border-radius: 10px; }")
            #elf.frame_3.setStyleSheet("background-color: #232429;")
            self.stackedWidget.setStyleSheet("background-color: #2b2e35; color:white;")
            self.games_scroll.setStyleSheet(self.dark_scrollbar_style)
            self.services_scroll.setStyleSheet(self.dark_scrollbar_style)
            # Update active button style if one is selected
            if self.active_button:
                self.active_button.setStyleSheet(self.dark_active_style)
            
            # Update inactive buttons
            for button in self.menu_buttons:
                if button != self.active_button:
                    button.setStyleSheet(self.dark_inactive_style)
            self.progressBar.bg_color = QColor(45, 45, 45)
            #self.progressBar.progress_color = QColor(0, 150, 255)
            self.progressBar.text_color = QColor(200, 200, 200)
            self.statusLabel.setStyleSheet("color: #ddd;")
            self.fileLabel.setStyleSheet("color: #aaa;")
        else:
            self.setStyleSheet("background-color: #f1f1f1; border-radius: 10px; color: black;")
            self.header.setStyleSheet("background-color: transparent; color: black;")
            #self.sidemenu.setStyleSheet("QFrame { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #7fddfa, stop: 1 #8ff9eb); border-radius: 10px; }")
            self.stackedWidget.setStyleSheet("background-color: #ffffff; color:black;")
            self.games_scroll.setStyleSheet(self.light_scrollbar_style)
            self.services_scroll.setStyleSheet(self.light_scrollbar_style)
            # Update active button style if one is selected
            if self.active_button:
                self.active_button.setStyleSheet(self.light_active_style)
            
            # Update inactive buttons
            for button in self.menu_buttons:
                if button != self.active_button:
                    button.setStyleSheet(self.light_inactive_style)
            self.progressBar.bg_color = QColor(230, 230, 230)
            #self.progressBar.progress_color = QColor(0, 122, 255)
            self.progressBar.text_color = QColor(50, 50, 50)
            self.statusLabel.setStyleSheet("color: #333;")
            self.fileLabel.setStyleSheet("color: #666;")
        self.progressBar.update()
        # Rest of your existing theme code...
        for i in range(self.stackedWidget.count()):
            page = self.stackedWidget.widget(i)
            frames = page.findChildren(QFrame, "frame1")
            for frame in frames:           
                frame.setStyleSheet("background-color: #34373e; min-height: 35px; border-radius: 10px;" if state else "background-color: #ffffff; min-height: 35px; border-radius: 10px;")
        for i in range(self.stackedWidget.count()):
            page = self.stackedWidget.widget(i)
            label = page.findChildren(QLabel, "title_label")
            for lbl in label:
                lbl.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 15px;" if state else "color: #1f1f1f; font-weight: bold; font-size: 15px")
        for i in range(self.stackedWidget.count()):
            page = self.stackedWidget.widget(i)
            label = page.findChildren(QLabel, "status_label")
            for lbl in label:
                lbl.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 15px;" if state else "color: #1f1f1f; font-weight: bold; font-size: 15px")
        
        self.update()
        # Update process manager styles
        if hasattr(self, 'process_scroll'):
            self.process_scroll.setStyleSheet(self.dark_scrollbar_style if state else self.light_scrollbar_style)
        # Update process list items
        if hasattr(self, 'process_list_layout'):
            for i in range(self.process_list_layout.count()):
                item = self.process_list_layout.itemAt(i)
                if item.widget():
                    frame = item.widget()
                    frame.setStyleSheet("""
                        QFrame {
                            background-color: transparent;
                            border-radius: 5px;
                            padding: 10px;
                            font-size: 14px;
                            font-weight: bold;
                        }
                    """ if not state else """
                        QFrame {
                            background-color: transparent;
                            border-radius: 5px;
                            padding: 10px;
                            font-size: 14px;
                            font-weight: bold;
                        }
                    """)
                    for child in frame.children():
                        if isinstance(child, QLabel):
                            child.setStyleSheet("color: #000000; font-size: 14px; font-weight: bold; " if not state else "color: #ffffff; font-size: 14px; font-weight: bold;")
                            
    def connect_menu_buttons(self):
        # Map buttons to their page indices (button_order matches stackedWidget page order)
        self.menu_buttons = [
            self.pushButton_2,  # item1 -> page0
            self.pushButton_3,  # item2 -> page1
            self.pushButton_4,  # item3 -> page2
            self.pushButton_5,  # item4 -> page3
            self.pushButton_6,  # item5 -> page4
            self.pushButton_7,  # item6 -> page5
            self.pushButton_8,  # item7 -> page6
            self.pushButton_9,  # item8 -> page7
            self.pushButton_10, # item9 -> page8
            self.pushButton_11, # item10 -> page9
            self.pushButton_12, # item11 -> page10
            self.pushButton_13, # item12 -> page11
            self.pushButton_14, # item13 -> page12
            self.pushButton_15  # item14 -> page13
        ]

        # Connect each button to its page using lambda
        for index, button in enumerate(self.menu_buttons):
            button.clicked.connect(
                lambda _, idx=index: self.stackedWidget.setCurrentIndex(idx)
            )

        # Set initial active page
        self.stackedWidget.setCurrentIndex(12)
            
        self.active_button = None
            
            # Define the style sheets for light and dark modes
        self.light_active_style = """
            QPushButton {
                background-color: #f1f1f1;
                border-radius: 8px;
                color: black;
                padding: 8px 16px;
                font-weight: bold;
            }
            """
            
        self.light_inactive_style = """
            QPushButton {
                background-color: transparent;
                border-radius: 5px;
                color: #333;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7bc5e1;
            }
            QPushButton:pressed {
                background-color: #80daf6;
            }
            """
            
        self.dark_active_style = """
            QPushButton {
                background-color: #34373e;
                border-radius: 8px;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
            }
            """
            
        self.dark_inactive_style = """
            QPushButton {
                background-color: transparent;
                border-radius: 5px;
                color: black;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a4e57;
            }
            QPushButton:pressed {
                background-color: #5a5e67;
            }
            """
            
        for i, button in enumerate(self.menu_buttons):
                button.clicked.connect(lambda _, idx=i, btn=button: self.change_page(idx, btn))
            
            # Set initial active button (first button)
        if self.menu_buttons:
                self.change_page(0, self.menu_buttons[0])

    def change_page(self, index, button):
        # Reset previous active button style
        if self.active_button:
            if self.dark_mode:
                self.active_button.setStyleSheet(self.dark_inactive_style)
            else:
                self.active_button.setStyleSheet(self.light_inactive_style)
        
        # Set new active button style
        if self.dark_mode:
            button.setStyleSheet(self.dark_active_style)
        else:
            button.setStyleSheet(self.light_active_style)
        
        self.active_button = button
        
        # Change the page
        self.stackedWidget.setCurrentIndex(index)
    
    

    def setup_menu_button(self):
        self.pushButton_17.clicked.connect(self.showMinimized)
        self.pushButton_17.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 5px;
                font-size: 16px;
                font-weight: bold;                         
            }
            QPushButton:hover {
                background-color: rgba(0,0,0,0.1);
            }
        """)
        
        self.pushButton_17.setIconSize(QSize(20, 20))
        self.pushButton_17.setFixedSize(30, 30)
        self.pushButton_17.setCursor(QCursor(Qt.PointingHandCursor))

  
        
        self.pushButton.clicked.connect(self.close_application)
        
        self.pushButton.setIconSize(QSize(20, 20))
        self.pushButton.setFixedSize(30, 30)
        self.pushButton.setCursor(QCursor(Qt.PointingHandCursor))
        
        self.pushButton.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0,0,0,0.1);                          
            }                          
        """)

    

    
    def _check_bios_setting(self, setting):
        """Check current BIOS setting state"""
        try:
            if setting == "XMP":
                output = subprocess.check_output(
                    'wmic memorychip get ConfiguredClockSpeed /value',
                    shell=True, creationflags=subprocess.CREATE_NO_WINDOW
                ).decode(errors='ignore')
                speeds = [int(line.split('=')[1]) for line in output.splitlines()
                        if '=' in line and line.split('=')[1].strip().isdigit()]
                return any(speed > 2400 for speed in speeds)              

            elif setting == "CStates":
                output = subprocess.check_output(
                    'wmic cpu get PowerManagementCapabilities /value',
                    shell=True, creationflags=subprocess.CREATE_NO_WINDOW
                ).decode()
                return "1" not in output  # If 1 is not present, C-States might be off

            elif setting == "HPET":
                output = subprocess.check_output(
                    'bcdedit /enum', 
                    shell=True, creationflags=subprocess.CREATE_NO_WINDOW
                ).decode().lower()
                return "useplatformclock" in output and "yes" in output

            elif setting == "SpeedStep":
                output = subprocess.check_output(
                    'powercfg -query',
                    shell=True, creationflags=subprocess.CREATE_NO_WINDOW
                ).decode()
                return "Processor performance increase policy" not in output

            elif setting == "TurboBoost":
                output = subprocess.check_output(
                    'wmic cpu get Name,CurrentClockSpeed,MaxClockSpeed /format:list',
                    shell=True, creationflags=subprocess.CREATE_NO_WINDOW
                ).decode()
                speeds = dict(line.split('=') for line in output.strip().splitlines() if '=' in line)
                return int(speeds.get('CurrentClockSpeed', 0)) > int(speeds.get('MaxClockSpeed', 0))

            elif setting == "SecureBoot":
                output = subprocess.check_output(
                    'powershell -Command "Confirm-SecureBootUEFI"',
                    shell=True, creationflags=subprocess.CREATE_NO_WINDOW
                ).decode().strip()
                return output.lower() == "true"

            elif setting == "AHCI":
                output = subprocess.check_output(
                    'reg query HKLM\\SYSTEM\\CurrentControlSet\\Services\\iaStorV',
                    shell=True, creationflags=subprocess.CREATE_NO_WINDOW
                ).decode().lower()


            elif setting == "Virtualization":
                output = subprocess.check_output(
                    'bcdedit',
                    shell=True, 
                    creationflags=subprocess.CREATE_NO_WINDOW
                ).decode().lower()
                # Extract hypervisorlaunchtype value
                for line in output.splitlines():
                    if "hypervisorlaunchtype" in line:
                        value = line.split()[-1].strip()
                        return value == "auto"  # True if enabled

            elif setting == "FastBoot":
                output = subprocess.check_output(
                    'powercfg /a',
                    shell=True, creationflags=subprocess.CREATE_NO_WINDOW
                ).decode().lower()
                return "fast startup" not in output

            elif setting == "Above4G":
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers") as key:
                        value, _ = winreg.QueryValueEx(key, "EnableAbove4G")
                        return value == 1
                except:
                    return False

            elif setting == "CSM":
                return False  # No way to detect from OS, assume disabled

            elif setting == "TPM":
                output = subprocess.check_output(
                    'powershell -Command "Get-WmiObject -Namespace \"Root\\CIMv2\\Security\\MicrosoftTpm\" -Class Win32_Tpm"',
                    shell=True, creationflags=subprocess.CREATE_NO_WINDOW
                ).decode()
                return "IsEnabled_InitialValue : True" in output

            elif setting == "SVM":
                return False  # AMD SVM cannot be read directly from OS

            elif setting == "IOMMU":
                return False  # IOMMU detection is very hardware-specific

            elif setting == "PCIeGen":
                try:
                    output = subprocess.check_output(
                        'powershell -Command "Get-CimInstance -ClassName Win32_VideoController | Select-Object -ExpandProperty CurrentBitsPerPixel"',
                        shell=True, creationflags=subprocess.CREATE_NO_WINDOW
                    ).decode().strip()
                    return "Max" if int(output) >= 32 else "Auto"
                except:
                    return "Unknown"

            else:
                return False

        except Exception as e:
            print(f"Error checking BIOS setting {setting}: {e}")
            return False


    def check_power_plan(self):
        """Check current power plan"""
        try:
            output = subprocess.check_output(
                'powercfg /getactivescheme',
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            ).decode()
            if "High performance" in output:
                return "High performance"
            return "Balanced"
        except:
            return "Unknown"

    def check_registry_state(self, key_path, value_name, default=False):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                value, _ = winreg.QueryValueEx(key, value_name)
                return str(value) == "1"
        except:
            return default
    
    def check_service_state(self, service_name):
        """Check if a service is disabled (4) or not"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                f"SYSTEM\\CurrentControlSet\\Services\\{service_name}"
            )
            start_value, _ = winreg.QueryValueEx(key, "Start")
            winreg.CloseKey(key)
            return start_value
        except:
            return 2  # Assume automatic start if key doesn't exist
    
    def set_service_state(self, service_id, state, display_name=""):
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, f"SYSTEM\\CurrentControlSet\\Services\\{service_id}")
            winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, state)
            winreg.CloseKey(key)
            
            if not self.silent_mode and display_name:
                status = "disabled" if state == 4 else "enabled"
                self.show_message("Success", f"{display_name} {status}")
            return True
        except Exception as e:
            if not self.silent_mode:
                self.show_message("Error", f"Service control failed: {str(e)}", True)
            return False
        
    def reset_toggle(self, toggle_number, desired_state):
        """Reset a toggle to a specific state if it exists"""
        toggle_name = f"toggle_{toggle_number}"
        for toggle in self.toggles:
            if toggle.objectName() == toggle_name:
                # Block signals temporarily to prevent triggering the action
                old_silent = self.silent_mode
                self.silent_mode = True  # Prevent messages during reset
                toggle.blockSignals(True)
                toggle.setChecked(desired_state)
                toggle.blockSignals(False)
                self.silent_mode = old_silent
                
                # Update the status label
                parent = toggle.parent()
                if parent:
                    for child in parent.children():
                        if isinstance(child, QLabel) and child.text() in ["OPTIMIZED", "NOT OPT"]:
                            child.setText("OPTIMIZED" if desired_state else "NOT OPT")
                break
        
    def init_toggles(self):
        toggle = ToggleButton(active_color=QColor().fromHsv(self.current_hue, 150, 245))
        self.toggles = []
        self.status_labels = []  # Store references to all status labels
        toggle_labels = [
            ("Disable Game Bar", "Reduces background processes"),
            ("Disable Fullscreen Opt", "Improves fullscreen performance"),
            ("High Perf Power Plan", "Maximizes system performance"),
            ("Disable Animations", "Reduces UI latency"),
            ("Enable HPET", "High Precision Event Timer for better timing"),
            ("Disable Telemetry", "Reduces system tracking"),
            ("Disable Notifications", "Prevents pop-up distractions"),
            ("Disable Cortana", "Reduces search indexing"),
            ("Disable Windows Defender", "Reduces scanning impact"),
            ("Optimize NTFS", "Improves file system performance"),
            ("Disable Superfetch (Registry)", "Reduces disk usage via registry"),
            ("CPU Priority Boost", "Prioritizes gaming processes"),
            ("Disable Diagnostics Tracking", "Reduces background telemetry"),
            ("Disable Error Reporting", "Reduces background tasks"),
            ("Network Throttle Off", "Optimizes gaming traffic"),
            ("Disable Windows Tips", "Reduces system interruptions"),
            ("Disable Background Apps", "Frees up system resources"),
            ("Disable Aero Peek", "Reduces GPU load"),
            ("Disable Xbox DVR", "Eliminates recording overhead"),
            ("Timer Resolution Boost", "Improves frame pacing"),
            ("Disable Firewall", "Reduces network latency"),
            ("Disable Updates", "Prevents background updates"),
            ("Disable Shadows", "Reduces GPU workload"),
            ("Disable Transparency", "Reduces compositing load"),
            ("Disable Widgets", "Reduces memory usage"),
            ("Disable V-Sync", "Reduces input lag"),
            ("Disable Game Mode", "Alternative optimization"),
            ("Disable Spectre/Meltdown", "Improves CPU performance"),
            ("Enable ULPS", "Optimizes multi-GPU systems"),
            ("Disable HPET", "Alternative timer setting"),
            ("Disable Core Parking", "Improves CPU utilization"),
            ("Enable MSI Mode", "Improves interrupt handling"),
            ("Disable Memory Compression", "Reduces CPU overhead"),
            ("Disable SysMain (Service)", "Stops the Superfetch service"),
            ("Disable Write Combining", "Improves GPU performance"),
            ("Disable DWM", "Reduces compositing overhead"),
            ("Disable WSearch", "Reduces disk activity"),
            ("Disable Print Spooler", "Reduces background services"),
            ("Disable Windows Ink", "Reduces touch overhead"),
            ("Disable Touch Keyboard", "Reduces input services"),
            ("Disable Biometrics", "Reduces security overhead"),
            ("Disable Location", "Reduces tracking services"),
            ("Disable Camera", "Reduces privacy services"),
            ("Disable Microphone", "Reduces audio services"),
            ("Disable Bluetooth", "Reduces radio interference"),
            ("Disable WiFi Sense", "Reduces network sharing"),
            ("Disable Hotspot", "Reduces radio services"),
            ("Disable Airplane Mode", "Ensures connectivity"),
            ("Disable NFC", "Reduces radio services"),
            ("Disable AutoPlay", "Reduces disk interrupts"),
            ("Disable AutoUpdate", "Prevents background updates"),
            ("Disable SmartScreen", "Reduces security checks"),
            ("Disable UAC", "Reduces permission prompts"),
            ("Disable Hibernation", "Frees up disk space"),
            ("Disable Sleep", "Prevents performance drops"),
            ("Disable Fast Startup", "Improves cold boot"),
            ("Disable Remote Desktop Services", "Reduces remote access overhead"),
            ("Disable Thumbnails", "Reduces file explorer load"),
            ("Disable Recent Files", "Reduces tracking"),
            ("Disable OneDrive", "Reduces cloud sync"),
            ("Disable Clipboard History", "Reduces memory usage"),
            ("Disable Focus Assist", "Reduces notifications"),
            ("Disable Night Light", "Reduces color processing"),
            ("Disable Magnifier", "Reduces accessibility services"),
             #- System Services
            ("Disable SysMain", "Formerly Superfetch - reduces disk usage"),
            ("Disable Windows Update", "Prevents automatic updates"),
            ("Disable Windows Defender", "Disables real-time protection"),
            ("Disable Print Spooler", "Not needed if no printers are used"),
            ("Disable Remote Registry", "Security risk if enabled"),
            ("Disable Error Reporting", "Reduces background tasks"),
            ("Disable Windows Search", "Reduces disk activity"),
            ("Disable Diagnostics Tracking", "Improves privacy"),
            ("Disable Connected Devices", "Reduces background services"),
            ("Disable Bluetooth Support", "If not using Bluetooth"),
            ("Disable Xbox Live Services", "For non-gaming systems"),
            ("Disable IP Helper", "IPv6 tunneling service"),
            ("Disable Secondary Logon", "Security improvement"),
            ("Disable Program Compatibility", "For legacy app support"),
            ("Disable Downloaded Maps", "If not using offline maps"),
            ("Disable Fax Service", "Legacy fax support"),
            ("Disable HomeGroup Provider", "Unnecessary for non-HomeGroup networks"),
            ("Disable HomeGroup Listener", "If not using HomeGroup sharing"),
            ("Disable Smart Card", "If not using smart card authentication"),
            ("Disable Windows Insider", "For non-Insider builds"),
            ("Disable Windows Media Scheduler", "If not using Windows Media recording"),
            ("Disable AllJoyn Router", "IoT service rarely used"),
            ("Disable Device Association", "For automatic device pairing"),
            ("Disable Device Management", "Enterprise device management"),
            ("Disable Retail Demo", "For store demo mode"),
            ("Disable Sensor Services", "For devices without sensors"),
            ("Disable Geolocation Service", "If not using location services"),
            ("Disable Touch Keyboard", "For desktop PCs without touch"),
            ("Disable Tablet Input", "For non-tablet devices"),
            ("Disable Windows Font Cache", "Can be manually rebuilt"),
            ("Disable Windows Image Acquisition", "For old scanners/cameras"),
            ("Disable Windows Mobile Hotspot", "If not using hotspot feature"),
            ("Disable Work Folders", "Enterprise sync feature"),
            ("Disable Windows Backup", "If using third-party backup"),
            ("Disable Windows Camera Frame Server", "For camera effects"),
            ("Disable Windows Connect Now", "Wi-Fi configurator"),
            ("Disable Windows Event Collector", "Enterprise event logging"),
            ("Disable Windows Push Notifications", "Reduces notifications"),
            ("Disable Windows Time", "If not syncing time automatically"),
            ("Disable WLAN AutoConfig", "If not using Wi-Fi"),
                    # Page 8- BIOS Optimizations
            ("Enable XMP Profile", "Optimizes RAM speed and timings"),
            ("Disable C-States", "Prevents CPU sleep states for max performance"),
            ("Enable HPET", "High Precision Event Timer for better timing"),
            ("Disable SpeedStep", "Keeps CPU at max clock speed"),
            ("Enable Turbo Boost", "Allows CPU to exceed base clock"),
            ("Disable Secure Boot", "May improve compatibility with some hardware"),
            ("Enable AHCI Mode", "Better SSD performance than IDE mode"),
            ("Disable Virtualization", "If not running virtual machines"),
            
            # Page 9 - More BIOS Options
            ("Disable Fast Boot", "More thorough boot process"),
            ("Enable Above 4G Decoding", "Helps with large GPU memory"),
            ("Disable CSM", "UEFI-only mode for faster boots"),
            ("Set Performance Power Plan", "Maximizes power delivery"),
            ("Disable TPM", "If not using security features"),
            ("Enable SVM Mode", "AMD virtualization technology"),
            ("Disable IOMMU", "If not using hardware passthrough"),
            ("Set PCIe Gen3/Gen4", "Force maximum PCIe generation")
       
        ]


        
        for page_idx in range(10):
            page = self.stackedWidget.widget(page_idx)
            container = QFrame(page)
            container.setGeometry(10, 60, 810, 430)
            
            grid = QGridLayout(container)
            grid.setSpacing(15)
            grid.setContentsMargins(4, 4, 4, 4)
            
            for i, toggle in enumerate(self.toggles):
                #toggle.toggled.connect(lambda state, idx=i: self.handle_toggle(state, idx))
                toggle.toggled.connect(self.update_optimization_stats)  # Add this line
            for i in range(12):
                toggle_idx = page_idx * 12 + i
                if toggle_idx >= len(toggle_labels):
                    break
                    
                label, description = toggle_labels[toggle_idx]
                
                frame1 = QFrame()
                frame1.setObjectName("frame1")
                frame1.setFrameShape(QFrame.StyledPanel)
                frame1.setLineWidth(1)
                frame1.setStyleSheet("""
                    QFrame {
                        border-radius: 10px;
                        min-height: 35px;
                        background-color: #ffffff; /* Default light mode color */
                    }
                """)
                shadow_effect = QGraphicsDropShadowEffect()
                shadow_effect.setBlurRadius(8)
                shadow_effect.setOffset(5, 5)  # Offset shadow to the right and bottom
                shadow_effect.setColor(QColor(0, 0, 0, 40))
                frame1.setGraphicsEffect(shadow_effect)
                
                frame_layout = QHBoxLayout(frame1)
                frame_layout.setContentsMargins(7, 5, 5, 5)
                frame_layout.setSpacing(25)
                
                # Text section
                text_layout = QVBoxLayout()
                text_layout.setSpacing(8)
                
                title_label = QLabel(f"<b>{label}</b>")
                title_label.setObjectName("title_label")
                title_label.setStyleSheet("font-size: 15px; color: #333333;")
                title_label.setWordWrap(True)

                desc_label = QLabel(description)
                desc_label.setStyleSheet("font-size: 12px; color: #666666;")
                desc_label.setWordWrap(True)
                
                text_layout.addWidget(title_label)
                text_layout.addWidget(desc_label)
                text_layout.addStretch()
                
                # Toggle section
                toggle_layout = QVBoxLayout()
                toggle_layout.setAlignment(Qt.AlignCenter)
                toggle_layout.setSpacing(8)
                
                toggle = ToggleButton(width=70, height=34)
                toggle.setObjectName(f"toggle_{toggle_idx + 1}")
                
                # Set initial state based on actual system configuration
                initial_state = self.check_initial_state(toggle_idx)
                toggle.setChecked(initial_state)
                
                status_label = QLabel("OPTIMIZED" if initial_state else "NOT OPT")
                status_label.setAlignment(Qt.AlignCenter)
                status_label.setObjectName("status_label")
                status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333;")
                self.status_labels.append(status_label)  # Store the reference
                
                toggle.toggled.connect(lambda state, lbl=status_label: lbl.setText("OPTIMIZED" if state else "NOT OPT"))
                
                toggle_layout.addWidget(toggle)
                toggle_layout.addWidget(status_label)
                
                frame_layout.addLayout(text_layout, 70)
                frame_layout.addLayout(toggle_layout, 30)
                
                row = i // 3
                col = i % 3
                grid.addWidget(frame1, row, col, Qt.AlignTop)
                
                self.toggles.append(toggle)
    
    def check_initial_state(self, index):
        # Optimization conditions for all 120 toggles
        toggle_conditions = {
            # Page 1 - General Optimizations (1-12)
            0: lambda: not self._get_reg_value(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR",
                "AppCaptureEnabled",
                1
            ),
            1: lambda: self._get_reg_value(
                r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
                "DisableFullscreenOptimization",
                0
            ),
            2: lambda: self._check_power_plan("8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"),
            3: lambda: self._get_reg_value(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
                "DisableStatusMessages",
                0
            ),
            4: lambda: self._get_reg_value(
                r"SYSTEM\CurrentControlSet\Services\W32Time\TimeProviders\NtpClient",
                "Enabled",
                0
            ),
            5: lambda: not self._get_reg_value(
                r"SOFTWARE\Policies\Microsoft\Windows\DataCollection",
                "AllowTelemetry",
                1
            ),
            6: lambda: self._get_reg_value(
                r"SOFTWARE\Policies\Microsoft\Windows\CurrentVersion\PushNotifications",
                "NoToastApplicationNotification",
                0
            ),
            7: lambda: not self._get_reg_value(
                r"SOFTWARE\Policies\Microsoft\Windows\Windows Search",
                "AllowCortana",
                1
            ),
            8: lambda: self._get_reg_value(
                r"SOFTWARE\Policies\Microsoft\Windows Defender",
                "DisableAntiSpyware",
                1
            ),
            9: lambda: self._get_reg_value(
                r"SYSTEM\CurrentControlSet\Control\FileSystem",
                "NtfsDisableLastAccessUpdate",
                0
            ) == 1,
            10: lambda: self._get_reg_value(
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters",
                "EnablePrefetcher",
                3
            ) == 0,
            11: lambda: self._get_reg_value(
                r"SYSTEM\CurrentControlSet\Control\PriorityControl",
                "Win32PrioritySeparation",
                2
            ) == 38,

            # Page 2 - More Optimizations (13-24)
            12: lambda: self._get_service_state("DPS") == 4,
            13: lambda: self._get_reg_value(
                r"SOFTWARE\Microsoft\Windows\Windows Error Reporting",
                "Disabled",
                1
            ),
            14: lambda: self._get_reg_value(
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
                "NetworkThrottlingIndex",
                0xA
            ) == 0xFFFFFFFF,
            15: lambda: not self._get_reg_value(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
                "SubscribedContent-338393Enabled",
                1
            ),
            16: lambda: self._get_reg_value(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications",
                "GlobalUserDisabled",
                1
            ),
            17: lambda: not self._get_reg_value(
                r"SOFTWARE\Microsoft\Windows\DWM",
                "EnableAeroPeek",
                1
            ),
            18: lambda: not self._get_reg_value(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR",
                "AppCaptureEnabled",
                1
            ),
            19: lambda: self._get_reg_value(
                r"SYSTEM\CurrentControlSet\Control\Session Manager\kernel",
                "GlobalTimerResolutionRequests",
                1
            ),
            20: lambda: not self._get_reg_value(
                r"SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\StandardProfile",
                "EnableFirewall",
                1
            ),
            21: lambda: self._get_reg_value(
                r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU",
                "NoAutoUpdate",
                1
            ),
            22: lambda: not self._get_reg_value(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                "ListviewShadow",
                1
            ),
            23: lambda: not self._get_reg_value(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                "EnableTransparency",
                1
            ),

            # Page 3 - UI/Performance (25-36)
            24: lambda: not self._get_reg_value(
                r"SOFTWARE\Policies\Microsoft\Dsh",
                "AllowNewsAndInterests",
                1
            ),
            25: lambda: not self._get_reg_value(
                r"SOFTWARE\Microsoft\Windows\DWM",
                "UseD3D9Ex",
                1
            ),
            26: lambda: not self._get_reg_value(
                r"SOFTWARE\Microsoft\GameBar",
                "AllowAutoGameMode",
                1
            ),
            27: lambda: self._get_reg_value(
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
                "FeatureSettingsOverride",
                3
            ),
            28: lambda: not self._get_reg_value(
                r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000",
                "EnableUlps",
                1
            ),
            29: lambda: not self._get_reg_value(
                r"SYSTEM\CurrentControlSet\Services\W32Time\TimeProviders\NtpServer",
                "Enabled",
                1
            ),
            30: lambda: self._get_reg_value(
                r"SYSTEM\CurrentControlSet\Control\Power\PowerSettings\54533251-82be-4824-96c1-47b60b740d00\0cc5b647-c1df-4637-891a-dec35c318583",
                "ValueMax",
                100
            ) == 0,
            31: lambda: self._get_reg_value(
                r"SYSTEM\CurrentControlSet\Services\msiserver",
                "Start",
                3
            ) == 4,
            32: lambda: self._get_reg_value(
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
                "DisableMemoryCompression",
                1
            ),
            33: lambda: self._get_reg_value(
                r"SYSTEM\CurrentControlSet\Services\SysMain",
                "Start",
                2
            ) == 4,
            34: lambda: not self._get_reg_value(
                r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
                "WriteCombiningSupported",
                1
            ),
            35: lambda: not self._get_reg_value(
                r"SOFTWARE\Microsoft\Windows\DWM",
                "Composition",
                1
            ),

            # Page 4 - System Services (37-48)
            36: lambda: self._get_service_state("WSearch") == 4,
            37: lambda: self._get_service_state("Spooler") == 4,
            38: lambda: not self._get_reg_value(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\PenWorkspace",
                "PenWorkspaceAppSuggestionsEnabled",
                1
            ),
            39: lambda: not self._get_reg_value(
                r"SOFTWARE\Microsoft\TabletTip\1.7",
                "TipbandDesiredVisibility",
                1
            ),
            40: lambda: not self._get_reg_value(
                r"SOFTWARE\Policies\Microsoft\Biometrics",
                "Enabled",
                1
            ),
            41: lambda: self._get_reg_value(
                r"SOFTWARE\Policies\Microsoft\Windows\LocationAndSensors",
                "DisableLocation",
                1
            ),
            42: lambda: self._get_reg_value(
                r"SOFTWARE\Policies\Microsoft\Windows\AppPrivacy",
                "LetAppsAccessCamera",
                2
            ),
            43: lambda: self._get_reg_value(
                r"SOFTWARE\Policies\Microsoft\Windows\AppPrivacy",
                "LetAppsAccessMicrophone",
                2
            ),
            44: lambda: not self._get_reg_value(
                r"SOFTWARE\Policies\Microsoft\Windows\Bluetooth",
                "AllowDiscoverableMode",
                1
            ),
            45: lambda: not self._get_reg_value(
                r"SOFTWARE\Microsoft\WcmSvc\wifinetworkmanager\config",
                "AutoConnectAllowedOEM",
                1
            ),
            46: lambda: not self._get_reg_value(
                r"SOFTWARE\Microsoft\WcmSvc\Tethering",
                "TetheringEnabled",
                1
            ),
            47: lambda: self._get_reg_value(
                r"SYSTEM\CurrentControlSet\Control\RadioManagement\SystemRadioState",
                "SystemRadioState",
                1
            ),

            # Page 5 - Network/Connectivity (49-60)
            48: lambda: not self._get_reg_value(
                r"SOFTWARE\Policies\Microsoft\Windows\Connect",
                "AllowNFC",
                1
            ),
            49: lambda: self._get_reg_value(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer",
                "NoDriveTypeAutoRun",
                145
            ) == 255,
            50: lambda: self._get_reg_value(
                r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU",
                "NoAutoUpdate",
                1
            ),
            51: lambda: self._get_reg_value(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer",
                "SmartScreenEnabled",
                "Warn",
                winreg.REG_SZ
            ) == "Off",
            52: lambda: not self._get_reg_value(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
                "EnableLUA",
                1
            ),
            53: lambda: not self._get_reg_value(
                r"SYSTEM\CurrentControlSet\Control\Power",
                "HibernateEnabled",
                1
            ),
            54: lambda: self._get_reg_value(
                r"SYSTEM\CurrentControlSet\Control\Power",
                "ACSettingIndex",
                0
            ),
            55: lambda: not self._get_reg_value(
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Power",
                "HiberbootEnabled",
                1
            ),
            56: lambda: self._get_service_state("TermService") == 4,
            57: lambda: self._get_reg_value(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                "IconsOnly",
                1
            ),
            58: lambda: self._get_reg_value(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer",
                "NoRecentDocsHistory",
                1
            ),
            59: lambda: self._get_reg_value(
                r"SOFTWARE\Policies\Microsoft\Windows\OneDrive",
                "DisableFileSyncNGSC",
                1
            ),

            # Page 6 - Privacy/Features (61-72)
            60: lambda: not self._get_reg_value(
                r"SOFTWARE\Policies\Microsoft\Windows\System",
                "AllowClipboardHistory",
                1
            ),
            61: lambda: self._get_reg_value(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\CloudContent",
                "DisableWindowsSpotlightFeatures",
                1
            ),
            62: lambda: self._get_reg_value(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\CloudContent",
                "DisableWindowsSpotlightWindowsWelcomeExperience",
                1
            ),
            63: lambda: not self._get_reg_value(
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Accessibility",
                "MagnifierEnabled",
                1
            ),

            # Service Toggles (64-103)
            64: lambda: self._get_service_state("SysMain") == 4,
            65: lambda: self._get_service_state("wuauserv") == 4,
            66: lambda: self._get_service_state("WinDefend") == 4,
            67: lambda: self._get_service_state("Spooler") == 4,
            68: lambda: self._get_service_state("RemoteRegistry") == 4,
            69: lambda: self._get_service_state("WerSvc") == 4,
            70: lambda: self._get_service_state("WSearch") == 4,
            71: lambda: self._get_service_state("DiagTrack") == 4,
            72: lambda: self._get_service_state("CDPUserSvc") == 4,
            73: lambda: self._get_service_state("bthserv") == 4,
            74: lambda: self._get_service_state("XblAuthManager") == 4,

            75: lambda: self._get_service_state("iphlpsvc") == 4,
            76: lambda: self._get_service_state("seclogon") == 4,
            77: lambda: self._get_service_state("PcaSvc") == 4,
            78: lambda: self._get_service_state("MapsBroker") == 4,
            79: lambda: self._get_service_state("Fax") == 4,
            80: lambda: self._get_service_state("HomeGroupProvider") == 4,
            81: lambda: self._get_service_state("HomeGroupListener") == 4,
            82: lambda: self._get_service_state("SCardSvr") == 4,
            83: lambda: self._get_service_state("wisvc") == 4,
            84: lambda: self._get_service_state("WMPNetworkSvc") == 4,
            85: lambda: self._get_service_state("AJRouter") == 4,
            86: lambda: self._get_service_state("DeviceAssociationService") == 4,

            87: lambda: self._get_service_state("DmEnrollmentSvc") == 4,
            88: lambda: self._get_service_state("RetailDemo") == 4,
            89: lambda: self._get_service_state("SensrSvc") == 4,
            90: lambda: self._get_service_state("lfsvc") == 4,
            91: lambda: self._get_service_state("TabletInputService") == 4,
            92: lambda: self._get_service_state("TabletInputService") == 4,
            93: lambda: self._get_service_state("FontCache") == 4,
            94: lambda: self._get_service_state("stisvc") == 4,
            95: lambda: self._get_service_state("icssvc") == 4,
            96: lambda: self._get_service_state("WorkFoldersSvc") == 4,
            97: lambda: self._get_service_state("SDRSVC") == 4,
            98: lambda: self._get_service_state("FrameServer") == 4,

            99: lambda: self._get_service_state("wcncsvc") == 4,
            100: lambda: self._get_service_state("Wecsvc") == 4,
            101: lambda: self._get_service_state("WpnService") == 4,
            102: lambda: self._get_service_state("W32Time") == 4,
            103: lambda: self._get_service_state("WlanSvc") == 4,
        

            # BIOS Optimizations (104-120)
            104: lambda: self._check_bios_setting("XMP"),
            105: lambda: not self._check_bios_setting("CStates"),
            106: lambda: self._check_bios_setting("HPET"),
            107: lambda: not self._check_bios_setting("SpeedStep"),
            108: lambda: self._check_bios_setting("TurboBoost"),
            109: lambda: not self._check_bios_setting("SecureBoot"),
            110: lambda: self._check_bios_setting("AHCI"),
            111: lambda: not self._check_bios_setting("Virtualization"),
            112: lambda: not self._check_bios_setting("FastBoot"),
            113: lambda: self._check_bios_setting("Above4G"),
            114: lambda: not self._check_bios_setting("CSM"),
            115: lambda: self._check_power_plan("8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"),  # High performance
            116: lambda: not self._check_bios_setting("TPM"),
            117: lambda: self._check_bios_setting("SVM"),
            118: lambda: not self._check_bios_setting("IOMMU"),
            119: lambda: self._check_bios_setting("PCIeGen") == "Max"
        }

        if index in toggle_conditions:
            return toggle_conditions[index]()
        return False

    # Required Helper Methods
    def _get_reg_value(self, key_path, value_name, default=None, value_type=winreg.REG_DWORD):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                value, reg_type = winreg.QueryValueEx(key, value_name)
                if reg_type != value_type:
                    return default
                return value
        except WindowsError:
            return default

    def _get_service_state(self, service_name):
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                f"SYSTEM\\CurrentControlSet\\Services\\{service_name}"
            )
            start_value, _ = winreg.QueryValueEx(key, "Start")
            winreg.CloseKey(key)
            return start_value
        except WindowsError:
            return 2  # Default to automatic start

    def _check_power_plan(self, guid):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Power\User\PowerSchemes") as key:
                value, _ = winreg.QueryValueEx(key, "ActivePowerScheme")
                return value == guid
        except WindowsError:
            return False


    def define_toggle_functions(self):
        # Connect each toggle only once
        for idx, toggle in enumerate(self.toggles):
            # Disconnect any existing connections to avoid duplicates
            try:
                toggle.toggled.disconnect()
            except TypeError:
                pass
            # Connect the toggle
            toggle.toggled.connect(lambda state, idx=idx: self.handle_toggle(state, idx))
    
    def handle_toggle(self, state, index):
        func_name = f"toggle_{index + 1}_action"
        if hasattr(self, func_name):
            getattr(self, func_name)(state)
        else:
            print(f"No handler for toggle {index + 1}")
    
    def modify_registry(self, key_path, value_name, value, value_type=winreg.REG_DWORD, msg=""):
        if not self.verify_windows_signature():
            QMessageBox.critical(self, "Security Error", "Operation not permitted")
            return False
        key = None
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            winreg.SetValueEx(key, value_name, 0, value_type, value)
            if msg and not self.silent_mode:
                self.show_message("Success", msg)
            return True
        except PermissionError:
            if not self.silent_mode:
                self.show_message("Error", "Permission denied. Please run as administrator.", True)
            return False
        except Exception as e:
            if not self.silent_mode:
                self.show_message("Error", f"Registry operation failed: {str(e)}", True)
            return False
        finally:
            if key:
                winreg.CloseKey(key)
    
    # ======================
    # Toggle Action Handlers
    # ======================
    
    def toggle_1_action(self, state):
        """Game Bar toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR", 
                "AppCaptureEnabled", 
                0, 
                winreg.REG_DWORD, 
                "Game Bar disabled"
            )
            if not success:
              self.reset_toggle(1, False)  # Reset to OFF if failed

        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR", 
                "AppCaptureEnabled", 
                1, 
                winreg.REG_DWORD, 
                "Game Bar enabled"
            )
            if not success:
              self.reset_toggle(1, True)  # Reset to OFF if failed
    
    def toggle_2_action(self, state):
        """Fullscreen Optimizations toggle handler"""
        if state:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", 
                "DisableFullscreenOptimization", 
                1, 
                winreg.REG_DWORD, 
                "Fullscreen optimizations disabled"
            )
            if not success:
              self.reset_toggle(2, False)  # Reset to OFF if failed
        else:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", 
                "DisableFullscreenOptimization", 
                0, 
                winreg.REG_DWORD, 
                "Fullscreen optimizations enabled"
            )
            if not success:
              self.reset_toggle(2, True)  # Reset to OFF if failed
    
    def toggle_3_action(self, state):
        """Power Plan toggle handler"""
        if state:
            # Try registry method first
            reg_success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\Power\User\PowerSchemes",
                "ActivePowerScheme",
                "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",  # High performance GUID
                winreg.REG_SZ,
                ""
            )
            
            # Fallback to powercfg command
            if not reg_success:
                try:
                    subprocess.run(
                        ['powercfg', '-setactive', '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c'],
                        check=True,
                        shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    QMessageBox.information(
                        self,
                        "Success",
                        "High performance power plan enabled"
                    )
                except subprocess.CalledProcessError as e:
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to enable high performance plan:\n{str(e)}\n\n"
                        "You may need to enable this power plan first."
                    )
                    if not reg_success:
                        self.reset_toggle(3, False)  # Reset to OFF if failed
        else:
            # Try registry method first
            reg_success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\Power\User\PowerSchemes",
                "ActivePowerScheme",
                "381b4222-f694-41f0-9685-ff5bb260df2e",  # Balanced GUID
                winreg.REG_SZ,
                ""
            )
            
            # Fallback to powercfg command
            if not reg_success:
                try:
                    subprocess.run(
                        ['powercfg', '-setactive', '381b4222-f694-41f0-9685-ff5bb260df2e'],
                        check=True,
                        shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    QMessageBox.information(
                        self,
                        "Success",
                        "Balanced power plan enabled"
                    )
                except subprocess.CalledProcessError as e:
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to enable balanced power plan:\n{str(e)}"
                    )
                    if not reg_success:
                        self.reset_toggle(3, True)  # Reset to OFF if failed
                            
    def toggle_4_action(self, state):
        """Animations toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", 
                "DisableStatusMessages", 
                1, 
                winreg.REG_DWORD, 
                "Animations disabled"
            )
            if not success:
              self.reset_toggle(4, False)  # Reset to OFF if failed
        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", 
                "DisableStatusMessages", 
                0, 
                winreg.REG_DWORD, 
                "Animations enabled"
            )
            if not success:
              self.reset_toggle(4, True)  # Reset to OFF if failed
    
    def toggle_5_action(self, state):
        """HPET toggle handler"""
        if state:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Services\W32Time\TimeProviders\NtpClient", 
                "Enabled", 
                1, 
                winreg.REG_DWORD, 
                "HPET enabled"
            )
            if not success:
              self.reset_toggle(5, False)  # Reset to OFF if failed
        else:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Services\W32Time\TimeProviders\NtpClient", 
                "Enabled", 
                0, 
                winreg.REG_DWORD, 
                "HPET disabled"
            )
            if not success:
              self.reset_toggle(5, True)  # Reset to OFF if failed
    
    def toggle_6_action(self, state):
        """Telemetry toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", 
                "AllowTelemetry", 
                0, 
                winreg.REG_DWORD, 
                "Telemetry disabled"
            )
            if not success:
              self.reset_toggle(6, False)  # Reset to OFF if failed
        else:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", 
                "AllowTelemetry", 
                1, 
                winreg.REG_DWORD, 
                "Telemetry enabled"
            )
            if not success:
              self.reset_toggle(6, True)  # Reset to OFF if failed
    
    def toggle_7_action(self, state):
        """Notifications toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows\CurrentVersion\PushNotifications", 
                "NoToastApplicationNotification", 
                1, 
                winreg.REG_DWORD, 
                "Notifications disabled"
            )
            if not success:
              self.reset_toggle(7, False)  # Reset to OFF if failed
        else:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows\CurrentVersion\PushNotifications", 
                "NoToastApplicationNotification", 
                0, 
                winreg.REG_DWORD, 
                "Notifications enabled"
            )
            if not success:
              self.reset_toggle(7, True)  # Reset to OFF if failed
    
    def toggle_8_action(self, state):
        """Cortana toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows\Windows Search", 
                "AllowCortana", 
                0, 
                winreg.REG_DWORD, 
                "Cortana disabled"
            )
            if not success:
              self.reset_toggle(8, False)  # Reset to OFF if failed
        else:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows\Windows Search", 
                "AllowCortana", 
                1, 
                winreg.REG_DWORD, 
                "Cortana enabled"
            )
            if not success:
              self.reset_toggle(8, True)  # Reset to OFF if failed
    
    def toggle_9_action(self, state):
        """Windows Defender toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows Defender", 
                "DisableAntiSpyware", 
                1, 
                winreg.REG_DWORD, 
                "Windows Defender disabled"
            )
            if not success:
              self.reset_toggle(9, False)  # Reset to OFF if failed
        else:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows Defender", 
                "DisableAntiSpyware", 
                0, 
                winreg.REG_DWORD, 
                "Windows Defender enabled"
            )
            if not success:
              self.reset_toggle(9, True)  # Reset to OFF if failed
 
    def toggle_10_action(self, state):
        """Optimize NTFS toggle handler"""
        if state:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\FileSystem", 
                "NtfsDisableLastAccessUpdate", 
                1, 
                winreg.REG_DWORD, 
                "NTFS last access updates disabled"
            )
            if not success:
                self.reset_toggle(10, False)
        else:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\FileSystem", 
                "NtfsDisableLastAccessUpdate", 
                0, 
                winreg.REG_DWORD, 
                "NTFS last access updates enabled"
            )
            if not success:
                self.reset_toggle(10, True)

    def toggle_11_action(self, state):
        """Disable Superfetch toggle handler"""
        if state:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters", 
                "EnableSuperfetch", 
                0, 
                winreg.REG_DWORD, 
                "Superfetch disabled"
            )
            if not success:
                self.reset_toggle(11, False)
        else:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters", 
                "EnableSuperfetch", 
                3, 
                winreg.REG_DWORD, 
                "Superfetch enabled"
            )
            if not success:
                self.reset_toggle(11, True)

    def toggle_12_action(self, state):
        """CPU Priority Boost toggle handler"""
        if state:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\PriorityControl", 
                "Win32PrioritySeparation", 
                38, 
                winreg.REG_DWORD, 
                "CPU priority boost enabled"
            )
            if not success:
                self.reset_toggle(12, False)
        else:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\PriorityControl", 
                "Win32PrioritySeparation", 
                2, 
                winreg.REG_DWORD, 
                "CPU priority boost disabled"
            )
            if not success:
                self.reset_toggle(12, True)

    def toggle_13_action(self, state):
        """Disable Diagnostic Policy Service (DPS)"""
        self.set_service_state("DPS", 4 if state else 2, "Diagnostic Policy Service")
        

    def toggle_14_action(self, state):
        """Disable Error Reporting toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\Windows Error Reporting", 
                "Disabled", 
                1, 
                winreg.REG_DWORD, 
                "Error reporting disabled"
            )
            if not success:
                self.reset_toggle(14, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\Windows Error Reporting", 
                "Disabled", 
                0, 
                winreg.REG_DWORD, 
                "Error reporting enabled"
            )
            if not success:
                self.reset_toggle(14, True)

    def toggle_15_action(self, state):
        """Network Throttle Off toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", 
                "NetworkThrottlingIndex", 
                0xFFFFFFFF, 
                winreg.REG_DWORD, 
                "Network throttling disabled"
            )
            if not success:
                self.reset_toggle(15, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", 
                "NetworkThrottlingIndex", 
                0xA, 
                winreg.REG_DWORD, 
                "Network throttling enabled"
            )
            if not success:
                self.reset_toggle(5, True)
    def toggle_16_action(self, state):
        """Disable Windows Tips toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager", 
                "SubscribedContent-338393Enabled", 
                0, 
                winreg.REG_DWORD, 
                "Windows tips disabled"
            )
            if not success:
                self.reset_toggle(16, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager", 
                "SubscribedContent-338393Enabled", 
                1, 
                winreg.REG_DWORD, 
                "Windows tips enabled"
            )
            if not success:
                self.reset_toggle(16, True)

    def toggle_17_action(self, state):
        """Disable Background Apps toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications", 
                "GlobalUserDisabled", 
                1, 
                winreg.REG_DWORD, 
                "Background apps disabled"
            )
            if not success:
                self.reset_toggle(17, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications", 
                "GlobalUserDisabled", 
                0, 
                winreg.REG_DWORD, 
                "Background apps enabled"
            )
            if not success:
                self.reset_toggle(17, True)

    def toggle_18_action(self, state):
        """Disable Aero Peek toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\DWM", 
                "EnableAeroPeek", 
                0, 
                winreg.REG_DWORD, 
                "Aero Peek disabled"
            )
            if not success:
                self.reset_toggle(18, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\DWM", 
                "EnableAeroPeek", 
                1, 
                winreg.REG_DWORD, 
                "Aero Peek enabled"
            )
            if not success:
                self.reset_toggle(18, True)

    def toggle_19_action(self, state):
        """Disable Xbox DVR toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR", 
                "AppCaptureEnabled", 
                0, 
                winreg.REG_DWORD, 
                "Xbox DVR disabled"
            )
            if not success:
                self.reset_toggle(19, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR", 
                "AppCaptureEnabled", 
                1, 
                winreg.REG_DWORD, 
                "Xbox DVR enabled"
            )
            if not success:
                self.reset_toggle(19, True)

    def toggle_20_action(self, state):
        """Timer Resolution Boost toggle handler"""
        if state:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\Session Manager\kernel", 
                "GlobalTimerResolutionRequests", 
                1, 
                winreg.REG_DWORD, 
                "Timer resolution boost enabled"
            )
            if not success:
                self.reset_toggle(20, False)
        else:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\Session Manager\kernel", 
                "GlobalTimerResolutionRequests", 
                0, 
                winreg.REG_DWORD, 
                "Timer resolution boost disabled"
            )
            if not success:
                self.reset_toggle(20, True)

    def toggle_21_action(self, state):
        """Disable Firewall toggle handler"""
        if state:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\StandardProfile", 
                "EnableFirewall", 
                0, 
                winreg.REG_DWORD, 
                "Firewall disabled"
            )
            if not success:
                self.reset_toggle(21, False)
        else:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\StandardProfile", 
                "EnableFirewall", 
                1, 
                winreg.REG_DWORD, 
                "Firewall enabled"
            )
            if not success:
                self.reset_toggle(11, True)

    def toggle_22_action(self, state):
        """Disable Updates toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU", 
                "NoAutoUpdate", 
                1, 
                winreg.REG_DWORD, 
                "Automatic updates disabled"
            )
            if not success:
                self.reset_toggle(22, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU", 
                "NoAutoUpdate", 
                0, 
                winreg.REG_DWORD, 
                "Automatic updates enabled"
            )
            if not success:
                self.reset_toggle(22, True)

    def toggle_23_action(self, state):
        """Disable Shadows toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", 
                "ListviewShadow", 
                0, 
                winreg.REG_DWORD, 
                "Shadows disabled"
            )
            if not success:
                self.reset_toggle(23, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", 
                "ListviewShadow", 
                1, 
                winreg.REG_DWORD, 
                "Shadows enabled"
            )
            if not success:
                self.reset_toggle(23, True)

    def toggle_24_action(self, state):
        """Disable Transparency toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize", 
                "EnableTransparency", 
                0, 
                winreg.REG_DWORD, 
                "Transparency effects disabled"
            )
            if not success:
                self.reset_toggle(24, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize", 
                "EnableTransparency", 
                1, 
                winreg.REG_DWORD, 
                "Transparency effects enabled"
            )
            if not success:
                self.reset_toggle(24, True)

    def toggle_25_action(self, state):
        """Disable Widgets toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Dsh", 
                "AllowNewsAndInterests", 
                0, 
                winreg.REG_DWORD, 
                "Widgets disabled"
            )
            if not success:
                self.reset_toggle(25, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Dsh", 
                "AllowNewsAndInterests", 
                1, 
                winreg.REG_DWORD, 
                "Widgets enabled"
            )
            if not success:
                self.reset_toggle(25, True)

    def toggle_26_action(self, state):
        """Disable V-Sync toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\DWM", 
                "UseD3D9Ex", 
                0, 
                winreg.REG_DWORD, 
                "V-Sync disabled"
            )
            if not success:
                self.reset_toggle(26, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\DWM", 
                "UseD3D9Ex", 
                1, 
                winreg.REG_DWORD, 
                "V-Sync enabled"
            )
            if not success:
                self.reset_toggle(16, True)

    def toggle_27_action(self, state):
        """Disable Game Mode toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\GameBar", 
                "AllowAutoGameMode", 
                0, 
                winreg.REG_DWORD, 
                "Game Mode disabled"
            )
            if not success:
                self.reset_toggle(27, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\GameBar", 
                "AllowAutoGameMode", 
                1, 
                winreg.REG_DWORD, 
                "Game Mode enabled"
            )
            if not success:
                self.reset_toggle(17, True)

    def toggle_28_action(self, state):
        """Disable Spectre/Meltdown toggle handler"""
        if state:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management", 
                "FeatureSettingsOverride", 
                3, 
                winreg.REG_DWORD, 
                "Spectre/Meltdown mitigations disabled"
            )
            if not success:
                self.reset_toggle(28, False)
        else:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management", 
                "FeatureSettingsOverride", 
                0, 
                winreg.REG_DWORD, 
                "Spectre/Meltdown mitigations enabled"
            )
            if not success:
                self.reset_toggle(18, True)

    def toggle_29_action(self, state):
        """Enable ULPS toggle handler"""
        if state:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000", 
                "EnableUlps", 
                0, 
                winreg.REG_DWORD, 
                "ULPS enabled"
            )
            if not success:
                self.reset_toggle(29, False)
        else:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000", 
                "EnableUlps", 
                1, 
                winreg.REG_DWORD, 
                "ULPS disabled"
            )
            if not success:
                self.reset_toggle(29, True)

    def toggle_30_action(self, state):
        """Disable HPET (Alternative) toggle handler"""
        if state:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Services\W32Time\TimeProviders\NtpServer", 
                "Enabled", 
                0, 
                winreg.REG_DWORD, 
                "Alternative HPET disabled"
            )
            if not success:
                self.reset_toggle(30, False)
        else:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Services\W32Time\TimeProviders\NtpServer", 
                "Enabled", 
                1, 
                winreg.REG_DWORD, 
                "Alternative HPET enabled"
            )
            if not success:
                self.reset_toggle(30, True)

    def toggle_31_action(self, state):
        """Disable Core Parking toggle handler"""
        if state:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\Power\PowerSettings\54533251-82be-4824-96c1-47b60b740d00\0cc5b647-c1df-4637-891a-dec35c318583", 
                "ValueMax", 
                0, 
                winreg.REG_DWORD, 
                "Core parking disabled"
            )
            if not success:
                self.reset_toggle(31, False)
        else:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\Power\PowerSettings\54533251-82be-4824-96c1-47b60b740d00\0cc5b647-c1df-4637-891a-dec35c318583", 
                "ValueMax", 
                100, 
                winreg.REG_DWORD, 
                "Core parking enabled"
            )
            if not success:
                self.reset_toggle(31, True)

    def toggle_32_action(self, state):
        """Enable MSI Mode toggle handler"""
        if state:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Services\msiserver", 
                "Start", 
                4, 
                winreg.REG_DWORD, 
                "MSI mode enabled"
            )
            if not success:
                self.reset_toggle(32, False)
        else:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Services\msiserver", 
                "Start", 
                3, 
                winreg.REG_DWORD, 
                "MSI mode disabled"
            )
            if not success:
                self.reset_toggle(32, True)

    def toggle_33_action(self, state):
        """Disable Memory Compression toggle handler"""
        if state:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management", 
                "DisableMemoryCompression", 
                1, 
                winreg.REG_DWORD, 
                "Memory compression disabled"
            )
            if not success:
                self.reset_toggle(33, False)
        else:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management", 
                "DisableMemoryCompression", 
                0, 
                winreg.REG_DWORD, 
                "Memory compression enabled"
            )
            if not success:
                self.reset_toggle(33, True)

    def toggle_34_action(self, state):
        """Disable SysMain toggle handler"""
        if state:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Services\SysMain", 
                "Start", 
                4, 
                winreg.REG_DWORD, 
                "SysMain disabled"
            )
            if not success:
                self.reset_toggle(34, False)
        else:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Services\SysMain", 
                "Start", 
                2, 
                winreg.REG_DWORD, 
                "SysMain enabled"
            )
            if not success:
                self.reset_toggle(34, True)

    def toggle_35_action(self, state):
        """Disable Write Combining toggle handler"""
        if state:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", 
                "WriteCombiningSupported", 
                0, 
                winreg.REG_DWORD, 
                "Write combining disabled"
            )
            if not success:
                self.reset_toggle(35, False)
        else:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", 
                "WriteCombiningSupported", 
                1, 
                winreg.REG_DWORD, 
                "Write combining enabled"
            )
            if not success:
                self.reset_toggle(35, True)

    def toggle_36_action(self, state):
        """Disable DWM toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\DWM", 
                "Composition", 
                0, 
                winreg.REG_DWORD, 
                "DWM disabled"
            )
            if not success:
                self.reset_toggle(36, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\DWM", 
                "Composition", 
                1, 
                winreg.REG_DWORD, 
                "DWM enabled"
            )
            if not success:
                self.reset_toggle(36, True)

    def toggle_37_action(self, state):
        """Disable WSearch toggle handler"""
        if state:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Services\WSearch", 
                "Start", 
                4, 
                winreg.REG_DWORD, 
                "Windows Search disabled"
            )
            if not success:
                self.reset_toggle(37, False)
        else:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Services\WSearch", 
                "Start", 
                2, 
                winreg.REG_DWORD, 
                "Windows Search enabled"
            )
            if not success:
                self.reset_toggle(37, True)

    def toggle_38_action(self, state):
        """Disable Print Spooler toggle handler"""
        if state:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Services\Spooler", 
                "Start", 
                4, 
                winreg.REG_DWORD, 
                "Print spooler disabled"
            )
            if not success:
                self.reset_toggle(38, False)
        else:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Services\Spooler", 
                "Start", 
                2, 
                winreg.REG_DWORD, 
                "Print spooler enabled"
            )
            if not success:
                self.reset_toggle(28, True)

    def toggle_39_action(self, state):
        """Disable Windows Ink toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\PenWorkspace", 
                "PenWorkspaceAppSuggestionsEnabled", 
                0, 
                winreg.REG_DWORD, 
                "Windows Ink disabled"
            )
            if not success:
                self.reset_toggle(39, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\PenWorkspace", 
                "PenWorkspaceAppSuggestionsEnabled", 
                1, 
                winreg.REG_DWORD, 
                "Windows Ink enabled"
            )
            if not success:
                self.reset_toggle(29, True)

    def toggle_40_action(self, state):
        """Disable Touch Keyboard toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\TabletTip\1.7", 
                "TipbandDesiredVisibility", 
                0, 
                winreg.REG_DWORD, 
                "Touch keyboard disabled"
            )
            if not success:
                self.reset_toggle(40, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\TabletTip\1.7", 
                "TipbandDesiredVisibility", 
                1, 
                winreg.REG_DWORD, 
                "Touch keyboard enabled"
            )
            if not success:
                self.reset_toggle(40, True)

    def toggle_41_action(self, state):
        """Disable Biometrics toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Biometrics", 
                "Enabled", 
                0, 
                winreg.REG_DWORD, 
                "Biometrics disabled"
            )
            if not success:
                self.reset_toggle(41, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Biometrics", 
                "Enabled", 
                1, 
                winreg.REG_DWORD, 
                "Biometrics enabled"
            )
            if not success:
                self.reset_toggle(41, True)

    def toggle_42_action(self, state):
        """Disable Location toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows\LocationAndSensors", 
                "DisableLocation", 
                1, 
                winreg.REG_DWORD, 
                "Location services disabled"
            )
            if not success:
                self.reset_toggle(42, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows\LocationAndSensors", 
                "DisableLocation", 
                0, 
                winreg.REG_DWORD, 
                "Location services enabled"
            )
            if not success:
                self.reset_toggle(42, True)

    def toggle_43_action(self, state):
        """Disable Camera toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows\AppPrivacy", 
                "LetAppsAccessCamera", 
                2, 
                winreg.REG_DWORD, 
                "Camera access disabled"
            )
            if not success:
                self.reset_toggle(43, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows\AppPrivacy", 
                "LetAppsAccessCamera", 
                0, 
                winreg.REG_DWORD, 
                "Camera access enabled"
            )
            if not success:
                self.reset_toggle(43, True)

    def toggle_44_action(self, state):
        """Disable Microphone toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows\AppPrivacy", 
                "LetAppsAccessMicrophone", 
                2, 
                winreg.REG_DWORD, 
                "Microphone access disabled"
            )
            if not success:
                self.reset_toggle(44, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows\AppPrivacy", 
                "LetAppsAccessMicrophone", 
                0, 
                winreg.REG_DWORD, 
                "Microphone access enabled"
            )
            if not success:
                self.reset_toggle(44, True)

    def toggle_45_action(self, state):
        """Disable Bluetooth toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows\Bluetooth", 
                "AllowDiscoverableMode", 
                0, 
                winreg.REG_DWORD, 
                "Bluetooth disabled"
            )
            if not success:
                self.reset_toggle(45, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows\Bluetooth", 
                "AllowDiscoverableMode", 
                1, 
                winreg.REG_DWORD, 
                "Bluetooth enabled"
            )
            if not success:
                self.reset_toggle(45, True)

    def toggle_46_action(self, state):
        """Disable WiFi Sense toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\WcmSvc\wifinetworkmanager\config", 
                "AutoConnectAllowedOEM", 
                0, 
                winreg.REG_DWORD, 
                "WiFi Sense disabled"
            )
            if not success:
                self.reset_toggle(46, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\WcmSvc\wifinetworkmanager\config", 
                "AutoConnectAllowedOEM", 
                1, 
                winreg.REG_DWORD, 
                "WiFi Sense enabled"
            )
            if not success:
                self.reset_toggle(46, True)

    def toggle_47_action(self, state):
        """Disable Hotspot toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\WcmSvc\Tethering", 
                "TetheringEnabled", 
                0, 
                winreg.REG_DWORD, 
                "Hotspot disabled"
            )
            if not success:
                self.reset_toggle(47, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\WcmSvc\Tethering", 
                "TetheringEnabled", 
                1, 
                winreg.REG_DWORD, 
                "Hotspot enabled"
            )
            if not success:
                self.reset_toggle(47, True)

    def toggle_48_action(self, state):
        """Disable Airplane Mode toggle handler"""
        if state:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\RadioManagement\SystemRadioState", 
                "SystemRadioState", 
                1, 
                winreg.REG_DWORD, 
                "Airplane mode disabled"
            )
            if not success:
                self.reset_toggle(48, False)
        else:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\RadioManagement\SystemRadioState", 
                "SystemRadioState", 
                0, 
                winreg.REG_DWORD, 
                "Airplane mode enabled"
            )
            if not success:
                self.reset_toggle(48, True)

    def toggle_49_action(self, state):
        """Disable NFC toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows\Connect", 
                "AllowNFC", 
                0, 
                winreg.REG_DWORD, 
                "NFC disabled"
            )
            if not success:
                self.reset_toggle(49, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows\Connect", 
                "AllowNFC", 
                1, 
                winreg.REG_DWORD, 
                "NFC enabled"
            )
            if not success:
                self.reset_toggle(49, True)

    def toggle_50_action(self, state):
        """Disable AutoPlay toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer", 
                "NoDriveTypeAutoRun", 
                255, 
                winreg.REG_DWORD, 
                "AutoPlay disabled"
            )
            if not success:
                self.reset_toggle(50, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer", 
                "NoDriveTypeAutoRun", 
                145, 
                winreg.REG_DWORD, 
                "AutoPlay enabled"
            )
            if not success:
                self.reset_toggle(50, True)

    def toggle_51_action(self, state):
        """Disable AutoUpdate toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU", 
                "NoAutoUpdate", 
                1, 
                winreg.REG_DWORD, 
                "AutoUpdate disabled"
            )
            if not success:
                self.reset_toggle(51, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU", 
                "NoAutoUpdate", 
                0, 
                winreg.REG_DWORD, 
                "AutoUpdate enabled"
            )
            if not success:
                self.reset_toggle(51, True)

    def toggle_52_action(self, state):
        """Disable SmartScreen toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer", 
                "SmartScreenEnabled", 
                "Off", 
                winreg.REG_SZ, 
                "SmartScreen disabled"
            )
            if not success:
                self.reset_toggle(52, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer", 
                "SmartScreenEnabled", 
                "Warn", 
                winreg.REG_SZ, 
                "SmartScreen enabled"
            )
            if not success:
                self.reset_toggle(52, True)

    def toggle_53_action(self, state):
        """Disable UAC toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", 
                "EnableLUA", 
                0, 
                winreg.REG_DWORD, 
                "UAC disabled"
            )
            if not success:
                self.reset_toggle(53, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", 
                "EnableLUA", 
                1, 
                winreg.REG_DWORD, 
                "UAC enabled"
            )
            if not success:
                self.reset_toggle(53, True)

    def toggle_54_action(self, state):
        """Disable Hibernation toggle handler"""
        if state:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\Power", 
                "HibernateEnabled", 
                0, 
                winreg.REG_DWORD, 
                "Hibernation disabled"
            )
            if not success:
                self.reset_toggle(54, False)
        else:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\Power", 
                "HibernateEnabled", 
                1, 
                winreg.REG_DWORD, 
                "Hibernation enabled"
            )
            if not success:
                self.reset_toggle(54, True)

    def toggle_55_action(self, state):
        """Disable Sleep toggle handler"""
        if state:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\Power", 
                "ACSettingIndex", 
                0, 
                winreg.REG_DWORD, 
                "Sleep disabled"
            )
            if not success:
                self.reset_toggle(55, False)
        else:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\Power", 
                "ACSettingIndex", 
                1, 
                winreg.REG_DWORD, 
                "Sleep enabled"
            )
            if not success:
                self.reset_toggle(55, True)

    def toggle_56_action(self, state):
        """Disable Fast Startup toggle handler"""
        if state:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Power", 
                "HiberbootEnabled", 
                0, 
                winreg.REG_DWORD, 
                "Fast startup disabled"
            )
            if not success:
                self.reset_toggle(56, False)
        else:
            success = self.modify_registry(
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Power", 
                "HiberbootEnabled", 
                1, 
                winreg.REG_DWORD, 
                "Fast startup enabled"
            )
            if not success:
                self.reset_toggle(56, True)

    def toggle_57_action(self, state):
        """Disable Remote Desktop Services"""
        self.set_service_state("TermService", 4 if state else 2, "Remote Desktop Services")

    def toggle_58_action(self, state):
        """Disable Thumbnails toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", 
                "IconsOnly", 
                1, 
                winreg.REG_DWORD, 
                "Thumbnails disabled"
            )
            if not success:
                self.reset_toggle(58, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", 
                "IconsOnly", 
                0, 
                winreg.REG_DWORD, 
                "Thumbnails enabled"
            )
            if not success:
                self.reset_toggle(58, True)

    def toggle_59_action(self, state):
        """Disable Recent Files toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer", 
                "NoRecentDocsHistory", 
                1, 
                winreg.REG_DWORD, 
                "Recent files history disabled"
            )
            if not success:
                self.reset_toggle(59, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer", 
                "NoRecentDocsHistory", 
                0, 
                winreg.REG_DWORD, 
                "Recent files history enabled"
            )
            if not success:
                self.reset_toggle(59, True)

    def toggle_60_action(self, state):
        """Disable OneDrive toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows\OneDrive", 
                "DisableFileSyncNGSC", 
                1, 
                winreg.REG_DWORD, 
                "OneDrive disabled"
            )
            if not success:
                self.reset_toggle(60, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows\OneDrive", 
                "DisableFileSyncNGSC", 
                0, 
                winreg.REG_DWORD, 
                "OneDrive enabled"
            )
            if not success:
                self.reset_toggle(60, True)

    def toggle_61_action(self, state):
        """Disable Clipboard History toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows\System", 
                "AllowClipboardHistory", 
                0, 
                winreg.REG_DWORD, 
                "Clipboard history disabled"
            )
            if not success:
                self.reset_toggle(61, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Policies\Microsoft\Windows\System", 
                "AllowClipboardHistory", 
                1, 
                winreg.REG_DWORD, 
                "Clipboard history enabled"
            )
            if not success:
                self.reset_toggle(61, True)

    def toggle_62_action(self, state):
        """Disable Focus Assist toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\CloudContent", 
                "DisableWindowsSpotlightFeatures", 
                1, 
                winreg.REG_DWORD, 
                "Focus Assist disabled"
            )
            if not success:
                self.reset_toggle(62, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\CloudContent", 
                "DisableWindowsSpotlightFeatures", 
                0, 
                winreg.REG_DWORD, 
                "Focus Assist enabled"
            )
            if not success:
                self.reset_toggle(52, True)

    def toggle_63_action(self, state):
        """Disable Night Light toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\CloudContent", 
                "DisableWindowsSpotlightWindowsWelcomeExperience", 
                1, 
                winreg.REG_DWORD, 
                "Night Light disabled"
            )
            if not success:
                self.reset_toggle(63, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\CloudContent", 
                "DisableWindowsSpotlightWindowsWelcomeExperience", 
                0, 
                winreg.REG_DWORD, 
                "Night Light enabled"
            )
            if not success:
                self.reset_toggle(63, True)

    def toggle_64_action(self, state):
        """Disable magnify toggle handler"""
        if state:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Accessibility", 
                "MagnifierEnabled", 
                1, 
                winreg.REG_DWORD, 
                "Magnifier disabled"
            )
            if not success:
                self.reset_toggle(64, False)
        else:
            success = self.modify_registry(
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Accessibility", 
                "DisableWindowsSpotlightWindowsWelcomeExperience", 
                0, 
                winreg.REG_DWORD, 
                "Magnifier Enabled"
            )
            if not success:
                self.reset_toggle(64, True) 

    # Page 3 Service Toggles
    def toggle_65_action(self, state):
        """SysMain (Superfetch) toggle handler"""
        self.set_service_state("SysMain", 4 if state else 2, "SysMain")

    def toggle_66_action(self, state):
        """Windows Update toggle handler"""
        self.set_service_state("wuauserv", 4 if state else 2, "Windows Update")

    def toggle_67_action(self, state):
        """Windows Defender toggle handler"""
        self.set_service_state("WinDefend", 4 if state else 2, "Windows Defender")

    def toggle_68_action(self, state):
        """Print Spooler toggle handler"""
        self.set_service_state("Spooler", 4 if state else 2, "Print Spooler")

    def toggle_69_action(self, state):
        """Remote Registry toggle handler"""
        self.set_service_state("RemoteRegistry", 4 if state else 2, "Remote Registry")

    def toggle_70_action(self, state):
        """Error Reporting toggle handler"""
        self.set_service_state("WerSvc", 4 if state else 2, "Windows Error Reporting")

    def toggle_71_action(self, state):
        """Windows Search toggle handler"""
        self.set_service_state("WSearch", 4 if state else 2, "Windows Search")

    def toggle_72_action(self, state):
        """Diagnostics Tracking toggle handler"""
        self.set_service_state("DiagTrack", 4 if state else 2, "Diagnostics Tracking")

    # Page 4 Service Toggles
    def toggle_73_action(self, state):
        """Connected Devices toggle handler"""
        self.set_service_state("CDPUserSvc", 4 if state else 2, "Connected Devices")

    def toggle_74_action(self, state):
        """Bluetooth Support toggle handler"""
        self.set_service_state("bthserv", 4 if state else 2, "Bluetooth Support")

    def toggle_75_action(self, state):
        """Xbox Live Services toggle handler"""
        self.set_service_state("XblAuthManager", 4 if state else 2, "Xbox Live Auth Manager")

    def toggle_76_action(self, state):
        """IP Helper toggle handler"""
        self.set_service_state("iphlpsvc", 4 if state else 2, "IP Helper")

    def toggle_77_action(self, state):
        """Secondary Logon toggle handler"""
        self.set_service_state("seclogon", 4 if state else 2, "Secondary Logon")

    def toggle_78_action(self, state):
        """Program Compatibility toggle handler"""
        self.set_service_state("PcaSvc", 4 if state else 2, "Program Compatibility")

    def toggle_79_action(self, state):
        """Downloaded Maps toggle handler"""
        self.set_service_state("MapsBroker", 4 if state else 2, "Downloaded Maps Manager")

    def toggle_80_action(self, state):
        """Fax Service toggle handler"""
        self.set_service_state("Fax", 4 if state else 2, "Fax Service")

    def toggle_81_action(self, state):
        self.set_service_state("HomeGroupProvider", 4 if state else 2, "HomeGroup Provider")

    def toggle_82_action(self, state):
        self.set_service_state("HomeGroupListener", 4 if state else 2, "HomeGroup Listener")

    def toggle_83_action(self, state):
        self.set_service_state("SCardSvr", 4 if state else 2, "Smart Card")

    def toggle_84_action(self, state):
        self.set_service_state("wisvc", 4 if state else 2, "Windows Insider Service")

    def toggle_85_action(self, state):
        self.set_service_state("WMPNetworkSvc", 4 if state else 2, "Windows Media Scheduler")

    def toggle_86_action(self, state):
        self.set_service_state("AJRouter", 4 if state else 2, "AllJoyn Router")

    def toggle_87_action(self, state):
        self.set_service_state("DeviceAssociationService", 4 if state else 2, "Device Association")

    def toggle_88_action(self, state):
        self.set_service_state("DmEnrollmentSvc", 4 if state else 2, "Device Management")

    # Page 11 Service Handlers
    def toggle_89_action(self, state):
        self.set_service_state("RetailDemo", 4 if state else 2, "Retail Demo")

    def toggle_90_action(self, state):
        self.set_service_state("SensrSvc", 4 if state else 2, "Sensor Services")

    def toggle_91_action(self, state):
        self.set_service_state("lfsvc", 4 if state else 2, "Geolocation Service")

    def toggle_92_action(self, state):
        self.set_service_state("TabletInputService", 4 if state else 2, "Touch Keyboard")

    def toggle_93_action(self, state):
        self.set_service_state("TabletInputService", 4 if state else 2, "Tablet Input")

    def toggle_94_action(self, state):
        self.set_service_state("FontCache", 4 if state else 2, "Windows Font Cache")

    def toggle_95_action(self, state):
        self.set_service_state("stisvc", 4 if state else 2, "Windows Image Acquisition")

    def toggle_96_action(self, state):
        self.set_service_state("icssvc", 4 if state else 2, "Windows Mobile Hotspot")

    # Page 12 Service Handlers
    def toggle_97_action(self, state):
        self.set_service_state("WorkFoldersSvc", 4 if state else 2, "Work Folders")

    def toggle_98_action(self, state):
        self.set_service_state("SDRSVC", 4 if state else 2, "Windows Backup")

    def toggle_99_action(self, state):
        self.set_service_state("FrameServer", 4 if state else 2, "Windows Camera Frame Server")

    def toggle_100_action(self, state):
        self.set_service_state("wcncsvc", 4 if state else 2, "Windows Connect Now")

    def toggle_101_action(self, state):
        self.set_service_state("Wecsvc", 4 if state else 2, "Windows Event Collector")

    def toggle_102_action(self, state):
        self.set_service_state("WpnService", 4 if state else 2, "Windows Push Notifications")

    def toggle_103_action(self, state):
        self.set_service_state("W32Time", 4 if state else 2, "Windows Time")

    def toggle_104_action(self, state):
        self.set_service_state("WlanSvc", 4 if state else 2, "WLAN AutoConfig")
    
        # BIOS Optimization Toggles (Buttons 105-120)
    def toggle_105_action(self, state):
        """XMP Profile toggle handler"""
        try:
            if state:
                # Enable XMP
                result = subprocess.run(
                    'wmic memorychip set ConfiguredClockSpeed=3200',
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    QMessageBox.information(self, "Success", "XMP Profile enabled. Restart required.")
                else:
                    raise Exception(result.stderr.decode().strip())
            else:
                # Disable XMP
                result = subprocess.run(
                    'wmic memorychip set ConfiguredClockSpeed=2133',
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    QMessageBox.information(self, "Success", "XMP Profile disabled. Restart required.")
                else:
                    raise Exception(result.stderr.decode().strip())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to configure XMP: {str(e)}")
            self.reset_toggle(105, not state)

    def toggle_106_action(self, state):
        """C-States toggle handler"""
        try:
            value = "0" if state else "1"  # 0=Disable, 1=Enable
            result = subprocess.run(
                f'powercfg /setacvalueindex scheme_current sub_processor PROCTHROTTLEMAX {value}',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                status = "disabled" if state else "enabled"
                QMessageBox.information(self, "Success", f"C-States {status}. Restart required.")
            else:
                raise Exception(result.stderr.decode().strip())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to configure C-States: {str(e)}")
            self.reset_toggle(106, not state)

    def toggle_107_action(self, state):
        """HPET toggle handler"""
        try:
            if state:
                # Enable HPET
                subprocess.run(
                    'bcdedit /set useplatformclock true',
                    shell=True,
                    check=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                QMessageBox.information(self, "Success", "HPET enabled. Restart required.")
            else:
                # Disable HPET
                subprocess.run(
                    'bcdedit /set useplatformclock false',
                    shell=True,
                    check=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                QMessageBox.information(self, "Success", "HPET disabled. Restart required.")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Error", f"Failed to configure HPET: {str(e)}")
            self.reset_toggle(107, not state)

    def toggle_108_action(self, state):
        """SpeedStep toggle handler"""
        try:
            value = "0" if state else "1"  # 0=Disable, 1=Enable
            result = subprocess.run(
                f'powercfg /setacvalueindex scheme_current sub_processor PPMENABLE {value}',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                status = "disabled" if state else "enabled"
                QMessageBox.information(self, "Success", f"SpeedStep {status}. Restart required.")
            else:
                raise Exception(result.stderr.decode().strip())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to configure SpeedStep: {str(e)}")
            self.reset_toggle(108, not state)

    def toggle_109_action(self, state):
        """Turbo Boost toggle handler"""
        try:
            value = "1" if state else "0"  # 1=Enable, 0=Disable
            result = subprocess.run(
                f'powercfg /setacvalueindex scheme_current sub_processor PERFBOOSTMODE {value}',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                status = "enabled" if state else "disabled"
                QMessageBox.information(self, "Success", f"Turbo Boost {status}. Restart required.")
            else:
                raise Exception(result.stderr.decode().strip())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to configure Turbo Boost: {str(e)}")
            self.reset_toggle(109, not state)

    def toggle_110_action(self, state):
        """Secure Boot toggle handler"""
        try:
            if state:
                # Disable Secure Boot
                result = subprocess.run(
                    'bcdedit /set {current} testsigning on',
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    QMessageBox.information(self, "Success", "Secure Boot disabled. BIOS change and restart required.")
                else:
                    raise Exception(result.stderr.decode().strip())
            else:
                # Enable Secure Boot
                result = subprocess.run(
                    'bcdedit /set {current} testsigning off',
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    QMessageBox.information(self, "Success", "Secure Boot enabled. BIOS change and restart required.")
                else:
                    raise Exception(result.stderr.decode().strip())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to configure Secure Boot: {str(e)}")
            self.reset_toggle(110, not state)

    def toggle_111_action(self, state):
        """AHCI Mode toggle handler"""
        try:
            if state:
                # Enable AHCI in registry
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\storahci")
                winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, 0)
                winreg.CloseKey(key)
                
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\iaStorV")
                winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, 0)
                winreg.CloseKey(key)
                
                QMessageBox.information(self, "Success", "AHCI mode enabled. BIOS change and restart required.")
            else:
                # Revert to default
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\storahci")
                winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, 3)
                winreg.CloseKey(key)
                
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\iaStorV")
                winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, 3)
                winreg.CloseKey(key)
                
                QMessageBox.information(self, "Success", "AHCI mode disabled. BIOS change and restart required.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to configure AHCI mode: {str(e)}")
            self.reset_toggle(111, not state)

    def toggle_112_action(self, state):
        """Virtualization toggle handler"""
        try:
            if state:
                # Disable Virtualization
                result = subprocess.run(
                    'bcdedit /set hypervisorlaunchtype off',
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    QMessageBox.information(self, "Success", "Virtualization disabled. BIOS change and restart required.")
                else:
                    raise Exception(result.stderr.decode().strip())
            else:
                # Enable Virtualization
                result = subprocess.run(
                    'bcdedit /set hypervisorlaunchtype auto',
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    QMessageBox.information(self, "Success", "Virtualization enabled. BIOS change and restart required.")
                else:
                    raise Exception(result.stderr.decode().strip())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to configure Virtualization: {str(e)}")
            self.reset_toggle(112, not state)

    # Page 18 BIOS Toggles (Buttons 113-120)
    def toggle_113_action(self, state):
        """Fast Boot toggle handler"""
        try:
            if state:
                # Disable Fast Boot
                result = subprocess.run(
                    'powercfg /h off',
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    QMessageBox.information(self, "Success", "Fast Boot disabled. Restart required.")
                else:
                    raise Exception(result.stderr.decode().strip())
            else:
                # Enable Fast Boot
                result = subprocess.run(
                    'powercfg /h on',
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    QMessageBox.information(self, "Success", "Fast Boot enabled. Restart required.")
                else:
                    raise Exception(result.stderr.decode().strip())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to configure Fast Boot: {str(e)}")
            self.reset_toggle(113, not state)

    def toggle_114_action(self, state):
        """Above 4G Decoding toggle handler"""
        try:
            # This is a BIOS-level setting we can only notify about
            if state:
                QMessageBox.information(
                    self, 
                    "Manual BIOS Change Needed", 
                    "Please enable 'Above 4G Decoding' in your BIOS/UEFI settings:\n"
                    "1. Restart and enter BIOS (usually DEL/F2/F12)\n"
                    "2. Find PCIe settings\n"
                    "3. Enable Above 4G Decoding\n"
                    "4. Save and exit"
                )
            else:
                QMessageBox.information(
                    self, 
                    "Manual BIOS Change Needed", 
                    "Please disable 'Above 4G Decoding' in your BIOS/UEFI settings"
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to show instructions: {str(e)}")
            self.reset_toggle(114, not state)

    def toggle_115_action(self, state):
        """CSM toggle handler"""
        try:
            # This is a BIOS-level setting we can only notify about
            if state:
                QMessageBox.information(
                    self, 
                    "Manual BIOS Change Needed", 
                    "Please disable CSM (Compatibility Support Module) in your BIOS/UEFI settings:\n"
                    "1. Restart and enter BIOS\n"
                    "2. Find Boot options\n"
                    "3. Disable CSM\n"
                    "4. Save and exit"
                )
            else:
                QMessageBox.information(
                    self, 
                    "Manual BIOS Change Needed", 
                    "Please enable CSM in your BIOS/UEFI settings if needed for legacy hardware"
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to show instructions: {str(e)}")
            self.reset_toggle(115, not state)

    def toggle_116_action(self, state):
        """Performance Power Plan toggle handler"""
        try:
            if state:
                # Set to High Performance
                result = subprocess.run(
                    'powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c',
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    QMessageBox.information(self, "Success", "High performance power plan activated")
                else:
                    raise Exception(result.stderr.decode().strip())
            else:
                # Set to Balanced
                result = subprocess.run(
                    'powercfg /setactive 381b4222-f694-41f0-9685-ff5bb260df2e',
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    QMessageBox.information(self, "Success", "Balanced power plan activated")
                else:
                    raise Exception(result.stderr.decode().strip())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to change power plan: {str(e)}")
            self.reset_toggle(116, not state)

    def toggle_117_action(self, state):
        """TPM toggle handler"""
        try:
            if state:
                # Disable TPM
                result = subprocess.run(
                    'sc config TBS start= disabled',
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    QMessageBox.information(self, "Success", "TPM disabled. BIOS change may also be required.")
                else:
                    raise Exception(result.stderr.decode().strip())
            else:
                # Enable TPM
                result = subprocess.run(
                    'sc config TBS start= auto',
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    QMessageBox.information(self, "Success", "TPM enabled. BIOS change may also be required.")
                else:
                    raise Exception(result.stderr.decode().strip())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to configure TPM: {str(e)}")
            self.reset_toggle(117, not state)

    def toggle_118_action(self, state):
        """SVM Mode toggle handler"""
        try:
            # AMD Virtualization - BIOS level setting
            if state:
                QMessageBox.information(
                    self, 
                    "Manual BIOS Change Needed", 
                    "Please enable SVM Mode in your BIOS/UEFI settings:\n"
                    "1. Restart and enter BIOS\n"
                    "2. Find CPU settings\n"
                    "3. Enable SVM Mode\n"
                    "4. Save and exit"
                )
            else:
                QMessageBox.information(
                    self, 
                    "Manual BIOS Change Needed", 
                    "Please disable SVM Mode in your BIOS/UEFI settings"
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to show instructions: {str(e)}")
            self.reset_toggle(118, not state)

    def toggle_119_action(self, state):
        """IOMMU toggle handler"""
        try:
            # BIOS-level setting notification
            if state:
                QMessageBox.information(
                    self, 
                    "Manual BIOS Change Needed", 
                    "Please disable IOMMU in your BIOS/UEFI settings:\n"
                    "1. Restart and enter BIOS\n"
                    "2. Find chipset/advanced settings\n"
                    "3. Disable IOMMU/VT-d\n"
                    "4. Save and exit"
                )
            else:
                QMessageBox.information(
                    self, 
                    "Manual BIOS Change Needed", 
                    "Please enable IOMMU in your BIOS/UEFI settings if needed"
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to show instructions: {str(e)}")
            self.reset_toggle(119, not state)

    def toggle_120_action(self, state):
        """PCIe Gen Setting toggle handler"""
        try:
            # BIOS-level setting notification
            if state:
                QMessageBox.information(
                    self, 
                    "Manual BIOS Change Needed", 
                    "Please set PCIe to maximum generation in BIOS/UEFI:\n"
                    "1. Restart and enter BIOS\n"
                    "2. Find PCIe/Graphics settings\n"
                    "3. Set PCIe to Gen3/Gen4\n"
                    "4. Save and exit"
                )
            else:
                QMessageBox.information(
                    self, 
                    "Manual BIOS Change Needed", 
                    "Please set PCIe to Auto in BIOS/UEFI settings"
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to show instructions: {str(e)}")
            self.reset_toggle(120, not state)

    def close_application(self):
        # Create a styled message box
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Exit Confirmation")
        msg_box.setText("<h3>Are you sure you want to exit?</h3>")
        msg_box.setInformativeText("Any unsaved changes will be lost.")
        msg_box.setIcon(QMessageBox.Question)
        
        # Customize buttons
        exit_button = msg_box.addButton("Exit", QMessageBox.YesRole)
        exit_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: white;
                padding: 5px 15px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
        """)
        
        cancel_button = msg_box.addButton("Cancel", QMessageBox.NoRole)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333;
                padding: 5px 15px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        
        # Set window styling
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #f8f8f8;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel#qt_msgbox_label {
                color: #333;
            }
            QLabel#qt_msgbox_informativelabel {
                color: #666;
            }
        """)
        
        # Execute and check response
        msg_box.exec_()
        if msg_box.clickedButton() == exit_button:
            self.close()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

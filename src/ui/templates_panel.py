from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QScrollArea, QGridLayout, QFrame, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

import os
import sys

# Ensure core is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.template_engine import TemplateEngine

class TemplateCard(QFrame):
    clicked = pyqtSignal(dict)

    def __init__(self, template_data, parent=None):
        super().__init__(parent)
        self.template_data = template_data
        self.setFixedSize(104, 120)
        self.setStyleSheet("""
            QFrame {
                background-color: #1A1A1A;
                border-radius: 8px;
                border: 2px solid transparent;
            }
            QFrame:hover {
                border: 2px solid #333333;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top 80px Thumb (gradient placeholder)
        self.thumb = QLabel()
        self.thumb.setFixedHeight(80)
        cat_lower = template_data.get('category', '').lower()
        colors = {
            "trending": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF512F, stop:1 #DD2476)",
            "cinematic": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #141E30, stop:1 #243B55)",
            "gaming": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #000000, stop:1 #0f9b0f)",
            "social": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f12711, stop:1 #f5af19)",
            "wedding": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ff9a9e, stop:1 #fecfef)"
        }
        bg = colors.get(cat_lower, "#333333")
        self.thumb.setStyleSheet(f"background: {bg}; border-top-left-radius: 8px; border-top-right-radius: 8px; border-bottom: none;")
        
        # Duration Badge
        badge = QLabel(f"{template_data.get('duration', 0.0)}s", self.thumb)
        badge.setStyleSheet("background-color: rgba(0,0,0,0.6); color: white; border-radius: 4px; padding: 2px; font-size: 9px;")
        badge.move(75, 5) # Top right roughly
        
        layout.addWidget(self.thumb)

        # Bottom 40px Name
        self.name_label = QLabel(template_data.get('name', 'Unknown'))
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("color: #E5E5E5; font-size: 10px; padding: 2px;")
        layout.addWidget(self.name_label)

    def mousePressEvent(self, event):
        self.clicked.emit(self.template_data)
        super().mousePressEvent(event)

    def set_selected(self, selected):
        if selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: #1A1A1A;
                    border-radius: 8px;
                    border: 2px solid #7C3AED;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #1A1A1A;
                    border-radius: 8px;
                    border: 2px solid transparent;
                }
                QFrame:hover {
                    border: 2px solid #333333;
                }
            """)


class TemplatesPanel(QWidget):
    template_applied = pyqtSignal(object) # emits openshot timeline

    def __init__(self, parent=None):
        super().__init__(parent)
        self.engine = TemplateEngine()
        self.selected_template = None
        self.cards = []
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Category Pills
        pills_layout = QHBoxLayout()
        categories = ["All", "Trending", "Cinematic", "Gaming", "Social", "Wedding"]
        self.pill_buttons = []
        for cat in categories:
            btn = QPushButton(cat)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            if cat == "All":
                btn.setChecked(True)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1E1E1E;
                    color: white;
                    border-radius: 12px;
                    padding: 4px 10px;
                    border: none;
                }
                QPushButton:checked {
                    background-color: #7C3AED;
                    font-weight: bold;
                }
            """)
            btn.clicked.connect(lambda checked, c=cat: self._filter_category(c))
            pills_layout.addWidget(btn)
            self.pill_buttons.append(btn)
        
        # Scroll area for pills if they overflow
        pills_widget = QWidget()
        pills_widget.setLayout(pills_layout)
        pills_scroll = QScrollArea()
        pills_scroll.setWidget(pills_widget)
        pills_scroll.setFixedHeight(40)
        pills_scroll.setFrameShape(QFrame.Shape.NoFrame)
        pills_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        main_layout.addWidget(pills_scroll)

        # 2-column Grid
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(10)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.grid_widget)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        main_layout.addWidget(scroll, stretch=1)

        # Use Template Action Area
        self.action_area = QWidget()
        action_layout = QVBoxLayout(self.action_area)
        self.use_btn = QPushButton("Use This Template ▶")
        self.use_btn.setStyleSheet("""
            QPushButton {
                background-color: #7C3AED;
                color: white;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6D28D9;
            }
        """)
        self.use_btn.clicked.connect(self._apply_template)
        action_layout.addWidget(self.use_btn)
        self.action_area.setVisible(False)
        main_layout.addWidget(self.action_area)

        # Load All initially
        self._load_templates("All")

    def _filter_category(self, category):
        for btn in self.pill_buttons:
            btn.setChecked(btn.text() == category)
        self._load_templates(category)

    def _load_templates(self, category):
        # Clear existing
        for i in reversed(range(self.grid_layout.count())): 
            self.grid_layout.itemAt(i).widget().setParent(None)
        self.cards.clear()
        self.selected_template = None
        self.action_area.setVisible(False)

        templates = self.engine.list_templates(category)
        row, col = 0, 0
        for tpl in templates:
            card = TemplateCard(tpl)
            card.clicked.connect(self._on_card_clicked)
            self.grid_layout.addWidget(card, row, col)
            self.cards.append(card)
            col += 1
            if col > 1: # 2-column
                col = 0
                row += 1

    def _on_card_clicked(self, template_data):
        self.selected_template = template_data
        for card in self.cards:
            card.set_selected(card.template_data['template_id'] == template_data['template_id'])
        self.action_area.setVisible(True)

    def _apply_template(self):
        if not self.selected_template:
            return

        # Calculate needed slots
        slots = sum(1 for track in self.selected_template.get('tracks', []) 
                    for clip in track.get('clips', []) if clip.get('placeholder'))
        
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, f"Select {slots} Media Files for Template", "", "Media Files (*.mp4 *.mov *.avi *.png *.jpg)"
        )

        if len(file_paths) < slots:
            QMessageBox.warning(self, "Not Enough Media", f"This template requires {slots} clips, but only {len(file_paths)} were selected.")
            return

        # Apply using engine
        try:
            timeline = self.engine.apply_template(self.selected_template, file_paths[:slots])
            self.template_applied.emit(timeline)
            QMessageBox.information(self, "Success", "Template loaded into main timeline successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply template: {str(e)}")

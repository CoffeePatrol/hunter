import sys
import csv
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTableWidget, QTableWidgetItem, QLabel, 
                            QHeaderView, QFrame)
from PyQt6.QtGui import QPixmap, QIcon, QColor
from PyQt6.QtCore import Qt

class RegionIcon(QLabel):
    def __init__(self, region_name):
        super().__init__()
        # Define region colors (based on the game's color scheme)
        self.region_colors = {
            'Misthalin': '#1E3A8A',  # blue-800
            'Karamja': '#15803D',    # green-700
            'Asgarnia': '#1D4ED8',   # blue-700
            'Fremenik': '#1F2937',   # gray-800
            'Kandarin': '#991B1B',   # red-800
            'Desert': '#A16207',      # yellow-700
            'Mortyania': '#312E81',  # indigo-900
            'Tirannwn': '#065F46',   # emerald-700
            'Wilderness': '#111827',  # gray-900
            'Kourend': '#0F766E',    # teal-700
            'Varlamore': '#C2410C'   # orange-700
        }
        
        self.setFixedSize(32, 32)  # Increased from 24x24 to 32x32
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {self.region_colors.get(region_name, '#666666')};
                color: white;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }}
        """)
        self.setText(region_name[0])  # First letter of region name

def capitalize_monster_name(name):
    """Properly capitalize monster names treating them as proper nouns"""
    # Split on spaces and hyphens, keeping the separators
    parts = []
    current_part = ""
    
    for char in name:
        if char in [' ', '-']:
            if current_part:
                parts.append(current_part)
            parts.append(char)
            current_part = ""
        else:
            current_part += char
    if current_part:
        parts.append(current_part)
    
    # Capitalize each part
    capitalized_parts = []
    for part in parts:
        if part in [' ', '-']:
            capitalized_parts.append(part)
        else:
            capitalized_parts.append(part.capitalize())
    
    return ''.join(capitalized_parts)

class HunterTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hunter Tracker")
        self.setMinimumSize(1000, 600)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create and set up the table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Level', 'Creature', 'Regions', 'Locations', 'Method'])
        
        # Set table properties
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #E7E5DC;
                gridline-color: #8B7355;
                border: none;
            }
            QHeaderView::section {
                background-color: #8B7355;
                color: white;
                padding: 5px;
                border: 1px solid #695B49;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        
        layout.addWidget(self.table)
        
        # Load data
        self.load_data('hunter_data.csv')

    def load_data(self, filename):
        with open(filename, 'r') as file:
            reader = csv.DictReader(file)
            data = list(reader)
            
        self.table.setRowCount(len(data))
        
        for row, hunter_data in enumerate(data):
            # Level
            level_item = QTableWidgetItem(hunter_data['Level'])
            level_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, level_item)
            
            # Creature name (properly capitalized)
            name_item = QTableWidgetItem(capitalize_monster_name(hunter_data['Name']))
            self.table.setItem(row, 1, name_item)
            
            # Regions
            regions_widget = QWidget()
            regions_layout = QHBoxLayout(regions_widget)
            regions_layout.setSpacing(4)  # Increased spacing between icons
            regions_layout.setContentsMargins(4, 4, 4, 4)  # Increased margins
            
            # Check each region column and add icons for TRUE values
            region_columns = ['Misthalin/Karamja', 'Asgarnia', 'Kandarin', 'Mortyania', 
                            'wildy', 'desert', 'fremenik', 'tirannwn', 'kourend', 'varlamore']
            
            for region in region_columns:
                if hunter_data[region].upper() == 'TRUE':
                    # Handle special case for Misthalin/Karamja
                    if region == 'Misthalin/Karamja':
                        if 'Karamja' in hunter_data['Name']:  # You might want to adjust this logic
                            regions_layout.addWidget(RegionIcon('Karamja'))
                        else:
                            regions_layout.addWidget(RegionIcon('Misthalin'))
                    else:
                        # Capitalize region name and handle special cases
                        region_name = region.title()
                        if region == 'wildy':
                            region_name = 'Wilderness'
                        regions_layout.addWidget(RegionIcon(region_name))
            
            regions_layout.addStretch()
            self.table.setCellWidget(row, 2, regions_widget)
            
            # Locations (placeholder for now)
            location_item = QTableWidgetItem("Location placeholder")
            self.table.setItem(row, 3, location_item)
            
            # Method (placeholder for now)
            method_item = QTableWidgetItem("Method placeholder")
            self.table.setItem(row, 4, method_item)
            
        # Adjust row heights to accommodate larger icons
        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, 50)  # Increased row height

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = HunterTracker()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
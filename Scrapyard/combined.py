import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTableWidget, QTableWidgetItem, QLabel, 
                            QHeaderView, QFrame, QPushButton, QSpinBox, 
                            QCheckBox, QGroupBox, QGridLayout, QMessageBox)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt
import pandas as pd
import random

class RegionIcon(QLabel):
    def __init__(self, region_name):
        super().__init__()
        self.region_colors = {
            'Misthalin': '#1E3A8A',
            'Karamja': '#15803D',
            'Asgarnia': '#1D4ED8',
            'Fremenik': '#1F2937',
            'Kandarin': '#991B1B',
            'Desert': '#A16207',
            'Mortyania': '#312E81',
            'Tirannwn': '#065F46',
            'Wilderness': '#111827',
            'Kourend': '#0F766E',
            'Varlamore': '#C2410C'
        }
        
        self.setFixedSize(32, 32)
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
        self.setText(region_name[0])

class HunterAssignment:
    def __init__(self, monster=None, is_active=False, is_blocked=False):
        self.monster = monster
        self.is_active = is_active
        self.is_blocked = is_blocked

class CombinedHunterTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hunter Tracker & Rumor Manager")
        self.setMinimumSize(1200, 800)
        
        # Initialize data
        self.df = pd.read_csv('hunter_data.csv')
        
        # Define rumor givers and their corresponding column names in CSV
        self.rumor_givers = {
            'Novice': {'level': 46, 'column': 'Novice'},
            'Adept(cervus)': {'level': 57, 'column': 'Adept(cervus)'},
            'Adept(ornus)': {'level': 57, 'column': 'Adept(ornus)'},
            'Expert(aco)': {'level': 72, 'column': 'Expert(aco)'},
            'Expert(teco)': {'level': 72, 'column': 'Expert(teco)'},
            'Master(wolf)': {'level': 91, 'column': 'Master(wolf)'}
        }
        
        # Initialize assignment_widgets dictionary
        self.assignment_widgets = {
            giver: {
                'display': None,
                'new_btn': None,
                'active_btn': None,
                'block_btn': None,
                'clear_btn': None,
                'assignment': None
            } for giver in self.rumor_givers
        }
        
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create control panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # Create assignment panel
        assignment_panel = self.create_assignment_panel()
        layout.addWidget(assignment_panel)
        
        # Create and set up the table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            'Level', 'Creature', 'Regions', 'Available From', 'Status', 'Method', 'Actions'
        ])
        
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
        
        # Initialize
        self.player_level = 1
        self.selected_regions = set(['Misthalin/Karamja'])  # Default region
        self.assignment_widgets = {}
        self.update_table()

    def create_control_panel(self):
        panel = QGroupBox("Controls")
        layout = QHBoxLayout()
        
        # Level control
        level_widget = QWidget()
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Player Level:"))
        self.level_spinner = QSpinBox()
        self.level_spinner.setRange(1, 99)
        self.level_spinner.valueChanged.connect(self.on_level_change)
        level_layout.addWidget(self.level_spinner)
        level_widget.setLayout(level_layout)
        layout.addWidget(level_widget)
        
        # Region selection
        region_widget = QWidget()
        region_layout = QGridLayout()
        self.region_checkboxes = {}
        
        # Only use actual regions (columns before Novice)
        regions = [col for col in self.df.columns if col not in ['Name', 'Level'] and 
                  col not in [info['column'] for info in self.rumor_givers.values()]]
        
        for i, region in enumerate(regions):
            checkbox = QCheckBox(region)
            if region == 'Misthalin/Karamja':
                checkbox.setChecked(True)
                checkbox.setEnabled(False)
            checkbox.stateChanged.connect(self.on_region_change)
            self.region_checkboxes[region] = checkbox
            region_layout.addWidget(checkbox, i // 3, i % 3)
        
        region_widget.setLayout(region_layout)
        layout.addWidget(region_widget)
        
        panel.setLayout(layout)
        return panel

    def create_assignment_panel(self):
        panel = QGroupBox("Current Assignments")
        layout = QGridLayout()
        
        row = 0
        for giver, info in self.rumor_givers.items():
            # Giver label
            layout.addWidget(QLabel(f"{giver} (Lvl {info['level']}):"), row, 0)
            
            # Assignment display
            display = QLabel("No assignment")
            layout.addWidget(display, row, 1)
            
            # Control buttons
            new_btn = QPushButton("Get New")
            new_btn.clicked.connect(lambda checked, g=giver: self.get_new_assignment(g))
            layout.addWidget(new_btn, row, 2)
            
            active_btn = QPushButton("Make Active")
            active_btn.clicked.connect(lambda checked, g=giver: self.toggle_active(g))
            layout.addWidget(active_btn, row, 3)
            
            block_btn = QPushButton("Block")
            block_btn.clicked.connect(lambda checked, g=giver: self.toggle_block(g))
            layout.addWidget(block_btn, row, 4)
            
            clear_btn = QPushButton("Clear")
            clear_btn.clicked.connect(lambda checked, g=giver: self.clear_assignment(g))
            layout.addWidget(clear_btn, row, 5)
            
            # Update the pre-initialized widgets dictionary
            self.assignment_widgets[giver] = {
                'display': display,
                'new_btn': new_btn,
                'active_btn': active_btn,
                'block_btn': block_btn,
                'clear_btn': clear_btn,
                'assignment': None
            }
            
            row += 1
        
        panel.setLayout(layout)
        return panel

    def get_available_monsters(self, giver):
        """Get available monsters for a given giver based on level and current assignments"""
        if self.player_level < self.rumor_givers[giver]['level']:
            return []
            
        # Get all currently assigned or blocked monsters
        assigned = set()
        for info in self.assignment_widgets.values():
            if info['assignment']:
                assigned.add(info['assignment'].monster)
        
        # Filter monsters based on giver's column in CSV
        giver_column = self.rumor_givers[giver]['column']
        available = []
        
        for _, row in self.df.iterrows():
            if (row['Level'] <= self.player_level and 
                row[giver_column] == True and  # Check if giver can assign this monster
                row['Name'] not in assigned and
                any(row[region] for region in self.selected_regions)):
                available.append(row['Name'])
        
        return available

    def get_new_assignment(self, giver):
        """Get a new assignment from a giver"""
        available = self.get_available_monsters(giver)
        if not available:
            QMessageBox.information(self, "No Assignments",
                                  f"No available assignments from {giver} at your level.")
            return
        
        # Randomly select from available monsters
        monster = random.choice(available)
        
        # Ensure the giver exists in assignment_widgets
        if giver not in self.assignment_widgets:
            print(f"Error: {giver} not found in assignment_widgets")
            print("Available givers:", list(self.assignment_widgets.keys()))
            return
            
        self.assignment_widgets[giver]['assignment'] = HunterAssignment(monster)
        self.update_display(giver)
        self.update_table()

    def toggle_active(self, giver):
        # Deactivate current active assignment
        for g, info in self.assignment_widgets.items():
            if info['assignment'] and info['assignment'].is_active:
                info['assignment'].is_active = False
                self.update_display(g)
        
        # Activate new assignment
        if self.assignment_widgets[giver]['assignment']:
            self.assignment_widgets[giver]['assignment'].is_active = True
            self.update_display(giver)
        
        self.update_table()

    def toggle_block(self, giver):
        assignment = self.assignment_widgets[giver]['assignment']
        if assignment:
            assignment.is_blocked = not assignment.is_blocked
            self.update_display(giver)
            self.update_table()

    def clear_assignment(self, giver):
        self.assignment_widgets[giver]['assignment'] = None
        self.update_display(giver)
        self.update_table()

    def update_display(self, giver):
        """Update the display for a giver's assignment"""
        info = self.assignment_widgets[giver]
        assignment = info['assignment']
        
        if assignment:
            status = []
            if assignment.is_active:
                status.append("ACTIVE")
            if assignment.is_blocked:
                status.append("BLOCKED")
            
            display_text = assignment.monster
            if status:
                display_text += f" ({', '.join(status)})"
        else:
            display_text = "No assignment"
        
        info['display'].setText(display_text)

    def on_level_change(self):
            """Handle level changes"""
            self.player_level = self.level_spinner.value()
            self.update_table()
            
            # Update button states based on level
            for giver, info in self.rumor_givers.items():
                if giver in self.assignment_widgets and 'new_btn' in self.assignment_widgets[giver]:
                    widgets = self.assignment_widgets[giver]
                    if self.player_level >= info['level']:
                        widgets['new_btn'].setEnabled(True)
                    else:
                        widgets['new_btn'].setEnabled(False)
                        if widgets['assignment']:
                            self.clear_assignment(giver)

    def on_region_change(self):
        self.selected_regions = set()
        for region, checkbox in self.region_checkboxes.items():
            if checkbox.isChecked():
                self.selected_regions.add(region)
        self.update_table()

    def update_table(self):
        self.table.setRowCount(0)
        row = 0
        
        for _, monster in self.df.iterrows():
            # Check if monster meets current filters
            if monster['Level'] > self.player_level:
                continue
            
            if not any(monster[region] for region in self.selected_regions):
                continue
            
            self.table.insertRow(row)
            
            # Level
            level_item = QTableWidgetItem(str(int(monster['Level'])))
            level_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, level_item)
            
            # Name
            name_item = QTableWidgetItem(monster['Name'])
            self.table.setItem(row, 1, name_item)
            
            # Regions
            regions_widget = QWidget()
            regions_layout = QHBoxLayout(regions_widget)
            regions_layout.setSpacing(4)
            regions_layout.setContentsMargins(4, 4, 4, 4)
            
            for region in self.region_checkboxes:
                if monster[region]:
                    if region == 'Misthalin/Karamja':
                        if 'Karamja' in monster['Name']:
                            regions_layout.addWidget(RegionIcon('Karamja'))
                        else:
                            regions_layout.addWidget(RegionIcon('Misthalin'))
                    else:
                        region_name = region.title()
                        regions_layout.addWidget(RegionIcon(region_name))
            
            regions_layout.addStretch()
            self.table.setCellWidget(row, 2, regions_widget)
            
            # Available from
            givers = []
            for giver, info in self.rumor_givers.items():
                if (monster['Level'] <= self.player_level and 
                    self.player_level >= info['level'] and
                    monster[info['column']] == True):
                    givers.append(giver)
            self.table.setItem(row, 3, QTableWidgetItem(", ".join(givers)))
            
            # Status
            status = []
            for giver, info in self.assignment_widgets.items():
                if info['assignment'] and info['assignment'].monster == monster['Name']:
                    if info['assignment'].is_active:
                        status.append("Active")
                    if info['assignment'].is_blocked:
                        status.append("Blocked")
            self.table.setItem(row, 4, QTableWidgetItem(" & ".join(status) if status else "Available"))
            
            # Method (placeholder)
            self.table.setItem(row, 5, QTableWidgetItem("Method placeholder"))
            
            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            
            assign_btn = QPushButton("Assign")
            assign_btn.clicked.connect(lambda checked, m=monster['Name']: self.quick_assign(m))
            action_layout.addWidget(assign_btn)
            
            self.table.setCellWidget(row, 6, action_widget)
            
            row += 1
        
        # Adjust row heights
        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, 50)

    def quick_assign(self, monster_name):
        """Quickly assign a monster to the lowest level available giver that can give this monster"""
        monster_data = self.df[self.df['Name'] == monster_name].iloc[0]
        
        # Find lowest level available giver that can assign this monster
        available_givers = []
        for giver, info in self.rumor_givers.items():
            if (self.player_level >= info['level'] and 
                not self.assignment_widgets[giver]['assignment'] and
                monster_data[info['column']] == True):
                available_givers.append(giver)
        
        if not available_givers:
            QMessageBox.warning(self, "No Available Givers",
                              "No eligible givers available for this assignment.")
            return
        
        # Sort by level requirement and take the first
        giver = min(available_givers, key=lambda g: self.rumor_givers[g]['level'])
        self.assignment_widgets[giver]['assignment'] = HunterAssignment(monster_name)
        self.update_display(giver)
        self.update_table()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = CombinedHunterTracker()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
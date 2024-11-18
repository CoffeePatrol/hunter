import os
import sys
import pandas as pd
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class HunterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hunter Monster & Rumor Finder")
        
        # Read CSV data
        self.df = pd.read_csv(resource_path('hunter_data.csv'))
        
        # Create main frame with scrollbar
        main_frame = ttk.Frame(root)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)
        
        # Input frame
        input_frame = ttk.LabelFrame(main_frame, text="Search Criteria", padding="10")
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Level input
        ttk.Label(input_frame, text="Enter your level (19-99):").grid(row=0, column=0, sticky=tk.W)
        self.level_var = tk.StringVar()
        level_entry = ttk.Entry(input_frame, textvariable=self.level_var, width=10)
        level_entry.grid(row=0, column=1, sticky=tk.W)
        level_entry.bind('<KeyRelease>', self.on_level_change)
        
        # Region selection
        ttk.Label(input_frame, text="Select regions:").grid(row=1, column=0, sticky=tk.W, pady=(10,0))
        
        # Get region names (excluding Name, Level and rumor giver columns)
        self.regions = list(self.df.columns[2:12])  # Columns 2-11 are regions
        self.checkbox_vars = {}
        
        # Create region checkboxes
        region_frame = ttk.Frame(input_frame)
        region_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        for i, region in enumerate(self.regions):
            var = tk.BooleanVar(value=(region == 'Misthalin/Karamja'))
            self.checkbox_vars[region] = var
            checkbox = ttk.Checkbutton(region_frame, text=region, variable=var)
            checkbox.grid(row=i//2, column=i%2, sticky=tk.W, padx=5)
            if region == 'Misthalin/Karamja':
                checkbox.state(['disabled'])
        
        # Define rumor givers and their level requirements
        self.rumor_givers = {
            'Novice': 46,
            'Adept(cervus)': 57,
            'Adept(ornus)': 57,
            'Expert(aco)': 72,
            'expert(teco)': 72,
            'Master(wolf)': 91
        }
        
        # Current assignments frame
        self.assignments_frame = ttk.LabelFrame(main_frame, text="Current Rumor Assignments", padding="10")
        self.assignments_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Track assignments and active rumor
        self.current_assignments = {}
        self.active_giver = None
        self.active_rumor = None
        
        # Create assignment displays and controls for each giver
        row = 0
        for giver, req_level in self.rumor_givers.items():
            # Giver label with level requirement
            ttk.Label(self.assignments_frame, text=f"{giver} (Lvl {req_level}):").grid(
                row=row, column=0, sticky=tk.W)
            
            # Display current assignment
            display = tk.Text(self.assignments_frame, height=1, width=30)
            display.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5)
            display.config(state='disabled')
            
            # Control buttons
            new_btn = ttk.Button(self.assignments_frame, text="Get New", 
                               command=lambda g=giver: self.get_new_assignment(g))
            new_btn.grid(row=row, column=2, padx=5)
            new_btn.state(['disabled'])
            
            active_btn = ttk.Button(self.assignments_frame, text="Toggle Active", 
                                  command=lambda g=giver: self.make_active(g))
            active_btn.grid(row=row, column=3, padx=5)
            active_btn.state(['disabled'])
            
            complete_btn = ttk.Button(self.assignments_frame, text="Complete", 
                                    command=lambda g=giver: self.complete_assignment(g))
            complete_btn.grid(row=row, column=4, padx=5)
            complete_btn.state(['disabled'])
            
            clear_btn = ttk.Button(self.assignments_frame, text="Clear", 
                                 command=lambda g=giver: self.clear_assignment(g))
            clear_btn.grid(row=row, column=5, padx=5)
            clear_btn.state(['disabled'])
            
            # Store UI elements for this giver
            self.current_assignments[giver] = {
                'task': None,
                'display': display,
                'new_btn': new_btn,
                'active_btn': active_btn,
                'complete_btn': complete_btn,
                'clear_btn': clear_btn
            }
            
            row += 1
            
        # Results section
        ttk.Button(main_frame, text="Find Available Monsters", 
                  command=self.find_monsters).grid(row=2, column=0, pady=10)
        
        results_frame = ttk.Frame(main_frame)
        results_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        self.results_text = tk.Text(results_frame, width=80, height=20)
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", 
                                command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(0, weight=1)

    def update_all_displays(self):
        """Update all giver displays"""
        for giver in self.rumor_givers:
            self.update_display(giver)

    def update_display(self, giver):
        """Update the display for a giver's assignment"""
        display = self.current_assignments[giver]['display']
        task = self.current_assignments[giver]['task']
        
        display.config(state='normal')
        display.delete(1.0, tk.END)
        if task:
            if giver == self.active_giver:
                display.insert(tk.END, f"{task} (ACTIVE)")
            else:
                display.insert(tk.END, task)
        display.config(state='disabled')

    def get_available_assignments(self, giver):
        """Get available assignments for a giver based on level and current assignments"""
        try:
            level = int(self.level_var.get())
            if level < self.rumor_givers[giver]:
                return []
            
            # Get selected regions
            selected_regions = [region for region, var in self.checkbox_vars.items() 
                              if var.get()]
            
            # Get all possible assignments for this giver
            giver_mask = self.df[giver] == True
            level_mask = self.df['Level'] <= level
            region_mask = self.df[selected_regions].any(axis=1)
            possible = self.df[giver_mask & level_mask & region_mask]['Name'].tolist()
            
            # Remove assignments currently given by any giver
            current_tasks = {info['task'] for info in self.current_assignments.values() 
                           if info['task'] is not None}
            
            return [task for task in possible if task not in current_tasks]
            
        except ValueError:
            return []

    def get_new_assignment(self, giver):
        """Get a new assignment from a giver"""
        available = self.get_available_assignments(giver)
        if not available:
            messagebox.showinfo("No Assignments", 
                              f"No available assignments from {giver} at your level.")
            return
        
        # Create selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Select Assignment from {giver}")
        dialog.grab_set()
        
        listbox = tk.Listbox(dialog, width=50, height=10)
        listbox.pack(padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.configure(yscrollcommand=scrollbar.set)
        
        # Populate listbox with available tasks
        task_info = {}
        for task in available:
            monster = self.df[self.df['Name'] == task].iloc[0]
            regions = [region for region in self.regions if monster[region]]
            info = f"{task} (Level {int(monster['Level'])}) - {', '.join(regions)}"
            task_info[info] = task
            listbox.insert(tk.END, info)
        
        def on_select():
            selection = listbox.curselection()
            if selection:
                info = listbox.get(selection[0])
                task = task_info[info]
                
                self.current_assignments[giver]['task'] = task
                self.update_display(giver)
                
                # Enable buttons
                self.current_assignments[giver]['active_btn'].state(['!disabled'])
                self.current_assignments[giver]['complete_btn'].state(['!disabled'])
                self.current_assignments[giver]['clear_btn'].state(['!disabled'])
                
                if not self.active_giver:
                    self.make_active(giver)
                    
                dialog.destroy()
            else:
                messagebox.showwarning("No Selection", 
                                     "Please select an assignment first.")
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Select", 
                  command=on_select).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Center dialog
        dialog.transient(self.root)
        dialog.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

    def make_active(self, giver):
        """Toggle a giver's assignment as the active rumor"""
        if self.active_giver == giver:
            self.active_giver = None
            self.active_rumor = None
        else:
            if self.active_giver:
                self.update_display(self.active_giver)
            self.active_giver = giver
            self.active_rumor = self.current_assignments[giver]['task']
        
        self.update_all_displays()

    def complete_assignment(self, giver):
        """Complete the current assignment from a giver"""
        if self.active_giver == giver:
            self.active_giver = None
            self.active_rumor = None
        
        self.current_assignments[giver]['task'] = None
        self.update_display(giver)
        
        # Update button states
        self.current_assignments[giver]['new_btn'].state(['!disabled'])
        self.current_assignments[giver]['active_btn'].state(['disabled'])
        self.current_assignments[giver]['complete_btn'].state(['disabled'])
        self.current_assignments[giver]['clear_btn'].state(['disabled'])

    def clear_assignment(self, giver):
        """Clear the current assignment without completing it"""
        if self.active_giver == giver:
            self.active_giver = None
            self.active_rumor = None
        
        self.current_assignments[giver]['task'] = None
        self.update_display(giver)
        
        # Update button states
        self.current_assignments[giver]['new_btn'].state(['!disabled'])
        self.current_assignments[giver]['active_btn'].state(['disabled'])
        self.current_assignments[giver]['complete_btn'].state(['disabled'])
        self.current_assignments[giver]['clear_btn'].state(['disabled'])

    def on_level_change(self, event=None):
        """Handle level changes"""
        try:
            level = int(self.level_var.get())
            for giver, req_level in self.rumor_givers.items():
                if level >= req_level:
                    self.current_assignments[giver]['new_btn'].state(['!disabled'])
                else:
                    # Disable and clear assignments for givers above current level
                    self.current_assignments[giver]['new_btn'].state(['disabled'])
                    if self.current_assignments[giver]['task']:
                        self.clear_assignment(giver)
        except ValueError:
            # Invalid level - disable all new assignment buttons
            for giver in self.rumor_givers:
                self.current_assignments[giver]['new_btn'].state(['disabled'])

    def find_monsters(self):
            """Display all available monsters grouped by giver"""
            self.results_text.delete(1.0, tk.END)
            
            try:
                level = int(self.level_var.get())
                if level < 19 or level > 99:
                    messagebox.showwarning("Invalid Level", "Level must be between 19 and 99")
                    return
            except ValueError:
                messagebox.showwarning("Invalid Input", "Please enter a valid level")
                return
            
            selected_regions = [region for region, var in self.checkbox_vars.items() 
                            if var.get()]
            
            if not selected_regions:
                messagebox.showwarning("No Regions", "Please select at least one region")
                return
            
            # Get currently assigned tasks
            assigned_tasks = {info['task'] for info in self.current_assignments.values() 
                            if info['task'] is not None}
            
            # Display available tasks by giver
            self.results_text.insert(tk.END, "=== Available Assignments by Giver ===\n\n")
            
            for giver, req_level in self.rumor_givers.items():
                if level >= req_level:
                    self.results_text.insert(tk.END, f"{giver} (Level {req_level}):\n")
                    
                    # Get monsters this giver can assign
                    giver_mask = self.df[giver] == True
                    level_mask = self.df['Level'] <= level
                    region_mask = self.df[selected_regions].any(axis=1)
                    available = self.df[giver_mask & level_mask & region_mask]
                    
                    if len(available) == 0:
                        self.results_text.insert(tk.END, "  No available assignments in selected regions\n")
                    else:
                        # Track if any unassigned tasks exist
                        has_unassigned = False
                        
                        for _, monster in available.iterrows():
                            monster_regions = [region for region in selected_regions if monster[region]]
                            name = monster['Name']
                            
                            # Check if task is currently assigned
                            if name in assigned_tasks:
                                status = " (Currently Assigned)"
                            else:
                                status = ""
                                has_unassigned = True
                                
                            result_text = (f"  {name} (Level {int(monster['Level'])})"
                                        f" - {', '.join(monster_regions)}{status}\n")
                            self.results_text.insert(tk.END, result_text)
                        
                        if not has_unassigned:
                            self.results_text.insert(tk.END, 
                                "  (All available tasks are currently assigned)\n")
                    
                    self.results_text.insert(tk.END, "\n")
                else:
                    self.results_text.insert(tk.END, 
                        f"{giver} - Requires level {req_level}\n\n")

def main():
    root = tk.Tk()
    app = HunterApp(root)
    root.mainloop()

def main():
    try:
        root = tk.Tk()
        app = HunterApp(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()

import tkinter as tk
from tkinter import ttk
import pandas as pd
from tkinter import messagebox

class HunterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hunter Monster Finder")
        
        # Read CSV data
        self.df = pd.read_csv('hunter_data.csv')
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Level input
        ttk.Label(main_frame, text="Enter your level (19-99):").grid(row=0, column=0, sticky=tk.W)
        self.level_var = tk.StringVar()
        level_entry = ttk.Entry(main_frame, textvariable=self.level_var, width=10)
        level_entry.grid(row=0, column=1, sticky=tk.W)
        
        # Region checkboxes
        ttk.Label(main_frame, text="Select regions:").grid(row=1, column=0, sticky=tk.W, pady=(10,0))
        
        # Get region names (excluding Name and Level columns)
        self.regions = list(self.df.columns[2:])
        self.checkbox_vars = {}
        
        # Create checkboxes for each region
        for i, region in enumerate(self.regions):
            var = tk.BooleanVar()
            self.checkbox_vars[region] = var
            ttk.Checkbutton(main_frame, text=region, variable=var).grid(
                row=i+2, column=0, sticky=tk.W
            )
        
        # Results
        ttk.Label(main_frame, text="Available Monsters:").grid(
            row=1, column=1, sticky=tk.W, pady=(10,0), padx=(20,0)
        )
        
        # Create text widget for results
        self.results_text = tk.Text(main_frame, width=40, height=20)
        self.results_text.grid(row=2, column=1, rowspan=len(self.regions), 
                             sticky=(tk.W, tk.E, tk.N, tk.S), padx=(20,0))
        
        # Search button
        ttk.Button(main_frame, text="Find Monsters", command=self.find_monsters).grid(
            row=len(self.regions)+2, column=0, columnspan=2, pady=(10,0)
        )
        
        # Bind level entry validation to FocusOut instead of KeyRelease
        level_entry.bind('<FocusOut>', self.validate_level)
        
    def validate_level(self, event=None):
        value = self.level_var.get()
        if value == '':  # Allow empty value
            return
            
        try:
            level = int(value)
            if level < 19 or level > 99:
                messagebox.showwarning("Invalid Level", "Level must be between 19 and 99")
                self.level_var.set('')
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a number between 19 and 99")
            self.level_var.set('')
    
    def find_monsters(self):
        # Validate level before searching
        value = self.level_var.get()
        if not value:
            messagebox.showwarning("Invalid Input", "Please enter a level")
            return
            
        try:
            level = int(value)
            if level < 19 or level > 99:
                messagebox.showwarning("Invalid Level", "Level must be between 19 and 99")
                return
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid level")
            return
            
        # Clear previous results
        self.results_text.delete(1.0, tk.END)
        
        # Get selected regions
        selected_regions = [region for region, var in self.checkbox_vars.items() 
                          if var.get()]
        
        if not selected_regions:
            messagebox.showwarning("No Regions", "Please select at least one region")
            return
        
        # Filter monsters
        level_mask = self.df['Level'] <= level
        region_mask = self.df[selected_regions].any(axis=1)
        available_monsters = self.df[level_mask & region_mask]
        
        # Display results
        if len(available_monsters) == 0:
            self.results_text.insert(tk.END, "No monsters found matching your criteria.")
            return
        
        # Format and display results
        for _, monster in available_monsters.iterrows():
            monster_regions = [region for region in selected_regions if monster[region]]
            result_text = f"{monster['Name']} (Level {monster['Level']})\n"
            result_text += f"Found in: {', '.join(monster_regions)}\n\n"
            self.results_text.insert(tk.END, result_text)

def main():
    root = tk.Tk()
    app = HunterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
import tkinter as tk
from tkinter import messagebox, filedialog, ttk, PhotoImage
import tkintermapview
import pandas as pd
import threading
from PIL import Image, ImageTk

class EdnaApp(tk.Tk):
    """
    An advanced eDNA Data Management and Visualization application with a professional,
    animated UI, interactive filters, and multithreaded map rendering.
    """
    def __init__(self):
        super().__init__()
        self.title('eSENSE - eDNA Data Management & Visualization')
        self.geometry('1400x900')
        self.configure(bg='#f0f4f7')

        self.data = None
        self.markers = []

        # --- Initialize the Animated Login Screen ---
        self.init_animated_login_screen()

    def init_animated_login_screen(self):
        """Creates a visually appealing login screen with smooth animations."""
        self.login_frame = tk.Frame(self, bg='#2c3e50')
        self.login_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # --- Load and prepare logo ---
        try:
            logo_image = Image.open("logo.png").resize((120, 120), Image.Resampling.LANCZOS)
            self.logo = ImageTk.PhotoImage(logo_image)
        except FileNotFoundError:
            self.logo = None
            print("Warning: 'logo.png' not found. Login screen will display without a logo.")

        # --- Widgets ---
        self.logo_label = tk.Label(self.login_frame, image=self.logo, bg='#2c3e50')
        self.title_label = tk.Label(self.login_frame, text="eSENSE", font=("Helvetica", 32, "bold"), fg='white', bg='#2c3e50')
        
        self.username_entry = tk.Entry(self.login_frame, font=("Helvetica", 14), width=30, relief='flat', insertbackground='white', fg='white', bg='#34495e')
        self.password_entry = tk.Entry(self.login_frame, font=("Helvetica", 14), width=30, show='*', relief='flat', insertbackground='white', fg='white', bg='#34495e')
        
        self.login_btn = tk.Button(self.login_frame, text='Login', command=self.login, bg='#3498db', fg='white', font=("Helvetica", 14, "bold"), relief='flat', activebackground='#2980b9', activeforeground='white')

        # --- Placeholder Text Simulation ---
        self.setup_placeholder(self.username_entry, "Username")
        self.setup_placeholder(self.password_entry, "Password", is_password=True)

        # --- Hover Effects for Login Button ---
        self.login_btn.bind("<Enter>", lambda e: self.login_btn.config(bg='#2980b9'))
        self.login_btn.bind("<Leave>", lambda e: self.login_btn.config(bg='#3498db'))

        # --- Initial positions for animation (off-screen) ---
        self.logo_label.place(relx=0.5, rely=-0.2, anchor='center')
        self.title_label.place(relx=0.5, rely=1.2, anchor='center')
        self.username_entry.place(relx=0.5, rely=1.3, anchor='center', width=350, height=40)
        self.password_entry.place(relx=0.5, rely=1.4, anchor='center', width=350, height=40)
        self.login_btn.place(relx=0.5, rely=1.5, anchor='center', width=350, height=50)

        # --- Start Animations ---
        self.animate_widget(self.logo_label, 0.3)
        self.animate_widget(self.title_label, 0.4, delay=100)
        self.animate_widget(self.username_entry, 0.5, delay=200)
        self.animate_widget(self.password_entry, 0.58, delay=300)
        self.animate_widget(self.login_btn, 0.68, delay=400)

    def setup_placeholder(self, entry, text, is_password=False):
        """Adds placeholder text functionality to an Entry widget."""
        entry.insert(0, text)
        entry.config(fg='grey')

        def on_focus_in(event):
            if entry.get() == text:
                entry.delete(0, 'end')
                entry.config(fg='white', show='*' if is_password else '')
        
        def on_focus_out(event):
            if not entry.get():
                entry.insert(0, text)
                entry.config(fg='grey', show='' if is_password else '')

        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)

    def animate_widget(self, widget, target_rely, delay=0):
        """Animates a widget to slide into its target vertical position."""
        self.after(delay, self._animate, widget, target_rely, widget.place_info()['rely'])

    def _animate(self, widget, target_rely, current_rely):
        """Recursive animation step."""
        current_rely = float(current_rely)
        distance = target_rely - current_rely
        
        if abs(distance) < 0.01:
            widget.place(rely=target_rely)
            return

        new_rely = current_rely + distance * 0.1 # Easing effect
        widget.place(rely=new_rely)
        
        self.after(15, self._animate, widget, target_rely, new_rely)
        
    def login(self):
        """Validates login credentials and proceeds to the dashboard."""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if username == 'admin' and password == 'password':
            self.login_frame.destroy()
            self.init_dashboard()
        else:
            messagebox.showerror('Login Failed', 'Invalid username or password')
            # Reset password field for security
            self.password_entry.delete(0, 'end')
            self.setup_placeholder(self.password_entry, "Password", is_password=True)

    def init_dashboard(self):
        """Initializes the main dashboard after successful login."""
        header_frame = tk.Frame(self, bg='#2c3e50', height=70)
        header_frame.pack(side='top', fill='x')
        header_frame.pack_propagate(False)

        if self.logo:
            logo_label = tk.Label(header_frame, image=self.logo, bg='#2c3e50')
            logo_label.pack(side='left', padx=15, pady=5)

        title_label = tk.Label(header_frame, text="eDNA Data Dashboard", font=("Helvetica", 22, "bold"), bg='#2c3e50', fg='white')
        title_label.pack(side='left', padx=10)

        main_frame = tk.Frame(self, bg='#f0f4f7')
        main_frame.pack(fill='both', expand=True)

        self.create_menu()
        self.create_sidebar(main_frame)
        self.create_map_area(main_frame)
        
    # --- The rest of the dashboard code remains the same ---
    # (create_menu, create_sidebar, create_map_area, open_file, etc.)

    def create_menu(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label='Open Data File...', command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.quit)
        menubar.add_cascade(label='File', menu=file_menu)
        self.config(menu=menubar)

    def create_sidebar(self, parent_frame):
        self.sidebar = tk.Frame(parent_frame, width=300, bg='white', padx=15, pady=15, relief='sunken', bd=2)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)
        tk.Label(self.sidebar, text="Data Filters", font=("Helvetica", 16, "bold"), bg='white').pack(pady=10, anchor='w')
        tk.Label(self.sidebar, text='Species Detected:', bg='white', font=("Helvetica", 12)).pack(anchor='w', pady=(15, 0))
        self.species_var = tk.StringVar()
        self.species_entry = ttk.Combobox(self.sidebar, textvariable=self.species_var, font=("Helvetica", 11))
        self.species_entry.pack(fill='x', pady=5)
        tk.Label(self.sidebar, text='Water Body Type:', bg='white', font=("Helvetica", 12)).pack(anchor='w', pady=(15, 0))
        self.waterbody_var = tk.StringVar()
        self.waterbody_entry = ttk.Combobox(self.sidebar, textvariable=self.waterbody_var, font=("Helvetica", 11))
        self.waterbody_entry.pack(fill='x', pady=5)
        tk.Label(self.sidebar, text='Date Range (YYYY-MM-DD):', bg='white', font=("Helvetica", 12)).pack(anchor='w', pady=(15, 0))
        self.date_from_entry = tk.Entry(self.sidebar, font=("Helvetica", 11), relief='solid', bd=1)
        self.date_from_entry.pack(fill='x', pady=5)
        self.date_to_entry = tk.Entry(self.sidebar, font=("Helvetica", 11), relief='solid', bd=1)
        self.date_to_entry.pack(fill='x', pady=5)
        self.apply_filter_btn = tk.Button(self.sidebar, text='Apply Filters', bg='#3498db', fg='white', command=self.apply_filters, relief='flat', font=("Helvetica", 12))
        self.apply_filter_btn.pack(pady=20, fill='x', ipady=5)
        self.clear_filter_btn = tk.Button(self.sidebar, text='Clear Filters', bg='#95a5a6', fg='white', command=self.clear_filters, relief='flat', font=("Helvetica", 12))
        self.clear_filter_btn.pack(pady=5, fill='x', ipady=5)

    def create_map_area(self, parent_frame):
        self.map_frame = tk.Frame(parent_frame, bg='white', relief='sunken', bd=2)
        self.map_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)
        self.map_widget = tkintermapview.TkinterMapView(self.map_frame, corner_radius=0)
        self.map_widget.pack(fill='both', expand=True)
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
        self.map_widget.set_position(20.5937, 78.9629)
        self.map_widget.set_zoom(5)

    def open_file(self):
        filepath = filedialog.askopenfilename(filetypes=[('Excel files', '*.xlsx *.xls'), ('CSV files', '*.csv')])
        if filepath:
            try:
                self.data = pd.read_excel(filepath) if filepath.endswith(('.xlsx', '.xls')) else pd.read_csv(filepath)
                messagebox.showinfo('File Loaded', f'Successfully loaded: {filepath}')
                self.populate_filters()
                threading.Thread(target=self.draw_map_markers, daemon=True).start()
            except Exception as e:
                messagebox.showerror('Error', f'Failed to load file: {e}')

    def populate_filters(self):
        if self.data is None: return
        species = sorted(set(s.strip() for sl in self.data['SpeciesDetected'].dropna() for s in sl.split(',')))
        self.species_entry['values'] = species
        self.waterbody_entry['values'] = sorted(self.data['WaterBodyType'].dropna().unique())

    def clear_filters(self):
        self.species_var.set(""); self.waterbody_var.set("")
        self.date_from_entry.delete(0, 'end'); self.date_to_entry.delete(0, 'end')
        if self.data is not None:
            threading.Thread(target=self.draw_map_markers, daemon=True).start()

    def apply_filters(self):
        if self.data is None:
            messagebox.showwarning('No Data', 'Please load a data file first.')
            return
        threading.Thread(target=self._filter_and_draw, daemon=True).start()

    def _filter_and_draw(self):
        filtered_data = self.data.copy()
        if self.species_var.get(): filtered_data = filtered_data[filtered_data['SpeciesDetected'].str.contains(self.species_var.get(), na=False)]
        if self.waterbody_var.get(): filtered_data = filtered_data[filtered_data['WaterBodyType'] == self.waterbody_var.get()]
        if self.date_from_entry.get(): filtered_data = filtered_data[pd.to_datetime(filtered_data['SamplingDate']) >= pd.to_datetime(self.date_from_entry.get())]
        if self.date_to_entry.get(): filtered_data = filtered_data[pd.to_datetime(filtered_data['SamplingDate']) <= pd.to_datetime(self.date_to_entry.get())]
        self.draw_map_markers(filtered_data)

    def draw_map_markers(self, data_to_plot=None):
        if data_to_plot is None: data_to_plot = self.data
        if data_to_plot is None: return
        for marker in self.markers: marker.delete()
        self.markers.clear()
        for _, row in data_to_plot.iterrows():
            text = f"SampleID: {row['SampleID']}\nSpecies: {row['SpeciesDetected']}"
            marker = self.map_widget.set_marker(row['Latitude'], row['Longitude'], text=text)
            self.markers.append(marker)


if __name__ == '__main__':
    # Dependencies: pip install pandas openpyxl tkintermapview pillow
    app = EdnaApp()
    app.mainloop()


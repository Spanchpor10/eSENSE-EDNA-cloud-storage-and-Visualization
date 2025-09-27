import threading
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import folium
import webbrowser
import requests
from datetime import datetime
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image, ImageTk
import numpy as np

# ---- SET FILE PATHS ----
INDIA_SHP = "india_ds.shp"  # matches your file

# ---- READ SHAPEFILE AND HANDLE CRS ----
india_gdf = gpd.read_file(INDIA_SHP)
if india_gdf.crs is None:
    india_gdf.set_crs(epsg=4326, inplace=True)

state_col = "DISTRICT"
state_list = sorted(india_gdf[state_col].astype(str).unique().tolist())

# ---- GENERATE MOCK eDNA DATA ----
np.random.seed(42)
species_list = [f"Species {c}" for c in "ABCDE"]
num_samples = 100
mock_df = pd.DataFrame({
    "sample_id": range(1, num_samples+1),
    "latitude": np.random.uniform(8, 37, num_samples),
    "longitude": np.random.uniform(68, 97, num_samples),
    "species": np.random.choice(species_list, num_samples),
    "district": np.random.choice(state_list, num_samples),
    "detection_count": np.random.poisson(3, num_samples),
    "sample_date": np.random.choice(pd.date_range("2023-01-01", "2023-12-31"), num_samples)
})

# ---- Species info threading helper ----
species_info_cache = {}

def fetch_species_info(species, callback):
    def run():
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{species.replace(' ', '_')}"
        try:
            r = requests.get(url, timeout=6)
            if r.status_code == 200:
                data = r.json()
                callback({
                    "title": data.get("title", species),
                    "desc": data.get("extract", "No info found."),
                    "img": data.get("thumbnail", {}).get("source", None)
                })
                species_info_cache[species] = {
                    "title": data.get("title", species),
                    "desc": data.get("extract", "No info found."),
                    "img": data.get("thumbnail", {}).get("source", None)
                }
            else:
                callback(None)
        except Exception:
            callback(None)
    threading.Thread(target=run, daemon=True).start()

# ---- MAIN DASHBOARD APP ----
class EDNAApp(tb.Window):
    def __init__(self):
        super().__init__(themename="superhero")
        self.title("eDNA Visualization for India [Your Shape Files]")
        self.geometry("1000x650")
        self.df = mock_df.copy()
        self.filtered_df = self.df.copy()
        self.create_widgets()
        self.update_summary_plots()

    def create_widgets(self):
        notebook = tb.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # FILTER PANEL
        self.species_var = tk.Variable(value=species_list)
        self.district_var = tk.StringVar(value="All")
        self.date_from = tk.StringVar(value=str(self.df["sample_date"].min())[:10])
        self.date_to = tk.StringVar(value=str(self.df["sample_date"].max())[:10])

        frame_filter = tb.Frame(notebook)
        notebook.add(frame_filter, text="Map")

        # Sidebar controls
        subpanel = tb.Frame(frame_filter)
        subpanel.pack(side="left", fill="y", padx=8, pady=4)
        tb.Label(subpanel, text="Species:").pack(anchor="w")
        self.lb_species = tk.Listbox(subpanel, listvariable=self.species_var, selectmode="multiple", height=6)
        self.lb_species.pack(anchor="w", fill="x")
        for i in range(len(species_list)): self.lb_species.selection_set(i)
        tb.Label(subpanel, text="District:").pack(anchor="w", pady=(10,0))
        cb_state = tb.Combobox(subpanel, values=["All"]+state_list, textvariable=self.district_var, width=18)
        cb_state.pack(anchor="w")
        tb.Label(subpanel, text="Date from:").pack(anchor="w", pady=(10,0))
        tb.Entry(subpanel, textvariable=self.date_from, width=13).pack(anchor="w")
        tb.Label(subpanel, text="Date to:").pack(anchor="w", pady=(0,0))
        tb.Entry(subpanel, textvariable=self.date_to, width=13).pack(anchor="w")
        tb.Button(subpanel, text="Apply Filter", bootstyle=SUCCESS, command=self.apply_filter).pack(pady=10, anchor="w")
        tb.Button(subpanel, text="Show Map", bootstyle=INFO, command=self.show_map).pack(pady=(0,8), anchor="w")
        tb.Button(subpanel, text="Export CSV", bootstyle=WARNING, command=self.export_csv).pack(pady=2, anchor="w")

        # Species info box
        self.info_title = tb.Label(subpanel, text="", font=("Segoe UI", 12, "bold"), bootstyle=PRIMARY)
        self.info_title.pack(pady=(16,2), anchor="w")
        self.info_img = tb.Label(subpanel)
        self.info_img.pack(anchor="w")
        self.info_desc = tk.Message(subpanel, text="", width=220)
        self.info_desc.pack(anchor="w", pady=(2,8))

        # Map placeholder
        self.map_frame = tb.Frame(frame_filter)
        self.map_frame.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        tb.Label(self.map_frame, text="Map will open in your browser.", font=("Arial", 12, "italic")).pack()

        # Plots tab
        frame_plot = tb.Frame(notebook)
        self.plots_frame = frame_plot
        notebook.add(frame_plot, text="Plots")
        self.plot_species = tb.Label(frame_plot)
        self.plot_species.pack(padx=10, pady=(18,10))
        self.plot_state = tb.Label(frame_plot)
        self.plot_state.pack(padx=10, pady=(12,10))
        self.plot_date = tb.Label(frame_plot)
        self.plot_date.pack(padx=10, pady=(12,10))

        # Data table tab
        frame_table = tb.Frame(notebook)
        notebook.add(frame_table, text="Table")
        tb.Label(frame_table, text="Filtered eDNA Data", font=("Segoe UI", 12)).pack(anchor="w", padx=10, pady=4)
        frm = tb.Frame(frame_table)
        frm.pack(fill="both", expand=True)
        self.table = tb.Treeview(frm, columns=tuple(self.df.columns), show="headings", height=18)
        self.table.pack(side="left", fill="both", expand=True)
        for col in self.df.columns:
            self.table.heading(col, text=col)
            self.table.column(col, width=90)
        scroll = tb.Scrollbar(frm, orient="vertical", command=self.table.yview)
        scroll.pack(side="right", fill="y")
        self.table.configure(yscroll=scroll.set)
        self.update_table()

        # About tab
        frame_about = tb.Frame(notebook)
        notebook.add(frame_about, text="About")
        tb.Label(frame_about, text="eDNA India Dashboard (Python/Tkinter)", font=("Segoe UI", 13, "bold")).pack(pady=(20,10))
        tb.Label(frame_about, text="Features:\n- District boundary from your files\n- eDNA mock data points\n- Filter by species, district, date\n- Map in browser, export CSV, live Wikipedia species info", font=("Segoe UI", 11)).pack(pady=5)

    def apply_filter(self):
        species_sel = [self.lb_species.get(idx) for idx in self.lb_species.curselection()]
        df = self.df[self.df["species"].isin(species_sel)]
        district = self.district_var.get()
        if district != "All":
            df = df[df["district"] == district]
        try:
            d1 = pd.to_datetime(self.date_from.get())
            d2 = pd.to_datetime(self.date_to.get())
            df = df[(df["sample_date"] >= d1) & (df["sample_date"] <= d2)]
        except Exception: pass
        self.filtered_df = df
        self.update_table()
        self.update_summary_plots()

    def update_table(self):
        self.table.delete(*self.table.get_children())
        for _, row in self.filtered_df.iterrows():
            vals = [str(v) for v in row.values]
            self.table.insert("", "end", values=vals)

    def export_csv(self):
        file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if file:
            self.filtered_df.to_csv(file, index=False)
            messagebox.showinfo("Exported", f"Exported {len(self.filtered_df)} rows.")

    def show_map(self):
        if self.filtered_df.empty:
            messagebox.showinfo("No Data", "No samples to show with current filter.")
            return
        m = folium.Map(location=[22., 80.], zoom_start=5, tiles="CartoDB positron")
        # Draw district polygons
        folium.GeoJson(
            india_gdf.to_json(),
            name="Districts",
            style_function=lambda f: dict(color="blue", weight=1, fillOpacity=0.08),
            tooltip=folium.GeoJsonTooltip(fields=[state_col])
        ).add_to(m)
        # Draw points
        for ix, row in self.filtered_df.iterrows():
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=5 + row["detection_count"],
                color="red",
                fill=True, fill_color="red",
                popup=folium.Popup(f"<b>Sample:</b> {row['sample_id']}<br>"
                                   f"<b>Species:</b> {row['species']}<br>"
                                   f"<b>District:</b> {row['district']}<br>"
                                   f"<b>Date:</b> {row['sample_date']}<br>"
                                   f"<b>Detections:</b> {row['detection_count']}",
                                   max_width=300),
                tooltip=str(row["species"])
            ).add_to(m)
        m.save("edna_map.html")
        webbrowser.open("edna_map.html")

    def update_summary_plots(self):
        # By species
        fig1, ax1 = plt.subplots(figsize=(4,2.5), dpi=100)
        self.filtered_df["species"].value_counts().plot(kind="bar", ax=ax1, color="skyblue")
        ax1.set_title("Detections by Species")
        plt.tight_layout()
        buf1 = BytesIO()
        fig1.savefig(buf1, format="png")
        ax1.clear(); plt.close(fig1); self._show_img(self.plot_species, buf1)
        # By district
        fig2, ax2 = plt.subplots(figsize=(4,2.5), dpi=100)
        self.filtered_df["district"].value_counts().plot(kind="bar", ax=ax2, color="lightgreen")
        ax2.set_title("Detections by District")
        plt.tight_layout()
        buf2 = BytesIO()
        fig2.savefig(buf2, format="png")
        ax2.clear(); plt.close(fig2); self._show_img(self.plot_state, buf2)
        # By date
        fig3, ax3 = plt.subplots(figsize=(8,2.5), dpi=100)
        self.filtered_df["sample_date"].value_counts().sort_index().plot(kind="line", ax=ax3, color="tomato", marker="o")
        ax3.set_title("Samples by Date")
        plt.tight_layout()
        buf3 = BytesIO()
        fig3.savefig(buf3, format="png")
        ax3.clear(); plt.close(fig3); self._show_img(self.plot_date, buf3)

    def _show_img(self, widget, buf):
        buf.seek(0)
        img = Image.open(buf)
        img = ImageTk.PhotoImage(img)
        widget.configure(image=img)
        widget.image = img

    def lb_species_event(self, evt):
        sel = self.lb_species.curselection()
        if not sel: return
        species = self.lb_species.get(sel[0])
        self.display_species_info(species)

    def display_species_info(self, species):
        self.info_title.configure(text="Loading info...")
        self.info_img.configure(image=""); self.info_desc.configure(text="")
        if species in species_info_cache:
            info = species_info_cache[species]
            self._show_species_info(info); return
        def callback(info):
            if info: self._show_species_info(info)
            else:
                self.info_title.configure(text=species)
                self.info_img.configure(image="")
                self.info_desc.configure(text="No info found online.")
        fetch_species_info(species, callback)

    def _show_species_info(self, info):
        self.info_title.configure(text=info["title"])
        self.info_desc.configure(text=info["desc"])
        if info["img"]:
            try:
                resp = requests.get(info["img"], timeout=5)
                if resp.status_code == 200:
                    img_data = Image.open(BytesIO(resp.content)).resize((70,70))
                    imgtk = ImageTk.PhotoImage(img_data)
                    self.info_img.configure(image=imgtk)
                    self.info_img.image = imgtk
                    return
            except Exception: pass
        self.info_img.configure(image="")
        self.info_img.image = None

# ---- RUN APP ----
if __name__ == "__main__":
    app = EDNAApp()
    app.lb_species.bind('<<ListboxSelect>>', app.lb_species_event)
    app.mainloop()

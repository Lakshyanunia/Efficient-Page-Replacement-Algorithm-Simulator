import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import random
import pygame
import os
import numpy as np

class GanttChart:
    def __init__(self, master, gantt_data, algorithm, max_frames, faults, pages):
        self.window = tk.Toplevel(master)
        self.window.title(f"Gantt Chart - {algorithm}")
        self.window.geometry("1200x800")

        # Validate input data
        if not gantt_data or not faults or not pages:
            messagebox.showerror("Error", "Incomplete simulation data. Please run the simulation first.")
            self.window.destroy()
            return

        self.gantt_data = gantt_data
        self.algorithm = algorithm
        self.max_frames = max_frames
        self.faults = faults
        self.pages = pages

        print(f"GanttChart initialized with: gantt_data={len(gantt_data)}, faults={len(faults)}, pages={len(pages)}, max_frames={max_frames}, algorithm={algorithm}")

        # Main frame for tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: Gantt Chart (Static and Animated)
        self.gantt_frame = tk.Frame(self.notebook)
        self.notebook.add(self.gantt_frame, text="Gantt Chart")

        # Graph type selection for Gantt chart
        graph_type_frame = tk.Frame(self.gantt_frame)
        graph_type_frame.pack(pady=5)
        tk.Label(graph_type_frame, text="Graph Type:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.graph_type = ttk.Combobox(graph_type_frame, values=["Broken Bar", "Bar", "Histogram"], width=15)
        self.graph_type.pack(side=tk.LEFT)
        self.graph_type.set("Broken Bar")
        self.graph_type.bind("<<ComboboxSelected>>", lambda e: self.show_static_gantt())

        self.fig_gantt = plt.Figure(figsize=(12, 5), dpi=100)
        self.ax_gantt = self.fig_gantt.add_subplot(111)
        self.canvas_gantt = FigureCanvasTkAgg(self.fig_gantt, master=self.gantt_frame)
        self.canvas_gantt.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.animation = None

        # Speed control for Gantt chart animation
        speed_frame = tk.Frame(self.gantt_frame)
        speed_frame.pack(pady=5)
        self.speed = tk.IntVar(value=500)
        tk.Scale(speed_frame, from_=100, to=2000, orient=tk.HORIZONTAL, variable=self.speed,
                 label="Animation Speed (ms)", font=("Arial", 10)).pack()

        # Control buttons for Gantt chart
        button_frame = tk.Frame(self.gantt_frame)
        button_frame.pack(pady=10)
        button_style = {"width": 12, "font": ("Arial", 10, "bold")}
        self.static_btn = tk.Button(button_frame, text="Static View", command=self.show_static_gantt, bg="green", fg="white", **button_style)
        self.static_btn.pack(side=tk.LEFT, padx=5)
        self.animate_btn = tk.Button(button_frame, text="Animate", command=self.start_animation, bg="purple", fg="white", **button_style)
        self.animate_btn.pack(side=tk.LEFT, padx=5)
        self.export_btn = tk.Button(button_frame, text="Export Chart", command=self.export_chart, bg="orange", fg="white", **button_style)
        self.export_btn.pack(side=tk.LEFT, padx=5)
        self.close_btn = tk.Button(button_frame, text="Close", command=self.window.destroy, bg="red", fg="white", **button_style)
        self.close_btn.pack(side=tk.LEFT, padx=5)

        for btn in (self.static_btn, self.animate_btn, self.export_btn, self.close_btn):
            btn.default_bg = btn["bg"]
            btn.bind("<Enter>", lambda e: e.widget.config(bg="#d3d3d3"))
            btn.bind("<Leave>", lambda e: e.widget.config(bg=e.widget.default_bg))

        # Initialize pygame for sound
        pygame.mixer.init()
        try:
            self.fault_sound = pygame.mixer.Sound("fault.wav")
            self.hit_sound = pygame.mixer.Sound("hit.wav")
        except pygame.error as e:
            print(f"Error loading sound files: {e}")
            self.fault_sound = None
            self.hit_sound = None

        # Tab 2: Analysis Graphs
        self.analysis_frame = tk.Frame(self.notebook)
        self.notebook.add(self.analysis_frame, text="Analysis Graphs")

        # Sub-tabs for different analysis graphs
        self.analysis_notebook = ttk.Notebook(self.analysis_frame)
        self.analysis_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Cumulative Faults
        self.cumulative_frame = tk.Frame(self.analysis_notebook)
        self.analysis_notebook.add(self.cumulative_frame, text="Cumulative Faults")
        self.fig_cumulative = plt.Figure(figsize=(12, 5), dpi=100)
        self.ax_cumulative = self.fig_cumulative.add_subplot(111)
        self.canvas_cumulative = FigureCanvasTkAgg(self.fig_cumulative, master=self.cumulative_frame)
        self.canvas_cumulative.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Page Fault Rate
        self.fault_rate_frame = tk.Frame(self.analysis_notebook)
        self.analysis_notebook.add(self.fault_rate_frame, text="Page Fault Rate")
        self.fig_fault_rate = plt.Figure(figsize=(12, 5), dpi=100)
        self.ax_fault_rate = self.fig_fault_rate.add_subplot(111)
        self.canvas_fault_rate = FigureCanvasTkAgg(self.fig_fault_rate, master=self.fault_rate_frame)
        self.canvas_fault_rate.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Memory Utilization
        self.utilization_frame = tk.Frame(self.analysis_notebook)
        self.analysis_notebook.add(self.utilization_frame, text="Memory Utilization")
        self.fig_utilization = plt.Figure(figsize=(12, 5), dpi=100)
        self.ax_utilization = self.fig_utilization.add_subplot(111)
        self.canvas_utilization = FigureCanvasTkAgg(self.fig_utilization, master=self.utilization_frame)
        self.canvas_utilization.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Page Frequency
        self.frequency_frame = tk.Frame(self.analysis_notebook)
        self.analysis_notebook.add(self.frequency_frame, text="Page Frequency")
        self.fig_frequency = plt.Figure(figsize=(12, 5), dpi=100)
        self.ax_frequency = self.fig_frequency.add_subplot(111)
        self.canvas_frequency = FigureCanvasTkAgg(self.fig_frequency, master=self.frequency_frame)
        self.canvas_frequency.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Hit/Fault Distribution
        self.distribution_frame = tk.Frame(self.analysis_notebook)
        self.analysis_notebook.add(self.distribution_frame, text="Hit/Fault Distribution")
        self.fig_distribution = plt.Figure(figsize=(12, 5), dpi=100)
        self.ax_distribution = self.fig_distribution.add_subplot(111)
        self.canvas_distribution = FigureCanvasTkAgg(self.fig_distribution, master=self.distribution_frame)
        self.canvas_distribution.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Page Replacement Timeline
        self.timeline_frame = tk.Frame(self.analysis_notebook)
        self.analysis_notebook.add(self.timeline_frame, text="Page Replacement Timeline")
        self.fig_timeline = plt.Figure(figsize=(12, 5), dpi=100)
        self.ax_timeline = self.fig_timeline.add_subplot(111)
        self.canvas_timeline = FigureCanvasTkAgg(self.fig_timeline, master=self.timeline_frame)
        self.canvas_timeline.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Fault Distribution by Page
        self.fault_dist_frame = tk.Frame(self.analysis_notebook)
        self.analysis_notebook.add(self.fault_dist_frame, text="Fault Distribution by Page")
        self.fig_fault_dist = plt.Figure(figsize=(12, 5), dpi=100)
        self.ax_fault_dist = self.fig_fault_dist.add_subplot(111)
        self.canvas_fault_dist = FigureCanvasTkAgg(self.fig_fault_dist, master=self.fault_dist_frame)
        self.canvas_fault_dist.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Frame Occupancy Heatmap
        self.heatmap_frame = tk.Frame(self.analysis_notebook)
        self.analysis_notebook.add(self.heatmap_frame, text="Frame Occupancy Heatmap")
        self.fig_heatmap = plt.Figure(figsize=(12, 5), dpi=100)
        self.ax_heatmap = self.fig_heatmap.add_subplot(111)
        self.canvas_heatmap = FigureCanvasTkAgg(self.fig_heatmap, master=self.heatmap_frame)
        self.canvas_heatmap.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Render all analysis graphs
        self.update_analysis_graphs()

        # Show the Gantt chart initially
        self.show_static_gantt()

    def show_static_gantt(self):
        if self.animation is not None:
            self.animation.event_source.stop()
            self.animation = None
        self.ax_gantt.clear()

        graph_type = self.graph_type.get()
        print(f"Rendering static Gantt chart with {len(self.gantt_data)} steps, type={graph_type}")

        if graph_type == "Broken Bar":
            # Plot the entire history up to the last step
            for time in range(len(self.gantt_data)):
                memory, page = self.gantt_data[time][1], self.gantt_data[time][2]
                for j, p in enumerate(memory):
                    if p is not None:  # Skip None values
                        color = 'red' if p == page and self.faults[time] else 'blue'
                        self.ax_gantt.broken_barh([(time, 0.8)], (j - 0.4, 0.8), facecolors=color, edgecolors='black')
                        self.ax_gantt.text(time + 0.4, j, str(p), ha='center', va='center', color='white', fontweight='bold', fontsize=10)

        elif graph_type == "Bar":
            # Plot as a bar chart showing page occupancy over time
            for time in range(len(self.gantt_data)):
                memory, page = self.gantt_data[time][1], self.gantt_data[time][2]
                for j, p in enumerate(memory):
                    if p is not None:
                        color = 'red' if p == page and self.faults[time] else 'blue'
                        self.ax_gantt.bar(time, 1, bottom=j, width=0.8, color=color, edgecolor='black')
                        self.ax_gantt.text(time, j + 0.5, str(p), ha='center', va='center', color='white', fontweight='bold', fontsize=10)

        elif graph_type == "Histogram":
            # Plot a histogram of page faults over time
            fault_times = [i for i, fault in enumerate(self.faults) if fault]
            self.ax_gantt.hist(fault_times, bins=range(len(self.gantt_data) + 1), color='red', alpha=0.7, rwidth=0.8)
            self.ax_gantt.set_xlabel('Time', fontsize=12)
            self.ax_gantt.set_ylabel('Fault Count', fontsize=12)
            self.ax_gantt.set_title(f'Page Fault Histogram - {self.algorithm}', fontsize=14)
            self.ax_gantt.grid(True, linestyle='--', alpha=0.7)
            self.fig_gantt.tight_layout()
            self.canvas_gantt.draw()
            return

        self.format_gantt_chart()
        self.fig_gantt.tight_layout()
        self.canvas_gantt.draw()

    def start_animation(self):
        # Stop any existing animation
        if self.animation is not None:
            self.animation.event_source.stop()
            self.animation = None

        self.ax_gantt.clear()
        print(f"Starting animation with {len(self.gantt_data)} frames, interval={self.speed.get()}ms")

        # Create a new animation
        self.animation = FuncAnimation(
            self.fig_gantt,
            self.update_animation,
            frames=len(self.gantt_data),
            interval=self.speed.get(),
            repeat=False,
            blit=False
        )
        # Ensure the canvas is updated
        self.canvas_gantt.draw()

    def update_animation(self, frame):
        self.ax_gantt.clear()
        graph_type = self.graph_type.get()
        print(f"Animating frame {frame + 1}/{len(self.gantt_data)}, type={graph_type}")

        if graph_type == "Broken Bar":
            # Plot the history up to the current frame
            for time in range(frame + 1):
                memory, page = self.gantt_data[time][1], self.gantt_data[time][2]
                for j, p in enumerate(memory):
                    if p is not None:
                        color = 'red' if p == page and self.faults[time] else 'blue'
                        self.ax_gantt.broken_barh([(time, 0.8)], (j - 0.4, 0.8), facecolors=color, edgecolors='black')
                        self.ax_gantt.text(time + 0.4, j, str(p), ha='center', va='center', color='white', fontweight='bold', fontsize=10)

        elif graph_type == "Bar":
            for time in range(frame + 1):
                memory, page = self.gantt_data[time][1], self.gantt_data[time][2]
                for j, p in enumerate(memory):
                    if p is not None:
                        color = 'red' if p == page and self.faults[time] else 'blue'
                        self.ax_gantt.bar(time, 1, bottom=j, width=0.8, color=color, edgecolor='black')
                        self.ax_gantt.text(time, j + 0.5, str(p), ha='center', va='center', color='white', fontweight='bold', fontsize=10)

        elif graph_type == "Histogram":
            fault_times = [i for i, fault in enumerate(self.faults[:frame + 1]) if fault]
            self.ax_gantt.hist(fault_times, bins=range(frame + 2), color='red', alpha=0.7, rwidth=0.8)
            self.ax_gantt.set_xlabel('Time', fontsize=12)
            self.ax_gantt.set_ylabel('Fault Count', fontsize=12)
            self.ax_gantt.set_title(f'Page Fault Histogram - {self.algorithm} (Step {frame + 1}/{len(self.gantt_data)})', fontsize=14)
            self.ax_gantt.grid(True, linestyle='--', alpha=0.7)
            self.fig_gantt.tight_layout()
            return

        # Play sound if available
        if self.fault_sound and self.hit_sound:
            try:
                if self.faults[frame]:
                    self.fault_sound.play()
                else:
                    self.hit_sound.play()
            except Exception as e:
                print(f"Error playing sound: {e}")

        self.format_gantt_chart(f" (Step {frame + 1}/{len(self.gantt_data)})")
        self.fig_gantt.tight_layout()

    def format_gantt_chart(self, extra_title=""):
        self.ax_gantt.set_xlim(-0.5, len(self.gantt_data))
        self.ax_gantt.set_ylim(-0.5, self.max_frames - 0.5)
        self.ax_gantt.set_xlabel('Time', fontsize=12, labelpad=10)
        self.ax_gantt.set_ylabel('Frames', fontsize=12, labelpad=10)
        self.ax_gantt.set_yticks(range(self.max_frames))
        self.ax_gantt.set_yticklabels([f"Frame {i+1}" for i in range(self.max_frames)], fontsize=10)
        self.ax_gantt.set_xticks(range(len(self.gantt_data)))
        self.ax_gantt.set_title(f'Gantt Chart - {self.algorithm}{extra_title}', fontsize=14, pad=15)
        self.ax_gantt.grid(True, linestyle='--', alpha=0.7)

    def update_analysis_graphs(self):
        try:
            # Cumulative Faults
            self.ax_cumulative.clear()
            cumulative_faults = [0]
            fault_count = 0
            for i in range(len(self.gantt_data)):
                fault = self.faults[i]
                fault_count += 1 if fault else 0
                cumulative_faults.append(fault_count)
            self.ax_cumulative.plot(range(len(cumulative_faults)), cumulative_faults, marker='o', color='red', label='Cumulative Faults')
            self.ax_cumulative.set_xlabel('Time', fontsize=12)
            self.ax_cumulative.set_ylabel('Cumulative Faults', fontsize=12)
            self.ax_cumulative.set_title('Cumulative Faults Over Time', fontsize=14)
            self.ax_cumulative.grid(True, linestyle='--', alpha=0.7)
            self.ax_cumulative.legend()
            self.fig_cumulative.tight_layout()
            self.canvas_cumulative.draw()

            # Page Fault Rate
            self.ax_fault_rate.clear()
            window_size = 5
            fault_counts = [1 if fault else 0 for fault in self.faults]
            fault_rate = []
            for i in range(len(fault_counts)):
                start = max(0, i - window_size + 1)
                window = fault_counts[start:i+1]
                rate = sum(window) / len(window)
                fault_rate.append(rate)
            self.ax_fault_rate.plot(range(len(fault_rate)), fault_rate, marker='o', color='purple', label='Fault Rate')
            self.ax_fault_rate.set_xlabel('Time', fontsize=12)
            self.ax_fault_rate.set_ylabel('Fault Rate', fontsize=12)
            self.ax_fault_rate.set_title('Page Fault Rate Over Time (Moving Average)', fontsize=14)
            self.ax_fault_rate.grid(True, linestyle='--', alpha=0.7)
            self.ax_fault_rate.legend()
            self.fig_fault_rate.tight_layout()
            self.canvas_fault_rate.draw()

            # Memory Utilization
            self.ax_utilization.clear()
            utilization = []
            for time, memory, _ in self.gantt_data:
                utilization.append(len([p for p in memory if p is not None]) if memory else 0)
            self.ax_utilization.bar(range(len(utilization)), utilization, color='green', alpha=0.7)
            self.ax_utilization.set_xlabel('Time', fontsize=12)
            self.ax_utilization.set_ylabel('Frames in Use', fontsize=12)
            self.ax_utilization.set_title('Memory Utilization Over Time', fontsize=14)
            self.ax_utilization.set_ylim(0, self.max_frames + 1)
            self.ax_utilization.grid(True, linestyle='--', alpha=0.7)
            self.fig_utilization.tight_layout()
            self.canvas_utilization.draw()

            # Page Frequency
            self.ax_frequency.clear()
            if self.pages:
                self.ax_frequency.hist(self.pages, bins=range(min(self.pages), max(self.pages) + 2), color='blue', alpha=0.7, rwidth=0.8)
                self.ax_frequency.set_xlabel('Page Number', fontsize=12)
                self.ax_frequency.set_ylabel('Frequency', fontsize=12)
                self.ax_frequency.set_title('Page Frequency in Reference String', fontsize=14)
                self.ax_frequency.grid(True, linestyle='--', alpha=0.7)
            else:
                self.ax_frequency.set_title('Page Frequency - No Data', fontsize=14)
            self.fig_frequency.tight_layout()
            self.canvas_frequency.draw()

            # Hit/Fault Distribution
            self.ax_distribution.clear()
            faults_count = sum(1 for fault in self.faults if fault)
            hits_count = len(self.faults) - faults_count
            labels = ['Faults', 'Hits']
            sizes = [faults_count, hits_count]
            colors = ['red', 'green']
            self.ax_distribution.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
            self.ax_distribution.set_title('Hit/Fault Distribution', fontsize=14)
            self.fig_distribution.tight_layout()
            self.canvas_distribution.draw()

            # Page Replacement Timeline (Stacked Area Chart)
            self.ax_timeline.clear()
            unique_pages = sorted(set(self.pages))
            timeline_data = {page: [] for page in unique_pages}
            for time, memory, _ in self.gantt_data:
                page_counts = {page: 0 for page in unique_pages}
                for page in memory:
                    if page is not None:
                        page_counts[page] += 1
                for page in unique_pages:
                    timeline_data[page].append(page_counts[page])

            stack_data = np.array([timeline_data[page] for page in unique_pages])
            self.ax_timeline.stackplot(range(len(self.gantt_data)), stack_data, labels=[f"Page {page}" for page in unique_pages], alpha=0.7)
            self.ax_timeline.set_xlabel('Time', fontsize=12)
            self.ax_timeline.set_ylabel('Frame Occupancy', fontsize=12)
            self.ax_timeline.set_title('Page Replacement Timeline', fontsize=14)
            self.ax_timeline.legend(loc='upper right', bbox_to_anchor=(1.15, 1))
            self.ax_timeline.grid(True, linestyle='--', alpha=0.7)
            self.fig_timeline.tight_layout()
            self.canvas_timeline.draw()

            # Fault Distribution by Page
            self.ax_fault_dist.clear()
            fault_counts = {page: 0 for page in set(self.pages)}
            for i, page in enumerate(self.pages):
                if self.faults[i]:
                    fault_counts[page] += 1
            pages_sorted = sorted(fault_counts.keys())
            fault_values = [fault_counts[page] for page in pages_sorted]
            self.ax_fault_dist.bar(pages_sorted, fault_values, color='orange', alpha=0.7)
            self.ax_fault_dist.set_xlabel('Page Number', fontsize=12)
            self.ax_fault_dist.set_ylabel('Number of Faults', fontsize=12)
            self.ax_fault_dist.set_title('Fault Distribution by Page', fontsize=14)
            self.ax_fault_dist.grid(True, linestyle='--', alpha=0.7)
            self.fig_fault_dist.tight_layout()
            self.canvas_fault_dist.draw()

            # Frame Occupancy Heatmap
            self.ax_heatmap.clear()
            frame_occupancy = np.zeros((self.max_frames, len(self.gantt_data)))
            unique_pages = sorted(set(self.pages))
            page_to_idx = {page: idx for idx, page in enumerate(unique_pages)}
            for time, memory, _ in self.gantt_data:
                for frame_idx, page in enumerate(memory):
                    if page in page_to_idx:
                        frame_occupancy[frame_idx, time] = page_to_idx[page] + 1  # +1 to avoid 0 for colormap

            im = self.ax_heatmap.imshow(frame_occupancy, aspect='auto', cmap='viridis', interpolation='nearest')
            self.ax_heatmap.set_xlabel('Time', fontsize=12)
            self.ax_heatmap.set_ylabel('Frame', fontsize=12)
            self.ax_heatmap.set_title('Frame Occupancy Heatmap', fontsize=14)
            self.ax_heatmap.set_yticks(range(self.max_frames))
            self.ax_heatmap.set_yticklabels([f"Frame {i+1}" for i in range(self.max_frames)])
            self.ax_heatmap.set_xticks(range(len(self.gantt_data)))
            self.fig_heatmap.colorbar(im, label='Page Number', ticks=range(1, len(unique_pages) + 1),
                                     format=plt.FuncFormatter(lambda x, _: unique_pages[int(x)-1] if int(x) > 0 else ""))
            self.fig_heatmap.tight_layout()
            self.canvas_heatmap.draw()

        except Exception as e:
            print(f"Error in update_analysis_graphs: {e}")
            messagebox.showerror("Error", f"Failed to render analysis graphs: {str(e)}")

    def export_chart(self):
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 0:  # Gantt Chart tab
            fig_to_save = self.fig_gantt
        else:
            # Analysis tab
            analysis_tab = self.analysis_notebook.index(self.analysis_notebook.select())
            figs = [self.fig_cumulative, self.fig_fault_rate, self.fig_utilization, self.fig_frequency,
                    self.fig_distribution, self.fig_timeline, self.fig_fault_dist, self.fig_heatmap]
            fig_to_save = figs[analysis_tab]

        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
        if file_path:
            fig_to_save.savefig(file_path, bbox_inches='tight')
            messagebox.showinfo("Success", f"Chart exported to {file_path}")

class PageReplacementSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Page Replacement Simulator")
        self.root.geometry("900x800")

        self.style = ttk.Style()
        self.define_themes()
        self.current_theme = self.load_theme()
        self.style.theme_use(self.current_theme)
        self.root.configure(bg=self.style.lookup("TFrame", "background"))

        self.undo_stack = []
        self.redo_stack = []
        self.last_page_entry = ""
        self.last_frame_entry = ""

        main_frame = tk.Frame(self.root, bg=self.style.lookup("TFrame", "background"))
        main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        theme_frame = tk.Frame(main_frame, bg=self.style.lookup("TFrame", "background"))
        theme_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(theme_frame, text="Theme:", bg=self.style.lookup("TFrame", "background"), font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.theme_choice = ttk.Combobox(theme_frame, values=["Light", "Dark", "Ocean", "Forest", "Sunset"], width=10)
        self.theme_choice.pack(side=tk.LEFT)
        self.theme_choice.set(self.current_theme)
        self.theme_choice.bind("<<ComboboxSelected>>", self.change_theme)

        input_frame = ttk.LabelFrame(main_frame, text="Input Parameters", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        self.page_entry_var = tk.StringVar()
        ttk.Label(input_frame, text="Page Reference String (comma-separated):", font=("Arial", 10)).grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.page_entry = ttk.Entry(input_frame, width=50, font=("Arial", 10), textvariable=self.page_entry_var)
        self.page_entry.grid(row=0, column=1, padx=5, pady=5)
        self.page_entry_var.trace("w", self.validate_entry)

        ttk.Label(input_frame, text="Number of Frames:", font=("Arial", 10)).grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.frame_entry = ttk.Entry(input_frame, width=10, font=("Arial", 10))
        self.frame_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        undo_redo_frame = tk.Frame(input_frame, bg=self.style.lookup("TFrame", "background"))
        undo_redo_frame.grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(undo_redo_frame, text="Undo", command=self.undo).pack(side=tk.LEFT, padx=2)
        ttk.Button(undo_redo_frame, text="Redo", command=self.redo).pack(side=tk.LEFT, padx=2)

        algo_frame = tk.Frame(input_frame, bg=self.style.lookup("TFrame", "background"))
        algo_frame.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(input_frame, text="Select Algorithm:", font=("Arial", 10)).grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.algo_choice = ttk.Combobox(algo_frame, values=["FIFO", "LRU", "Optimal", "Custom"], width=20, font=("Arial", 10))
        self.algo_choice.pack(side=tk.LEFT)
        self.algo_choice.set("FIFO")
        ttk.Button(algo_frame, text="Explain", command=self.explain_algorithm).pack(side=tk.LEFT, padx=5)

        button_frame = tk.Frame(main_frame, bg=self.style.lookup("TFrame", "background"))
        button_frame.pack(pady=10)
        button_style = {"width": 20, "font": ("Arial", 10, "bold")}
        self.simulate_btn = tk.Button(button_frame, text="Simulate", command=self.run_simulation, bg="blue", fg="white", **button_style)
        self.simulate_btn.grid(row=0, column=0, padx=10)
        self.random_btn = tk.Button(button_frame, text="Generate Random", command=self.open_random_generator, bg="orange", fg="white", **button_style)
        self.random_btn.grid(row=0, column=1, padx=10)
        self.view_btn = tk.Button(button_frame, text="View Chart", command=self.view_chart, state=tk.DISABLED, bg="green", fg="white", **button_style)
        self.view_btn.grid(row=0, column=2, padx=10)
        self.step_btn = tk.Button(button_frame, text="Step Through", command=self.interactive_step_through, bg="cyan", fg="white", **button_style)
        self.step_btn.grid(row=1, column=0, padx=10, pady=5)
        self.compare_btn = tk.Button(button_frame, text="Compare All", command=self.compare_algorithms, bg="purple", fg="white", **button_style)
        self.compare_btn.grid(row=1, column=1, padx=10, pady=5)
        self.batch_btn = tk.Button(button_frame, text="Batch Process", command=self.batch_process, bg="magenta", fg="white", **button_style)
        self.batch_btn.grid(row=1, column=2, padx=10, pady=5)
        self.help_btn = tk.Button(button_frame, text="Help", command=self.show_help, bg="gray", fg="white", **button_style)
        self.help_btn.grid(row=2, column=0, padx=10, pady=5)
        self.save_btn = tk.Button(button_frame, text="Save Results", command=self.save_results, bg="teal", fg="white", **button_style)
        self.save_btn.grid(row=2, column=1, padx=10, pady=5)
        self.load_btn = tk.Button(button_frame, text="Load Input", command=self.load_input, bg="brown", fg="white", **button_style)
        self.load_btn.grid(row=2, column=2, padx=10, pady=5)

        for btn in (self.simulate_btn, self.random_btn, self.view_btn, self.step_btn,
                   self.compare_btn, self.batch_btn, self.help_btn, self.save_btn, self.load_btn):
            btn.default_bg = btn["bg"]
            btn.bind("<Enter>", lambda e: e.widget.config(bg="#d3d3d3"))
            btn.bind("<Leave>", lambda e: e.widget.config(bg=e.widget.default_bg))

        output_frame = ttk.LabelFrame(main_frame, text="Simulation Results", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.output_text = tk.Text(output_frame, height=15, width=80, font=("Courier", 10))
        self.output_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        self.stats_frame = ttk.LabelFrame(main_frame, text="Statistics", padding=10)
        self.stats_frame.pack(fill=tk.X, pady=(10, 0))
        self.hit_label = ttk.Label(self.stats_frame, text="Hit Ratio: N/A", font=("Arial", 10))
        self.hit_label.pack()
        self.fault_label = ttk.Label(self.stats_frame, text="Fault Rate: N/A", font=("Arial", 10))
        self.fault_label.pack()

        self.gantt_data = None
        self.algorithm = None
        self.max_frames = 0
        self.faults = []
        self.pages = []
        self.custom_algorithm_code = None

    def define_themes(self):
        self.style.theme_create("Light", parent="clam", settings={
            "TFrame": {"configure": {"background": "#f0f0f0"}},
            "TLabel": {"configure": {"background": "#f0f0f0", "foreground": "#333333", "font": ("Arial", 10)}},
            "TLabelFrame": {"configure": {"background": "#f0f0f0", "foreground": "#333333", "font": ("Arial", 12, "bold")}},
            "TLabelFrame.Label": {"configure": {"background": "#f0f0f0", "foreground": "#333333"}},
            "TEntry": {"configure": {"fieldbackground": "#ffffff", "foreground": "#333333", "font": ("Arial", 10)}},
            "TCombobox": {"configure": {"fieldbackground": "#ffffff", "foreground": "#333333", "font": ("Arial", 10),
                                        "selectbackground": "#d3d3d3", "selectforeground": "#333333"}},
            "TText": {"configure": {"background": "#ffffff", "foreground": "#333333", "font": ("Courier", 10)}}
        })

        self.style.theme_create("Dark", parent="clam", settings={
            "TFrame": {"configure": {"background": "#2b2b2b"}},
            "TLabel": {"configure": {"background": "#2b2b2b", "foreground": "#e0e0e0", "font": ("Helvetica", 10)}},
            "TLabelFrame": {"configure": {"background": "#2b2b2b", "foreground": "#e0e0e0", "font": ("Helvetica", 12, "bold")}},
            "TLabelFrame.Label": {"configure": {"background": "#2b2b2b", "foreground": "#e0e0e0"}},
            "TEntry": {"configure": {"fieldbackground": "#3c3c3c", "foreground": "#e0e0e0", "font": ("Helvetica", 10)}},
            "TCombobox": {"configure": {"fieldbackground": "#3c3c3c", "foreground": "#e0e0e0", "font": ("Helvetica", 10),
                                        "selectbackground": "#555555", "selectforeground": "#e0e0e0"}},
            "TText": {"configure": {"background": "#3c3c3c", "foreground": "#e0e0e0", "font": ("Courier", 10)}}
        })

        self.style.theme_create("Ocean", parent="clam", settings={
            "TFrame": {"configure": {"background": "#e0f7fa"}},
            "TLabel": {"configure": {"background": "#e0f7fa", "foreground": "#01579b", "font": ("Verdana", 10)}},
            "TLabelFrame": {"configure": {"background": "#e0f7fa", "foreground": "#01579b", "font": ("Verdana", 12, "bold")}},
            "TLabelFrame.Label": {"configure": {"background": "#e0f7fa", "foreground": "#01579b"}},
            "TEntry": {"configure": {"fieldbackground": "#ffffff", "foreground": "#01579b", "font": ("Verdana", 10)}},
            "TCombobox": {"configure": {"fieldbackground": "#ffffff", "foreground": "#01579b", "font": ("Verdana", 10),
                                        "selectbackground": "#b3e5fc", "selectforeground": "#01579b"}},
            "TText": {"configure": {"background": "#ffffff", "foreground": "#01579b", "font": ("Courier", 10)}}
        })

        self.style.theme_create("Forest", parent="clam", settings={
            "TFrame": {"configure": {"background": "#e8f5e9"}},
            "TLabel": {"configure": {"background": "#e8f5e9", "foreground": "#2e7d32", "font": ("Georgia", 10)}},
            "TLabelFrame": {"configure": {"background": "#e8f5e9", "foreground": "#2e7d32", "font": ("Georgia", 12, "bold")}},
            "TLabelFrame.Label": {"configure": {"background": "#e8f5e9", "foreground": "#2e7d32"}},
            "TEntry": {"configure": {"fieldbackground": "#ffffff", "foreground": "#2e7d32", "font": ("Georgia", 10)}},
            "TCombobox": {"configure": {"fieldbackground": "#ffffff", "foreground": "#2e7d32", "font": ("Georgia", 10),
                                        "selectbackground": "#c8e6c9", "selectforeground": "#2e7d32"}},
            "TText": {"configure": {"background": "#ffffff", "foreground": "#2e7d32", "font": ("Courier", 10)}}
        })

        self.style.theme_create("Sunset", parent="clam", settings={
            "TFrame": {"configure": {"background": "#fff3e0"}},
            "TLabel": {"configure": {"background": "#fff3e0", "foreground": "#e65100", "font": ("Trebuchet MS", 10)}},
            "TLabelFrame": {"configure": {"background": "#fff3e0", "foreground": "#e65100", "font": ("Trebuchet MS", 12, "bold")}},
            "TLabelFrame.Label": {"configure": {"background": "#fff3e0", "foreground": "#e65100"}},
            "TEntry": {"configure": {"fieldbackground": "#ffffff", "foreground": "#e65100", "font": ("Trebuchet MS", 10)}},
            "TCombobox": {"configure": {"fieldbackground": "#ffffff", "foreground": "#e65100", "font": ("Trebuchet MS", 10),
                                        "selectbackground": "#ffe0b2", "selectforeground": "#e65100"}},
            "TText": {"configure": {"background": "#ffffff", "foreground": "#e65100", "font": ("Courier", 10)}}
        })

    def load_theme(self):
        try:
            with open("config.txt", "r") as f:
                for line in f:
                    if line.startswith("theme="):
                        theme = line.strip().split("=")[1]
                        if theme in ["Light", "Dark", "Ocean", "Forest", "Sunset"]:
                            return theme
        except FileNotFoundError:
            pass
        return "Light"

    def save_theme(self):
        with open("config.txt", "w") as f:
            f.write(f"theme={self.current_theme}\n")

    def change_theme(self, event=None):
        selected_theme = self.theme_choice.get()
        if selected_theme != self.current_theme:
            self.style.theme_use(selected_theme)
            self.current_theme = selected_theme
            self.root.configure(bg=self.style.lookup("TFrame", "background"))
            for widget in self.root.winfo_children():
                self.update_widget_background(widget)
            self.save_theme()

    def update_widget_background(self, widget):
        if isinstance(widget, (tk.Frame, ttk.LabelFrame, tk.Label, ttk.Label)):
            widget.configure(bg=self.style.lookup("TFrame", "background"))
        for child in widget.winfo_children():
            self.update_widget_background(child)

    def validate_entry(self, *args):
        value = self.page_entry_var.get()
        if not value:
            return
        if not all(c.isdigit() or c in ", " for c in value):
            self.page_entry.delete(0, tk.END)
            self.page_entry.insert(0, "".join(c for c in value if c.isdigit() or c in ", "))
        current_page = self.page_entry.get()
        current_frame = self.frame_entry.get()
        if current_page != self.last_page_entry or current_frame != self.last_frame_entry:
            self.undo_stack.append((self.last_page_entry, self.last_frame_entry))
            self.redo_stack.clear()
            self.last_page_entry = current_page
            self.last_frame_entry = current_frame

    def undo(self):
        if not self.undo_stack:
            return
        current_page = self.page_entry.get()
        current_frame = self.frame_entry.get()
        self.redo_stack.append((current_page, current_frame))
        last_state = self.undo_stack.pop()
        self.page_entry.delete(0, tk.END)
        self.page_entry.insert(0, last_state[0])
        self.frame_entry.delete(0, tk.END)
        self.frame_entry.insert(0, last_state[1])
        self.last_page_entry = last_state[0]
        self.last_frame_entry = last_state[1]

    def redo(self):
        if not self.redo_stack:
            return
        current_page = self.page_entry.get()
        current_frame = self.frame_entry.get()
        self.undo_stack.append((current_page, current_frame))
        next_state = self.redo_stack.pop()
        self.page_entry.delete(0, tk.END)
        self.page_entry.insert(0, next_state[0])
        self.frame_entry.delete(0, tk.END)
        self.frame_entry.insert(0, next_state[1])
        self.last_page_entry = next_state[0]
        self.last_frame_entry = next_state[1]

    def open_random_generator(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Custom Random Page Reference Generator")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="String Length (5-50):", font=("Arial", 10)).pack(pady=5)
        length_entry = ttk.Entry(dialog, width=10)
        length_entry.pack()
        length_entry.insert(0, "10")

        ttk.Label(dialog, text="Page Number Range:", font=("Arial", 10)).pack(pady=5)
        range_frame = tk.Frame(dialog)
        range_frame.pack()
        ttk.Label(range_frame, text="Min (1-10):", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        min_entry = ttk.Entry(range_frame, width=5)
        min_entry.pack(side=tk.LEFT)
        min_entry.insert(0, "1")
        ttk.Label(range_frame, text="Max (1-20):", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        max_entry = ttk.Entry(range_frame, width=5)
        max_entry.pack(side=tk.LEFT)
        max_entry.insert(0, "9")

        locality_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(dialog, text="Enable Locality of Reference", variable=locality_var).pack(pady=10)

        ttk.Label(dialog, text="Number of Frames (2-10):", font=("Arial", 10)).pack(pady=5)
        frames_entry = ttk.Entry(dialog, width=10)
        frames_entry.pack()
        frames_entry.insert(0, "4")

        def generate():
            try:
                length = int(length_entry.get())
                min_page = int(min_entry.get())
                max_page = int(max_entry.get())
                frames = int(frames_entry.get())

                if not (5 <= length <= 50):
                    raise ValueError("String length must be between 5 and 50.")
                if not (1 <= min_page <= 10) or not (1 <= max_page <= 20) or min_page > max_page:
                    raise ValueError("Invalid page number range. Min (1-10), Max (1-20), Min <= Max.")
                if not (2 <= frames <= 10):
                    raise ValueError("Number of frames must be between 2 and 10.")

                if locality_var.get():
                    pages = []
                    recent_pages = []
                    for _ in range(length):
                        if random.random() < 0.7 and recent_pages:
                            page = random.choice(recent_pages[-5:])
                        else:
                            page = random.randint(min_page, max_page)
                        pages.append(page)
                        recent_pages.append(page)
                else:
                    pages = [random.randint(min_page, max_page) for _ in range(length)]

                self.page_entry.delete(0, tk.END)
                self.page_entry.insert(0, ", ".join(map(str, pages)))
                self.frame_entry.delete(0, tk.END)
                self.frame_entry.insert(0, str(frames))
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Error", str(e), parent=dialog)

        ttk.Button(dialog, text="Generate", command=generate).pack(pady=20)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()

    def explain_algorithm(self):
        algo = self.algo_choice.get()
        explanations = {
            "FIFO": ("First In First Out (FIFO)",
                     "Replaces the oldest page in memory.\n\n"
                     "Advantages:\n- Simple to implement\n- Low overhead\n\n"
                     "Disadvantages:\n- May suffer from Belady's anomaly (more frames can lead to more faults)\n- Does not consider page usage frequency"),
            "LRU": ("Least Recently Used (LRU)",
                    "Replaces the page that has not been used for the longest time.\n\n"
                    "Advantages:\n- Considers page usage history\n- Generally performs well\n\n"
                    "Disadvantages:\n- Requires tracking of page usage (higher overhead)\n- Can be complex to implement efficiently"),
            "Optimal": ("Optimal Page Replacement",
                       "Replaces the page that will not be used for the longest time in the future.\n\n"
                       "Advantages:\n- Theoretically the best performance\n- Minimizes page faults\n\n"
                       "Disadvantages:\n- Requires future knowledge (not practical in real systems)\n- Used mainly for comparison"),
            "Custom": ("Custom Algorithm",
                       "User-defined algorithm.\n\n"
                       "Define your own page replacement logic by writing a Python function.\n"
                       "The function should take 'pages' and 'frames' as input and return (result, faults, gantt_data).")
        }
        title, explanation = explanations.get(algo, ("Unknown Algorithm", "No explanation available."))
        messagebox.showinfo(title, explanation)

    def run_simulation(self):
        try:
            if not self.page_entry.get().strip() or not self.frame_entry.get().strip():
                messagebox.showerror("Error", "Please provide both page references and frame number!")
                return

            pages = [int(x.strip()) for x in self.page_entry.get().split(",") if x.strip()]
            if not pages:
                raise ValueError("No valid page numbers provided")

            frames = int(self.frame_entry.get())
            self.algorithm = self.algo_choice.get()
            self.max_frames = frames
            self.pages = pages

            if frames <= 0:
                messagebox.showerror("Error", "Frames must be a positive number!")
                return

            print(f"Running simulation with pages={pages}, frames={frames}, algorithm={self.algorithm}")

            if self.algorithm == "FIFO":
                result, faults, self.gantt_data, self.faults = self.fifo(pages, frames)
            elif self.algorithm == "LRU":
                result, faults, self.gantt_data, self.faults = self.lru(pages, frames)
            elif self.algorithm == "Optimal":
                result, faults, self.gantt_data, self.faults = self.optimal(pages, frames)
            elif self.algorithm == "Custom":
                if not self.custom_algorithm_code:
                    self.define_custom_algorithm()
                    if not self.custom_algorithm_code:
                        messagebox.showerror("Error", "No custom algorithm defined!")
                        return
                result, faults, self.gantt_data, self.faults = self.run_custom_algorithm(pages, frames)
            else:
                messagebox.showerror("Error", "Invalid algorithm selected!")
                return

            print(f"Simulation completed: faults={faults}, gantt_data length={len(self.gantt_data)}")

            self.display_result(result, faults, self.algorithm)
            self.view_btn.config(state=tk.NORMAL)
        except ValueError as e:
            if "list.remove" in str(e):
                messagebox.showerror("Error", "An error occurred in the simulation: Page not found in memory.")
            else:
                messagebox.showerror("Error", f"Invalid input! {str(e)}. Ensure numbers are separated by commas and are valid.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

    def fifo(self, pages, frames):
        memory, page_faults, result, gantt_data, faults = [], 0, [], [], []
        for i, page in enumerate(pages):
            fault = page not in memory
            if fault:
                if len(memory) < frames:
                    memory.append(page)
                else:
                    memory.pop(0)
                    memory.append(page)
                page_faults += 1
            # Pad memory with None to ensure consistent length
            memory_padded = memory + [None] * (frames - len(memory))
            result.append(f"Page: {page:2d} | Memory: {memory_padded} | {'Fault' if fault else 'Hit'}")
            gantt_data.append((i, memory_padded, page))
            faults.append(fault)
        return result, page_faults, gantt_data, faults

    def lru(self, pages, frames):
        memory, page_faults, result, recent, gantt_data, faults = [], 0, [], {}, [], []
        for i, page in enumerate(pages):
            fault = page not in memory
            if fault:
                if len(memory) < frames:
                    memory.append(page)
                else:
                    lru_page = min(recent, key=recent.get)
                    memory.remove(lru_page)
                    del recent[lru_page]
                    memory.append(page)
                page_faults += 1
            recent[page] = i
            memory_padded = memory + [None] * (frames - len(memory))
            result.append(f"Page: {page:2d} | Memory: {memory_padded} | {'Fault' if fault else 'Hit'}")
            gantt_data.append((i, memory_padded, page))
            faults.append(fault)
        return result, page_faults, gantt_data, faults

    def optimal(self, pages, frames):
        memory, page_faults, result, gantt_data, faults = [], 0, [], [], []
        for i, page in enumerate(pages):
            fault = page not in memory
            if fault:
                if len(memory) < frames:
                    memory.append(page)
                else:
                    future = {p: (pages[i+1:].index(p) if p in pages[i+1:] else float('inf')) for p in memory}
                    memory.remove(max(future, key=future.get))
                    memory.append(page)
                page_faults += 1
            memory_padded = memory + [None] * (frames - len(memory))
            result.append(f"Page: {page:2d} | Memory: {memory_padded} | {'Fault' if fault else 'Hit'}")
            gantt_data.append((i, memory_padded, page))
            faults.append(fault)
        return result, page_faults, gantt_data, faults

    def define_custom_algorithm(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Define Custom Algorithm")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Write your custom algorithm (Python code):", font=("Arial", 10)).pack(pady=5)
        ttk.Label(dialog, text="Function must be named 'custom_algorithm' and take 'pages' and 'frames' as arguments.\n"
                              "Return (result, faults, gantt_data, faults_list).", font=("Arial", 8)).pack()
        code_text = tk.Text(dialog, height=15, width=70, font=("Courier", 10))
        code_text.pack(pady=5)
        code_text.insert(tk.END, "# Example custom algorithm (similar to FIFO)\n"
                                "def custom_algorithm(pages, frames):\n"
                                "    memory, page_faults, result, gantt_data, faults = [], 0, [], [], []\n"
                                "    for i, page in enumerate(pages):\n"
                                "        fault = page not in memory\n"
                                "        if fault:\n"
                                "            if len(memory) < frames:\n"
                                "                memory.append(page)\n"
                                "            else:\n"
                                "                memory.pop(0)\n"
                                "                memory.append(page)\n"
                                "            page_faults += 1\n"
                                "        memory_padded = memory + [None] * (frames - len(memory))\n"
                                "        result.append(f'Page: {page:2d} | Memory: {memory_padded} | {'Fault' if fault else 'Hit'}')\n"
                                "        gantt_data.append((i, memory_padded, page))\n"
                                "        faults.append(fault)\n"
                                "    return result, page_faults, gantt_data, faults")

        def save_code():
            self.custom_algorithm_code = code_text.get("1.0", tk.END).strip()
            dialog.destroy()

        ttk.Button(dialog, text="Save", command=save_code).pack(pady=10)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()

    def run_custom_algorithm(self, pages, frames):
        if not self.custom_algorithm_code:
            raise ValueError("Custom algorithm not defined")
        try:
            local_vars = {}
            exec(self.custom_algorithm_code, globals(), local_vars)
            custom_func = local_vars.get("custom_algorithm")
            if not callable(custom_func):
                raise ValueError("Custom algorithm function 'custom_algorithm' not found")
            return custom_func(pages, frames)
        except Exception as e:
            raise ValueError(f"Error in custom algorithm: {str(e)}")

    def display_result(self, result, faults, algorithm):
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, f"Algorithm: {algorithm}\n")
        self.output_text.insert(tk.END, "\n".join(result))
        self.output_text.insert(tk.END, f"\n\nTotal Page Faults: {faults}")
        self.display_stats(faults, len(result))

    def display_stats(self, faults, total_pages):
        hit_ratio = (total_pages - faults) / total_pages * 100 if total_pages > 0 else 0
        fault_rate = (faults / total_pages * 100) if total_pages > 0 else 0
        self.hit_label.config(text=f"Hit Ratio: {hit_ratio:.2f}%")
        self.fault_label.config(text=f"Fault Rate: {fault_rate:.2f}%")

    def interactive_step_through(self):
        if not self.gantt_data:
            messagebox.showinfo("Info", "No simulation data available. Run simulation first.")
            return

        step_window = tk.Toplevel(self.root)
        step_window.title("Interactive Step-by-Step")
        step_window.geometry("900x750")

        graph_frame = tk.Frame(step_window)
        graph_frame.pack(pady=5)
        tk.Label(graph_frame, text="Analysis Graph:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.step_graph_choice = ttk.Combobox(graph_frame, values=[
            "Cumulative Faults", "Page Fault Rate", "Memory Utilization", "Page Frequency", "Hit/Fault Distribution"
        ], width=20)
        self.step_graph_choice.pack(side=tk.LEFT)
        self.step_graph_choice.set("Cumulative Faults")

        chart_frame = tk.Frame(step_window)
        chart_frame.pack(fill=tk.BOTH, expand=True)
        self.fig = plt.Figure(figsize=(12, 7), dpi=100)
        self.ax_gantt = self.fig.add_subplot(211)
        self.ax_fault = self.fig.add_subplot(212)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        text_frame = tk.Frame(step_window)
        text_frame.pack(fill=tk.X, pady=5)
        self.step_text = tk.Text(text_frame, height=5, width=80, font=("Courier", 10))
        self.step_text.pack(pady=5)

        nav_frame = tk.Frame(step_window)
        nav_frame.pack(pady=5)
        ttk.Button(nav_frame, text="Previous", command=lambda: self.update_step(-1)).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Next", command=lambda: self.update_step(1)).pack(side=tk.LEFT, padx=5)

        pygame.mixer.init()
        try:
            self.fault_sound = pygame.mixer.Sound("fault.wav")
            self.hit_sound = pygame.mixer.Sound("hit.wav")
        except pygame.error as e:
            print(f"Error loading sound files: {e}")
            self.fault_sound = None
            self.hit_sound = None

        self.current_step = 0
        self.update_step(0)

    def update_step(self, direction):
        new_step = self.current_step + direction
        if 0 <= new_step < len(self.gantt_data):
            self.current_step = new_step
            self.ax_gantt.clear()
            self.ax_fault.clear()

            # Plot Gantt chart up to the current step
            for time in range(self.current_step + 1):
                memory, page = self.gantt_data[time][1], self.gantt_data[time][2]
                for j, p in enumerate(memory):
                    if p is not None:
                        color = 'red' if p == page and self.faults[time] else 'blue'
                        self.ax_gantt.broken_barh([(time, 0.8)], (j - 0.4, 0.8), facecolors=color, edgecolors='black')
                        self.ax_gantt.text(time + 0.4, j, str(p), ha='center', va='center', color='white', fontweight='bold', fontsize=10)

            graph_type = self.step_graph_choice.get()
            end_frame = self.current_step + 1

            if graph_type == "Cumulative Faults":
                cumulative_faults = [0]
                fault_count = 0
                for i in range(end_frame):
                    fault = self.faults[i]
                    fault_count += 1 if fault else 0
                    cumulative_faults.append(fault_count)
                self.ax_fault.plot(range(len(cumulative_faults)), cumulative_faults, marker='o', color='red', label='Cumulative Faults')
                self.ax_fault.set_xlabel('Time', fontsize=12)
                self.ax_fault.set_ylabel('Cumulative Faults', fontsize=12)
                self.ax_fault.set_title('Cumulative Faults Over Time', fontsize=14)
                self.ax_fault.grid(True, linestyle='--', alpha=0.7)
                self.ax_fault.legend()

            elif graph_type == "Page Fault Rate":
                window_size = 5
                fault_counts = [1 if fault else 0 for fault in self.faults[:end_frame]]
                fault_rate = []
                for i in range(len(fault_counts)):
                    start = max(0, i - window_size + 1)
                    window = fault_counts[start:i+1]
                    rate = sum(window) / len(window)
                    fault_rate.append(rate)
                self.ax_fault.plot(range(len(fault_rate)), fault_rate, marker='o', color='purple', label='Fault Rate')
                self.ax_fault.set_xlabel('Time', fontsize=12)
                self.ax_fault.set_ylabel('Fault Rate', fontsize=12)
                self.ax_fault.set_title('Page Fault Rate Over Time (Moving Average)', fontsize=14)
                self.ax_fault.grid(True, linestyle='--', alpha=0.7)
                self.ax_fault.legend()

            elif graph_type == "Memory Utilization":
                utilization = [len([p for p in memory if p is not None]) for time, memory, page in self.gantt_data[:end_frame]]
                self.ax_fault.bar(range(len(utilization)), utilization, color='green', alpha=0.7)
                self.ax_fault.set_xlabel('Time', fontsize=12)
                self.ax_fault.set_ylabel('Frames in Use', fontsize=12)
                self.ax_fault.set_title('Memory Utilization Over Time', fontsize=14)
                self.ax_fault.set_ylim(0, self.max_frames + 1)
                self.ax_fault.grid(True, linestyle='--', alpha=0.7)

            elif graph_type == "Page Frequency":
                pages_to_plot = self.pages[:end_frame]
                if pages_to_plot:
                    self.ax_fault.hist(pages_to_plot, bins=range(min(pages_to_plot), max(pages_to_plot) + 2), color='blue', alpha=0.7, rwidth=0.8)
                    self.ax_fault.set_xlabel('Page Number', fontsize=12)
                    self.ax_fault.set_ylabel('Frequency', fontsize=12)
                    self.ax_fault.set_title('Page Frequency in Reference String', fontsize=14)
                    self.ax_fault.grid(True, linestyle='--', alpha=0.7)
                else:
                    self.ax_fault.set_title('Page Frequency - No Data', fontsize=14)

            elif graph_type == "Hit/Fault Distribution":
                faults_count = sum(1 for fault in self.faults[:end_frame] if fault)
                hits_count = end_frame - faults_count
                labels = ['Faults', 'Hits']
                sizes = [faults_count, hits_count]
                colors = ['red', 'green']
                self.ax_fault.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
                self.ax_fault.set_title('Hit/Fault Distribution', fontsize=14)

            fault = self.faults[self.current_step]
            status = "Fault" if fault else "Hit"
            time, memory, page = self.gantt_data[self.current_step]
            self.step_text.delete(1.0, tk.END)
            self.step_text.insert(tk.END, f"Step {self.current_step + 1}: Page {page} -> Memory: {memory} | {status}\n")

            if self.fault_sound and self.hit_sound:
                try:
                    if fault:
                        self.fault_sound.play()
                    else:
                        self.hit_sound.play()
                except Exception as e:
                    print(f"Error playing sound: {e}")

            self.ax_gantt.set_xlim(-0.5, len(self.gantt_data))
            self.ax_gantt.set_ylim(-0.5, self.max_frames - 0.5)
            self.ax_gantt.set_xlabel('Time', fontsize=12, labelpad=10)
            self.ax_gantt.set_ylabel('Frames', fontsize=12, labelpad=10)
            self.ax_gantt.set_yticks(range(self.max_frames))
            self.ax_gantt.set_yticklabels([f"Frame {i+1}" for i in range(self.max_frames)], fontsize=10)
            self.ax_gantt.set_xticks(range(len(self.gantt_data)))
            self.ax_gantt.set_title(f'Gantt Chart - {self.algorithm} (Step {self.current_step + 1}/{len(self.gantt_data)})', fontsize=14, pad=15)
            self.ax_gantt.grid(True, linestyle='--', alpha=0.7)
            self.fig.tight_layout()
            self.canvas.draw()

    def batch_process(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Batch Processing")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Enter multiple page reference strings (one per line):", font=("Arial", 10)).pack(pady=5)
        input_text = tk.Text(dialog, height=10, width=70, font=("Courier", 10))
        input_text.pack(pady=5)
        input_text.insert(tk.END, "1, 2, 3, 4, 5\n2, 3, 4, 5, 1\n3, 4, 5, 1, 2")

        ttk.Label(dialog, text="Number of Frames:", font=("Arial", 10)).pack(pady=5)
        frames_entry = ttk.Entry(dialog, width=10)
        frames_entry.pack()
        frames_entry.insert(0, "3")

        def run_batch():
            try:
                frames = int(frames_entry.get())
                if frames <= 0:
                    raise ValueError("Frames must be a positive number!")

                strings = input_text.get("1.0", tk.END).strip().split("\n")
                results = []
                for idx, string in enumerate(strings):
                    if not string.strip():
                        continue
                    pages = [int(x.strip()) for x in string.split(",") if x.strip()]
                    if not pages:
                        continue

                    algo_results = {}
                    for algo in ["FIFO", "LRU", "Optimal"]:
                        self.algorithm = algo
                        result, faults, _, _ = getattr(self, algo.lower())(pages, frames)
                        algo_results[algo] = faults
                    results.append((f"String {idx + 1}: {string}", algo_results))

                result_window = tk.Toplevel(self.root)
                result_window.title("Batch Processing Results")
                result_window.geometry("600x400")
                tree = ttk.Treeview(result_window, columns=("String", "FIFO", "LRU", "Optimal"), show="headings")
                tree.heading("String", text="Page Reference String")
                tree.heading("FIFO", text="FIFO Faults")
                tree.heading("LRU", text="LRU Faults")
                tree.heading("Optimal", text="Optimal Faults")
                tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

                for string, algo_results in results:
                    tree.insert("", tk.END, values=(string, algo_results["FIFO"], algo_results["LRU"], algo_results["Optimal"]))

                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid input! {str(e)}", parent=dialog)

        ttk.Button(dialog, text="Run Batch", command=run_batch).pack(pady=10)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()

    def compare_algorithms(self):
        try:
            pages = [int(x.strip()) for x in self.page_entry.get().split(",") if x.strip()]
            frames = int(self.frame_entry.get())
            if frames <= 0:
                messagebox.showerror("Error", "Frames must be a positive number!")
                return

            results = {}
            for algo in ["FIFO", "LRU", "Optimal"]:
                self.algorithm = algo
                result, faults, _, _ = getattr(self, algo.lower())(pages, frames)
                results[algo] = faults

            compare_window = tk.Toplevel(self.root)
            compare_window.title("Algorithm Comparison")
            compare_window.geometry("300x150")
            tk.Label(compare_window, text="Algorithm Comparison Results", font=("Arial", 12, "bold")).pack(pady=5)
            for algo, faults in results.items():
                tk.Label(compare_window, text=f"{algo}: {faults} faults").pack(pady=2)
        except ValueError:
            messagebox.showerror("Error", "Invalid input! Enter numbers separated by commas.")

    def show_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title("Help")
        help_window.geometry("600x400")
        help_text = tk.Text(help_window, height=20, width=80, font=("Arial", 10))
        help_text.pack(pady=10)
        help_text.insert(tk.END, "FIFO: First In First Out - Replaces the oldest page\n\n"
                               "LRU: Least Recently Used - Replaces the least recently used page\n\n"
                               "Optimal: Replaces the page that will not be used for the longest time\n\n"
                               "Usage:\n- Enter page references (e.g., 1, 2, 3)\n- Set frame number\n- Choose algorithm\n- Use buttons for various functions")

    def save_results(self):
        if self.output_text.get(1.0, tk.END).strip():
            with open("simulation_results.txt", "w") as f:
                f.write(f"Pages: {self.page_entry.get()}\n")
                f.write(f"Frames: {self.frame_entry.get()}\n")
                f.write(self.output_text.get(1.0, tk.END))
            messagebox.showinfo("Saved", "Results saved to simulation_results.txt")
        else:
            messagebox.showwarning("Warning", "No results to save!")

    def load_input(self):
        try:
            with open("simulation_results.txt", "r") as f:
                lines = f.readlines()
                if lines:
                    self.page_entry.delete(0, tk.END)
                    self.page_entry.insert(0, lines[0].split(":", 1)[1].strip())
                    self.frame_entry.delete(0, tk.END)
                    self.frame_entry.insert(0, lines[1].split(":", 1)[1].strip())
                    self.output_text.delete(1.0, tk.END)
                    self.output_text.insert(tk.END, "".join(lines[2:]))
            messagebox.showinfo("Loaded", "Input loaded from simulation_results.txt")
        except FileNotFoundError:
            messagebox.showerror("Error", "No saved file found")

    def view_chart(self):
        if not all([self.gantt_data, self.algorithm, self.max_frames, self.faults, self.pages]):
            messagebox.showinfo("Info", "No simulation data available. Run simulation first.")
            return

        print(f"Opening Gantt chart with: gantt_data={len(self.gantt_data)}, algorithm={self.algorithm}, max_frames={self.max_frames}, faults={len(self.faults)}, pages={len(self.pages)}")
        GanttChart(self.root, self.gantt_data, self.algorithm, self.max_frames, self.faults, self.pages)

if __name__ == "__main__":
    root = tk.Tk()
    app = PageReplacementSimulator(root)
    root.mainloop()

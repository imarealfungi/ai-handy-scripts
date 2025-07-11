import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import time
import logging
from device_handler import PatternManager, IntifaceClient, PlaybackEngine
from session_manager import SessionManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HandyAIStrokerGUI:
    """Main GUI application"""
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("The Handy AI Stroker")
        self.root.geometry("600x800")  # Taller for arousal timeline
        self.root.configure(bg='#1a1a1a')
        self.root.resizable(False, False)
        
        # Backend components
        self.pattern_manager = None
        self.twerk_pattern_manager = None
        self.device_client = IntifaceClient("http://localhost:8080")
        self.playback_engine = None
        self.session_manager = SessionManager()  # NEW: Session management
        self.device_client.set_connection_callback(self._on_connection_change)
        
        # GUI state variables
        self.min_range = 0
        self.max_range = 100
        self.slow_mode = False
        self.twerk_mode = False
        
        # Arousal timeline variables
        self.arousal_timeline_canvas = None
        self.arousal_button_id = None
        self.arousal_position = 0.0  # 0.0 to 1.0
        self.dragging_arousal = False
        self.session_active = False
        self.peaks_count = 3
        
        # GUI components (will be created in _setup_gui)
        self.connection_status_label = None
        self.device_status_label = None
        self.pattern_status_label = None
        self.play_button = None
        self.stop_button = None
        self.random_button = None
        self.speed_button = None
        self.twerk_button = None
        
        # Session controls
        self.session_time_entry = None
        self.peaks_entry = None
        self.start_session_button = None
        self.reset_session_button = None
        self.arousal_display_label = None
        self.session_timer_label = None
        
        self.range_canvas = None
        self.min_button_id = None
        self.max_button_id = None
        self.min_text_id = None
        self.max_text_id = None
        self.clamp_values_label = None
        self.dragging_item = None
        self.drag_start_x = 0
        
        self._setup_gui()
        self._setup_initial_states()
        self._auto_load_patterns()
        
        # Start arousal timeline update loop
        self._update_arousal_timeline()
    
    def _setup_gui(self):
        """Set up the GUI elements"""
        # Title
        title_label = tk.Label(
            self.root, 
            text="THE HANDY AI STROKER",
            font=("Arial", 20, "bold"),
            fg='#ffffff',
            bg='#1a1a1a'
        )
        title_label.pack(pady=20)
        
        # Connection Status
        status_frame = tk.Frame(self.root, bg='#1a1a1a')
        status_frame.pack(pady=10)
        
        tk.Label(
            status_frame,
            text="Status:",
            font=("Arial", 12),
            fg='#ffffff',
            bg='#1a1a1a'
        ).pack(side=tk.LEFT)
        
        self.connection_status_label = tk.Label(
            status_frame,
            text="● Disconnected",
            font=("Arial", 12, "bold"),
            fg='#ff4444',
            bg='#1a1a1a'
        )
        self.connection_status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Device Status
        self.device_status_label = tk.Label(
            self.root,
            text="Device: Not Found",
            font=("Arial", 10),
            fg='#888888',
            bg='#1a1a1a'
        )
        self.device_status_label.pack(pady=5)
        
        # Session Controls Section
        self._setup_session_controls()
        
        # Range Slider
        range_frame = tk.Frame(self.root, bg='#1a1a1a')
        range_frame.pack(pady=20)
        
        tk.Label(
            range_frame,
            text="Range:",
            font=("Arial", 12),
            fg='#ffffff',
            bg='#1a1a1a'
        ).pack()
        
        range_control_frame = tk.Frame(range_frame, bg='#1a1a1a')
        range_control_frame.pack(pady=10)
        
        self.range_canvas = tk.Canvas(
            range_control_frame,
            width=400,
            height=60,
            bg='#1a1a1a',
            highlightthickness=0
        )
        self.range_canvas.pack()
        
        # Track line
        self.range_canvas.create_line(50, 30, 350, 30, fill='#666666', width=4)
        
        # Tick marks
        for i in range(5):
            x = 50 + (i * 75)
            self.range_canvas.create_line(x, 25, x, 35, fill='#888888', width=2)
            self.range_canvas.create_text(x, 45, text=str(i*25), fill='#888888', font=("Arial", 8))
        
        # MIN button
        self.min_button_id = self.range_canvas.create_rectangle(
            45, 20, 65, 40, 
            fill='#4444ff', outline='#6666ff', width=2
        )
        self.min_text_id = self.range_canvas.create_text(
            55, 30, text="MIN", fill='white', font=("Arial", 8, "bold")
        )
        
        # MAX button  
        self.max_button_id = self.range_canvas.create_rectangle(
            335, 20, 355, 40,
            fill='#ff4444', outline='#ff6666', width=2
        )
        self.max_text_id = self.range_canvas.create_text(
            345, 30, text="MAX", fill='white', font=("Arial", 8, "bold")
        )
        
        # Range values display
        self.clamp_values_label = tk.Label(
            range_frame,
            text="Min: 0  |  Max: 100",
            font=("Arial", 10),
            fg='#888888',
            bg='#1a1a1a'
        )
        self.clamp_values_label.pack(pady=5)
        
        # Bind mouse events
        self.range_canvas.bind("<Button-1>", self._on_range_click)
        self.range_canvas.bind("<B1-Motion>", self._on_range_drag)
        self.range_canvas.bind("<ButtonRelease-1>", self._on_range_release)
        
        # Speed Control
        speed_frame = tk.Frame(self.root, bg='#1a1a1a')
        speed_frame.pack(pady=20)
        
        tk.Label(
            speed_frame,
            text="Speed:",
            font=("Arial", 12),
            fg='#ffffff',
            bg='#1a1a1a'
        ).pack()
        
        self.speed_button = tk.Button(
            speed_frame,
            text="NORMAL",
            font=("Arial", 14, "bold"),
            bg='#44ff44',
            fg='black',
            width=15,
            height=2,
            command=self._toggle_speed
        )
        self.speed_button.pack(pady=10)
        
        # Twerk Mode Button
        self.twerk_button = tk.Button(
            speed_frame,
            text="TWERK: OFF",
            font=("Arial", 14, "bold"),
            bg='#888888',
            fg='white',
            width=15,
            height=2,
            command=self._toggle_twerk
        )
        self.twerk_button.pack(pady=5)
        
        # Pattern Status
        self.pattern_status_label = tk.Label(
            self.root,
            text="Patterns: Loading...",
            font=("Arial", 12),
            fg='#888888',
            bg='#1a1a1a'
        )
        self.pattern_status_label.pack(pady=10)
        
        # Control Buttons
        button_frame = tk.Frame(self.root, bg='#1a1a1a')
        button_frame.pack(pady=20)
        
        # First row - PLAY and STOP
        top_button_frame = tk.Frame(button_frame, bg='#1a1a1a')
        top_button_frame.pack(pady=5)
        
        self.play_button = tk.Button(
            top_button_frame,
            text="PLAY",
            font=("Arial", 16, "bold"),
            bg='#44ff44',
            fg='black',
            width=12,
            height=2,
            command=self._toggle_play
        )
        self.play_button.pack(side=tk.LEFT, padx=10)
        
        self.stop_button = tk.Button(
            top_button_frame,
            text="STOP",
            font=("Arial", 16, "bold"),
            bg='#ff4444',
            fg='white',
            width=12,
            height=2,
            command=self._emergency_stop
        )
        self.stop_button.pack(side=tk.LEFT, padx=10)
        
        # Second row - RANDOM
        bottom_button_frame = tk.Frame(button_frame, bg='#1a1a1a')
        bottom_button_frame.pack(pady=5)
        
        self.random_button = tk.Button(
            bottom_button_frame,
            text="RANDOM: ON",
            font=("Arial", 16, "bold"),
            bg='#ffaa44',
            fg='black',
            width=25,
            height=2,
            command=self._toggle_random
        )
        self.random_button.pack()
        
        # Menu Bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Patterns...", command=self._load_patterns)
        file_menu.add_separator()
        file_menu.add_command(label="Connect to C# Server", command=self._connect_device)
        file_menu.add_command(label="Disconnect", command=self._disconnect_device)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
    
    def _setup_session_controls(self):
        """Set up session and arousal timeline controls"""
        # Session Control Frame
        session_frame = tk.Frame(self.root, bg='#1a1a1a')
        session_frame.pack(pady=15)
        
        tk.Label(
            session_frame,
            text="SESSION CONTROL",
            font=("Arial", 14, "bold"),
            fg='#ffffff',
            bg='#1a1a1a'
        ).pack()
        
        # Session inputs row
        inputs_frame = tk.Frame(session_frame, bg='#1a1a1a')
        inputs_frame.pack(pady=10)
        
        # Session time input
        tk.Label(
            inputs_frame,
            text="Time:",
            font=("Arial", 10),
            fg='#ffffff',
            bg='#1a1a1a'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.session_time_entry = tk.Entry(
            inputs_frame,
            width=8,
            font=("Arial", 10),
            bg='#333333',
            fg='#ffffff',
            insertbackground='#ffffff'
        )
        self.session_time_entry.pack(side=tk.LEFT, padx=(0, 15))
        self.session_time_entry.insert(0, "5:30")
        
        # Peaks input
        tk.Label(
            inputs_frame,
            text="Peaks:",
            font=("Arial", 10),
            fg='#ffffff',
            bg='#1a1a1a'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.peaks_entry = tk.Entry(
            inputs_frame,
            width=3,
            font=("Arial", 10),
            bg='#333333',
            fg='#ffffff',
            insertbackground='#ffffff'
        )
        self.peaks_entry.pack(side=tk.LEFT, padx=(0, 15))
        self.peaks_entry.insert(0, "3")
        
        # Session buttons row
        buttons_frame = tk.Frame(session_frame, bg='#1a1a1a')
        buttons_frame.pack(pady=5)
        
        self.start_session_button = tk.Button(
            buttons_frame,
            text="START SESSION",
            font=("Arial", 10, "bold"),
            bg='#44aa44',
            fg='white',
            width=12,
            command=self._start_session
        )
        self.start_session_button.pack(side=tk.LEFT, padx=5)
        
        self.reset_session_button = tk.Button(
            buttons_frame,
            text="RESET",
            font=("Arial", 10, "bold"),
            bg='#aa4444',
            fg='white',
            width=8,
            command=self._reset_session
        )
        self.reset_session_button.pack(side=tk.LEFT, padx=5)
        
        # Session status display
        status_frame = tk.Frame(session_frame, bg='#1a1a1a')
        status_frame.pack(pady=5)
        
        self.session_timer_label = tk.Label(
            status_frame,
            text="Session: Inactive",
            font=("Arial", 10),
            fg='#888888',
            bg='#1a1a1a'
        )
        self.session_timer_label.pack()
        
        # Arousal Timeline
        timeline_frame = tk.Frame(session_frame, bg='#1a1a1a')
        timeline_frame.pack(pady=10)
        
        tk.Label(
            timeline_frame,
            text="Arousal Timeline:",
            font=("Arial", 12),
            fg='#ffffff',
            bg='#1a1a1a'
        ).pack()
        
        # Arousal timeline canvas
        self.arousal_timeline_canvas = tk.Canvas(
            timeline_frame,
            width=450,
            height=80,
            bg='#1a1a1a',
            highlightthickness=1,
            highlightbackground='#666666'
        )
        self.arousal_timeline_canvas.pack(pady=5)
        
        # Arousal display
        self.arousal_display_label = tk.Label(
            timeline_frame,
            text="Arousal: 0% | Speed: 1.00x",
            font=("Arial", 10),
            fg='#888888',
            bg='#1a1a1a'
        )
        self.arousal_display_label.pack(pady=5)
        
        # Bind arousal timeline events
        self.arousal_timeline_canvas.bind("<Button-1>", self._on_arousal_click)
        self.arousal_timeline_canvas.bind("<B1-Motion>", self._on_arousal_drag)
        self.arousal_timeline_canvas.bind("<ButtonRelease-1>", self._on_arousal_release)
        
        # Draw initial timeline
        self._draw_arousal_timeline()
    
    def _draw_arousal_timeline(self):
        """Draw the arousal timeline with peaks visualization"""
        canvas = self.arousal_timeline_canvas
        canvas.delete("all")
        
        # Timeline background
        canvas.create_rectangle(20, 20, 430, 60, fill='#333333', outline='#666666')
        
        # Draw arousal curve if session active
        if self.session_active and hasattr(self.session_manager, 'target_arousal_curve'):
            curve = self.session_manager.target_arousal_curve
            if curve:
                # Draw curve line
                points = []
                for i, arousal in enumerate(curve):
                    x = 20 + (i / (len(curve) - 1)) * 410
                    y = 60 - ((arousal / 100) * 40)  # Invert Y axis
                    points.extend([x, y])
                
                if len(points) >= 4:  # Need at least 2 points
                    canvas.create_line(points, fill='#44aaff', width=2, smooth=True)
        
        # Draw timeline markers
        for i in range(5):
            x = 20 + (i * 102.5)
            canvas.create_line(x, 55, x, 65, fill='#888888', width=1)
            progress = i * 25
            canvas.create_text(x, 70, text=f"{progress}%", fill='#888888', font=("Arial", 8))
        
        # Draw arousal position button
        button_x = 20 + (self.arousal_position * 410)
        self.arousal_button_id = canvas.create_oval(
            button_x - 8, 32, button_x + 8, 48,
            fill='#ff4444', outline='#ff6666', width=2
        )
        
        # Add arousal level text on button
        canvas.create_text(
            button_x, 40, text=f"{int(self.arousal_position * 100)}",
            fill='white', font=("Arial", 8, "bold")
        )
    
    def _on_arousal_click(self, event):
        """Handle click on arousal timeline"""
        x = event.x
        if 20 <= x <= 430:
            # Check if clicking on the button
            button_coords = self.arousal_timeline_canvas.coords(self.arousal_button_id)
            if button_coords and button_coords[0] <= x <= button_coords[2]:
                self.dragging_arousal = True
            else:
                # Click on timeline - jump to position
                new_position = (x - 20) / 410
                self._set_arousal_position(new_position)
    
    def _on_arousal_drag(self, event):
        """Handle dragging arousal timeline"""
        if self.dragging_arousal:
            x = max(20, min(430, event.x))
            new_position = (x - 20) / 410
            self._set_arousal_position(new_position)
    
    def _on_arousal_release(self, event):
        """Handle release of arousal timeline"""
        self.dragging_arousal = False
    
    def _set_arousal_position(self, position):
        """Set arousal position and update session manager"""
        self.arousal_position = max(0.0, min(1.0, position))
        
        # Convert position to arousal level
        arousal_level = self.arousal_position * 100
        
        # Update session manager
        if self.session_active:
            # Manual override of arousal
            elapsed, remaining, progress = self.session_manager.get_session_progress()
            self.session_manager.update_arousal(arousal_level)
            
            # Force position in session timeline
            if self.session_manager.session_length > 0:
                override_time = self.arousal_position * self.session_manager.session_length
                self.session_manager.session_start_time = time.time() - override_time
        else:
            # Manual control when no session active
            self.session_manager.update_arousal(arousal_level)
        
        # Update PlaybackEngine if available
        if self.playback_engine and hasattr(self.playback_engine, 'session_manager'):
            self.playback_engine.session_manager = self.session_manager
        
        self._draw_arousal_timeline()
        logger.info(f"Manual arousal override: {arousal_level:.1f}%")
    
    def _start_session(self):
        """Start a new session"""
        try:
            session_time = self.session_time_entry.get().strip()
            peaks_str = self.peaks_entry.get().strip()
            peaks = int(peaks_str) if peaks_str else 3
            
            # Update session manager with peaks
            self.session_manager.peaks_count = peaks
            
            if self.session_manager.start_session(session_time):
                self.session_active = True
                self.arousal_position = 0.0
                
                # Update PlaybackEngine with session manager
                if self.playback_engine:
                    self.playback_engine.session_manager = self.session_manager
                
                self.start_session_button.config(state='disabled')
                self.reset_session_button.config(state='normal')
                
                logger.info(f"Started session: {session_time} with {peaks} peaks")
                self._draw_arousal_timeline()
            else:
                messagebox.showerror("Error", "Failed to start session")
                
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            messagebox.showerror("Error", f"Invalid session parameters: {e}")
    
    def _reset_session(self):
        """Reset session to beginning"""
        self.session_manager.stop_session()
        self.session_active = False
        self.arousal_position = 0.0
        
        # Reset PlaybackEngine
        if self.playback_engine and hasattr(self.playback_engine, 'session_manager'):
            self.playback_engine.session_manager = None
        
        self.start_session_button.config(state='normal')
        self.reset_session_button.config(state='disabled')
        
        self._draw_arousal_timeline()
        logger.info("Session reset")
    
    def _update_arousal_timeline(self):
        """Update arousal timeline display (called periodically)"""
        if self.session_active and self.session_manager.is_session_active():
            # Auto-update position based on session progress
            if not self.dragging_arousal:  # Don't override manual dragging
                elapsed, remaining, progress = self.session_manager.get_session_progress()
                
                # Get current target arousal
                target_arousal = self.session_manager.get_target_arousal(elapsed)
                current_arousal = self.session_manager.current_arousal
                
                # Update position based on session progress
                self.arousal_position = progress
                
                # Update session manager
                self.session_manager.update_arousal(target_arousal)
                
                # Update display
                speed_mult = 1.0
                if self.playback_engine and hasattr(self.playback_engine, 'session_manager'):
                    _, speed_mult = self.session_manager.get_next_pattern_recommendation()
                
                # Update labels
                minutes = remaining // 60
                seconds = remaining % 60
                self.session_timer_label.config(
                    text=f"Session: {minutes:02d}:{seconds:02d} remaining",
                    fg='#44ff44'
                )
                
                self.arousal_display_label.config(
                    text=f"Arousal: {current_arousal:.0f}% | Target: {target_arousal:.0f}% | Speed: {speed_mult:.2f}x"
                )
                
                self._draw_arousal_timeline()
        
        elif self.session_active and not self.session_manager.is_session_active():
            # Session ended
            self._reset_session()
            self.session_timer_label.config(text="Session: Completed!", fg='#ffaa44')
        
        else:
            # No active session
            if not self.dragging_arousal:
                current_arousal = self.session_manager.current_arousal
                self.session_timer_label.config(text="Session: Inactive", fg='#888888')
                self.arousal_display_label.config(
                    text=f"Arousal: {current_arousal:.0f}% | Speed: 1.00x"
                )
        
        # Schedule next update
        self.root.after(1000, self._update_arousal_timeline)  # Update every second
    
    def _setup_initial_states(self):
        """Set up initial GUI states"""
        self.play_button.config(state='disabled')
        self.stop_button.config(state='disabled')
        self.random_button.config(state='disabled')
        self.twerk_button.config(state='disabled')
        self.reset_session_button.config(state='disabled')
        self._update_clamp_display()
    
    def _auto_load_patterns(self):
        """Auto-load patterns from funscript folder"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            possible_locations = [
                os.path.join(script_dir, "funscript"),
                os.path.join(script_dir, "FUNSCRIPTS"),
                os.path.join(script_dir, "funscripts")
            ]
            
            for location in possible_locations:
                if os.path.exists(location):
                    logger.info(f"Found funscript folder at: {location}")
                    self._load_patterns_from_folder(location)
                    
                    # Also try to load twerk patterns
                    twerk_folder = os.path.join(location, "twerk")
                    if os.path.exists(twerk_folder):
                        self._load_twerk_patterns(twerk_folder)
                    else:
                        logger.warning(f"No twerk folder found at: {twerk_folder}")
                    
                    return
            
            logger.warning("No funscript folder found")
            self.pattern_status_label.config(
                text="Patterns: Auto-load failed - use File > Load Patterns",
                fg='#ffaa44'
            )
            
        except Exception as e:
            logger.error(f"Error during auto-load: {e}")
    
    def _load_patterns_from_folder(self, folder_path):
        """Load patterns from specified folder"""
        try:
            self.pattern_manager = PatternManager(folder_path)
            
            # Create playback engine with session manager integration
            self.playback_engine = PlaybackEngine(self.pattern_manager, self.device_client)
            self.playback_engine.set_range(self.min_range, self.max_range)
            self.playback_engine.set_slow_mode(self.slow_mode)
            
            # Add session manager to playback engine
            self.playback_engine.session_manager = self.session_manager
            
            total_patterns = self.pattern_manager.get_total_count()
            
            if total_patterns > 0:
                self.pattern_status_label.config(
                    text=f"Patterns: {total_patterns} loaded (auto)",
                    fg='#44ff44'
                )
                
                if self.device_client.connected and self.device_client.device_connected:
                    self.play_button.config(state='normal')
                    self.stop_button.config(state='normal')
                    self.random_button.config(state='normal')
                    if self.twerk_pattern_manager:
                        self.twerk_button.config(state='normal')
                
                logger.info(f"Auto-loaded {total_patterns} patterns successfully!")
            else:
                self.pattern_status_label.config(
                    text="Patterns: Folder found but no valid patterns",
                    fg='#ffaa44'
                )
                
        except Exception as e:
            logger.error(f"Failed to auto-load patterns: {e}")
            self.pattern_status_label.config(
                text="Patterns: Auto-load error - check console",
                fg='#ff4444'
            )
    
    def _load_twerk_patterns(self, twerk_folder_path):
        """Load twerk patterns from twerk subfolder"""
        try:
            logger.info(f"Attempting to load twerk patterns from: {twerk_folder_path}")
            
            # List all files in twerk folder for debugging
            import glob
            twerk_files = glob.glob(os.path.join(twerk_folder_path, "*.funscript"))
            logger.info(f"Found {len(twerk_files)} .funscript files in twerk folder")
            
            # Try to load with PatternManager
            self.twerk_pattern_manager = PatternManager(twerk_folder_path)
            twerk_count = self.twerk_pattern_manager.get_total_count()
            
            if twerk_count > 0:
                logger.info(f"Successfully loaded {twerk_count} twerk patterns")
                if self.device_client.connected and self.device_client.device_connected and self.pattern_manager:
                    self.twerk_button.config(state='normal')
            else:
                logger.warning(f"No valid twerk patterns found")
                
        except Exception as e:
            logger.error(f"Failed to load twerk patterns: {e}")
    
    def _toggle_twerk(self):
        """Toggle twerk mode on/off"""
        if not self.twerk_pattern_manager:
            messagebox.showerror("Error", "No twerk patterns loaded")
            return
        
        self.twerk_mode = not self.twerk_mode
        
        if self.twerk_mode:
            # Switch to twerk patterns
            self.playback_engine.pattern_manager = self.twerk_pattern_manager
            
            # Update button appearance
            self.twerk_button.config(
                text="TWERK: ON",
                bg='#ff44ff',
                fg='white'
            )
            
            logger.info("Twerk mode activated - using twerk patterns")
            
        else:
            # Switch back to normal patterns
            self.playback_engine.pattern_manager = self.pattern_manager
            
            # Update button appearance
            self.twerk_button.config(
                text="TWERK: OFF",
                bg='#888888',
                fg='white'
            )
            
            logger.info("Twerk mode deactivated - restored normal operation")
    
    def _on_connection_change(self, connected: bool, device_found: bool = False):
        """Handle connection status changes"""
        def update_gui():
            if connected:
                if device_found:
                    self.connection_status_label.config(
                        text="● Connected + Device Found",
                        fg='#44ff44'
                    )
                    self.device_status_label.config(
                        text="Device: The Handy (Ready)",
                        fg='#44ff44'
                    )
                    if self.pattern_manager:
                        self.play_button.config(state='normal')
                        self.stop_button.config(state='normal')
                        self.random_button.config(state='normal')
                        if self.twerk_pattern_manager:
                            self.twerk_button.config(state='normal')
                else:
                    self.connection_status_label.config(
                        text="● Connected (No Device)",
                        fg='#ffaa44'
                    )
                    self.device_status_label.config(
                        text="Device: Scanning for The Handy...",
                        fg='#ffaa44'
                    )
            else:
                self.connection_status_label.config(
                    text="● Disconnected",
                    fg='#ff4444'
                )
                self.device_status_label.config(
                    text="Device: Not Connected",
                    fg='#888888'
                )
                self.play_button.config(state='disabled')
                self.stop_button.config(state='disabled')
                self.random_button.config(state='disabled')
                self.twerk_button.config(state='disabled')
        
        self.root.after(0, update_gui)
    
    def _on_range_click(self, event):
        """Handle mouse click on range slider"""
        x, y = event.x, event.y
        
        min_coords = self.range_canvas.coords(self.min_button_id)
        if min_coords[0] <= x <= min_coords[2] and min_coords[1] <= y <= min_coords[3]:
            self.dragging_item = 'min'
            self.drag_start_x = x
            return
            
        max_coords = self.range_canvas.coords(self.max_button_id)
        if max_coords[0] <= x <= max_coords[2] and max_coords[1] <= y <= max_coords[3]:
            self.dragging_item = 'max'
            self.drag_start_x = x
            return
    
    def _on_range_drag(self, event):
        """Handle dragging of range buttons"""
        if not self.dragging_item:
            return
            
        x = event.x
        x = max(50, min(350, x))
        
        relative_x = x - 50
        value = int((relative_x / 300) * 100)
        snapped_value = round(value / 5) * 5
        snapped_x = 50 + (snapped_value / 100) * 300
        
        if self.dragging_item == 'min':
            max_coords = self.range_canvas.coords(self.max_button_id)
            max_center_x = (max_coords[0] + max_coords[2]) / 2
            if snapped_x >= max_center_x - 15:
                return
                
            self.range_canvas.coords(self.min_button_id, snapped_x-10, 20, snapped_x+10, 40)
            self.range_canvas.coords(self.min_text_id, snapped_x, 30)
            self.min_range = snapped_value
            
        elif self.dragging_item == 'max':
            min_coords = self.range_canvas.coords(self.min_button_id)
            min_center_x = (min_coords[0] + min_coords[2]) / 2
            if snapped_x <= min_center_x + 15:
                return
                
            self.range_canvas.coords(self.max_button_id, snapped_x-10, 20, snapped_x+10, 40)
            self.range_canvas.coords(self.max_text_id, snapped_x, 30)
            self.max_range = snapped_value
            
        self._update_clamp_display()
        
        # Update playback engine if it exists
        if self.playback_engine:
            self.playback_engine.set_range(self.min_range, self.max_range)
    
    def _on_range_release(self, event):
        """Handle mouse release"""
        self.dragging_item = None
    
    def _update_clamp_display(self):
        """Update the clamp values display"""
        self.clamp_values_label.config(text=f"Min: {self.min_range}  |  Max: {self.max_range}")
    
    def _toggle_speed(self):
        """Toggle between normal and slow speed"""
        self.slow_mode = not self.slow_mode
        if self.slow_mode:
            self.speed_button.config(
                text="SLOW",
                bg='#ff8844'
            )
        else:
            self.speed_button.config(
                text="NORMAL", 
                bg='#44ff44'
            )
        
        # Update playback engine if it exists
        if self.playback_engine:
            self.playback_engine.set_slow_mode(self.slow_mode)
    
    def _emergency_stop(self):
        """Emergency stop"""
        if self.playback_engine:
            self.playback_engine.emergency_stop()
        
        self.play_button.config(
            text="PLAY",
            bg='#44ff44',
            fg='black'
        )
    
    def _toggle_play(self):
        """Toggle play/pause"""
        if not self.playback_engine:
            messagebox.showerror("Error", "Patterns not loaded or device not connected")
            return
        
        if self.playback_engine.is_playing:
            self._pause_playback()
        else:
            self._start_playback()
    
    def _start_playback(self):
        """Start pattern playback"""
        if self.playback_engine and self.playback_engine.start_playback():
            self.play_button.config(
                text="PAUSE",
                bg='#ff8844',
                fg='white'
            )
        else:
            messagebox.showerror("Error", "Failed to start playback")
    
    def _pause_playback(self):
        """Pause pattern playback"""
        if self.playback_engine:
            self.playback_engine.stop_playback()
        
        self.play_button.config(
            text="PLAY",
            bg='#44ff44',
            fg='black'
        )
    
    def _toggle_random(self):
        """Toggle random mode (placeholder for now)"""
        pass
    
    def _load_patterns(self):
        """Manually load patterns from folder"""
        folder = filedialog.askdirectory(title="Select funscript folder")
        if folder:
            self._load_patterns_from_folder(folder)
            # Also try to load twerk patterns
            twerk_folder = os.path.join(folder, "twerk")
            if os.path.exists(twerk_folder):
                self._load_twerk_patterns(twerk_folder)
    
    def _connect_device(self):
        """Connect to C# Buttplug Server"""
        self.device_client.connect()
    
    def _disconnect_device(self):
        """Disconnect from C# server"""
        self.device_client.disconnect()
        if self.playback_engine:
            self.playback_engine.stop_playback()
    
    def run(self):
        """Run the application"""
        logger.info("Starting The Handy AI Stroker")
        self.root.mainloop()

if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        print("Installing required packages...")
        import subprocess
        subprocess.run(["pip", "install", "requests"])
        import requests
    
    app = HandyAIStrokerGUI()
    app.run()
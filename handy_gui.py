import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Canvas
import requests
import threading
import time
import json
import pandas as pd
import ast
import random
import os
import math

class DualHandleSlider(tk.Frame):
    def __init__(self, parent, from_=0, to=100, initial_min=0, initial_max=100, callback=None):
        super().__init__(parent)
        
        self.from_ = from_
        self.to = to
        self.min_val = initial_min
        self.max_val = initial_max
        self.callback = callback
        
        self.canvas = Canvas(self, width=400, height=50, highlightthickness=0, bg='#1a1a1a')
        self.canvas.pack(fill=tk.X, expand=True)
        
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        self.dragging = None
        self.draw_slider()
        
    def draw_slider(self):
        self.canvas.delete("all")
        
        slider_y = 25
        slider_height = 8
        handle_size = 12
        width = self.canvas.winfo_width() or 400
        margin = 20
        slider_width = width - 2 * margin
        
        min_pos = margin + (self.min_val - self.from_) / (self.to - self.from_) * slider_width
        max_pos = margin + (self.max_val - self.from_) / (self.to - self.from_) * slider_width
        
        # Dark theme colors
        self.canvas.create_rectangle(margin, slider_y - slider_height//2, 
                                   margin + slider_width, slider_y + slider_height//2,
                                   fill="#444444", outline="#666666")
        
        self.canvas.create_rectangle(min_pos, slider_y - slider_height//2,
                                   max_pos, slider_y + slider_height//2,
                                   fill="#00ff41", outline="#00ff41")
        
        self.min_handle = self.canvas.create_oval(min_pos - handle_size//2, slider_y - handle_size//2,
                                                min_pos + handle_size//2, slider_y + handle_size//2,
                                                fill="#00ff41", outline="#ffffff", width=2)
        
        self.max_handle = self.canvas.create_oval(max_pos - handle_size//2, slider_y - handle_size//2,
                                                max_pos + handle_size//2, slider_y + handle_size//2,
                                                fill="#00ff41", outline="#ffffff", width=2)
        
        self.canvas.after(1, self.update_canvas_bindings)
    
    def update_canvas_bindings(self):
        self.canvas.bind("<Configure>", lambda e: self.draw_slider())
    
    def on_click(self, event):
        min_handle_bbox = self.canvas.bbox(self.min_handle)
        max_handle_bbox = self.canvas.bbox(self.max_handle)
        
        if min_handle_bbox and self.point_in_bbox(event.x, event.y, min_handle_bbox):
            self.dragging = "min"
        elif max_handle_bbox and self.point_in_bbox(event.x, event.y, max_handle_bbox):
            self.dragging = "max"
    
    def point_in_bbox(self, x, y, bbox):
        return bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]
    
    def on_drag(self, event):
        if self.dragging:
            width = self.canvas.winfo_width()
            margin = 20
            slider_width = width - 2 * margin
            
            relative_pos = (event.x - margin) / slider_width
            value = self.from_ + relative_pos * (self.to - self.from_)
            value = max(self.from_, min(self.to, value))
            
            if self.dragging == "min":
                self.min_val = min(value, self.max_val)
            elif self.dragging == "max":
                self.max_val = max(value, self.min_val)
            
            self.draw_slider()
            if self.callback:
                self.callback(self.min_val, self.max_val)
    
    def on_release(self, event):
        self.dragging = None
    
    def get_values(self):
        return self.min_val, self.max_val
    
    def set_values(self, min_val, max_val):
        self.min_val = max(self.from_, min(self.to, min_val))
        self.max_val = max(self.from_, min(self.to, max_val))
        if self.min_val > self.max_val:
            self.min_val, self.max_val = self.max_val, self.min_val
        self.draw_slider()

class AIPatternEngine:
    def __init__(self):
        self.patterns = {}
        self.current_pattern = None
        self.pattern_start_time = 0
        self.session_start_time = 0
        self.session_duration = 0
        self.wave_count = 1
        self.base_pleasure = 0
        self.experience_level = 'experienced'
        self.climax_mode = False
        
        # FUNSCRIPT ACCURATE: Track actual keyframe positions
        self.current_action_index = 0
        self.next_keyframe_time = 0
        
    def load_patterns(self, csv_path):
        """Load patterns from processed CSV"""
        try:
            df = pd.read_csv(csv_path)
            
            for level in ['virgin', 'amateur', 'experienced', 'expert', 'pornstar']:
                level_patterns = df[df['intensity'] == level]
                self.patterns[level] = []
                
                for _, row in level_patterns.iterrows():
                    try:
                        positions = ast.literal_eval(row['positions'])
                        times = ast.literal_eval(row['times'])
                        
                        # Convert to funscript-style actions
                        actions = []
                        for i, (pos, t) in enumerate(zip(positions, times)):
                            actions.append({
                                'at': int(t),  # Time in ms
                                'pos': int(pos)  # Position 0-100
                            })
                        
                        pattern = {
                            'actions': actions,
                            'duration': row['duration'],
                            'source': row['source_file']
                        }
                        self.patterns[level].append(pattern)
                    except:
                        continue
            
            print(f"Loaded patterns: {sum(len(p) for p in self.patterns.values())}")
            return True
            
        except Exception as e:
            print(f"Error loading patterns: {e}")
            return False
    
    def start_session(self, experience_level, session_duration, wave_count, initial_pleasure):
        """Start a new AI session"""
        self.session_start_time = time.time()
        self.session_duration = session_duration
        self.wave_count = wave_count
        self.base_pleasure = initial_pleasure
        self.experience_level = experience_level
        self.climax_mode = False
        
        self.switch_pattern()
    
    def switch_pattern(self):
        """Switch to a new pattern with session awareness"""
        if self.experience_level in self.patterns and len(self.patterns[self.experience_level]) > 0:
            # Check if we should progress based on session time
            session_elapsed = time.time() - self.session_start_time if self.session_start_time > 0 else 0
            session_progress = min(1.0, session_elapsed / self.session_duration) if self.session_duration > 0 else 0
            
            # Select pattern based on session progress and wave count
            available_patterns = [p for p in self.patterns[self.experience_level] 
                                if p != self.current_pattern]
            
            if available_patterns:
                # Use session progress to influence pattern selection
                if session_progress > 0.8 or self.climax_mode:
                    # Late in session or climax - prefer more intense patterns
                    self.current_pattern = random.choice(available_patterns[-len(available_patterns)//3:] or available_patterns)
                elif session_progress > 0.5:
                    # Mid session - balanced patterns
                    mid_start = len(available_patterns)//3
                    mid_end = 2 * len(available_patterns)//3
                    self.current_pattern = random.choice(available_patterns[mid_start:mid_end] or available_patterns)
                else:
                    # Early session - gentler patterns
                    self.current_pattern = random.choice(available_patterns[:len(available_patterns)//2] or available_patterns)
            else:
                self.current_pattern = random.choice(self.patterns[self.experience_level])
            
            self.pattern_start_time = time.time()
            
            # FUNSCRIPT ACCURATE: Reset to first keyframe
            self.current_action_index = 0
            self.next_keyframe_time = time.time()
            
            progress_pct = int(session_progress * 100)
            print(f"SWITCHED to new {self.experience_level} pattern: {len(self.current_pattern['actions'])} keyframes, "
                  f"{self.current_pattern['duration']:.1f}s (Session: {progress_pct}%)")
    
    def get_next_action(self):
        """Get next action with NATURAL funscript timing - no overthinking"""
        if not self.current_pattern or not self.current_pattern['actions']:
            return None
        
        current_time = time.time()
        actions = self.current_pattern['actions']
        
        # Check if pattern finished
        pattern_time_ms = (current_time - self.pattern_start_time) * 1000
        session_elapsed = current_time - self.session_start_time if self.session_start_time > 0 else 0
        session_progress = min(1.0, session_elapsed / self.session_duration) if self.session_duration > 0 else 0
        
        # Simple session progression - just speed up gradually
        if session_progress > 0.8 or self.climax_mode:
            speed_factor = 1.6  # Fast
        elif session_progress > 0.5:
            speed_factor = 1.3  # Medium
        else:
            speed_factor = 1.0  # Normal
            
        # Pattern duration with speed factor
        adjusted_duration = (self.current_pattern['duration'] * 1000) / speed_factor
            
        if pattern_time_ms > adjusted_duration:
            self.switch_pattern()
            return self.get_next_action()
        
        # Check if it's time for the next keyframe
        if current_time >= self.next_keyframe_time and self.current_action_index < len(actions):
            # Get the current keyframe
            action = actions[self.current_action_index]
            position = action['pos']
            
            # Apply scaling to position
            scaled_position = self.apply_scaling(position, session_progress)
            
            # Move to next keyframe
            self.current_action_index += 1
            
            # Calculate when the NEXT keyframe should be sent - SIMPLE
            if self.current_action_index < len(actions):
                next_action = actions[self.current_action_index]
                # Use RAW timing from funscript, just apply speed factor
                current_time_in_pattern = action['at'] / speed_factor
                next_time_in_pattern = next_action['at'] / speed_factor
                time_to_next = (next_time_in_pattern - current_time_in_pattern) / 1000.0
                
                self.next_keyframe_time = current_time + max(0.02, time_to_next)  # Minimum 20ms
            else:
                self.next_keyframe_time = current_time + 0.1
            
            return {
                'position': scaled_position,
                'session_progress': session_progress,
                'keyframe_index': self.current_action_index - 1,
                'total_keyframes': len(actions),
                'speed_factor': speed_factor
            }
        
        return None
    
    def calculate_next_delay(self, current_time_ms):
        """Calculate optimal delay to next update based on funscript timing"""
        actions = self.current_pattern['actions']
        
        # Find next keyframe
        for action in actions:
            if action['at'] > current_time_ms:
                time_to_next = action['at'] - current_time_ms
                # Ensure smooth interpolation with multiple updates between keyframes
                optimal_steps = max(2, min(10, int(time_to_next / 50)))  # 2-10 steps between keyframes
                return max(0.05, min(0.2, time_to_next / 1000 / optimal_steps))  # 50-200ms range
        
        # Default to 100ms if no next keyframe found
        return 0.1
    
    def interpolate_position_at_time(self, time_ms):
        """Find position by interpolating between funscript keyframes with smoothing"""
        actions = self.current_pattern['actions']
        
        if not actions:
            return None
        
        # If before first point, return first position
        if time_ms <= actions[0]['at']:
            return actions[0]['pos']
        
        # If after last point, return last position
        if time_ms >= actions[-1]['at']:
            return actions[-1]['pos']
        
        # Find the two keyframes we're between
        for i in range(len(actions) - 1):
            if actions[i]['at'] <= time_ms <= actions[i + 1]['at']:
                # Smooth interpolation between these two points
                t1, pos1 = actions[i]['at'], actions[i]['pos']
                t2, pos2 = actions[i + 1]['at'], actions[i + 1]['pos']
                
                # Smooth cubic interpolation instead of linear
                ratio = (time_ms - t1) / (t2 - t1) if t2 != t1 else 0
                # Apply easing for smoother movement
                smoothed_ratio = self.ease_in_out_cubic(ratio)
                interpolated_pos = pos1 + (pos2 - pos1) * smoothed_ratio
                return interpolated_pos
        
        return None
    
    def ease_in_out_cubic(self, t):
        """Smooth cubic easing function for natural movement"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
    
    def apply_scaling(self, position, session_progress=0):
        """Apply experience and pleasure scaling with session progression"""
        # Experience scaling
        experience_multiplier = {
            'virgin': 0.4,
            'amateur': 0.6,
            'experienced': 0.8,
            'expert': 1.0,
            'pornstar': 1.2
        }[self.experience_level]
        
        # Use manual pleasure level with session progression
        base_pleasure_factor = max(0.3, self.base_pleasure / 100.0)
        
        # Session progression affects intensity (builds up over time)
        if session_progress > 0:
            session_multiplier = 0.7 + (session_progress * 0.5)  # 0.7 to 1.2 range
        else:
            session_multiplier = 1.0
            
        # Wave count affects intensity variance
        wave_intensity = 1.0 + (self.wave_count - 1) * 0.1  # Each wave adds 10%
        
        # Climax mode override
        if self.climax_mode:
            climax_multiplier = 1.5
        else:
            climax_multiplier = 1.0
        
        # Apply all scaling factors
        final_multiplier = experience_multiplier * base_pleasure_factor * session_multiplier * wave_intensity * climax_multiplier
        scaled = position * final_multiplier
        
        return min(100, max(0, scaled))
    
    def toggle_climax(self):
        """Toggle climax mode on/off"""
        self.climax_mode = not self.climax_mode
        if self.climax_mode:
            self.pattern_start_time = time.time()
        return self.climax_mode

class AIHandyGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Handy Controller - Fixed")
        self.root.geometry("1200x900")
        self.root.configure(bg='#1a1a1a')
        
        # State variables
        self.is_playing = False
        self.session_length_seconds = 1800
        self.experience_level = 'experienced'
        self.wave_count = 1
        self.pleasure_level = 0
        self.speed_multiplier = 1.0
        self.stroke_min = 0
        self.stroke_max = 100
        self.server_url = "http://localhost:8080"
        self._last_sent_pos = None
        self._last_send_time = 0
        
        # AI Engine
        self.ai_engine = AIPatternEngine()
        
        # VLC integration
        self.vlc_process = None
        self.vlc_path = self.find_vlc_executable()
        
        # Setup
        try:
            self.setup_vlc()
            self.setup_gui()
            self.load_ai_patterns()
            self.check_server_connection()
            
            # IMPROVED update loop with dynamic timing
            self.schedule_next_action()
        except Exception as e:
            print(f"Setup error: {e}")
            import traceback
            traceback.print_exc()
    
    def find_vlc_executable(self):
        """Find VLC executable on the system"""
        import subprocess
        
        if os.name == 'nt':
            possible_paths = [
                r"C:\Program Files\VideoLAN\VLC\vlc.exe",
                r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
                r"C:\Users\{}\AppData\Local\Programs\VideoLAN\VLC\vlc.exe".format(os.getenv('USERNAME', ''))
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    return path
            
            try:
                result = subprocess.run(['where', 'vlc'], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip().split('\n')[0]
            except:
                pass
        else:
            try:
                result = subprocess.run(['which', 'vlc'], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
            except:
                pass
        
        return None
    
    def setup_vlc(self):
        """Setup VLC integration"""
        if self.vlc_path:
            print(f"Found VLC at: {self.vlc_path}")
        else:
            print("VLC not found in standard locations")
    
    def launch_vlc(self):
        """Launch VLC media player"""
        if not self.vlc_path:
            messagebox.showerror("VLC Not Found", "VLC media player not found. Please install VLC.")
            return
        
        try:
            import subprocess
            self.vlc_process = subprocess.Popen([self.vlc_path])
            self.vlc_status.config(text="VLC launched", fg='#00ff41')
        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to launch VLC: {e}")
    
    def schedule_next_action(self):
        """Schedule next action - check frequently but send only when ready"""
        if self.is_playing:
            next_action = self.ai_engine.get_next_action()
            
            if next_action:
                # Apply stroke range mapping
                ai_position = next_action['position']
                range_span = self.stroke_max - self.stroke_min
                mapped_position = self.stroke_min + (ai_position / 100.0) * range_span
                device_position = mapped_position / 100.0
                
                # Send immediately - no filtering or delays
                self.send_move_command(device_position)
                
                # Update displays
                self.position_display.config(text=f"{int(mapped_position)}%")
                
                # Show session progress
                if 'session_progress' in next_action:
                    progress = next_action['session_progress']
                    remaining_time = max(0, self.session_length_seconds - (time.time() - self.ai_engine.session_start_time))
                    remaining_mins = int(remaining_time // 60)
                    remaining_secs = int(remaining_time % 60)
                    self.session_entry.delete(0, tk.END)
                    self.session_entry.insert(0, f"{remaining_mins:02d}:{remaining_secs:02d}")
            
            # Check again quickly - let the AI engine handle timing
            self.root.after(5, self.schedule_next_action)  # Very frequent checks
        else:
            # Not playing, check again later
            self.root.after(100, self.schedule_next_action)
    
    def should_send_position(self, position):
        """Determine if position should be sent (minimal filtering for smoothness)"""
        current_time = time.time()
        
        # Rate limiting: Match our target FPS (15 Hz = 66ms)
        if current_time - self._last_send_time < self.ai_engine.frame_time:
            return False
        
        # Very minimal position filtering: Only filter tiny changes
        if self._last_sent_pos is not None:
            position_diff = abs(position - self._last_sent_pos)
            if position_diff < 0.003:  # Only 0.3% threshold for ultra-smooth movement
                return False
        
        self._last_send_time = current_time
        return True
    
    def load_ai_patterns(self):
        """Load AI patterns from CSV"""
        original_csv_path = os.path.join("funscripts", "processed_patterns_original.csv")
        
        if os.path.exists(original_csv_path):
            if self.ai_engine.load_patterns(original_csv_path):
                total_patterns = sum(len(patterns) for patterns in self.ai_engine.patterns.values())
                print(f"Native Funscript Patterns loaded! Total: {total_patterns}")
                for level, patterns in self.ai_engine.patterns.items():
                    print(f"  {level}: {len(patterns)} patterns")
                self.status_label.config(text=f"✓ Native Patterns ({total_patterns})", fg='#00ff41')
            else:
                self.status_label.config(text="❌ Failed to load patterns", fg='#ff4444')
        else:
            self.status_label.config(text="❌ No patterns found", fg='#ff4444')
    
    def setup_gui(self):
        # Main container
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left side: Video player
        video_frame = tk.Frame(main_paned, bg='#1a1a1a')
        main_paned.add(video_frame, weight=2)
        
        video_label = tk.Label(video_frame, text="VLC Video Player", 
                              font=("Arial", 12, "bold"), bg='#1a1a1a', fg='white')
        video_label.pack(pady=(5, 10))
        
        video_controls = tk.Frame(video_frame, bg='#1a1a1a')
        video_controls.pack(fill=tk.X, padx=5, pady=5)
        
        launch_btn = tk.Button(video_controls, text="Launch VLC", command=self.launch_vlc,
                              bg='#333333', fg='white', font=("Arial", 10))
        launch_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.vlc_status = tk.Label(video_controls, text="VLC not launched", 
                                  bg='#1a1a1a', fg='#cccccc')
        self.vlc_status.pack(side=tk.LEFT, padx=(20, 0))
        
        # VLC placeholder
        self.vlc_frame = tk.Frame(video_frame, relief='sunken', borderwidth=2, bg='#333333')
        self.vlc_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        vlc_placeholder = tk.Label(self.vlc_frame, text="VLC will appear here when launched", 
                                  font=("Arial", 14), bg='#333333', fg='gray')
        vlc_placeholder.pack(expand=True)
        
        # Right side: AI Controls
        control_frame = tk.Frame(main_paned, bg='#1a1a1a')
        main_paned.add(control_frame, weight=1)
        
        # Connection status
        self.status_label = tk.Label(control_frame, text="Checking connection...", 
                                    font=("Arial", 12), bg='#1a1a1a', fg='#ff8800')
        self.status_label.pack(pady=(10, 15))
        
        # Experience Level
        exp_frame = tk.LabelFrame(control_frame, text="EXPERIENCE", 
                                 font=("Arial", 10, "bold"), bg='#1a1a1a', fg='#ff00ff')
        exp_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        exp_values = ["virgin", "amateur", "experienced", "expert", "pornstar"]
        self.experience_scale = tk.Scale(exp_frame, from_=0, to=len(exp_values)-1, 
                                        orient=tk.HORIZONTAL, length=300,
                                        command=self.on_experience_change,
                                        bg='#1a1a1a', fg='#ff00ff', highlightthickness=0,
                                        troughcolor='#333333', activebackground='#ff00ff')
        self.experience_scale.set(2)  # Default to "experienced"
        self.experience_scale.pack(fill=tk.X, padx=10, pady=10)
        
        self.exp_display = tk.Label(exp_frame, text="EXPERIENCED", 
                                   font=("Arial", 12, "bold"), bg='#1a1a1a', fg='#ff00ff')
        self.exp_display.pack(pady=(0, 10))
        
        # Session Length
        session_frame = tk.LabelFrame(control_frame, text="SESSION LENGTH", 
                                     font=("Arial", 10, "bold"), bg='#1a1a1a', fg='#ff00ff')
        session_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        time_entry_frame = tk.Frame(session_frame, bg='#1a1a1a')
        time_entry_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.session_entry = tk.Entry(time_entry_frame, width=10, font=("Arial", 14, "bold"),
                                     bg='#333333', fg='white', insertbackground='white')
        self.session_entry.insert(0, "30:00")
        self.session_entry.pack(side=tk.LEFT)
        self.session_entry.bind('<KeyRelease>', self.on_session_time_change)
        
        # Speed
        speed_frame = tk.LabelFrame(control_frame, text="SPEED", 
                                   font=("Arial", 10, "bold"), bg='#1a1a1a', fg='#ff00ff')
        speed_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        self.speed_scale = tk.Scale(speed_frame, from_=0.5, to=2.0, resolution=0.1,
                                   orient=tk.HORIZONTAL, length=300,
                                   command=self.on_speed_change,
                                   bg='#1a1a1a', fg='#ff00ff', highlightthickness=0,
                                   troughcolor='#333333', activebackground='#ff00ff')
        self.speed_scale.set(1.0)
        self.speed_scale.pack(fill=tk.X, padx=10, pady=10)
        
        # Range (dual handle slider)
        range_frame = tk.LabelFrame(control_frame, text="RANGE", 
                                   font=("Arial", 10, "bold"), bg='#1a1a1a', fg='#ff00ff')
        range_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        self.range_slider = DualHandleSlider(range_frame, from_=0, to=100, 
                                           initial_min=0, initial_max=100,
                                           callback=self.on_stroke_range_change)
        self.range_slider.pack(fill=tk.X, pady=(10, 10))
        
        self.range_display = tk.Label(range_frame, text="Range: 0% - 100%", 
                                     font=("Arial", 12, "bold"), bg='#1a1a1a', fg='#00ff41')
        self.range_display.pack(pady=(0, 5))
        
        # Pleasure Level
        pleasure_frame = tk.LabelFrame(control_frame, text="PLEASURE LEVEL (Wave Control)", 
                                      font=("Arial", 12, "bold"), bg='#1a1a1a', fg='#ff00ff')
        pleasure_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        self.pleasure_var = tk.IntVar()
        self.pleasure_scale = tk.Scale(pleasure_frame, from_=0, to=100, 
                                      variable=self.pleasure_var, orient=tk.HORIZONTAL, 
                                      length=350, font=("Arial", 14, "bold"),
                                      command=self.on_pleasure_change,
                                      bg='#1a1a1a', fg='#ff00ff', highlightthickness=0,
                                      troughcolor='#333333', activebackground='#ff00ff')
        self.pleasure_scale.pack(fill=tk.X, padx=10, pady=15)
        
        pleasure_display_frame = tk.Frame(pleasure_frame, bg='#1a1a1a')
        pleasure_display_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        tk.Label(pleasure_display_frame, text="Pleasure:", font=("Arial", 12), 
                bg='#1a1a1a', fg='white').pack(side=tk.LEFT)
        self.pleasure_display = tk.Label(pleasure_display_frame, text="0%", 
                                        font=("Arial", 16, "bold"), bg='#1a1a1a', fg='#ff00ff')
        self.pleasure_display.pack(side=tk.LEFT, padx=(10, 20))
        
        tk.Label(pleasure_display_frame, text="Position:", font=("Arial", 12), 
                bg='#1a1a1a', fg='white').pack(side=tk.LEFT)
        self.position_display = tk.Label(pleasure_display_frame, text="0%", 
                                        font=("Arial", 14, "bold"), bg='#1a1a1a', fg='#00ff41')
        self.position_display.pack(side=tk.LEFT, padx=(10, 0))
        
        # Wave Count
        wave_frame = tk.LabelFrame(control_frame, text="WAVE COUNT", 
                                  font=("Arial", 10, "bold"), bg='#1a1a1a', fg='#ff00ff')
        wave_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        self.wave_scale = tk.Scale(wave_frame, from_=1, to=8, 
                                  orient=tk.HORIZONTAL, length=300,
                                  command=self.on_wave_change,
                                  bg='#1a1a1a', fg='#ff00ff', highlightthickness=0,
                                  troughcolor='#333333', activebackground='#ff00ff')
        self.wave_scale.set(1)
        self.wave_scale.pack(fill=tk.X, padx=10, pady=10)
        
        # Main Control Buttons
        button_frame = tk.Frame(control_frame, bg='#1a1a1a')
        button_frame.pack(fill=tk.X, padx=10, pady=20)
        
        # Play/Pause Button
        self.play_button = tk.Button(button_frame, text="▶ PLAY", command=self.toggle_play,
                                    font=("Arial", 14, "bold"), bg='#ff00ff', fg='white',
                                    width=12, height=2)
        self.play_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Climax Button
        self.climax_button = tk.Button(button_frame, text="💦 CLIMAX", command=self.toggle_climax,
                                      font=("Arial", 14, "bold"), bg='#ff4444', fg='white',
                                      width=12, height=2)
        self.climax_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Home Button (Emergency)
        self.home_button = tk.Button(button_frame, text="🛑 HOME", command=self.emergency_home,
                                    font=("Arial", 14, "bold"), bg='#ffaa00', fg='white',
                                    width=12, height=2)
        self.home_button.pack(side=tk.LEFT)
    
    def on_experience_change(self, value):
        exp_levels = ["virgin", "amateur", "experienced", "expert", "pornstar"]
        level = exp_levels[int(float(value))]
        self.experience_level = level
        self.ai_engine.experience_level = level
        self.exp_display.config(text=level.upper())
    
    def on_session_time_change(self, event=None):
        time_str = self.session_entry.get()
        try:
            if ':' in time_str:
                parts = time_str.split(':')
                minutes = int(parts[0])
                seconds = int(parts[1]) if len(parts) > 1 else 0
                self.session_length_seconds = minutes * 60 + seconds
            else:
                self.session_length_seconds = int(time_str) * 60
        except:
            self.session_length_seconds = 1800  # Default 30 minutes
    
    def on_speed_change(self, value):
        speed = min(2.0, float(value))
        self.speed_multiplier = speed
        self.send_speed_command(speed)
    
    def on_stroke_range_change(self, min_val, max_val):
        self.stroke_min = int(min_val)
        self.stroke_max = int(max_val)
        self.range_display.config(text=f"Range: {self.stroke_min}% - {self.stroke_max}%")
    
    def on_pleasure_change(self, value):
        self.pleasure_level = int(float(value))
        self.ai_engine.base_pleasure = self.pleasure_level
        self.pleasure_display.config(text=f"{self.pleasure_level}%")
    
    def on_wave_change(self, value):
        self.wave_count = int(float(value))
    
    def toggle_play(self):
        if self.is_playing:
            print("STOPPING AI session")
            self.is_playing = False
            self.play_button.config(text="▶ PLAY", bg='#ff00ff')
            self.send_pause()
            self.position_display.config(text="Paused")
        else:
            print(f"STARTING AI session - Experience: {self.experience_level}, "
                  f"Length: {self.session_length_seconds}s, Waves: {self.wave_count}")
            self.is_playing = True
            self.play_button.config(text="⏸ PAUSE", bg='#ff4444')
            self.send_resume()
            
            # Start AI session with proper session length
            self.ai_engine.start_session(
                self.experience_level,
                self.session_length_seconds,
                self.wave_count,
                self.pleasure_level
            )
            
            # Show initial session time
            mins = self.session_length_seconds // 60
            secs = self.session_length_seconds % 60
            print(f"Session will run for {mins}:{secs:02d}")
    
    def toggle_climax(self):
        climax_active = self.ai_engine.toggle_climax()
        if climax_active:
            self.climax_button.config(text="💦 ACTIVE", bg='#ff0000')
        else:
            self.climax_button.config(text="💦 CLIMAX", bg='#ff4444')
    
    def emergency_home(self):
        """Emergency stop"""
        self.is_playing = False
        self.play_button.config(text="▶ PLAY", bg='#ff00ff')
        self.ai_engine.climax_mode = False
        self.climax_button.config(text="💦 CLIMAX", bg='#ff4444')
        self.send_move_command(0.0)
        self.position_display.config(text="HOME")
    
    def check_server_connection(self):
        """Check connection to Handy server"""
        try:
            response = requests.get(f"{self.server_url}/status", timeout=2)
            if response.status_code == 200:
                data = response.json()
                if data.get('connected'):
                    device_name = data.get('device', 'Unknown')
                    self.status_label.config(text=f"✓ Connected to {device_name}", fg='#00ff41')
                else:
                    self.status_label.config(text="❌ Handy not connected", fg='#ff4444')
            else:
                self.status_label.config(text="❌ Server error", fg='#ff4444')
        except requests.exceptions.RequestException:
            self.status_label.config(text="❌ Cannot connect to Handy server", fg='#ff4444')
        
        self.root.after(5000, self.check_server_connection)
    
    def send_move_command(self, position):
        """Send move command to device - no filtering for funscript accuracy"""
        # Send every keyframe position directly
        pos = round(position, 3)
        self._last_sent_pos = pos
        threading.Thread(target=self._send_request, args=(f"/move/{pos}",), daemon=True).start()
    
    def send_pause(self):
        """Send pause command to device"""
        threading.Thread(target=self._send_request, args=("/pause",), daemon=True).start()
    
    def send_resume(self):
        """Send resume command to device"""
        threading.Thread(target=self._send_request, args=("/resume",), daemon=True).start()
    
    def send_speed_command(self, speed):
        """Send speed command to device"""
        threading.Thread(target=self._send_request, args=(f"/speed/{speed}",), daemon=True).start()
    
    def _send_request(self, endpoint):
        """Send HTTP request to device server"""
        try:
            response = requests.get(f"{self.server_url}{endpoint}", timeout=1)
        except requests.exceptions.RequestException:
            pass
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = AIHandyGUI()
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
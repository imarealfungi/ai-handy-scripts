#!/usr/bin/env python3
"""
Complete AI Stroker System
- Uses your C# Buttplug server
- Dynamic pattern processor
- Arousal progression timeline
- Respects original funscript timing (no jitter)
"""

import tkinter as tk
from tkinter import ttk
import requests
import threading
import time
import pickle
import random
from typing import List, Dict, Optional
from dataclasses import dataclass
import queue

@dataclass
class Scene:
    file_name: str
    start_time: int
    end_time: int
    duration: float
    actions: List[Dict]
    intensity: float
    category: str
    avg_speed: float
    position_range: float
    action_density: float

class AIStrokerSystem:
    def __init__(self):
        # Core components
        self.scenes = []
        self.gentle_scenes = []
        self.medium_scenes = []
        self.intense_scenes = []
        
        # Session state
        self.is_playing = False
        self.session_start_time = None
        self.session_duration = 30  # minutes
        self.current_arousal = 0.0  # 0-100%
        self.manual_arousal_override = False
        
        # Device settings
        self.server_url = "http://localhost:8080"
        self.stroke_min = 0
        self.stroke_max = 100
        self.speed_mode = "medium"  # slow, medium, fast, random
        self.connected = False
        self.device_name = "Not Connected"
        
        # Pattern playback
        self.current_pattern = []
        self.pattern_start_time = None
        self.pattern_index = 0
        self.last_position = 0.5
        self.pattern_queue = queue.Queue()
        
        # Timing control (NO JITTER!)
        self.min_command_interval = 0.020  # 20ms minimum between commands
        self.last_command_time = 0
        
        # Load scene database
        self.load_scenes()
        
        # Setup GUI
        self.setup_gui()
        
        # Start background threads
        self.start_background_threads()
    
    def load_scenes(self):
        """Load the balanced scenes database"""
        try:
            with open("balanced_scenes_database.pkl", 'rb') as f:
                database = pickle.load(f)
            
            self.scenes = database['scenes']
            self.gentle_scenes = [s for s in self.scenes if s.category == "gentle"]
            self.medium_scenes = [s for s in self.scenes if s.category == "medium"]
            self.intense_scenes = [s for s in self.scenes if s.category == "intense"]
            
            print(f"✅ Loaded {len(self.scenes)} scenes")
            print(f"📊 Categories: {len(self.gentle_scenes)} gentle, {len(self.medium_scenes)} medium, {len(self.intense_scenes)} intense")
            
        except Exception as e:
            print(f"❌ Error loading scenes: {e}")
            self.scenes = []
    
    def setup_gui(self):
        """Create the GUI (similar to your previous working version)"""
        self.root = tk.Tk()
        self.root.title("AI Stroker - Motion Tracked Patterns")
        self.root.geometry("800x600")
        self.root.configure(bg='#2b2b2b')
        
        # Title
        title_frame = tk.Frame(self.root, bg='#2b2b2b')
        title_frame.pack(pady=20)
        
        title_label = tk.Label(title_frame, text="AI Stroker System", 
                              font=("Arial", 16, "bold"), fg="white", bg='#2b2b2b')
        title_label.pack()
        
        # Connection status
        self.status_label = tk.Label(title_frame, text="Checking connection...", 
                                   font=("Arial", 10), fg="#00ff00", bg='#2b2b2b')
        self.status_label.pack(pady=(5, 0))
        
        # Session controls
        session_frame = tk.LabelFrame(self.root, text="SESSION CONTROLS", 
                                    font=("Arial", 10, "bold"), fg="#00ffff", bg='#2b2b2b')
        session_frame.pack(fill=tk.X, padx=20, pady=10)
        
        session_inner = tk.Frame(session_frame, bg='#2b2b2b')
        session_inner.pack(fill=tk.X, padx=10, pady=10)
        
        # Session duration
        tk.Label(session_inner, text="Duration (min):", fg="white", bg='#2b2b2b').pack(side=tk.LEFT)
        self.duration_var = tk.StringVar(value="30")
        duration_entry = tk.Entry(session_inner, textvariable=self.duration_var, width=8)
        duration_entry.pack(side=tk.LEFT, padx=(5, 20))
        
        # Arousal level display and manual override
        tk.Label(session_inner, text="Arousal:", fg="white", bg='#2b2b2b').pack(side=tk.LEFT)
        self.arousal_label = tk.Label(session_inner, text="0%", font=("Arial", 12, "bold"), 
                                    fg="#ff6600", bg='#2b2b2b')
        self.arousal_label.pack(side=tk.LEFT, padx=(5, 20))
        
        # Manual arousal override slider
        tk.Label(session_inner, text="Manual Override:", fg="white", bg='#2b2b2b').pack(side=tk.LEFT)
        self.manual_arousal_var = tk.DoubleVar()
        self.arousal_slider = tk.Scale(session_inner, from_=0, to=100, orient=tk.HORIZONTAL,
                                     variable=self.manual_arousal_var, length=150,
                                     command=self.on_manual_arousal_change, bg='#2b2b2b', fg="white")
        self.arousal_slider.pack(side=tk.LEFT, padx=(5, 0))
        
        # Speed selection (like your previous version)
        speed_frame = tk.LabelFrame(self.root, text="SPEED SELECTION", 
                                  font=("Arial", 10, "bold"), fg="#00ffff", bg='#2b2b2b')
        speed_frame.pack(fill=tk.X, padx=20, pady=10)
        
        speed_buttons = tk.Frame(speed_frame, bg='#2b2b2b')
        speed_buttons.pack(pady=10)
        
        self.speed_var = tk.StringVar(value="medium")
        
        speeds = [
            ("SLOW", "slow", "#00ff00"),
            ("MEDIUM", "medium", "#ffff00"),
            ("FAST", "fast", "#ff0000"),
            ("RANDOM", "random", "#ff00ff")
        ]
        
        for text, value, color in speeds:
            btn = tk.Radiobutton(speed_buttons, text=text, variable=self.speed_var, value=value,
                               command=self.on_speed_change, bg='#2b2b2b', fg=color, 
                               selectcolor='#444444', font=("Arial", 10, "bold"))
            btn.pack(side=tk.LEFT, padx=20)
        
        # Pattern info
        self.pattern_info = tk.Label(speed_frame, text=f"Loaded {len(self.scenes)} motion-tracked patterns", 
                                   fg="#00ff00", bg='#2b2b2b')
        self.pattern_info.pack()
        
        # Stroke range (like your previous version)
        range_frame = tk.LabelFrame(self.root, text="STROKE RANGE", 
                                  font=("Arial", 10, "bold"), fg="#ff00ff", bg='#2b2b2b')
        range_frame.pack(fill=tk.X, padx=20, pady=10)
        
        range_inner = tk.Frame(range_frame, bg='#2b2b2b')
        range_inner.pack(fill=tk.X, padx=10, pady=10)
        
        self.range_var = tk.DoubleVar()
        self.range_var.set(100)  # Default to full range
        range_slider = tk.Scale(range_inner, from_=0, to=100, orient=tk.HORIZONTAL,
                              variable=self.range_var, length=400, 
                              command=self.on_range_change, bg='#2b2b2b', fg="white")
        range_slider.pack()
        
        self.range_label = tk.Label(range_inner, text="Range: 0% - 100%", 
                                  fg="#00ff41", bg='#2b2b2b')
        self.range_label.pack()
        
        # Position display
        position_frame = tk.Frame(self.root, bg='#2b2b2b')
        position_frame.pack(pady=10)
        
        tk.Label(position_frame, text="Position:", font=("Arial", 12), 
                fg="white", bg='#2b2b2b').pack(side=tk.LEFT)
        self.position_label = tk.Label(position_frame, text="0%", font=("Arial", 14, "bold"), 
                                     fg="#00ff41", bg='#2b2b2b')
        self.position_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Control buttons (like your previous version)
        button_frame = tk.Frame(self.root, bg='#2b2b2b')
        button_frame.pack(pady=20)
        
        # Play/Pause button
        self.play_button = tk.Button(button_frame, text="▶ PLAY", command=self.toggle_play,
                                   font=("Arial", 14, "bold"), bg="#ff4444", fg="white",
                                   width=12, height=2)
        self.play_button.pack(side=tk.LEFT, padx=10)
        
        # Pause button
        pause_button = tk.Button(button_frame, text="⏸ PAUSE", command=self.pause_session,
                               font=("Arial", 14, "bold"), bg="#ff8800", fg="white", 
                               width=12, height=2)
        pause_button.pack(side=tk.LEFT, padx=10)
        
        # Home button
        home_button = tk.Button(button_frame, text="🏠 HOME", command=self.home_device,
                              font=("Arial", 14, "bold"), bg="#ffaa00", fg="black",
                              width=12, height=2)
        home_button.pack(side=tk.LEFT, padx=10)
        
        # Test range button
        test_button = tk.Button(button_frame, text="🧪 TEST RANGE", command=self.test_range,
                              font=("Arial", 14, "bold"), bg="#00dddd", fg="black",
                              width=12, height=2)
        test_button.pack(side=tk.LEFT, padx=10)
    
    def start_background_threads(self):
        """Start background threads for connection checking and pattern playback"""
        # Connection checker
        connection_thread = threading.Thread(target=self.connection_checker, daemon=True)
        connection_thread.start()
        
        # Pattern player
        player_thread = threading.Thread(target=self.pattern_player, daemon=True)
        player_thread.start()
        
        # Pattern generator
        generator_thread = threading.Thread(target=self.pattern_generator, daemon=True)
        generator_thread.start()
    
    def check_server_connection(self):
        """Check C# server connection"""
        try:
            response = requests.get(f"{self.server_url}/status", timeout=2)
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('connected'):
                        self.connected = True
                        self.device_name = data.get('device', 'Unknown Device')
                        return True
                except:
                    # Try text response
                    if "connected" in response.text.lower():
                        self.connected = True
                        self.device_name = "Device Connected"
                        return True
        except Exception:
            pass
        
        self.connected = False
        self.device_name = "Not Connected"
        return False
    
    def connection_checker(self):
        """Background thread to check connection status"""
        while True:
            try:
                self.check_server_connection()
                
                if self.connected:
                    status_text = f"✅ Connected to {self.device_name} | {len(self.scenes)} patterns loaded"
                    color = "#00ff00"
                else:
                    status_text = "❌ C# Server not connected - Start your C# server!"
                    color = "#ff4444"
                
                # Update GUI on main thread
                self.root.after(0, lambda: self.status_label.config(text=status_text, fg=color))
                
                time.sleep(3)  # Check every 3 seconds
                
            except Exception as e:
                time.sleep(5)
    
    def create_dynamic_pattern(self, arousal_level, duration=60):
        """Create dynamic pattern using the processor logic"""
        if arousal_level < 30:
            available_scenes = self.gentle_scenes
        elif arousal_level < 70:
            available_scenes = self.medium_scenes
        else:
            available_scenes = self.intense_scenes
        
        if not available_scenes:
            return []
        
        # Create pattern by chaining 5-10 second segments
        segments = []
        time_used = 0
        recent_files = []
        
        while time_used < duration:
            # Pick segment length
            remaining_time = duration - time_used
            segment_length = min(random.uniform(5, 10), remaining_time)
            
            # Anti-repetition
            available_for_selection = [
                scene for scene in available_scenes 
                if scene.file_name not in recent_files[-3:]
            ]
            if not available_for_selection:
                available_for_selection = available_scenes
                recent_files = []
            
            # Pick random scene and extract segment
            scene = random.choice(available_for_selection)
            recent_files.append(scene.file_name)
            
            # Extract segment from random part of scene
            if scene.duration > segment_length:
                max_start = scene.duration - segment_length
                start_offset = random.uniform(0, max_start)
            else:
                start_offset = 0
                segment_length = scene.duration
            
            # Get actions within segment
            scene_start_time = scene.actions[0]['at']
            segment_start_time = scene_start_time + (start_offset * 1000)
            segment_end_time = segment_start_time + (segment_length * 1000)
            
            segment_actions = [
                action for action in scene.actions
                if segment_start_time <= action['at'] <= segment_end_time
            ]
            
            if len(segment_actions) >= 2:
                segments.append(segment_actions)
                time_used += segment_length
            else:
                time_used += segment_length  # Prevent infinite loop
        
        # Chain segments together with original timing preserved
        if not segments:
            return []
        
        chained_actions = []
        current_time_offset = 0
        
        for i, segment in enumerate(segments):
            # Normalize segment timing
            first_time = segment[0]['at']
            normalized_segment = [
                {
                    'at': action['at'] - first_time + current_time_offset,
                    'pos': action['pos']
                }
                for action in segment
            ]
            
            # Add smooth transition between segments if needed
            if i > 0 and chained_actions and normalized_segment:
                last_pos = chained_actions[-1]['pos']
                first_pos = normalized_segment[0]['pos']
                
                if abs(last_pos - first_pos) > 20:  # Large jump
                    transition_action = {
                        'at': current_time_offset,
                        'pos': first_pos
                    }
                    chained_actions.append(transition_action)
                    current_time_offset += 200  # 200ms transition
                    
                    # Update timing for rest of segment
                    for action in normalized_segment:
                        action['at'] += 200
            
            chained_actions.extend(normalized_segment)
            
            if normalized_segment:
                segment_duration = normalized_segment[-1]['at'] - normalized_segment[0]['at']
                current_time_offset = normalized_segment[-1]['at'] + 100  # Small gap between segments
        
        return chained_actions
    
    def pattern_generator(self):
        """Background thread to generate patterns ahead of time"""
        while True:
            try:
                if self.is_playing and self.pattern_queue.qsize() < 2:
                    # Generate next pattern based on current arousal
                    arousal = self.get_current_arousal()
                    pattern = self.create_dynamic_pattern(arousal, duration=60)
                    
                    if pattern:
                        self.pattern_queue.put(pattern)
                        print(f"🎲 Generated pattern for {arousal:.1f}% arousal ({len(pattern)} actions)")
                
                time.sleep(5)  # Generate every 5 seconds if needed
                
            except Exception as e:
                print(f"❌ Pattern generator error: {e}")
                time.sleep(10)
    
    def get_current_arousal(self):
        """Get current arousal level (auto or manual override)"""
        if self.manual_arousal_override:
            return self.current_arousal
        
        if not self.session_start_time:
            return 0.0
        
        # Auto progression
        elapsed_minutes = (time.time() - self.session_start_time) / 60.0
        progress = min(1.0, elapsed_minutes / self.session_duration)
        return progress * 100
    
    def pattern_player(self):
        """Background thread for smooth pattern playback (NO JITTER!)"""
        while True:
            try:
                if self.is_playing and self.connected:
                    # Get current pattern or load next one
                    if not self.current_pattern or self.pattern_index >= len(self.current_pattern):
                        if not self.pattern_queue.empty():
                            self.current_pattern = self.pattern_queue.get()
                            self.pattern_index = 0
                            self.pattern_start_time = time.time()
                            print(f"🎮 Started new pattern ({len(self.current_pattern)} actions)")
                        else:
                            time.sleep(0.1)
                            continue
                    
                    # Play current pattern with ORIGINAL TIMING (no interpolation!)
                    current_time_ms = (time.time() - self.pattern_start_time) * 1000
                    
                    while (self.pattern_index < len(self.current_pattern) and 
                           self.current_pattern[self.pattern_index]['at'] <= current_time_ms):
                        
                        action = self.current_pattern[self.pattern_index]
                        
                        # Rate limiting to prevent device flooding
                        if time.time() - self.last_command_time >= self.min_command_interval:
                            self.send_position_to_device(action['pos'])
                            self.last_command_time = time.time()
                        
                        self.pattern_index += 1
                
                time.sleep(0.01)  # 10ms timing precision
                
            except Exception as e:
                print(f"❌ Pattern player error: {e}")
                time.sleep(1)
    
    def send_position_to_device(self, position):
        """Send position to C# server with stroke range mapping"""
        try:
            # Apply stroke range
            range_span = self.stroke_max - self.stroke_min
            mapped_position = self.stroke_min + (position / 100.0) * range_span
            device_position = mapped_position / 100.0  # Convert to 0-1
            
            # Send to C# server (non-blocking)
            def send_request():
                try:
                    requests.get(f"{self.server_url}/move/{device_position}", timeout=0.5)
                except:
                    pass
            
            threading.Thread(target=send_request, daemon=True).start()
            
            # Update GUI
            self.last_position = mapped_position
            self.root.after(0, lambda: self.position_label.config(text=f"{int(mapped_position)}%"))
            
        except Exception as e:
            print(f"❌ Error sending position: {e}")
    
    def toggle_play(self):
        """Toggle play/pause"""
        if self.is_playing:
            self.is_playing = False
            self.play_button.config(text="▶ PLAY", bg="#00ff00")
        else:
            if not self.connected:
                print("❌ Not connected to device")
                return
            
            self.is_playing = True
            self.play_button.config(text="⏸ PAUSE", bg="#ff4444")
            
            if not self.session_start_time:
                try:
                    self.session_duration = float(self.duration_var.get())
                except:
                    self.session_duration = 30
                
                self.session_start_time = time.time()
                print(f"🚀 Started {self.session_duration}-minute session")
            
            # Resume device
            try:
                requests.get(f"{self.server_url}/resume", timeout=1)
            except:
                pass
    
    def pause_session(self):
        """Pause session"""
        self.is_playing = False
        self.play_button.config(text="▶ PLAY", bg="#00ff00")
        
        try:
            requests.get(f"{self.server_url}/pause", timeout=1)
        except:
            pass
    
    def home_device(self):
        """Send device to home position"""
        self.is_playing = False
        self.play_button.config(text="▶ PLAY", bg="#00ff00")
        
        try:
            requests.get(f"{self.server_url}/move/0.5", timeout=1)  # 50% position
        except:
            pass
    
    def test_range(self):
        """Test the current stroke range"""
        if not self.connected:
            return
        
        def test_sequence():
            try:
                # Test min position
                min_pos = self.stroke_min / 100.0
                requests.get(f"{self.server_url}/move/{min_pos}", timeout=1)
                time.sleep(1)
                
                # Test max position
                max_pos = self.stroke_max / 100.0
                requests.get(f"{self.server_url}/move/{max_pos}", timeout=1)
                time.sleep(1)
                
                # Return to middle
                requests.get(f"{self.server_url}/move/0.5", timeout=1)
            except:
                pass
        
        threading.Thread(target=test_sequence, daemon=True).start()
    
    def on_speed_change(self):
        """Handle speed selection change"""
        self.speed_mode = self.speed_var.get()
        print(f"🎚️ Speed mode: {self.speed_mode}")
    
    def on_range_change(self, value):
        """Handle stroke range change"""
        range_val = float(value)
        self.stroke_min = 0
        self.stroke_max = int(range_val)
        
        self.range_label.config(text=f"Range: {self.stroke_min}% - {self.stroke_max}%")
    
    def on_manual_arousal_change(self, value):
        """Handle manual arousal override"""
        self.current_arousal = float(value)
        self.manual_arousal_override = True
        
        # Update arousal display
        self.arousal_label.config(text=f"{int(self.current_arousal)}%")
        
        # Auto-disable override after 30 seconds
        def disable_override():
            time.sleep(30)
            self.manual_arousal_override = False
        
        threading.Thread(target=disable_override, daemon=True).start()
    
    def update_arousal_display(self):
        """Update arousal level display"""
        if not self.manual_arousal_override:
            arousal = self.get_current_arousal()
            self.arousal_label.config(text=f"{int(arousal)}%")
        
        # Schedule next update
        self.root.after(1000, self.update_arousal_display)
    
    def run(self):
        """Start the application"""
        self.update_arousal_display()
        self.root.mainloop()

def main():
    print("🚀 AI Stroker System Starting...")
    print("🔌 Make sure your C# Buttplug server is running!")
    print("📁 Make sure balanced_scenes_database.pkl exists!")
    
    app = AIStrokerSystem()
    app.run()

if __name__ == "__main__":
    main()
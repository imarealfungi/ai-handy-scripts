#!/usr/bin/env python3
"""
Dynamic Pattern Processor
Creates varied, non-boring patterns by chaining scene segments
"""

import pickle
import random
import time
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
import threading

@dataclass
class Scene:
    """Scene class for loading from database"""
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

class DynamicPatternProcessor:
    def __init__(self, database_file="balanced_scenes_database.pkl"):
        self.database_file = database_file
        self.scenes = []
        self.gentle_scenes = []
        self.medium_scenes = []
        self.intense_scenes = []
        
        # Pattern generation settings
        self.min_segment_length = 5    # seconds - minimum for rhythm
        self.max_segment_length = 10   # seconds - variety without boredom
        self.transition_time = 200     # milliseconds for smooth transitions
        
        # Load the scene database
        self.load_scene_database()
        
        print(f"🎲 Dynamic Pattern Processor Ready!")
        print(f"📊 Loaded: {len(self.gentle_scenes)} gentle, {len(self.medium_scenes)} medium, {len(self.intense_scenes)} intense")
    
    def load_scene_database(self):
        """Load the balanced scenes database"""
        try:
            with open(self.database_file, 'rb') as f:
                database = pickle.load(f)
            
            self.scenes = database['scenes']
            
            # Separate by category for fast selection
            self.gentle_scenes = [s for s in self.scenes if s.category == "gentle"]
            self.medium_scenes = [s for s in self.scenes if s.category == "medium"]
            self.intense_scenes = [s for s in self.scenes if s.category == "intense"]
            
            print(f"📖 Loaded {len(self.scenes)} scenes from database")
            
        except Exception as e:
            print(f"❌ Error loading scene database: {e}")
            self.scenes = []
    
    def extract_segment(self, scene: Scene, start_offset: float = None, duration: float = 15.0) -> List[Dict]:
        """
        Extract a segment from a scene
        
        Args:
            scene: The scene to extract from
            start_offset: Starting point in seconds (None for random)
            duration: Length of segment in seconds
        """
        if not scene.actions or len(scene.actions) < 2:
            return []
        
        # Determine starting point
        if start_offset is None:
            max_start = max(0, scene.duration - duration)
            start_offset = random.uniform(0, max_start)
        
        # Calculate time window
        scene_start_time = scene.actions[0]['at']
        segment_start_time = scene_start_time + (start_offset * 1000)  # to milliseconds
        segment_end_time = segment_start_time + (duration * 1000)
        
        # Extract actions within the window
        segment_actions = [
            action for action in scene.actions
            if segment_start_time <= action['at'] <= segment_end_time
        ]
        
        # Must have at least 2 actions to be useful
        if len(segment_actions) < 2:
            return []
        
        return segment_actions
    
    def normalize_segment_timing(self, segment_actions: List[Dict]) -> List[Dict]:
        """Reset segment timing to start at 0"""
        if not segment_actions:
            return []
        
        first_time = segment_actions[0]['at']
        
        normalized = [
            {
                'at': action['at'] - first_time,
                'pos': action['pos']
            }
            for action in segment_actions
        ]
        
        return normalized
    
    def create_smooth_transition(self, from_pos: int, to_pos: int) -> List[Dict]:
        """Create a smooth transition between two positions"""
        if abs(from_pos - to_pos) <= 5:  # Small jump, no transition needed
            return []
        
        # Create smooth transition over transition_time
        transition_action = {
            'at': 0,  # Will be adjusted when chaining
            'pos': to_pos
        }
        
        return [transition_action]
    
    def chain_segments(self, segments: List[List[Dict]]) -> List[Dict]:
        """
        Chain multiple segments together with smooth transitions
        
        Args:
            segments: List of segment action lists
            
        Returns:
            Single chained action list
        """
        if not segments:
            return []
        
        chained_actions = []
        current_time_offset = 0
        
        for i, segment in enumerate(segments):
            if not segment:
                continue
                
            # Normalize this segment's timing
            normalized_segment = self.normalize_segment_timing(segment)
            
            # Handle transitions between segments
            if i > 0 and chained_actions and normalized_segment:
                last_pos = chained_actions[-1]['pos']
                first_pos = normalized_segment[0]['pos']
                
                # Create smooth transition if needed
                transition_actions = self.create_smooth_transition(last_pos, first_pos)
                
                for transition in transition_actions:
                    chained_actions.append({
                        'at': current_time_offset,
                        'pos': transition['pos']
                    })
                    current_time_offset += self.transition_time
            
            # Add all actions from this segment
            for action in normalized_segment:
                chained_actions.append({
                    'at': action['at'] + current_time_offset,
                    'pos': action['pos']
                })
            
            # Update time offset for next segment
            if normalized_segment:
                segment_duration = normalized_segment[-1]['at']
                current_time_offset += segment_duration
        
        return chained_actions
    
    def get_scenes_for_arousal(self, arousal_level: float) -> List[Scene]:
        """Get appropriate scenes for current arousal level"""
        if arousal_level < 30:
            return self.gentle_scenes
        elif arousal_level < 70:
            return self.medium_scenes
        else:
            return self.intense_scenes
    
    def create_dynamic_pattern(self, arousal_level: float, pattern_duration: float = 60.0) -> List[Dict]:
        """
        Create a dynamic pattern by chaining random segments
        
        Args:
            arousal_level: 0-100 arousal level
            pattern_duration: Total pattern length in seconds
            
        Returns:
            Chained action list ready for playback
        """
        available_scenes = self.get_scenes_for_arousal(arousal_level)
        
        if not available_scenes:
            print(f"⚠️ No scenes available for arousal level {arousal_level}")
            return []
        
        segments = []
        time_used = 0
        recent_scenes = []  # Anti-repetition
        
        print(f"🎲 Creating dynamic pattern: {arousal_level:.1f}% arousal, {pattern_duration:.1f}s duration")
        
        while time_used < pattern_duration:
            # Pick segment length (varied for unpredictability)
            remaining_time = pattern_duration - time_used
            max_segment = min(self.max_segment_length, remaining_time)
            segment_length = random.uniform(self.min_segment_length, max_segment)
            
            # Anti-repetition: avoid recently used scenes
            available_for_selection = [
                scene for scene in available_scenes 
                if scene.file_name not in recent_scenes[-5:]  # Avoid last 5 scenes
            ]
            
            if not available_for_selection:
                available_for_selection = available_scenes  # Reset if we've used them all
                recent_scenes = []
            
            # Pick random scene
            scene = random.choice(available_for_selection)
            recent_scenes.append(scene.file_name)
            
            # Extract segment from random part of the scene
            segment = self.extract_segment(scene, duration=segment_length)
            
            if segment:
                segments.append(segment)
                time_used += segment_length
                print(f"  📝 Added {segment_length:.1f}s from {scene.file_name} (intensity: {scene.intensity:.1f})")
            else:
                print(f"  ⚠️ Failed to extract segment from {scene.file_name}")
                time_used += segment_length  # Prevent infinite loop
        
        # Chain all segments together
        print(f"🔗 Chaining {len(segments)} segments...")
        chained_pattern = self.chain_segments(segments)
        
        print(f"✅ Created dynamic pattern: {len(chained_pattern)} actions, {(chained_pattern[-1]['at'] if chained_pattern else 0)/1000:.1f}s duration")
        
        return chained_pattern
    
    def play_pattern_realtime(self, pattern_actions: List[Dict], position_callback=None):
        """
        Play a pattern in real-time
        
        Args:
            pattern_actions: The action list to play
            position_callback: Function to call with each position (pos_0_to_1)
        """
        if not pattern_actions:
            print("❌ No pattern to play")
            return
        
        print(f"🎮 Starting real-time playback: {len(pattern_actions)} actions")
        
        start_time = time.time()
        action_index = 0
        
        while action_index < len(pattern_actions):
            current_time_ms = (time.time() - start_time) * 1000
            action = pattern_actions[action_index]
            
            # Check if it's time for this action
            if current_time_ms >= action['at']:
                position_0_to_1 = action['pos'] / 100.0
                
                # Send position via callback
                if position_callback:
                    position_callback(position_0_to_1)
                else:
                    print(f"📍 Position: {action['pos']}% ({position_0_to_1:.3f})")
                
                action_index += 1
            else:
                # Sleep until next action (but not too long)
                sleep_time = min(0.01, (action['at'] - current_time_ms) / 1000.0)
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        print("✅ Pattern playback complete")
    
    def demo_arousal_progression(self, session_duration: float = 300.0):
        """
        Demo: Create patterns for different arousal levels
        
        Args:
            session_duration: Total session length in seconds
        """
        print(f"\n🚀 Demo: Arousal Progression Over {session_duration/60:.1f} Minutes")
        print("=" * 60)
        
        # Simulate arousal progression
        pattern_length = 30  # 30-second patterns
        num_patterns = int(session_duration / pattern_length)
        
        for i in range(num_patterns):
            # Calculate arousal level (0 to 100 over session)
            progress = i / (num_patterns - 1)
            arousal_level = progress * 100
            
            print(f"\n🌡️ Pattern {i+1}/{num_patterns}: {arousal_level:.1f}% arousal")
            
            # Create dynamic pattern
            pattern = self.create_dynamic_pattern(arousal_level, pattern_length)
            
            if pattern:
                print(f"   Ready to play {len(pattern)} actions over {pattern_length}s")
                # In real implementation, would play this pattern here
            else:
                print(f"   ❌ Failed to create pattern")
    
    def test_pattern_creation(self):
        """Test pattern creation for each arousal level"""
        print(f"\n🧪 Testing Pattern Creation")
        print("=" * 40)
        
        test_levels = [10, 25, 50, 75, 90]
        
        for arousal in test_levels:
            print(f"\n🎯 Testing {arousal}% arousal...")
            pattern = self.create_dynamic_pattern(arousal, 20)  # 20-second test pattern
            
            if pattern:
                # Analyze the pattern
                positions = [action['pos'] for action in pattern]
                min_pos = min(positions)
                max_pos = max(positions)
                range_span = max_pos - min_pos
                
                print(f"   ✅ Created: {len(pattern)} actions")
                print(f"   📊 Position range: {min_pos}-{max_pos} (span: {range_span})")
                print(f"   ⏱️ Duration: {pattern[-1]['at']/1000:.1f}s")
            else:
                print(f"   ❌ Failed to create pattern")

def main():
    print("🎲 Dynamic Pattern Processor")
    print("=" * 50)
    
    # Create processor
    processor = DynamicPatternProcessor()
    
    if not processor.scenes:
        print("❌ No scenes loaded, cannot continue")
        return
    
    # Test pattern creation
    processor.test_pattern_creation()
    
    # Demo arousal progression
    processor.demo_arousal_progression(300)  # 5-minute demo
    
    print(f"\n✅ Dynamic Pattern Processor ready for integration!")
    print(f"🎯 Use create_dynamic_pattern(arousal_level, duration) to generate varied patterns")

if __name__ == "__main__":
    main()
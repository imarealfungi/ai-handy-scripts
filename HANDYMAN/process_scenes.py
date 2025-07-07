#!/usr/bin/env python3
"""
Fix the intensity distribution using percentiles of YOUR actual data
"""

import pickle
import numpy as np
from dataclasses import dataclass
from typing import List, Dict

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

def fix_intensity_distribution():
    """Fix the intensity categorization using data-driven thresholds"""
    
    print("🔧 Fixing Intensity Distribution")
    print("=" * 40)
    
    # Load the fixed scenes database
    try:
        with open("fixed_scenes_database.pkl", 'rb') as f:
            database = pickle.load(f)
        scenes = database['scenes']
        print(f"📖 Loaded {len(scenes)} scenes")
    except Exception as e:
        print(f"❌ Error loading database: {e}")
        return
    
    # Analyze the actual intensity distribution in YOUR data
    intensities = [scene.intensity for scene in scenes]
    
    print(f"\n📊 Your Data Intensity Stats:")
    print(f"  Min intensity: {min(intensities):.1f}")
    print(f"  Max intensity: {max(intensities):.1f}")
    print(f"  Average: {np.mean(intensities):.1f}")
    print(f"  Median: {np.median(intensities):.1f}")
    
    # Use percentiles of YOUR data for thresholds
    # This ensures proper 40/35/25 distribution
    gentle_threshold = np.percentile(intensities, 40)    # Bottom 40% = gentle
    intense_threshold = np.percentile(intensities, 75)   # Top 25% = intense
    
    print(f"\n🎚️ Data-Driven Thresholds:")
    print(f"  Gentle: 0 - {gentle_threshold:.1f}")
    print(f"  Medium: {gentle_threshold:.1f} - {intense_threshold:.1f}")
    print(f"  Intense: {intense_threshold:.1f} - 100")
    
    # Recategorize all scenes using these thresholds
    gentle_count = 0
    medium_count = 0
    intense_count = 0
    
    for scene in scenes:
        if scene.intensity <= gentle_threshold:
            scene.category = "gentle"
            gentle_count += 1
        elif scene.intensity <= intense_threshold:
            scene.category = "medium"
            medium_count += 1
        else:
            scene.category = "intense"
            intense_count += 1
    
    print(f"\n✅ Recategorized {len(scenes)} scenes:")
    print(f"  🟢 Gentle: {gentle_count} ({gentle_count/len(scenes)*100:.1f}%)")
    print(f"  🟡 Medium: {medium_count} ({medium_count/len(scenes)*100:.1f}%)")
    print(f"  🔴 Intense: {intense_count} ({intense_count/len(scenes)*100:.1f}%)")
    
    # Update database stats
    database['stats']['gentle_scenes'] = gentle_count
    database['stats']['medium_scenes'] = medium_count
    database['stats']['intense_scenes'] = intense_count
    database['version'] = '2.1_balanced'
    
    # Save the fixed database
    try:
        with open("balanced_scenes_database.pkl", 'wb') as f:
            pickle.dump(database, f)
        print(f"\n💾 Saved balanced database to: balanced_scenes_database.pkl")
        
        # Show some sample scenes from each category
        print(f"\n📋 Sample Scenes From Each Category:")
        
        gentle_scenes = [s for s in scenes if s.category == "gentle"][:3]
        medium_scenes = [s for s in scenes if s.category == "medium"][:3]
        intense_scenes = [s for s in scenes if s.category == "intense"][:3]
        
        print(f"\n🟢 GENTLE SAMPLES:")
        for scene in gentle_scenes:
            print(f"  {scene.file_name} - {scene.duration:.1f}s, intensity: {scene.intensity:.1f}")
            print(f"    Speed: {scene.avg_speed:.1f}, Range: {scene.position_range:.1f}")
        
        print(f"\n🟡 MEDIUM SAMPLES:")
        for scene in medium_scenes:
            print(f"  {scene.file_name} - {scene.duration:.1f}s, intensity: {scene.intensity:.1f}")
            print(f"    Speed: {scene.avg_speed:.1f}, Range: {scene.position_range:.1f}")
        
        print(f"\n🔴 INTENSE SAMPLES:")
        for scene in intense_scenes:
            print(f"  {scene.file_name} - {scene.duration:.1f}s, intensity: {scene.intensity:.1f}")
            print(f"    Speed: {scene.avg_speed:.1f}, Range: {scene.position_range:.1f}")
        
        print(f"\n🎯 PERFECT! Now you have properly balanced training data!")
        print(f"✅ Ready to build the AI arousal progression system!")
        
    except Exception as e:
        print(f"❌ Error saving balanced database: {e}")

if __name__ == "__main__":
    fix_intensity_distribution()
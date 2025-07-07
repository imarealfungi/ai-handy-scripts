#!/usr/bin/env python3
"""
View the extracted scenes database
"""

import pickle
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Scene:
    """Represents one extracted scene - needed for pickle loading"""
    file_name: str
    start_time: int  # milliseconds
    end_time: int    # milliseconds
    duration: float  # seconds
    actions: List[Dict]  # the actual funscript actions
    intensity: float  # 0-100 intensity score
    category: str    # gentle/medium/intense
    avg_speed: float
    position_range: float
    action_density: float

def view_scenes_database():
    print("📖 Viewing Scenes Database")
    print("=" * 40)
    
    # Check if database exists
    db_file = "scenes_database.pkl"
    if not os.path.exists(db_file):
        print("❌ scenes_database.pkl not found!")
        return
    
    # Get file size
    file_size = os.path.getsize(db_file)
    print(f"💾 Database file size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
    
    try:
        # Load the database
        print("📖 Loading database...")
        with open(db_file, 'rb') as f:
            database = pickle.load(f)
        
        scenes = database.get('scenes', [])
        stats = database.get('stats', {})
        created_at = database.get('created_at', 0)
        
        print(f"✅ Database loaded successfully!")
        print(f"🕐 Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(created_at)) if created_at else 'Unknown'}")
        
        # Show overall stats
        print(f"\n📊 OVERALL STATS:")
        print(f"  Files processed: {stats.get('files_processed', 0)}")
        print(f"  Total scenes extracted: {len(scenes)}")
        
        if scenes:
            total_duration = sum(scene.duration for scene in scenes)
            print(f"  Total content: {total_duration/60:.1f} minutes")
            
            # Category breakdown
            gentle_count = len([s for s in scenes if s.category == 'gentle'])
            medium_count = len([s for s in scenes if s.category == 'medium'])  
            intense_count = len([s for s in scenes if s.category == 'intense'])
            
            print(f"\n🎚️ INTENSITY CATEGORIES:")
            print(f"  🟢 Gentle: {gentle_count} scenes ({gentle_count/len(scenes)*100:.1f}%)")
            print(f"  🟡 Medium: {medium_count} scenes ({medium_count/len(scenes)*100:.1f}%)")
            print(f"  🔴 Intense: {intense_count} scenes ({intense_count/len(scenes)*100:.1f}%)")
            
            # Show sample scenes from each category
            print(f"\n📋 SAMPLE SCENES:")
            
            categories = [
                ('🟢 GENTLE', [s for s in scenes if s.category == 'gentle']),
                ('🟡 MEDIUM', [s for s in scenes if s.category == 'medium']),
                ('🔴 INTENSE', [s for s in scenes if s.category == 'intense'])
            ]
            
            for cat_name, cat_scenes in categories:
                if cat_scenes:
                    print(f"\n{cat_name} SCENES (showing first 5):")
                    for i, scene in enumerate(cat_scenes[:5], 1):
                        print(f"  {i}. {scene.file_name}")
                        print(f"     Duration: {scene.duration:.1f}s, Intensity: {scene.intensity:.1f}")
                        print(f"     Speed: {scene.avg_speed:.1f}, Range: {scene.position_range:.1f}")
            
            # Show intensity distribution
            print(f"\n📊 INTENSITY DISTRIBUTION:")
            intensities = [scene.intensity for scene in scenes]
            import numpy as np
            
            bins = [0, 20, 40, 60, 80, 100]
            labels = ['0-20', '20-40', '40-60', '60-80', '80-100']
            
            for i in range(len(bins)-1):
                count = len([x for x in intensities if bins[i] <= x < bins[i+1]])
                bar = "█" * max(1, count // 10)
                print(f"  {labels[i]:>6}: {count:4d} scenes {bar}")
            
            # Show files with most scenes
            print(f"\n📁 TOP FILES BY SCENE COUNT:")
            file_scene_counts = {}
            for scene in scenes:
                file_scene_counts[scene.file_name] = file_scene_counts.get(scene.file_name, 0) + 1
            
            top_files = sorted(file_scene_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            for filename, count in top_files:
                print(f"  {count:3d} scenes: {filename}")
                
        else:
            print("⚠️ No scenes found in database")
            
    except Exception as e:
        print(f"❌ Error loading database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import time
    import numpy as np
    view_scenes_database()
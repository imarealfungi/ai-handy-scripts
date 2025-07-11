import json
import os
from pathlib import Path

def analyze_pattern_speed(funscript_path):
    """Analyze a funscript and return intensity metrics"""
    with open(funscript_path, 'r') as f:
        data = json.load(f)
        actions = data.get('actions', [])
    
    if len(actions) < 2:
        return 0  # No movement = 0 intensity
    
    # Calculate average speed between actions
    speeds = []
    for i in range(1, len(actions)):
        time_diff = actions[i]['at'] - actions[i-1]['at']
        pos_diff = abs(actions[i]['pos'] - actions[i-1]['pos'])
        if time_diff > 0:
            speed = pos_diff / time_diff  # positions per ms
            speeds.append(speed)
    
    return sum(speeds) / len(speeds) if speeds else 0

def classify_all_patterns():
    """Scan all patterns and classify them"""
    funscript_folder = "FUNSCRIPTS"  # Your folder path
    results = {}
    
    for folder in ['bj', 'transitions', 'twerk']:
        folder_path = os.path.join(funscript_folder, folder)
        if os.path.exists(folder_path):
            for file in os.listdir(folder_path):
                if file.endswith('.funscript'):
                    file_path = os.path.join(folder_path, file)
                    intensity = analyze_pattern_speed(file_path)
                    results[file] = {
                        'category': folder,
                        'intensity': intensity,
                        'speed_class': 'slow' if intensity < 0.1 else 'medium' if intensity < 0.3 else 'fast'
                    }
    
    # Save results
    with open('pattern_speeds.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Analyzed {len(results)} patterns:")
    for speed_class in ['slow', 'medium', 'fast']:
        count = sum(1 for p in results.values() if p['speed_class'] == speed_class)
        print(f"  {speed_class}: {count} patterns")

if __name__ == "__main__":
    classify_all_patterns()
## **Current Working Components:**

### **1. Core Device Control System**
- **`rpg.py`** - Main GUI with device controls, pattern playbook, range sliders, **speed control (basic 1.5x multiplier)**, and **NEW TWERK MODE**
- **`device_handler.py`** - Pattern management with endpoint categorization (0→0, 100→100, **50→50 twerk patterns**), smart chaining, smooth transitions
- **C# Buttplug Server** - Handles The Handy device communication via Intiface Central (position rounding fix applied)
- **Pattern Library** - Organized funscripts in folders: `bj/`, `transitions/`, `twerk/` with 70+ twerk patterns (50→50 format)

### **2. Pattern Processing Pipeline**
- **`sort.py`** - Extracts 10-second pattern slices, categorizes by start/end positions including 50→50 twerk patterns
- **Smart Pattern Selection** - Automatic smooth transitions between pattern types based on current position
- **Range Control** - User-adjustable min/max limits, twerk mode switches pattern sets

### **3. Speed & Queuing System Design**

#### **Current Speed Implementation:**
- Basic `* 1.5` multiplier in `device_handler.py` (barely noticeable)
- **Future Enhancement:** AI-controlled dynamic speed adjustment based on arousal/session

#### **Planned Session Queue System:**
- **Pattern Speed Analysis:** Classify patterns by natural intensity/speed
- **AI Speed Control:** Dynamic speed multipliers (1.0x to 3.0x+) controlled by arousal level
- **Session Progression:** Pre-built queue with speed ramping over session length
- **Real-time Adjustments:** AI modifies speed multipliers based on chat interaction

### **4. Current Workflow**
1. Load patterns from funscript folders (auto-detects normal + twerk)
2. Connect to C# server → Intiface Central → The Handy device
3. Play/pause with smooth pattern chaining and transitions
4. Twerk mode button switches to 50→50 patterns seamlessly

## **Next Integration Goals:**

### **AI Chat & Dynamic Control System**
- Local LLM integration for chat interface
- Session timer input (MM:SS format)
- **AI-Controlled Speed:** Dynamic speed multipliers based on arousal + chat analysis
- **Pattern Speed Classification:** Analyze patterns to determine base intensity levels
- Arousal meter that increases based on:
  - Session duration progression
  - Chat content "steaminess" analysis
  - **Speed adjustments:** AI slows down intense patterns for buildup, speeds up gentle ones for climax

### **Session Queue with Speed Control**
- **Pattern Analysis:** Classify all patterns by natural speed/intensity
- **Queue Building:** Pre-select pattern sequence based on session length
- **Dynamic Speed Layer:** AI applies real-time speed multipliers (0.5x - 3.0x) to queued patterns
- **Progression Curve:** Slow start → gradual buildup → intensity peaks → controlled finish

### **Image Generation & Character System**
- ComfyUI integration (workflow ready with PuLID)
- 1024×1536 generated images from prompts
- 512×512 character upload box
- Auto-convert uploaded images to JPEG → overwrites PuLID reference image
- Character consistency across generated images

### **Files to Create:**
1. **`ai_engine.py`** - Local LLM client + arousal tracking + **dynamic speed control**
2. **`session_manager.py`** - Pattern analysis, queue building, **speed classification & control**
3. **`comfyui_client.py`** - ComfyUI API + PuLID workflow
4. **`chat_ui.py`** - Chat interface components
5. **`image_display.py`** - Generated image viewer
6. **`face_manager.py`** - Character image upload/management
7. **`arousal_display.py`** - Visual arousal meter + session timer

### **Integration Points:**
- **AI Speed Control:** Real-time speed multiplier adjustments (bypass manual SLOW button)
- **Pattern Speed Analysis:** Classify patterns by intensity for smart queue building
- **Session-Based Progression:** Pre-built queues with AI-controlled speed ramping
- **Arousal-Driven Adjustments:** Chat analysis influences speed changes dynamically
- Character uploads trigger ComfyUI image generation
- All components modular, importable into main `rpg.py`

### **Implementation Priority:**
1. **Pattern speed analysis** - classify existing patterns by intensity
2. **AI speed control layer** - dynamic multipliers replacing static slow mode
3. **Session queue system** - pre-built progression with speed ramping
4. **Chat + arousal integration** - AI-driven real-time adjustments

**Current Status:** Basic device control complete. Ready for AI-controlled dynamic speed system and session management integration.

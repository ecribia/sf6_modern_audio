import cv2
import numpy as np
import time
import platform
from pathlib import Path
from pygame import mixer

mixer.init()

REFERENCE_IMAGE = "modern.png"
AUDIO_FILE = "audio.mp3"
CHECK_INTERVAL = 2  # seconds
COOLDOWN_PERIOD = 20  # seconds
SIMILARITY_THRESHOLD = 0.98

REGIONS = [
    {"top": 834, "left": 56, "width": 35, "height": 31},
    {"top": 835, "left": 1830, "width": 35, "height": 31}
]

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

def load_reference_image():
    """Load the reference image for comparison"""
    ref_path = Path(__file__).parent / REFERENCE_IMAGE
    if not ref_path.exists():
        raise FileNotFoundError(f"Reference image not found: {ref_path}")
    
    img = cv2.imread(str(ref_path), cv2.IMREAD_UNCHANGED)
    
    if img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    
    return img

def capture_region_windows(region):
    """Capture region on Windows using mss"""
    import mss
    with mss.mss() as sct:
        screenshot = sct.grab(region)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img

def capture_region_linux(region):
    """Capture region on Linux (Wayland/X11) using grim"""
    import subprocess
    
    left = region["left"]
    top = region["top"]
    width = region["width"]
    height = region["height"]
    
    geometry = f"{left},{top} {width}x{height}"
    
    try:
        result = subprocess.run(
            ['grim', '-g', geometry, '-'],
            capture_output=True,
            check=True
        )
        img_array = np.frombuffer(result.stdout, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return img
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode() if e.stderr else "No error message"
        raise RuntimeError(f"grim failed: {stderr}")

def capture_region(region):
    """Cross-platform screenshot capture"""
    if IS_WINDOWS:
        return capture_region_windows(region)
    elif IS_LINUX:
        return capture_region_linux(region)
    else:
        raise NotImplementedError(f"Unsupported OS: {platform.system()}")

def compare_images(img1, img2):
    """Compare two images and return similarity score (0-1)"""
    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
    
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    mse = np.mean((gray1.astype(float) - gray2.astype(float)) ** 2)
    
    max_mse = 255 ** 2
    similarity = 1 - (mse / max_mse)
    
    return similarity

def play_audio():
    """Play the audio file"""
    audio_path = Path(__file__).parent / AUDIO_FILE
    if not audio_path.exists():
        print(f"Warning: Audio file not found: {audio_path}")
        return
    
    try:
        mixer.music.load(str(audio_path))
        mixer.music.play()
    except Exception as e:
        print(f"Error playing audio: {e}")

def main():
    print(f"Screen Monitor Starting on {platform.system()}...")
    print(f"Monitoring {len(REGIONS)} regions every {CHECK_INTERVAL} seconds")
    print(f"Similarity threshold: {SIMILARITY_THRESHOLD * 100}%")
    print(f"Audio cooldown: {COOLDOWN_PERIOD} seconds")
    print("Press Ctrl+C to stop\n")
    
    try:
        reference_img = load_reference_image()
        print(f"✓ Reference image loaded: {REFERENCE_IMAGE}")
        print(f"  Reference image size: {reference_img.shape}")
        
        # Save reference for debugging
        cv2.imwrite("debug_reference.png", reference_img)
        print(f"  Saved reference as debug_reference.png for comparison\n")
    except Exception as e:
        print(f"Error loading reference image: {e}")
        return
    
    last_audio_time = 0
    
    try:
        while True:
            match_found = False
            
            for i, region in enumerate(REGIONS, 1):
                try:
                    screen_img = capture_region(region)
                    
                    # DEBUG: Save what we captured
                    debug_path = f"debug_region_{i}.png"
                    cv2.imwrite(debug_path, screen_img)
                    
                    similarity = compare_images(screen_img, reference_img)
                    
                    print(f"Region {i}: {similarity * 100:.1f}% match", end=" | ")
                    
                    if similarity >= SIMILARITY_THRESHOLD:
                        match_found = True
                        print(f"✓ MATCH!", end="")
                except Exception as e:
                    print(f"Region {i}: Error - {e}", end=" | ")
            
            print()
            
            if match_found:
                current_time = time.time()
                if current_time - last_audio_time >= COOLDOWN_PERIOD:
                    print("🔊 Playing audio alert...")
                    play_audio()
                    last_audio_time = current_time
                else:
                    remaining = int(COOLDOWN_PERIOD - (current_time - last_audio_time))
                    print(f"⏳ Cooldown active ({remaining}s remaining)")
            
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")

if __name__ == "__main__":
    main()

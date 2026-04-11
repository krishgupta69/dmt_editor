import json
import os

def create_template(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    base_dir = "templates"
    
    # templates/trending/cinematic_reel.json: 30s, 6 video slots 5s each, orange+teal LUT, zoom_blur transitions
    clips = []
    for i in range(6):
        clips.append({
            "slot_id": i+1, "placeholder": True, "position": float(i*5), "duration": 5.0,
            "effects": ["zoom_blur"], "color_grade": "orange+teal_lut", "transition_in": "fade", "transition_out": "fade"
        })
    create_template(f"{base_dir}/trending/cinematic_reel.json", {
        "template_id": "trending_cinematic_01", "name": "Cinematic Reel", "category": "Trending",
        "thumbnail": "gradient_cinematic", "duration": 30.0, "fps": 30.0, "resolution": [1920, 1080],
        "tracks": [{"track_id": 1, "type": "video", "clips": clips}]
    })

    # templates/trending/gaming_montage.json: 15s, 5 slots 3s each, high contrast LUT, flash transitions
    clips = []
    for i in range(5):
        clips.append({
            "slot_id": i+1, "placeholder": True, "position": float(i*3), "duration": 3.0,
            "effects": [], "color_grade": "high_contrast", "transition_in": "flash", "transition_out": "flash"
        })
    create_template(f"{base_dir}/trending/gaming_montage.json", {
        "template_id": "trending_gaming_01", "name": "Gaming Montage", "category": "Trending",
        "thumbnail": "gradient_gaming", "duration": 15.0, "fps": 60.0, "resolution": [1920, 1080],
        "tracks": [{"track_id": 1, "type": "video", "clips": clips}]
    })

    # templates/trending/vlog_aesthetic.json: 60s, 8 slots mixed duration, warm LUT, crossfades
    clips = []
    for i in range(8):
        dur = 7.5
        clips.append({
            "slot_id": i+1, "placeholder": True, "position": float(i*dur), "duration": dur,
            "effects": [], "color_grade": "warm_lut", "transition_in": "crossfade", "transition_out": "crossfade"
        })
    create_template(f"{base_dir}/trending/vlog_aesthetic.json", {
        "template_id": "trending_vlog_01", "name": "Vlog Aesthetic", "category": "Trending",
        "thumbnail": "gradient_vlog", "duration": 60.0, "fps": 30.0, "resolution": [1920, 1080],
        "tracks": [{"track_id": 1, "type": "video", "clips": clips}]
    })

    # templates/social/tiktok_viral.json: 15s, 9:16 vertical, 5 slots 3s, fast cuts no transitions
    clips = []
    for i in range(5):
        clips.append({
            "slot_id": i+1, "placeholder": True, "position": float(i*3), "duration": 3.0,
            "effects": [], "color_grade": None, "transition_in": "cut", "transition_out": "cut"
        })
    create_template(f"{base_dir}/social/tiktok_viral.json", {
        "template_id": "social_tiktok_01", "name": "TikTok Viral", "category": "Social",
        "thumbnail": "gradient_tiktok", "duration": 15.0, "fps": 30.0, "resolution": [1080, 1920],
        "tracks": [{"track_id": 1, "type": "video", "clips": clips}]
    })

    # templates/social/instagram_reel.json: 30s, 9:16, 4 slots 7.5s, soft grade
    clips = []
    for i in range(4):
        clips.append({
            "slot_id": i+1, "placeholder": True, "position": float(i*7.5), "duration": 7.5,
            "effects": [], "color_grade": "soft_grade", "transition_in": "cut", "transition_out": "cut"
        })
    create_template(f"{base_dir}/social/instagram_reel.json", {
        "template_id": "social_ig_01", "name": "Instagram Reel", "category": "Social",
        "thumbnail": "gradient_ig", "duration": 30.0, "fps": 30.0, "resolution": [1080, 1920],
        "tracks": [{"track_id": 1, "type": "video", "clips": clips}]
    })

    # templates/social/youtube_shorts.json: 60s, 9:16, 6 slots
    clips = []
    for i in range(6):
        clips.append({
            "slot_id": i+1, "placeholder": True, "position": float(i*10), "duration": 10.0,
            "effects": [], "color_grade": None, "transition_in": "cut", "transition_out": "cut"
        })
    create_template(f"{base_dir}/social/youtube_shorts.json", {
        "template_id": "social_shorts_01", "name": "YouTube Shorts", "category": "Social",
        "thumbnail": "gradient_yt", "duration": 60.0, "fps": 30.0, "resolution": [1080, 1920],
        "tracks": [{"track_id": 1, "type": "video", "clips": clips}]
    })

    # templates/cinematic/film_noir.json: 60s, 6 slots, black+white LUT, slow crossfades
    clips = []
    for i in range(6):
        clips.append({
            "slot_id": i+1, "placeholder": True, "position": float(i*10), "duration": 10.0,
            "effects": [], "color_grade": "bw_lut", "transition_in": "slow_crossfade", "transition_out": "slow_crossfade"
        })
    create_template(f"{base_dir}/cinematic/film_noir.json", {
        "template_id": "cinematic_noir_01", "name": "Film Noir", "category": "Cinematic",
        "thumbnail": "gradient_noir", "duration": 60.0, "fps": 24.0, "resolution": [1920, 1080],
        "tracks": [{"track_id": 1, "type": "video", "clips": clips}]
    })

    # templates/wedding/romantic.json: 120s, 8 slots, soft pink warm LUT
    clips = []
    for i in range(8):
        clips.append({
            "slot_id": i+1, "placeholder": True, "position": float(i*15), "duration": 15.0,
            "effects": [], "color_grade": "soft_pink_lut", "transition_in": "fade", "transition_out": "fade"
        })
    create_template(f"{base_dir}/wedding/romantic.json", {
        "template_id": "wedding_romantic_01", "name": "Romantic Wedding", "category": "Wedding",
        "thumbnail": "gradient_wedding", "duration": 120.0, "fps": 30.0, "resolution": [1920, 1080],
        "tracks": [{"track_id": 1, "type": "video", "clips": clips}]
    })

if __name__ == "__main__":
    main()

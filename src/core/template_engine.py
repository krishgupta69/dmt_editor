import os
import json
import glob

try:
    import openshot
    OPENSHOT_AVAILABLE = True
except ImportError:
    OPENSHOT_AVAILABLE = False
    class MockTimeline:
        pass
    class openshot:
        Timeline = MockTimeline

class TemplateEngine:
    def __init__(self, templates_dir="templates"):
        self.templates_dir = templates_dir

    def load_template(self, path):
        """Loads and validates a template JSON against the basic schema."""
        with open(path, 'r') as f:
            data = json.load(f)
            
        # Basic validation
        required_keys = ['template_id', 'name', 'category', 'thumbnail', 
                         'duration', 'fps', 'resolution', 'tracks']
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Template {path} missing required key: {key}")
                
        return data

    def list_templates(self, category=None):
        """Returns a list of template dicts, optionally filtered by category."""
        templates = []
        # Search recursively for JSON files in the templates directory
        search_pattern = os.path.join(self.templates_dir, "**", "*.json")
        for path in glob.glob(search_pattern, recursive=True):
            try:
                tpl = self.load_template(path)
                if category is None or category.lower() == "all" or tpl['category'].lower() == category.lower():
                    templates.append(tpl)
            except Exception as e:
                print(f"Error loading template {path}: {e}")
        return templates

    def apply_template(self, template, media_paths):
        """
        Takes a template dict and a list of absolute media paths.
        Returns a configured openshot.Timeline.
        """
        # Count required placeholders
        slots_needed = 0
        for track in template.get('tracks', []):
            for clip in track.get('clips', []):
                if clip.get('placeholder', False):
                    slots_needed += 1

        if len(media_paths) < slots_needed:
            raise ValueError(f"Template requires {slots_needed} media files, but {len(media_paths)} were provided.")

        if OPENSHOT_AVAILABLE:
            width, height = template['resolution']
            timeline = openshot.Timeline(width, height, openshot.Fraction(int(template['fps']), 1), 
                                       int(template['fps']), 44100, 2)
            timeline.Open()
            # In a full implementation, we traverse media_paths and create openshot.Clip 
            # and openshot.Reader, placing them at position according to clip['position']
            media_idx = 0
            for track in template.get('tracks', []):
                track_id = track['track_id']
                for clip_data in track.get('clips', []):
                    if clip_data.get('placeholder', False):
                        path = media_paths[media_idx]
                        media_idx += 1
                        # c = openshot.Clip(path)
                        # c.Position(clip_data['position'])
                        # c.Layer(track_id)
                        # timeline.AddClip(c)
                        # Apply fx based on clip_data
            return timeline
        else:
            # Fallback mock for UI development
            print(f"Mocking template application for {template['name']} using {len(media_paths)} files.")
            mock = openshot.Timeline()
            mock.template_data = template
            mock.media_paths = media_paths
            return mock

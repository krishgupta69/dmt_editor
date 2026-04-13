from PyQt6.QtGui import QUndoCommand
from PyQt6.QtCore import Qt
from pathlib import Path

class AddClipCommand(QUndoCommand):
    def __init__(self, project, timeline_widget, file_path, track, position, clip_item):
        super().__init__(f"Add {Path(file_path).name}")
        self.project = project
        self.widget = timeline_widget
        self.file_path = file_path
        self.track = track
        self.position = position
        self.clip_item = clip_item
        self.clip_id = None
        
    def redo(self):
        self.clip_id = self.project.add_clip(self.file_path, self.track, self.position)
        self.clip_item.setData(Qt.ItemDataRole.UserRole, self.clip_id)
        if self.clip_item.scene() is None:
            self.widget.scene.addItem(self.clip_item)
            
    def undo(self):
        self.project.remove_clip(self.clip_id)
        self.widget.scene.removeItem(self.clip_item)

class RemoveClipCommand(QUndoCommand):
    def __init__(self, project, timeline_widget, clip_id, clip_item):
        name = clip_item.text.toPlainText() if hasattr(clip_item, 'text') else "Clip"
        super().__init__(f"Remove {name}")
        self.project = project
        self.widget = timeline_widget
        self.clip_id = clip_id
        self.clip_item = clip_item
        # Assuming we need to store track/position if we redid it
        self.track = 0  # Simplified
        self.position = self.clip_item.x() / 10.0
        self.file_path = getattr(self.clip_item, 'file_path', '')
        
    def redo(self):
        self.project.remove_clip(self.clip_id)
        self.widget.scene.removeItem(self.clip_item)
        
    def undo(self):
        # We simulate re-adding with the same id, but DummyProject might give a new one
        # So we better just use the standard add and re-assign
        new_id = self.project.add_clip(self.file_path, self.track, self.position)
        self.clip_id = new_id
        self.clip_item.setData(Qt.ItemDataRole.UserRole, self.clip_id)
        if self.clip_item.scene() is None:
            self.widget.scene.addItem(self.clip_item)

class MoveClipCommand(QUndoCommand):
    def __init__(self, project, clip_id, clip_item, old_pos, new_pos):
        super().__init__(f"Move Clip")
        self.project = project
        self.clip_id = clip_id
        self.clip_item = clip_item
        self.old_pos = old_pos
        self.new_pos = new_pos
        
    def redo(self):
        self.project.move_clip(self.clip_id, self.new_pos)
        self.clip_item.setX(self.new_pos * 10.0)
        
    def undo(self):
        self.project.move_clip(self.clip_id, self.old_pos)
        self.clip_item.setX(self.old_pos * 10.0)

class TrimClipCommand(QUndoCommand):
    def __init__(self, project, clip_id, clip_item, old_start, old_end, new_start, new_end):
        super().__init__(f"Trim Clip")
        self.project = project
        self.clip_id = clip_id
        self.clip_item = clip_item
        self.old_start = old_start
        self.old_end = old_end
        self.new_start = new_start
        self.new_end = new_end
        
    def redo(self):
        self.project.trim_clip(self.clip_id, self.new_start, self.new_end)
        w = max(10, (self.new_end - self.new_start) * 10.0)
        rect = self.clip_item.rect()
        rect.setWidth(w)
        self.clip_item.setRect(rect)
        
    def undo(self):
        self.project.trim_clip(self.clip_id, self.old_start, self.old_end)
        w = max(10, (self.old_end - self.old_start) * 10.0)
        rect = self.clip_item.rect()
        rect.setWidth(w)
        self.clip_item.setRect(rect)

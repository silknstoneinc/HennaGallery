"""
Track changes for undo/redo functionality
"""

class HistoryManager:
    def __init__(self, max_steps=50):
        self.undo_stack = []
        self.redo_stack = []
        self.max_steps = max_steps

    def record_change(self, item_id, old_state, new_state):
        self.undo_stack.append((item_id, old_state, new_state))
        if len(self.undo_stack) > self.max_steps:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            return self.undo_stack.pop()
        return None

    def redo(self):
        if self.redo_stack:
            return self.redo_stack.pop()
        return None
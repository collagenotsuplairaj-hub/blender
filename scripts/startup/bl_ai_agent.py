import bpy
import traceback
from datetime import datetime
from pathlib import Path

AI_VERSION = "v3"

def _log_error(msg: str):
    try:
        log_path = Path(bpy.utils.user_resource('SCRIPTS', create=True)) / "ai_agent_log.txt"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except Exception:
        pass

def _find_view3d_area():
    """Find a VIEW_3D area in any window."""
    try:
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    return window, area
    except Exception as e:
        _log_error(f"_find_view3d_area: {e}\n{traceback.format_exc()}")
    return None, None

# Timer to wait for window and VIEW_3D area
_popup_timer_count = 0

def _popup_timer():
    """Timer that runs every 0.5s until window and VIEW_3D area are available."""
    global _popup_timer_count
    try:
        _popup_timer_count += 1

        if not bpy.context.window_manager.windows:
            if _popup_timer_count >= 40:
                _log_error("_popup_timer: max attempts reached, no windows")
                return None
            return 0.5

        window, area = _find_view3d_area()
        if window is None or area is None:
            if _popup_timer_count >= 40:
                _log_error("_popup_timer: max attempts reached, no VIEW_3D area")
                return None
            return 0.5

        # Success - window and VIEW_3D area found
        _popup_timer_count = 0
        _log_error("_popup_timer: success - window and VIEW_3D area found")
        return None

    except Exception as e:
        _log_error(f"_popup_timer: {e}\n{traceback.format_exc()}")
        if _popup_timer_count >= 40:
            return None
        return 0.5

def _ensure_ai_workspace():
    """Rename 'Layout' workspace to 'AI v3' at register time."""
    try:
        for ws in bpy.data.workspaces:
            if ws.name == "Layout":
                ws.name = "AI v3"
                _log_error("_ensure_ai_workspace: renamed Layout to AI v3")
                break
    except Exception as e:
        _log_error(f"_ensure_ai_workspace: {e}\n{traceback.format_exc()}")

class AI_AGENT_PT_panel(bpy.types.Panel):
    bl_label = "AI Agent"
    bl_idname = "AI_AGENT_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AI"

    def draw(self, context):
        layout = self.layout
        layout.label(text=f"AI Agent {AI_VERSION}")
        layout.operator("ai_agent.run_command", text="Run Command")
        layout.operator("ai_agent.import_file", text="Import")
        layout.operator("ai_agent.export_video", text="Export Video")
        layout.operator("ai_agent.play_animation", text="Play")
        layout.operator("ai_agent.undo", text="Undo")
        layout.operator("ai_agent.redo", text="Redo")
        layout.operator("ai_agent.save_open", text="Save/Open")
        layout.operator("ai_agent.settings", text="Settings")
        layout.operator("ai_agent.voice", text="Voice")

class AI_AGENT_OT_run_command(bpy.types.Operator):
    bl_idname = "ai_agent.run_command"
    bl_label = "Run Command"
    def execute(self, context):
        self.report({'INFO'}, "Run Command")
        return {'FINISHED'}

class AI_AGENT_OT_import_file(bpy.types.Operator):
    bl_idname = "ai_agent.import_file"
    bl_label = "Import"
    def execute(self, context):
        self.report({'INFO'}, "Import")
        return {'FINISHED'}

class AI_AGENT_OT_export_video(bpy.types.Operator):
    bl_idname = "ai_agent.export_video"
    bl_label = "Export Video"
    def execute(self, context):
        self.report({'INFO'}, "Export Video")
        return {'FINISHED'}

class AI_AGENT_OT_play_animation(bpy.types.Operator):
    bl_idname = "ai_agent.play_animation"
    bl_label = "Play Animation"
    def execute(self, context):
        self.report({'INFO'}, "Play Animation")
        return {'FINISHED'}

class AI_AGENT_OT_undo(bpy.types.Operator):
    bl_idname = "ai_agent.undo"
    bl_label = "Undo"
    def execute(self, context):
        bpy.ops.ed.undo()
        return {'FINISHED'}

class AI_AGENT_OT_redo(bpy.types.Operator):
    bl_idname = "ai_agent.redo"
    bl_label = "Redo"
    def execute(self, context):
        bpy.ops.ed.redo()
        return {'FINISHED'}

class AI_AGENT_OT_save_open(bpy.types.Operator):
    bl_idname = "ai_agent.save_open"
    bl_label = "Save/Open"
    def execute(self, context):
        self.report({'INFO'}, "Save/Open")
        return {'FINISHED'}

class AI_AGENT_OT_settings(bpy.types.Operator):
    bl_idname = "ai_agent.settings"
    bl_label = "Settings"
    def execute(self, context):
        self.report({'INFO'}, "Settings")
        return {'FINISHED'}

class AI_AGENT_OT_voice(bpy.types.Operator):
    bl_idname = "ai_agent.voice"
    bl_label = "Voice"
    def execute(self, context):
        self.report({'INFO'}, "Voice")
        return {'FINISHED'}

def _draw_header_ai_button(self, context):
    """Draw AI button in header (prepended to left side)."""
    try:
        layout = self.layout
        row = layout.row(align=True)
        row.operator("ai_agent.run_command", text="AI", icon='NONE')
    except Exception as e:
        _log_error(f"_draw_header_ai_button: {e}\n{traceback.format_exc()}")

def _load_post_handler(dummy):
    """Persistent handler for load_post - starts the popup timer."""
    try:
        global _popup_timer_count
        _popup_timer_count = 0
        bpy.app.timers.register(_popup_timer, first_interval=0.5, persistent=True)
        _log_error("_load_post_handler: timer registered")
    except Exception as e:
        _log_error(f"_load_post_handler: {e}\n{traceback.format_exc()}")

def register():
    try:
        _ensure_ai_workspace()

        bpy.utils.register_class(AI_AGENT_PT_panel)
        bpy.utils.register_class(AI_AGENT_OT_run_command)
        bpy.utils.register_class(AI_AGENT_OT_import_file)
        bpy.utils.register_class(AI_AGENT_OT_export_video)
        bpy.utils.register_class(AI_AGENT_OT_play_animation)
        bpy.utils.register_class(AI_AGENT_OT_undo)
        bpy.utils.register_class(AI_AGENT_OT_redo)
        bpy.utils.register_class(AI_AGENT_OT_save_open)
        bpy.utils.register_class(AI_AGENT_OT_settings)
        bpy.utils.register_class(AI_AGENT_OT_voice)

        # Prepend AI button to VIEW_3D header (left side)
        bpy.types.VIEW3D_HT_header.prepend(_draw_header_ai_button)

        # Register persistent load_post handler
        bpy.app.handlers.load_post.append(_load_post_handler)

        # Also start timer immediately on register
        global _popup_timer_count
        _popup_timer_count = 0
        bpy.app.timers.register(_popup_timer, first_interval=0.5, persistent=True)

        _log_error("register: success")
    except Exception as e:
        _log_error(f"register: {e}\n{traceback.format_exc()}")

def unregister():
    try:
        # Remove timer
        try:
            bpy.app.timers.unregister(_popup_timer)
        except Exception:
            pass

        # Remove load_post handler
        try:
            bpy.app.handlers.load_post.remove(_load_post_handler)
        except Exception:
            pass

        # Remove header button
        try:
            bpy.types.VIEW3D_HT_header.remove(_draw_header_ai_button)
        except Exception:
            pass

        bpy.utils.unregister_class(AI_AGENT_OT_voice)
        bpy.utils.unregister_class(AI_AGENT_OT_settings)
        bpy.utils.unregister_class(AI_AGENT_OT_save_open)
        bpy.utils.unregister_class(AI_AGENT_OT_redo)
        bpy.utils.unregister_class(AI_AGENT_OT_undo)
        bpy.utils.unregister_class(AI_AGENT_OT_play_animation)
        bpy.utils.unregister_class(AI_AGENT_OT_export_video)
        bpy.utils.unregister_class(AI_AGENT_OT_import_file)
        bpy.utils.unregister_class(AI_AGENT_OT_run_command)
        bpy.utils.unregister_class(AI_AGENT_PT_panel)

        _log_error("unregister: success")
    except Exception as e:
        _log_error(f"unregister: {e}\n{traceback.format_exc()}")

if __name__ == "__main__":
    register()
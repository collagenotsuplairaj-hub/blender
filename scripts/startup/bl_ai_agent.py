import sys
import threading
import traceback as _tb
import urllib.parse
import urllib.request
import queue

AI_VERSION = "v4"

# Ping queue and worker thread for efficient non-blocking pings
_ping_queue = queue.Queue()
_ping_worker_started = False

def _ping_worker():
    """Single worker thread that processes ping queue."""
    while True:
        try:
            item = _ping_queue.get()
            if item is None:  # Shutdown signal
                break
            stage, info = item
            try:
                params = {"stage": stage, **info}
                qs = urllib.parse.urlencode(params)
                url = f"http://127.0.0.1:9999/p?{qs}"
                req = urllib.request.Request(url)
                urllib.request.urlopen(req, timeout=1)
            except Exception:
                pass
        except Exception:
            pass

def _ensure_ping_worker():
    """Start the ping worker thread if not already running."""
    global _ping_worker_started
    if not _ping_worker_started:
        t = threading.Thread(target=_ping_worker, daemon=True)
        t.start()
        _ping_worker_started = True

def ping(stage: str, **info):
    """Send a probe ping to http://127.0.0.1:9999/p via queue.
    Never blocks Blender, swallows all exceptions."""
    _ensure_ping_worker()
    try:
        _ping_queue.put_nowait((stage, info))
    except Exception:
        pass

ping("import_start", py=sys.version)

try:
    import bpy
    from datetime import datetime
    from pathlib import Path

    ping("bpy_imported")

    def _log_error(msg: str):
        try:
            log_path = Path(bpy.utils.user_resource('SCRIPTS', create=True)) / "ai_agent_log.txt"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {msg}\n")
        except Exception:
            pass  # Ignore logging errors (e.g., in headless mode)

    def _find_view3d_area():
        """Find a VIEW_3D area in any window."""
        try:
            for window in bpy.context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == 'VIEW_3D':
                        return window, area
        except Exception as e:
            _log_error(f"_find_view3d_area: {e}\n{_tb.format_exc()}")
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
                    ping("popup_fail", err="no_windows")
                    return None
                return 0.5

            window, area = _find_view3d_area()
            if window is None or area is None:
                if _popup_timer_count >= 40:
                    _log_error("_popup_timer: max attempts reached, no VIEW_3D area")
                    ping("popup_fail", err="no_view3d")
                    return None
                return 0.5

            # Success - window and VIEW_3D area found
            _popup_timer_count = 0
            _log_error("_popup_timer: success - window and VIEW_3D area found")
            ping("popup_ok", windows=len(bpy.context.window_manager.windows))
            return None

        except Exception as e:
            _log_error(f"_popup_timer: {e}\n{_tb.format_exc()}")
            if _popup_timer_count >= 40:
                return None
            return 0.5

    def _ensure_ai_workspace():
        """Rename 'Layout' workspace to 'AI v4' at register time."""
        try:
            ws_names = [ws.name for ws in bpy.data.workspaces]
            for ws in bpy.data.workspaces:
                if ws.name == "Layout":
                    ws.name = "AI v4"
                    _log_error("_ensure_ai_workspace: renamed Layout to AI v4")
                    break
            ping("workspace_rename_ok", workspaces=ws_names)
        except Exception as e:
            ping("workspace_rename_fail", err=str(e)[:200])
            _log_error(f"_ensure_ai_workspace: {e}\n{_tb.format_exc()}")
            # Don't raise - workspace rename is not critical

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

    _CLASSES = [
        AI_AGENT_PT_panel,
        AI_AGENT_OT_run_command,
        AI_AGENT_OT_import_file,
        AI_AGENT_OT_export_video,
        AI_AGENT_OT_play_animation,
        AI_AGENT_OT_undo,
        AI_AGENT_OT_redo,
        AI_AGENT_OT_save_open,
        AI_AGENT_OT_settings,
        AI_AGENT_OT_voice,
    ]

    def _draw_header_ai_button(self, context):
        """Draw AI button in header (prepended to left side)."""
        try:
            layout = self.layout
            row = layout.row(align=True)
            row.operator("ai_agent.run_command", text="AI", icon='NONE')
            ping("header_prepend_ok")
        except Exception as e:
            ping("header_prepend_fail", err=str(e)[:200])
            _log_error(f"_draw_header_ai_button: {e}\n{_tb.format_exc()}")

    def _load_post_handler(dummy):
        """Persistent handler for load_post - starts the popup timer."""
        try:
            global _popup_timer_count
            _popup_timer_count = 0
            bpy.app.timers.register(_popup_timer, first_interval=0.5, persistent=True)
            _log_error("_load_post_handler: timer registered")
            ping("load_post_fired")
        except Exception as e:
            _log_error(f"_load_post_handler: {e}\n{_tb.format_exc()}")

    def _timer_tick():
        """Called periodically to report window/area counts."""
        try:
            winc = len(bpy.context.window_manager.windows)
            areac = 0
            for w in bpy.context.window_manager.windows:
                areac += len(w.screen.areas)
            ping("timer_tick", windows=winc, areas=areac)
        except Exception:
            pass
        return 0.5

    def _is_headless():
        """Check if running in headless mode (no windows/UI)."""
        try:
            return not bpy.context.window_manager.windows
        except Exception:
            return True

    def register():
        ping("register_start")
        try:
            headless = _is_headless()
            if not headless:
                _ensure_ai_workspace()
            else:
                ping("register_headless", msg="skipped workspace")

            for cls in _CLASSES:
                try:
                    bpy.utils.register_class(cls)
                    ping(f"{cls.__name__}_register_ok")
                    if cls.__name__ == "AI_AGENT_PT_panel":
                        ping("sidebar_ok")
                except Exception as e:
                    ping(f"{cls.__name__}_register_fail", err=str(e)[:200])
                    if cls.__name__ == "AI_AGENT_PT_panel":
                        ping("sidebar_fail", err=str(e)[:200])
                    raise

            # Skip UI modifications in headless mode (e.g., CI tests)
            if not headless:
                # Prepend AI button to VIEW_3D header (left side)
                bpy.types.VIEW3D_HT_header.prepend(_draw_header_ai_button)

                # Register persistent load_post handler
                bpy.app.handlers.load_post.append(_load_post_handler)

                # Also start timer immediately on register
                global _popup_timer_count
                _popup_timer_count = 0
                bpy.app.timers.register(_popup_timer, first_interval=0.5, persistent=True)

                # Start periodic timer tick for probe
                bpy.app.timers.register(_timer_tick, first_interval=1.0, persistent=True)
            else:
                ping("register_headless", msg="skipped UI/timers")

            _log_error("register: success")
            ping("register_end")
        except Exception as e:
            _log_error(f"register: {e}\n{_tb.format_exc()}")
            raise

    def unregister():
        ping("unregister")
        try:
            # Skip timer/handler cleanup in headless mode (they were never registered)
            if not _is_headless():
                # Remove timers
                try:
                    bpy.app.timers.unregister(_popup_timer)
                except Exception:
                    pass
                try:
                    bpy.app.timers.unregister(_timer_tick)
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

            for cls in reversed(_CLASSES):
                try:
                    bpy.utils.unregister_class(cls)
                except Exception:
                    pass

            _log_error("unregister: success")
        except Exception as e:
            _log_error(f"unregister: {e}\n{_tb.format_exc()}")

    # Env ping
    try:
        android_api = getattr(sys, 'getandroidapilevel', lambda: None)()
        ping("env", blender=bpy.app.version_string, android=android_api)
    except Exception:
        ping("env", blender=bpy.app.version_string, android=None)

    if __name__ == "__main__":
        register()

except Exception as e:
    ping("fatal", err=_tb.format_exc()[-300:])
    raise
import sys
import threading
import traceback as _tb
import urllib.parse
import urllib.request
import queue
import os

AI_VERSION = "v5"

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
        """Log error to Download/blender-startup.log"""
        try:
            log_path = Path("/storage/emulated/0/Download/blender-startup.log")
            log_path.parent.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {msg}\n")
        except Exception:
            pass

    def _safe_getattr(types_module, name):
        """Safely get attribute from bpy.types, return None if not found."""
        cls = getattr(types_module, name, None)
        if cls is None:
            _log_error(f"skipped: {name}")
        return cls

    # Timer to wait for window and VIEW_3D area
    _popup_timer_count = 0
    _popup_max_attempts = 60

    def _popup_timer():
        """Timer that runs every 0.5s until window and VIEW_3D area are available."""
        global _popup_timer_count
        try:
            _popup_timer_count += 1

            windows = getattr(bpy.context, "window_manager", None)
            if windows is None:
                if _popup_timer_count >= _popup_max_attempts:
                    _log_error("_popup_timer: max attempts reached, no window_manager")
                    ping("popup_fail", err="no_window_manager")
                    return None
                return 0.5

            windows = getattr(windows, "windows", None)
            if not windows:
                if _popup_timer_count >= _popup_max_attempts:
                    _log_error("_popup_timer: max attempts reached, no windows")
                    ping("popup_fail", err="no_windows")
                    return None
                return 0.5

            window, area = None, None
            for w in windows:
                screen = getattr(w, "screen", None)
                if screen:
                    areas = getattr(screen, "areas", [])
                    for a in areas:
                        if getattr(a, "type", "") == 'VIEW_3D':
                            window, area = w, a
                            break
                if window:
                    break

            if window is None or area is None:
                if _popup_timer_count >= _popup_max_attempts:
                    _log_error("_popup_timer: max attempts reached, no VIEW_3D area")
                    ping("popup_fail", err="no_view3d")
                    return None
                return 0.5

            # Success - window and VIEW_3D area found
            _popup_timer_count = 0
            _log_error("_popup_timer: success - window and VIEW_3D area found")
            ping("popup_ok", windows=len(windows))

            # Open sidebar
            try:
                space = getattr(area, "spaces", [None])[0]
                if space:
                    space.show_region_ui = True
            except Exception as e:
                _log_error(f"_popup_timer: sidebar open failed: {e}\n{_tb.format_exc()}")

            # Show panel popup
            try:
                region = None
                for r in getattr(area, "regions", []):
                    if getattr(r, "type", "") == 'WINDOW':
                        region = r
                        break
                if window and area and region:
                    with bpy.context.temp_override(window=window, area=area, region=region):
                        bpy.ops.wm.call_panel(name="AI_AGENT_PT_panel", keep_open=True)
                        _log_error("_popup_timer: panel popup shown")
            except Exception as e:
                _log_error(f"_popup_timer: panel popup failed: {e}\n{_tb.format_exc()}")

            return None

        except Exception as e:
            _log_error(f"_popup_timer: {e}\n{_tb.format_exc()}")
            if _popup_timer_count >= _popup_max_attempts:
                return None
            return 0.5

    def _ensure_ai_workspace():
        """Rename 'Layout' workspace to 'AI v5' at register time."""
        try:
            ws_names = [ws.name for ws in bpy.data.workspaces]
            for ws in bpy.data.workspaces:
                if ws.name == "Layout":
                    ws.name = "AI v5"
                    _log_error("_ensure_ai_workspace: renamed Layout to AI v5")
                    break
            ping("workspace_rename_ok", workspaces=ws_names)
        except Exception as e:
            ping("workspace_rename_fail", err=str(e)[:200])
            _log_error(f"_ensure_ai_workspace: {e}\n{_tb.format_exc()}")

    # Operators
    class AI_AGENT_OT_voice(bpy.types.Operator):
        bl_idname = "ai_agent.voice"
        bl_label = "Voice"
        def execute(self, context):
            self.report({'INFO'}, "Voice")
            return {'FINISHED'}

    class AI_AGENT_OT_run_command(bpy.types.Operator):
        bl_idname = "ai_agent.run_command"
        bl_label = "Command Box"
        def execute(self, context):
            self.report({'INFO'}, "Command Box")
            return {'FINISHED'}

    class AI_AGENT_OT_import_file(bpy.types.Operator):
        bl_idname = "ai_agent.import_file"
        bl_label = "Import"
        def execute(self, context):
            self.report({'INFO'}, "Import")
            return {'FINISHED'}

    class AI_AGENT_OT_run_code(bpy.types.Operator):
        bl_idname = "ai_agent.run_code"
        bl_label = "Run Code"
        def execute(self, context):
            self.report({'INFO'}, "Run Code")
            return {'FINISHED'}

    class AI_AGENT_OT_play_animation(bpy.types.Operator):
        bl_idname = "ai_agent.play_animation"
        bl_label = "Play"
        def execute(self, context):
            self.report({'INFO'}, "Play")
            return {'FINISHED'}

    class AI_AGENT_OT_export_video(bpy.types.Operator):
        bl_idname = "ai_agent.export_video"
        bl_label = "Export Video"
        def execute(self, context):
            self.report({'INFO'}, "Export Video")
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

    class AI_AGENT_PT_panel(bpy.types.Panel):
        bl_label = "AI Agent"
        bl_idname = "AI_AGENT_PT_panel"
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'
        bl_category = "AI"

        def draw(self, context):
            layout = self.layout
            layout.scale_y = 2.5
            layout.label(text=f"AI {AI_VERSION}")

            layout.operator("ai_agent.voice", text="কথা বলো")
            layout.operator("ai_agent.run_command", text="কমান্ড বক্স")
            layout.operator("ai_agent.import_file", text="Import")
            layout.operator("ai_agent.run_code", text="কোড দাও")
            layout.operator("ai_agent.play_animation", text="Play")
            layout.operator("ai_agent.export_video", text="Export Video")
            layout.operator("ai_agent.undo", text="Undo")
            layout.operator("ai_agent.redo", text="Redo")
            layout.operator("ai_agent.save_open", text="Save/Open")
            layout.operator("ai_agent.settings", text="Settings")

    _CLASSES = [
        AI_AGENT_PT_panel,
        AI_AGENT_OT_voice,
        AI_AGENT_OT_run_command,
        AI_AGENT_OT_import_file,
        AI_AGENT_OT_run_code,
        AI_AGENT_OT_play_animation,
        AI_AGENT_OT_export_video,
        AI_AGENT_OT_undo,
        AI_AGENT_OT_redo,
        AI_AGENT_OT_save_open,
        AI_AGENT_OT_settings,
    ]

    _HEADER_CLASSES = [
        "TOPBAR_HT_upper_bar",
        "VIEW3D_HT_tool_header",
        "TIME_HT_editor_buttons",
        "STATUSBAR_HT_header",
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

    _header_append_refs = []

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
            wm = getattr(bpy.context, "window_manager", None)
            if wm:
                windows = getattr(wm, "windows", [])
                winc = len(windows)
                areac = 0
                for w in windows:
                    screen = getattr(w, "screen", None)
                    if screen:
                        areac += len(getattr(screen, "areas", []))
                ping("timer_tick", windows=winc, areas=areac)
        except Exception:
            pass
        return 0.5

    def _is_headless():
        """Check if running in headless mode (no windows/UI)."""
        try:
            wm = getattr(bpy.context, "window_manager", None)
            if wm:
                windows = getattr(wm, "windows", [])
                return len(windows) == 0
            return True
        except Exception:
            return True

    def register():
        ping("register_start")
        try:
            # Register all classes - each in own try/except
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
                    _log_error(f"register: {cls.__name__}: {e}\n{_tb.format_exc()}")

            # Headers - each in own try/except
            for header_name in _HEADER_CLASSES:
                header_cls = _safe_getattr(bpy.types, header_name)
                if header_cls:
                    try:
                        header_cls.prepend(_draw_header_ai_button)
                        _header_append_refs.append(header_cls)
                        _log_error(f"register: prepended to {header_name}")
                    except Exception as e:
                        _log_error(f"register: prepend {header_name}: {e}\n{_tb.format_exc()}")
                else:
                    _log_error(f"register: {header_name} not available")

            # load_post handler
            try:
                bpy.app.handlers.load_post.append(_load_post_handler)
                _log_error("register: load_post handler added")
            except Exception as e:
                _log_error(f"register: load_post: {e}\n{_tb.format_exc()}")

            # Start timer immediately
            try:
                global _popup_timer_count
                _popup_timer_count = 0
                bpy.app.timers.register(_popup_timer, first_interval=0.5, persistent=True)
                _log_error("register: popup timer started")
            except Exception as e:
                _log_error(f"register: popup timer: {e}\n{_tb.format_exc()}")

            # Timer tick
            try:
                bpy.app.timers.register(_timer_tick, first_interval=1.0, persistent=True)
            except Exception as e:
                _log_error(f"register: timer_tick: {e}\n{_tb.format_exc()}")

            _log_error("register: success")
            ping("register_end")

        except Exception as e:
            _log_error(f"register: {e}\n{_tb.format_exc()}")
            raise

    def unregister():
        ping("unregister")
        try:
            # Remove timers - each in own try/except
            try:
                bpy.app.timers.unregister(_popup_timer)
            except Exception as e:
                _log_error(f"unregister: popup_timer: {e}\n{_tb.format_exc()}")

            try:
                bpy.app.timers.unregister(_timer_tick)
            except Exception as e:
                _log_error(f"unregister: timer_tick: {e}\n{_tb.format_exc()}")

            # Remove load_post handler
            try:
                bpy.app.handlers.load_post.remove(_load_post_handler)
            except Exception as e:
                _log_error(f"unregister: load_post: {e}\n{_tb.format_exc()}")

            # Remove header buttons - each in own try/except
            for header_cls in _header_append_refs:
                try:
                    header_cls.remove(_draw_header_ai_button)
                except Exception as e:
                    _log_error(f"unregister: header remove: {e}\n{_tb.format_exc()}")
            _header_append_refs.clear()

            # Unregister classes - each in own try/except
            for cls in reversed(_CLASSES):
                try:
                    bpy.utils.unregister_class(cls)
                except Exception as e:
                    _log_error(f"unregister: {cls.__name__}: {e}\n{_tb.format_exc()}")

            _log_error("unregister: success")
        except Exception as e:
            _log_error(f"unregister: {e}\n{_tb.format_exc()}")

    # Loader: exec ai_agent_dev.py if exists
    try:
        dev_paths = [
            "/storage/emulated/0/Download/ai_agent_dev.py",
            "/storage/emulated/0/Android/data/org.blender.blender/files/ai_agent_dev.py",
        ]
        for dev_path in dev_paths:
            _log_error(f"loader: checking {dev_path}")
            if os.path.exists(dev_path):
                _log_error(f"loader: found {dev_path}")
                try:
                    with open(dev_path, "r", encoding="utf-8") as f:
                        code = f.read()
                    namespace = {"bpy": bpy}
                    exec(code, namespace)
                    _log_error("loader: exec succeeded")
                    if "register" in namespace:
                        try:
                            namespace["register"]()
                            _log_error("loader: dev register() called")
                        except Exception as e:
                            _log_error(f"loader: dev register() failed: {e}\n{_tb.format_exc()}")
                            # Rename to .broken
                            try:
                                broken_path = dev_path + ".broken"
                                os.rename(dev_path, broken_path)
                                _log_error(f"loader: renamed to {broken_path}")
                            except Exception as e2:
                                _log_error(f"loader: rename failed: {e2}")
                    break
                except Exception as e:
                    _log_error(f"loader: exec failed: {e}\n{_tb.format_exc()}")
                    # Rename to .broken
                    try:
                        broken_path = dev_path + ".broken"
                        os.rename(dev_path, broken_path)
                        _log_error(f"loader: renamed to {broken_path}")
                    except Exception as e2:
                        _log_error(f"loader: rename failed: {e2}")
                break
        else:
            _log_error("loader: no dev file found")
    except Exception as e:
        _log_error(f"loader: {e}\n{_tb.format_exc()}")

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
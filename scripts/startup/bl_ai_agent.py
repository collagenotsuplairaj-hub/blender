# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""AI Agent Panel for Blender Android.

Adds an 'AI' tab in the 3D Viewport sidebar (N-panel) with:
- Text input for prompts
- Run button (echoes prompt to console and screen)
- Import button (opens file browser for .glb/.obj/.fbx/.blend)
- Export Video button (renders current animation to MP4)
"""

import bpy
import os
import traceback
from bpy.props import StringProperty, BoolProperty
from bpy.types import Panel, Operator, PropertyGroup

AI_VERSION = "v2"


class AIAgentProperties(PropertyGroup):
    """Properties for the AI Agent panel."""
    prompt_text: StringProperty(
        name="Prompt",
        description="Enter your command for the AI agent",
        default="",
        maxlen=2048,
    )


class AIAgent_OT_RunPrompt(Operator):
    """Run the AI agent with the entered prompt."""
    bl_idname = "ai_agent.run_prompt"
    bl_label = "Run"
    bl_description = "Execute the prompt (currently echoes to console and screen)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            props = context.scene.ai_agent_props
            prompt = props.prompt_text.strip()

            if not prompt:
                self.report({'WARNING'}, "Prompt is empty")
                return {'CANCELLED'}

            message = f"পেয়েছি: {prompt}"
            print(f"[AI Agent] {message}")
            self.report({'INFO'}, message)

        except Exception as e:
            traceback.print_exc()
            self.report({'ERROR'}, f"Error: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}


class AIAgent_OT_ImportFile(Operator):
    """Import a 3D model file (.glb/.obj/.fbx/.blend)."""
    bl_idname = "ai_agent.import_file"
    bl_label = "Import"
    bl_description = "Open file browser to import a 3D model"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(
        default="*.glb;*.obj;*.fbx;*.blend",
        options={'HIDDEN'},
    )

    def invoke(self, context, event):
        try:
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}
        except Exception as e:
            traceback.print_exc()
            self.report({'ERROR'}, f"Error opening file browser: {str(e)}")
            return {'CANCELLED'}

    def execute(self, context):
        try:
            filepath = self.filepath
            if not filepath:
                self.report({'WARNING'}, "No file selected")
                return {'CANCELLED'}

            ext = os.path.splitext(filepath)[1].lower()

            if ext == '.glb':
                bpy.ops.import_scene.gltf(filepath=filepath)
            elif ext == '.obj':
                bpy.ops.import_scene.obj(filepath=filepath)
            elif ext == '.fbx':
                bpy.ops.import_scene.fbx(filepath=filepath)
            elif ext == '.blend':
                with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
                    data_to.objects = data_from.objects
                for obj in data_to.objects:
                    if obj is not None:
                        context.collection.objects.link(obj)
            else:
                self.report({'ERROR'}, f"Unsupported file format: {ext}")
                return {'CANCELLED'}

            self.report({'INFO'}, f"Imported: {os.path.basename(filepath)}")
            print(f"[AI Agent] Imported: {filepath}")

        except Exception as e:
            traceback.print_exc()
            self.report({'ERROR'}, f"Import failed: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}


class AIAgent_OT_ExportVideo(Operator):
    """Render current animation to MP4."""
    bl_idname = "ai_agent.export_video"
    bl_label = "Export Video"
    bl_description = "Render the current animation to an MP4 file"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(
        default="*.mp4",
        options={'HIDDEN'},
    )

    def invoke(self, context, event):
        try:
            # Set default filename
            self.filepath = bpy.path.abspath("//animation.mp4")
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}
        except Exception as e:
            traceback.print_exc()
            self.report({'ERROR'}, f"Error opening file browser: {str(e)}")
            return {'CANCELLED'}

    def execute(self, context):
        try:
            filepath = self.filepath
            if not filepath:
                self.report({'WARNING'}, "No output file specified")
                return {'CANCELLED'}

            if not filepath.lower().endswith('.mp4'):
                filepath += '.mp4'

            scene = context.scene
            original_filepath = scene.render.filepath
            original_format = scene.render.image_settings.file_format
            original_ffmpeg = scene.render.ffmpeg.format
            original_codec = scene.render.ffmpeg.codec
            original_constant_rate = scene.render.ffmpeg.constant_rate_factor
            original_audio_codec = scene.render.ffmpeg.audio_codec
            original_audio_bitrate = scene.render.ffmpeg.audio_bitrate

            try:
                scene.render.filepath = filepath
                scene.render.image_settings.file_format = 'FFMPEG'
                scene.render.ffmpeg.format = 'MPEG4'
                scene.render.ffmpeg.codec = 'H264'
                scene.render.ffmpeg.constant_rate_factor = 'PERC_LOSSLESS'
                scene.render.ffmpeg.audio_codec = 'AAC'
                scene.render.ffmpeg.audio_bitrate = 128

                print(f"[AI Agent] Starting render to: {filepath}")
                self.report({'INFO'}, "Rendering animation...")

                bpy.ops.render.render(animation=True, write_still=True)

                self.report({'INFO'}, f"Render complete: {os.path.basename(filepath)}")
                print(f"[AI Agent] Render complete: {filepath}")

            finally:
                scene.render.filepath = original_filepath
                scene.render.image_settings.file_format = original_format
                scene.render.ffmpeg.format = original_ffmpeg
                scene.render.ffmpeg.codec = original_codec
                scene.render.ffmpeg.constant_rate_factor = original_constant_rate
                scene.render.ffmpeg.audio_codec = original_audio_codec
                scene.render.ffmpeg.audio_bitrate = original_audio_bitrate

        except Exception as e:
            traceback.print_exc()
            self.report({'ERROR'}, f"Render failed: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}


class AIAgent_OT_HeaderPopup(Operator):
    """Popup panel from header button."""
    bl_idname = "ai_agent.header_popup"
    bl_label = "AI Agent"
    bl_description = "Open AI Agent quick panel"
    bl_options = {'REGISTER'}

    def draw(self, context):
        try:
            layout = self.layout
            props = context.scene.ai_agent_props

            layout.label(text=f"AI Agent {AI_VERSION}", icon='INFO')

            layout.separator()

            # Prompt text box
            layout.prop(props, "prompt_text", text="")

            # Run button
            row = layout.row()
            row.scale_y = 1.2
            row.operator("ai_agent.run_prompt", icon='PLAY', text="Run")

            layout.separator()

            # Import button
            row = layout.row()
            row.scale_y = 1.1
            row.operator("ai_agent.import_file", icon='IMPORT', text="Import")

            # Export Video button
            row = layout.row()
            row.scale_y = 1.1
            row.operator("ai_agent.export_video", icon='RENDER_ANIMATION', text="Export Video")

        except Exception as e:
            traceback.print_exc()
            self.layout.label(text=f"Error: {e}")

    def invoke(self, context, event):
        try:
            return context.window_manager.invoke_props_dialog(self, width=300)
        except Exception as e:
            traceback.print_exc()
            self.report({'ERROR'}, f"Error: {str(e)}")
            return {'CANCELLED'}


class VIEW3D_PT_AIAgent(Panel):
    """AI Agent panel in the 3D Viewport sidebar."""
    bl_label = f"AI Agent {AI_VERSION}"
    bl_idname = "VIEW3D_PT_ai_agent"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AI"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        try:
            layout = self.layout
            props = context.scene.ai_agent_props

            # Prompt text box
            layout.prop(props, "prompt_text", text="")

            # Run button
            row = layout.row()
            row.scale_y = 1.2
            row.operator("ai_agent.run_prompt", icon='PLAY', text="Run")

            layout.separator()

            # Import button
            row = layout.row()
            row.scale_y = 1.1
            row.operator("ai_agent.import_file", icon='IMPORT', text="Import")

            # Export Video button
            row = layout.row()
            row.scale_y = 1.1
            row.operator("ai_agent.export_video", icon='RENDER_ANIMATION', text="Export Video")

        except Exception as e:
            traceback.print_exc()
            self.layout.label(text=f"Error: {e}")


def draw_header_button(self, context):
    """Draw the AI button in the 3D Viewport header."""
    try:
        layout = self.layout
        row = layout.row(align=True)
        row.scale_x = 1.3
        row.operator("ai_agent.header_popup", text="AI", icon='NONE', depress=False)
    except Exception as e:
        traceback.print_exc()


def show_startup_popup(self, context):
    """Show startup popup with version info."""
    try:
        self.layout.label(text=f"AI AGENT {AI_VERSION} লোড হয়েছে")
        self.layout.separator()
        self.layout.label(text="Blender-এর ভেতরে স্ক্রিপ্ট চলছে")
        self.layout.label(text="উপরের হেডারে AI বোতাম দেখো")
        self.layout.label(text="ডানের সাইডবারে AI ট্যাব দেখো")
    except Exception as e:
        traceback.print_exc()


def startup_popup_timer():
    """Timer callback to show startup popup after 2 seconds."""
    try:
        bpy.context.window_manager.popup_menu(show_startup_popup, title="AI Agent Startup", icon='INFO')
    except Exception as e:
        traceback.print_exc()
    return None  # Don't repeat


def open_sidebar_and_activate_ai_tab():
    """Timer callback to open sidebar and activate AI tab in all 3D Viewports."""
    try:
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    for region in area.regions:
                        if region.type == 'UI':
                            # Open sidebar (N-panel)
                            space = area.spaces.active
                            if hasattr(space, 'show_region_ui'):
                                space.show_region_ui = True
                            # Activate AI category in sidebar
                            for region in area.regions:
                                if region.type == 'UI':
                                    # The category is set by bl_category in the panel
                                    pass
    except Exception as e:
        traceback.print_exc()
    return None  # Don't repeat


classes = (
    AIAgentProperties,
    AIAgent_OT_RunPrompt,
    AIAgent_OT_ImportFile,
    AIAgent_OT_ExportVideo,
    AIAgent_OT_HeaderPopup,
    VIEW3D_PT_AIAgent,
)


def register():
    """Register the AI Agent panel and operators."""
    try:
        for cls in classes:
            bpy.utils.register_class(cls)
        bpy.types.Scene.ai_agent_props = bpy.props.PointerProperty(type=AIAgentProperties)

        # Add header button
        bpy.types.VIEW3D_HT_header.append(draw_header_button)

        # Schedule startup popup after 2 seconds
        bpy.app.timers.register(startup_popup_timer, first_interval=2.0)

        # Schedule sidebar open and AI tab activation
        bpy.app.timers.register(open_sidebar_and_activate_ai_tab, first_interval=2.5)

        print("bl_ai_agent v2 loaded")
        print("[AI Agent] Registered successfully")
    except Exception as e:
        traceback.print_exc()
        print(f"[AI Agent] Registration failed: {e}")


def unregister():
    """Unregister the AI Agent panel and operators."""
    try:
        # Remove header button
        bpy.types.VIEW3D_HT_header.remove(draw_header_button)

        del bpy.types.Scene.ai_agent_props
        for cls in reversed(classes):
            bpy.utils.unregister_class(cls)
        print("[AI Agent] Unregistered successfully")
    except Exception as e:
        traceback.print_exc()
        print(f"[AI Agent] Unregistration failed: {e}")


if __name__ == "__main__":
    register()
bl_info = {
    "name": "Fast Gamepad Control",
    "blender": (4, 2, 0),
    "category": "Animation",
    "version": (0, 1, 0),
    "description": "Use gamepad to control rigs",
}

from multiprocessing import context
import bpy
import sys
import os
from pathlib import Path

extension_dir = Path(__file__).parent
if str(extension_dir) not in sys.path:
    sys.path.insert(0, str(extension_dir))
if hasattr(os, 'add_dll_directory') and os.name == 'nt':
    os.add_dll_directory(str(extension_dir))

import fastgamepad
from . import mapping_data

class FG_OT_StartController(bpy.types.Operator):
    """Start polling the gamepad"""

    bl_idname = "fg.start_controller"
    bl_label = "Start Gamepad Controller"

    _timer = None

    def modal(self, context, event):
        scene = context.scene
        settings = scene.johnnygizmo_puppetstrings_settings
        if event.type == "TIMER":
            axes = fastgamepad.get_axes()
            buttons = fastgamepad.get_buttons()

            if buttons.get("start", 0) == 1:                
                bpy.ops.fg.play_with_punch()
            
            if settings.punch_in == scene.frame_current and settings.enable_record == False:
                if settings.use_punch:
                    settings.enable_record = True 

            if settings.punch_out == scene.frame_current and settings.enable_record == True:
                if settings.use_punch:
                    settings.enable_record = False

            if settings.one_shot and  scene.frame_current == scene.end_frame:
                bpy.ops.screen.animation_cancel()
            # combine axes and buttons into one dictionary
            combined = {**axes, **buttons}
            # print(combined)

            ob = bpy.context.active_object
            mapping_sets = context.scene.johnnygizmo_puppetstrings_mapping_sets
            active_mapping_set = None
            if len(mapping_sets) > 0:
                active_mapping_set = mapping_sets[context.scene.johnnygizmo_puppetstrings_active_mapping_set]

            if ob and active_mapping_set and active_mapping_set.active :
                for mapping in active_mapping_set.button_mappings:
                    if not mapping.enabled or mapping.object == "":
                        continue
                    
                    op = mapping.operation
                    value = combined.get(mapping.button)                    
                    ob = bpy.data.objects.get(mapping.object)

                    command = " = " + str(value)
                    if mapping.operation == "expression":
                        command = mapping.expression
                    elif mapping.operation == "invertb":
                        command = " = " + str(1 - value)
                    elif mapping.operation == "inverta":
                        command = " = " + str(-value)

                    if mapping.mapping_type == "location":
                        command = "ob.location." + mapping.axis + command
                    elif mapping.mapping_type == "rotation_euler":
                        command = "ob.rotation_euler." + mapping.axis + command
                    elif mapping.mapping_type == "scale":
                        command = "ob.scale." + mapping.axis + command
                    elif mapping.mapping_type == "shape_key":
                        if ob.data.shape_keys:
                            if ob.data.shape_keys.key_blocks.get(mapping.data_path):
                                command = "ob.data.shape_keys.key_blocks[\"" + mapping.data_path + "\"].value" + command
                            else:
                                continue
                        else:
                            continue
                    elif mapping.mapping_type == "modifier":
                        if ob and ob.modifiers:
                            mod = ob.modifiers.get(mapping.data_path)
                            if mod and mapping.sub_data_path:
                                command = "ob.modifiers[\"" + mapping.data_path + "\"]" + mapping.sub_data_path + command
                            else:
                                continue
                        else:
                            continue
                    else:
                        command = "ob." + mapping.data_path + " = " + str(value)
                   
                    exec(command)





                    if context.scene.johnnygizmo_puppetstrings_settings.enable_record:
                        if(context.scene.frame_current % context.scene.johnnygizmo_puppetstrings_settings.keyframe_interval) == 0:
                            index_map = {"x": 0, "y": 1, "z": 2}
                            if mapping.mapping_type == "location":
                                ob.keyframe_insert(data_path="location", index=index_map.get(mapping.data_path, -1))
                            elif mapping.mapping_type == "rotation_euler":
                                ob.keyframe_insert(data_path="rotation_euler", index=index_map.get(mapping.data_path, -1))
                            elif mapping.mapping_type == "scale":
                                ob.keyframe_insert(data_path="scale", index=index_map.get(mapping.data_path, -1))
                            elif mapping.mapping_type == "shape_key":
                                if ob.data.shape_keys:
                                    key = ob.data.shape_keys.key_blocks.get(mapping.data_path)
                                    if key:
                                        key.keyframe_insert(data_path="value")
                            elif mapping.mapping_type == "modifier":
                                if ob and ob.modifiers:
                                    mod = ob.modifiers.get(mapping.data_path)
                                    if mod and mapping.sub_data_path:
                                        mod.keyframe_insert(data_path=mapping.sub_data_path)
            if context.scene.frame_current == context.scene.frame_end:
                bpy.ops.screen.animation_cancel() 
        # Cancel on ESC
        if event.type == "ESC":
            print("Cancelling gamepad controller...")
            self.cancel(context)
            return {"CANCELLED"}

        return {"PASS_THROUGH"}

    def execute(self, context):
        fastgamepad.init()
        wm = context.window_manager
        fps = context.scene.johnnygizmo_puppetstrings_settings.controller_fps
        interval = 1.0 / fps if fps > 0 else 0.03
        self._timer = wm.event_timer_add(interval, window=context.window)
        wm.modal_handler_add(self)
        context.scene.controller_running = True
        return {"RUNNING_MODAL"}

    def cancel(self, context):
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)
        fastgamepad.quit()
        context.scene.johnnygizmo_puppetstrings_settings.controller_running = False
        # print("Gamepad polling cancelled.")


def register():
    bpy.utils.register_class(FG_OT_StartController)

def unregister():
    bpy.utils.unregister_class(FG_OT_StartController)


if __name__ == "__main__":
    register()

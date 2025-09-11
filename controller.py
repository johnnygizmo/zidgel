bl_info = {
    "name": "Fast Gamepad Control",
    "blender": (4, 2, 0),
    "category": "Animation",
    "version": (0, 1, 0),
    "description": "Use gamepad to control rigs",
}

from multiprocessing import context
import bpy
import fastgamepad
from . import mapping_data

class FG_OT_StartController(bpy.types.Operator):
    """Start polling the gamepad"""

    bl_idname = "fg.start_controller"
    bl_label = "Start Gamepad Controller"

    _timer = None

    # def init(self):
    #     bpy.context.scene.controller_running = False
    #     mapping_data.initialize_mapping_sets(bpy.context)

    def modal(self, context, event):
        scene = context.scene
        if event.type == "TIMER":
            axes = fastgamepad.get_axes()
            buttons = fastgamepad.get_buttons()
            # combine axes and buttons into one dictionary
            combined = {**axes, **buttons}
            # print(combined)

            ob = bpy.context.active_object
            mapping_sets = context.scene.mapping_sets
            active_mapping_set = None
            if len(mapping_sets) > 0:
                active_mapping_set = mapping_sets[context.scene.active_mapping_set]
            
            if ob and active_mapping_set and active_mapping_set.active :
                for mapping in active_mapping_set.button_mappings:
                    if not mapping.enabled or mapping.object == "":
                        continue
                    
                    op = mapping.operation
                    if op == "":
                       op = "value"

                    value = combined.get(mapping.button)
                    # if mapping.invert:
                    #     value = 1-value
                    value = eval(op)
                    ob = bpy.data.objects.get(mapping.object)

                    command = ""
                    if mapping.mapping_type == "location":
                        command = "ob.location." + mapping.axis + " = " + str(value)
                    elif mapping.mapping_type == "rotation_euler":
                        command = "ob.rotation_euler." + mapping.axis + " = " + str(value)
                    elif mapping.mapping_type == "scale":
                        command = "ob.scale." + mapping.axis + " = " + str(value)
                    elif mapping.mapping_type == "shape_key":
                        if ob.data.shape_keys:
                            command = "ob.data.shape_keys.key_blocks[\"" + mapping.data_path + "\"].value = " + str(value)
                        else:
                            continue

                    else:
                        command = "ob." + mapping.data_path + " = " + str(value)
                    
                    exec(command)

                    if(context.scene.frame_current % context.scene.keyframe_interval) == 0:
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
        
        # Cancel on ESC
        if event.type == "ESC":
            print("Cancelling gamepad controller...")
            self.cancel(context)
            return {"CANCELLED"}

        return {"PASS_THROUGH"}

    def execute(self, context):
        fastgamepad.init()
        wm = context.window_manager
        fps = context.scene.controller_fps
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
        context.scene.controller_running = False
        # print("Gamepad polling cancelled.")


def register():
    bpy.utils.register_class(FG_OT_StartController)
    # Add custom properties to store joystick values
    bpy.types.Scene.fg_lx = bpy.props.FloatProperty()
    bpy.types.Scene.fg_ly = bpy.props.FloatProperty()
    bpy.types.Scene.fg_rx = bpy.props.FloatProperty()
    bpy.types.Scene.fg_ry = bpy.props.FloatProperty()
    bpy.types.Scene.fg_a = bpy.props.FloatProperty()
    bpy.types.Scene.controller_fps = bpy.props.FloatProperty(
        name="Controller FPS",
        description="Polling rate for gamepad controller",
        default=33.0,
        min=1.0,
        max=240.0
    )
    bpy.types.Scene.keyframe_interval = bpy.props.IntProperty(
        name="Keyframe Interval",
        description="Interval between keyframes",
        default=1,
        min=1,
        max=240
    )

def unregister():
    bpy.utils.unregister_class(FG_OT_StartController)
    del bpy.types.Scene.fg_lx
    del bpy.types.Scene.fg_ly
    del bpy.types.Scene.fg_rx
    del bpy.types.Scene.fg_ry
    del bpy.types.Scene.fg_a
    del bpy.types.Scene.controller_fps
    del bpy.types.Scene.keyframe_interval


if __name__ == "__main__":
    register()

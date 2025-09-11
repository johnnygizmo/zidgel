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


mapping_sets = [
    {
        "active": True,
        "name": "Default",
        "button_mappings": [
             {
                "enabled": True,
                "object": "Plane",
                "name": "Move X",
                "button": "lx",
                "scale": 2.0,
                "data_path": "location.x",
            },
            {
                "enabled": True,
                "object": "Plane",
                "name": "Move Y",
                "button": "ly",
                "scale": 2.0,
                "data_path": "location.y",
            },
        ]
    },
    {
        "active": False,
        "name": "Mapping Set 1",
        "button_mappings": [
            {
                "enabled": False,
                "object": "Plane",
                "name": "Move X",
                "button": "lx",
                "scale": 2.0,
                "data_path": "location.x",
            },
            {
                "enabled": False,
                "object": "Plane",
                "name": "Move Y",
                "button": "ly",
                "scale": 2.0,
                "data_path": "location.y",
            },
            {
                "enabled": True,
                "object": "Plane",
                "name": "Rotate Z",
                "button": "rx",
                "scale": 1.0,
                "data_path": "rotation_euler.z",
            },
            {
                "enabled": True,
                "object": "Plane",
                "name": "Rotate X",
                "button": "ry",
                "scale": 1.0,
                "data_path": "rotation_euler.x",
            },
            {
                "enabled": True,
                "object": "Mouth",
                "name": "A",
                "button": "rt",
                "scale": 1.0,
                "data_path": 'data.shape_keys.key_blocks["Key 1"].value',
            },
            {
                "enabled": True,
                "object": "Plane",
                "name": "A",
                "button": "a",
                "scale": 1.0,
                "data_path": 'data.shape_keys.key_blocks["Key 1"].value',
            },
            {
                "enabled": True,
                "object": "Mouth",
                "name": "B",
                "button": "lt",
                "scale": 1.0,
                "data_path": 'data.shape_keys.key_blocks["Key 2"].value',
            },
            # Add more mappings as needed
        ],
    }
]


class FG_OT_StartController(bpy.types.Operator):
    """Start polling the gamepad"""

    bl_idname = "fg.start_controller"
    bl_label = "Start Gamepad Controller"

    _timer = None

    def modal(self, context, event):
        scene = context.scene
        if event.type == "TIMER":
            axes = fastgamepad.get_axes()
            buttons = fastgamepad.get_buttons()
            # combine axes and buttons into one dictionary
            combined = {**axes, **buttons}
            # print(combined)

            ob = bpy.context.active_object

            active_mapping_set = next((ms for ms in mapping_sets if ms["active"]), None)

            if ob and active_mapping_set:
                for mapping in active_mapping_set["button_mappings"]:
                    if not mapping["enabled"]:
                        continue
                    value = combined.get(mapping["button"], 0) * mapping["scale"]
                    ob = bpy.data.objects.get(mapping["object"])
                    command = "ob." + mapping["data_path"] + " = " + str(value)
                    # print(command)
                    exec(command)

        # Cancel on ESC
        if event.type == "ESC":
            self.cancel(context)
            return {"CANCELLED"}

        return {"PASS_THROUGH"}

    def execute(self, context):
        fastgamepad.init()
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.03, window=context.window)  # 33 Hz
        wm.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def cancel(self, context):
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)
        fastgamepad.quit()
        # print("Gamepad polling cancelled.")


def register():
    bpy.utils.register_class(FG_OT_StartController)
    # Add custom properties to store joystick values
    bpy.types.Scene.fg_lx = bpy.props.FloatProperty()
    bpy.types.Scene.fg_ly = bpy.props.FloatProperty()
    bpy.types.Scene.fg_rx = bpy.props.FloatProperty()
    bpy.types.Scene.fg_ry = bpy.props.FloatProperty()
    bpy.types.Scene.fg_a = bpy.props.FloatProperty()


def unregister():
    bpy.utils.unregister_class(FG_OT_StartController)
    del bpy.types.Scene.fg_lx
    del bpy.types.Scene.fg_ly
    del bpy.types.Scene.fg_rx
    del bpy.types.Scene.fg_ry
    del bpy.types.Scene.fg_a


if __name__ == "__main__":
    register()

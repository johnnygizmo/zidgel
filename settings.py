import bpy 

class JOHNNYGIZMO_PuppetStringsSettings(bpy.types.PropertyGroup):
    controller_fps: bpy.props.FloatProperty(
    name="Controller FPS",
    description="Polling rate for gamepad controller",
    default=33.0,
    min=1.0,
    max=240.0
)# type: ignore
    keyframe_interval: bpy.props.IntProperty(
    name="Keyframe Interval",
    description="Interval between keyframes",
    default=1,
    min=1,
    max=240
)# type: ignore
    enable_record: bpy.props.BoolProperty(
    name="Enable Record",
    description="Enable recording of keyframes",
    default=False
)# type: ignore
    controller_running: bpy.props.BoolProperty(
    name="Controller Running",
    default=False 
) # type: ignore
def register():
    bpy.utils.register_class(JOHNNYGIZMO_PuppetStringsSettings)
    bpy.types.Scene.johnnygizmo_puppetstrings_settings = bpy.props.PointerProperty(type=JOHNNYGIZMO_PuppetStringsSettings)

def unregister():
    del bpy.types.Scene.johnnygizmo_puppetstrings_settings
    bpy.utils.unregister_class(JOHNNYGIZMO_PuppetStringsSettings)
   
    
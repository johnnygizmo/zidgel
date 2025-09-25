import bpy
from . import fastgamepad

class JOHNNYGIZMO_PuppetStringsSettings(bpy.types.PropertyGroup):
    controller_fps: bpy.props.FloatProperty(
        name="Controller FPS",
        description="Polling rate for gamepad controller",
        default=33.0,
        min=1.0,
        max=240.0,
    )  # type: ignore
    keyframe_interval: bpy.props.IntProperty(
        name="Keyframe Interval",
        description="Interval between keyframes",
        default=1,
        min=1,
        max=240,
    )  # type: ignore
    enable_record: bpy.props.BoolProperty(
        name="Enable Record", description="Enable recording of keyframes", default=False
    )  # type: ignore

    controller_running: bpy.props.BoolProperty(
        name="Controller Running", default=False
    )  # type: ignore
    punch_in_marker: bpy.props.StringProperty(
        name="Punch In Marker", description="Timeline marker to punch in", default=""
    )  # type: ignore
    punch_out_marker: bpy.props.StringProperty(
        name="Punch Out Marker", description="Timeline marker to punch out", default=""
    )  # type: ignore

    pre_roll: bpy.props.IntProperty(
        name="Pre Roll",
        description="Number of frames to wait before starting recording",
        default=0,
        min=0,
    )  # type: ignore

    # punch_in: bpy.props.IntProperty(
    #     name="Punch In",
    #     description="Frame to start recording",
    #     default=1,
    #     min=1,
    # )  # type: ignore

    # punch_out: bpy.props.IntProperty(
    #     name="Punch Out",
    #     description="Frame to stop recording",
    #     default=10,
    #     min=1,
    # )  # type: ignore

    one_shot: bpy.props.BoolProperty(
        name="One Shot",
        description="Record only once between punch in and punch out",
        default=False,
    )  # type: ignore

    use_punch: bpy.props.BoolProperty(
        name="Use Punch", description="Use punch in and punch out frames", default=False
    )  # type: ignore

    def update_smoothing(self, context):
        if fastgamepad.initialized():
            fastgamepad.set_smoothing(self.smoothing)
    def update_debounce(self, context):
        if fastgamepad.initialized():
            fastgamepad.set_debounce(self.debounce_time)

    smoothing: bpy.props.IntProperty(
        name="Smoothing ms",
        description="Smoothing factor for input values",
        default=150,
        update=update_smoothing,
    ) # type: ignore
    debounce_time: bpy.props.IntProperty(
        name="Debounce Time ms",
        description="Debounce time for button presses",
        default=50,
        update=update_debounce,
    ) # type: ignore

    keyframes_muted: bpy.props.BoolProperty(
        name="Keyframes Muted",
        description="Mute all keyframes created by Puppet Strings",
        default=False,
    )  # type: ignore
    
    auto_simplify:  bpy.props.EnumProperty(
        name="Auto-Simplify",
        description="Automatically Enable/Disable Simplify on Playback",
        items=[
            ("none","None","Disable"),
            ("rec","Record","Only Disable if Record or Punch is Enabled"),
            ("play","Play/Rec","Disable during any playback/record")
        ],
        default="none",
    )  # type: ignore
    
    version: bpy.props.StringProperty(
        name="Version",
        default= ""
        )  # type: ignore

def register():
    bpy.utils.register_class(JOHNNYGIZMO_PuppetStringsSettings)
    bpy.types.Scene.johnnygizmo_puppetstrings_settings = bpy.props.PointerProperty(
        type=JOHNNYGIZMO_PuppetStringsSettings
    )


def unregister():
    del bpy.types.Scene.johnnygizmo_puppetstrings_settings
    bpy.utils.unregister_class(JOHNNYGIZMO_PuppetStringsSettings)

import bpy  # type: ignore


VECTOR_AXES = [("x", "X", ""), ("y", "Y", ""), ("z", "Z", "")]

MAPPING_TARGETS = [
    ("object", "Object", "Map to Object Properties"),

]

MAPPING_OPS = [
    ("value", "Direct Value", "Use the button/axis value directly"),
    ("invertb", "Inverted Button Value (1 - value)", "Use the inverted button value (1 - value)"),
    ("inverta", "Inverted Axis Value (-value)", "Use the inverted axis value (-value)"),
    ("expression", "AssignmentExpression", "Use a Python expression to modify the button/axis value"),
]

MAPPING_TYPES = [
    ("location", "Location", "","OBJECT_ORIGIN",1),
    ("rotation_euler", "Rotation Euler", "","DRIVER_ROTATIONAL_DIFFERENCE",2),
    ("scale", "Scale","", "FULLSCREEN_ENTER",4),
    ("shape_key", "Shape Key", "","SHAPEKEY_DATA",8),
    ("modifier", "Modifier Value", "","MODIFIER",16),

    ("other", "Data Path", "","QUESTION",2048),
]

GAMEPAD_BUTTONS = [
    ("lx", "Left Stick X", ""),
    ("ly", "Left Stick Y", ""),
    ("lstick", "Left Stick Press", ""),

    ("rx", "Right Stick X", ""),
    ("ry", "Right Stick Y", ""),
    ("rstick", "Right Stick Press", ""),

    ("south", "South Button", "Bottom face button (e.g. Xbox A button)"),
    ("east", "East Button", "Bottom face button (e.g. Xbox B button)"),
    ("west", "West Button", "Bottom face button (e.g. Xbox X button)"),
    ("north", "North Button", "Bottom face button (e.g. Xbox Y button)"),

    ("lshoulder", "Left Shoulder", ""),
    ("lt", "Left Trigger", ""),
    ("rshoulder", "Right Shoulder", ""),
    ("rt", "Right Trigger", ""),
    ("dpad_up", "D-Pad Up", ""),
    ("dpad_down", "D-Pad Down", ""),
    ("dpad_left", "D-Pad Left", ""),
    ("dpad_right", "D-Pad Right", ""),

    ("back", "Back Button", ""),
    ("start", "Start Button", ""),
    ("guide", "Guide Button", ""),

    ("lp1", "Left Paddle 1", "Upper or primary paddle, under your left hand (e.g. Xbox Elite paddle P3, DualSense Edge LB button, Left Joy-Con SL button)"),
    ("lp2", "Left Paddle 2", "Lower or secondary paddle, under your left hand (e.g. Xbox Elite paddle P4, DualSense Edge left Fn button, Left Joy-Con SR button) "),
    ("rp1", "Right Paddle 1", "Upper or primary paddle, under your right hand (e.g. Xbox Elite paddle P1, DualSense Edge RB button, Right Joy-Con SR button)"),
    ("rp2", "Right Paddle 2", "Lower or secondary paddle, under your right hand (e.g. Xbox Elite paddle P2, DualSense Edge right Fn button, Right Joy-Con SL button)"),

    ("misc1", "Misc1 Button", "Additional button (e.g. Xbox Series X share button, PS5 microphone button, Nintendo Switch Pro capture button, Amazon Luna microphone button, Google Stadia capture button)"),
    ("misc2", "Misc2 Button", "Additional button"), 
    ("misc3", "Misc3 Button", "Additional button (e.g. Nintendo GameCube left trigger click)"), 
    ("misc4", "Misc4 Button", "Additional button (e.g. Nintendo GameCube right trigger click)"), 
    ("misc5", "Misc5 Button", "Additional button"), 
    ("misc6", "Misc6 Button", "Additional button"), 
    ("touchbutton", "Touch Button", ""), 

    # Add more as needed
]

class ButtonMapping(bpy.types.PropertyGroup):
    target: bpy.props.EnumProperty(
        name="Target",
        items=MAPPING_TARGETS,
        description="Target to map to",
        default="object"
    ) # type: ignore

    enabled: bpy.props.BoolProperty(name="Enabled", default=True) # type: ignore
    object: bpy.props.StringProperty(name="Object") # type: ignore
    
    operation:  bpy.props.EnumProperty(
        name="Opeation",
        items=MAPPING_OPS,
        description=""
    ) # type: ignore
    expression: bpy.props.StringProperty(name="Expression", default=" = value") # type: ignore
    button: bpy.props.EnumProperty(
        name="Button",
        items=GAMEPAD_BUTTONS,
        description="Gamepad button"
    ) # type: ignore
    invert: bpy.props.BoolProperty(name="Invert", default=False) # type: ignore
    mapping_type: bpy.props.EnumProperty(
        name="Mapping Type",
        items=MAPPING_TYPES,
        description="Type of mapping"
    ) # type: ignore
    scale: bpy.props.FloatProperty(name="Scale", default=1.0) # type: ignore

    axis: bpy.props.EnumProperty(
        name="Axis",
        items=VECTOR_AXES,
        description="Axis to map"
    ) # type: ignore
    data_path: bpy.props.StringProperty(name="Data Path") # type: ignore
    sub_data_path: bpy.props.StringProperty(name="Sub Data Path") # type: ignore

class MappingSet(bpy.types.PropertyGroup):
    active: bpy.props.BoolProperty(name="Enabled", default=True) # type: ignore
    name: bpy.props.StringProperty(name="Name", default="New Mapping Set") # type: ignore
    button_mappings: bpy.props.CollectionProperty(type=ButtonMapping) # type: ignore
    active_button_mapping_index: bpy.props.IntProperty(name="Active Button Mapping Index", default=0) # type: ignore

def register():
    bpy.utils.register_class(ButtonMapping)
    bpy.utils.register_class(MappingSet)
    bpy.types.Scene.johnnygizmo_puppetstrings_mapping_sets = bpy.props.CollectionProperty(type=MappingSet)
    bpy.types.Scene.johnnygizmo_puppetstrings_active_mapping_set = bpy.props.IntProperty(name="Active Mapping Set", default=0)


def unregister():
    del bpy.types.Scene.johnnygizmo_puppetstrings_mapping_sets
    del bpy.types.Scene.johnnygizmo_puppetstrings_active_mapping_set
    bpy.utils.unregister_class(MappingSet)
    bpy.utils.unregister_class(ButtonMapping)


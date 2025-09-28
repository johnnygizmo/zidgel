import bpy  # type: ignore


VECTOR_AXES = [("x", "X", ""), ("y", "Y", ""), ("z", "Z", "")]

MAPPING_TARGETS = [
    ("object", "Object", "Map to Object Properties"),

]
INPUT_EASING = [
    ("linear", "Linear", "Linear response"),
    ("x2", "X^2", "Quadratic response"),
    ("x3", "X^3", "Cubic response"),
    ("sqrt", "Sqrt", "Square root response"),
    ("cubet", "Cubert", "Cube root response"),
    ("sin", "Sine", "Smooth S-shaped response"),
    ("log", "Logarithmic", "Fast at start then slow later"),
    ("smoothstep", "Smoothstep", "Smoothstep function response"),
]
MAPPING_OPS = [
    ("value", "Direct Value", "Use the button/axis value directly"),
    ("curve","Curve","Use a curve to define conversion"),
    ("invertb", "Inverted Button Value (1 - value)", "Use the inverted button value (1 - value)"),
    ("inverta", "Inverted Axis Value (-value)", "Use the inverted axis value (-value)"),
    ("expression", "AssignmentExpression", "Use a Python expression to modify the button/axis value"),
]

ASSIGNMENT_TYPES = [
    ("equal", "= Set Value", "Set value"),
    ("add", "+= Additive", "Add to value"),
    ("subtract", "-= Subtractive", "Subtract from value")
    #,
    #("multiply", "*=", "Multiply value"),
]

MAPPING_TYPES = [
    ("location", "Location", "","OBJECT_ORIGIN",1),
    ("rotation_euler", "Rotation Euler", "","DRIVER_ROTATIONAL_DIFFERENCE",2),
    ("scale", "Scale","", "FULLSCREEN_ENTER",4),
    ("shape_key", "Shape Key", "","SHAPEKEY_DATA",8),
    ("modifier", "Modifier Value", "","MODIFIER",16),

    ("other", "Data Path", "","QUESTION",2048),
]

class ButtonSetting(bpy.types.PropertyGroup):
    id: bpy.props.IntProperty(name="Id", default=-1) #type: ignore
    name: bpy.props.StringProperty(name="Name", default="none") # type: ignore
    full_name: bpy.props.StringProperty(name="Name", default="none") # type: ignore
    desc: bpy.props.StringProperty(name="Name", default="none") # type: ignore
    smooth: bpy.props.IntProperty(name="Smoothing ms", default=150) # type: ignore
    debounce:bpy.props.IntProperty(name="Debouncing ms", default=50)# type: ignore

BUTTON_DATA = [
    (1000,"lx", "Left Stick X", ""),
    (1001,"ly", "Left Stick Y", ""),
    (1002,"rx", "Right Stick X", ""),
    (1003,"ry", "Right Stick Y", ""),
    (1004,"lt", "Left Trigger", ""),
    (1005,"rt", "Right Trigger", ""), 
    
    (0,"south", "South Button", "Bottom face button (e.g. Xbox A button)"),
    (1,"east", "East Button", "Bottom face button (e.g. Xbox B button)"),
    (2,"west", "West Button", "Bottom face button (e.g. Xbox X button)"),
    (3,"north", "North Button", "Bottom face button (e.g. Xbox Y button)"),
    (4,"back", "Back Button", ""),
    (5,"guide", "Guide Button", ""),
    (6,"start", "Start Button", ""),
    (7,"lstick", "Left Stick Press", ""),
    (8,"rstick", "Right Stick Press", ""),
    (9,"lshoulder", "Left Shoulder", ""),
    (10,"rshoulder", "Right Shoulder", ""),
    (11,"dpad_up", "D-Pad Up", ""),
    (12,"dpad_down", "D-Pad Down", ""),
    (13,"dpad_left", "D-Pad Left", ""),
    (14,"dpad_right", "D-Pad Right", ""),   
    (16,"rp1", "Right Paddle 1", "Upper or primary paddle, under your right hand (e.g. Xbox Elite paddle P1, DualSense Edge RB button, Right Joy-Con SR button)"),
    (17,"lp1", "Left Paddle 1", "Upper or primary paddle, under your left hand (e.g. Xbox Elite paddle P3, DualSense Edge LB button, Left Joy-Con SL button)"),
    (18,"rp2", "Right Paddle 2", "Lower or secondary paddle, under your right hand (e.g. Xbox Elite paddle P2, DualSense Edge right Fn button, Right Joy-Con SL button)"),
    (19,"lp2", "Left Paddle 2", "Lower or secondary paddle, under your left hand (e.g. Xbox Elite paddle P4, DualSense Edge left Fn button, Left Joy-Con SR button) "),
    (20,"touchpad", "Touch Button", ""), 
    (15,"misc1", "Misc1 Button", "Additional button (e.g. Xbox Series X share button, PS5 microphone button, Nintendo Switch Pro capture button, Amazon Luna microphone button, Google Stadia capture button)"),
    # (21,"misc2", "Misc2 Button", "Additional button"), 
    # (22,"misc3", "Misc3 Button", "Additional button (e.g. Nintendo GameCube left trigger click)"), 
    # (23,"misc4", "Misc4 Button", "Additional button (e.g. Nintendo GameCube right trigger click)"), 
    # (24,"misc5", "Misc5 Button", "Additional button"), 
    # (25,"misc6", "Misc6 Button", "Additional button"), 


    (2001,"accelx", "Accelerometer X", "X axis of accelerometer sensor"),
    (2101,"accely", "Accelerometer Y", "Y axis of accelerometer sensor"),
    (2201,"accelz", "Accelerometer Z", "Z axis of accelerometer sensor"),
    (2002,"gyrox", "Gyroscope X", "X axis of gyroscope sensor"),
    (2102,"gyroy", "Gyroscope Y", "Y axis of gyroscope sensor"),
    (2202,"gyroz", "Gyroscope Z", "Z axis of gyroscope sensor"),


    (3000,"finger1down", "Touch Finger 1 Down", "Is finger 1 touching the touchpad"),
    (3100,"finger1x", "Touch Finger 1 X", "X position of finger 1 on the touchpad"),
    (3200,"finger1y", "Touch Finger 1 Y", "Y position of finger 1 on the touchpad"),
    #(3300,"finger1pressure", "Finger 1 Pressure", "Pressure of finger 1 on the touchpad"),

    (3001,"finger2down", "Touch Finger 2 Down", "Is finger 2 touching the touchpad"),
    (3101,"finger2x", "Touch Finger 2 X", "X position of finger 2 on the touchpad"),
    (3201,"finger2y", "Touch Finger 2 Y", "Y position of finger 2 on the touchpad"),
    #(3301,"finger2pressure", "Finger 2 Pressure", "Pressure of finger 2 on the touchpad"),


    # (2003,"accelx_l", "Left Accelerometer X", "X axis of left accelerometer sensor"),
    # (2103,"accely_l", "Left Accelerometer Y", "Y axis of left accelerometer sensor"),
    # (2203,"accelz_l", "Left Accelerometer Z", "Z axis of left accelerometer sensor"),
    # (2004,"gyrox_l", "Left Gyroscope X", "X axis of left gyroscope sensor"),
    # (2104,"gyroy_l", "Left Gyroscope Y", "Y axis of left gyroscope sensor"),
    # (2204,"gyroz_l", "Left Gyroscope Z", "Z axis of left gyroscope sensor"),

    # (2005,"accelx_r", "Right Accelerometer X", "X axis of right accelerometer sensor"),
    # (2105,"accely_r", "Right Accelerometer Y", "Y axis of right accelerometer sensor"),
    # (2205,"accelz_r", "Right Accelerometer Z", "Z axis of right accelerometer sensor"),
    # (2006,"gyrox_r", "Right Gyroscope X", "X axis of right gyroscope sensor"),
    # (2106,"gyroy_r", "Right Gyroscope Y", "Y axis of right gyroscope sensor"),
    # (2206,"gyroz_r", "Right Gyroscope Z", "Z axis of right gyroscope sensor"),

]
def create_buttons():
    scene = bpy.context.scene
    buttons = scene.johnnygizmo_puppetstrings_buttons_settings
    buttons.clear()

    for b in BUTTON_DATA:
        item = buttons.add()
        item.id = b[0]
        item.name = b[1]
        item.full_name = b[2]
        item.desc = b[3]

        
def get_buttons(a,aa):
    output = []
    for b in BUTTON_DATA:
        if b[0] not in (4,5,6):
            output.append((b[1],b[2],b[3]))
    return output


def set_active_object(mapping, context):
    if not mapping.object_target:
        mapping.sub_data_path = ""
        return None
    for o in bpy.context.selected_objects:
        o.select_set(False)
    mapping.object_target.select_set(True)
    bpy.context.view_layer.objects.active = mapping.object_target
    mapping.sub_data_path = ""
    if mapping.object_target.type == 'ARMATURE':
        if bpy.context.object.mode != 'POSE':
            bpy.ops.object.mode_set(mode='POSE')    
    return None

def post_bone_pick(mapping, context):
    if mapping.object_target.type == 'ARMATURE' and mapping.sub_data_path != "":
        if bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')     

class ButtonMapping(bpy.types.PropertyGroup):
    show_panel: bpy.props.BoolProperty(
        name="Show Panel",
        default=True
    ) # type: ignore
    
    target: bpy.props.EnumProperty(
        name="Target",
        items=MAPPING_TARGETS,
        description="Target to map to",
        default="object"
    ) # type: ignore


    name: bpy.props.StringProperty(name="Name", default="Name") # type: ignore
    enabled: bpy.props.BoolProperty(name="Enabled", default=True) # type: ignore
    object_target : bpy.props.PointerProperty(
        name="Selected Object",
        description="Selected Object",
        type=bpy.types.Object,
        update = set_active_object

    ) # type: ignore
    
    operation:  bpy.props.EnumProperty(
        name="Opeation",
        items=MAPPING_OPS,
        description=""
    ) # type: ignore
    expression: bpy.props.StringProperty(name="Expression", default=" = value") # type: ignore
    button: bpy.props.EnumProperty(
        name="Button",
        items=get_buttons,
        description="Gamepad button"
    ) # type: ignore
    invert: bpy.props.BoolProperty(name="Invert", default=False) # type: ignore
    mapping_type: bpy.props.EnumProperty(
        name="Mapping Type",
        items=MAPPING_TYPES,
        description="Type of mapping"
    ) # type: ignore
    input_easing: bpy.props.EnumProperty(
        name="Input Easing",
        items=INPUT_EASING,
        description="Easing function to apply to input value",
        default="linear"
    ) # type: ignore
    scale: bpy.props.FloatProperty(name="Scale", default=1.0) # type: ignore

    assignment: bpy.props.EnumProperty(
        name="Assignment Type",
        items=ASSIGNMENT_TYPES,
        description="Type of assignment to perform",
        default="equal"
    ) # type: ignore

    axis: bpy.props.EnumProperty(
        name="Axis",
        items=VECTOR_AXES,
        description="Axis to map"
    ) # type: ignore

    smoothing_ms: bpy.props.IntProperty(name="Smoothing ms", default = 100) #type: ignore
    debounce_ms: bpy.props.IntProperty(name="Debounce ms", default = 50) #type: ignore 
    data_path: bpy.props.StringProperty(name="Data Path") # type: ignore
    sub_data_path: bpy.props.StringProperty(name="Sub Data Path") # type: ignore
    curve_owner: bpy.props.PointerProperty(type=bpy.types.Brush)# type: ignore
    keyframe_rate_override: bpy.props.IntProperty(name="Keyframe Rate Override", default=0, min=0, description="Override the keyframe rate for this mapping, 0 for global setting") # type: ignore
    is_last_value_captured: bpy.props.BoolProperty(name="Last Value Captured", default=False) # type: ignore
    last_value: bpy.props.FloatProperty(name="Last Value", default=0.0) # type: ignore

    rounding: bpy.props.IntProperty(name="Rounding", default=3, min=0, max=6) # type: ignore
    scaling: bpy.props.FloatProperty(name="Scaling", default=1.0) # type: ignore


    use_input_clipping: bpy.props.BoolProperty(name="Input Clipping", default=False) # type: ignore
    input_clip_min: bpy.props.FloatProperty(name="Input Clip Min", default=-1.0) # type: ignore
    input_clip_max: bpy.props.FloatProperty(name="Input Clip Max", default=1.0) # type: ignore

    use_clipping: bpy.props.BoolProperty(name="Clipping", default=False) # type: ignore
    clip_min: bpy.props.FloatProperty(name="Clip Min", default=-1.0) # type: ignore
    clip_max: bpy.props.FloatProperty(name="Clip Max", default=1.0) # type: ignore


def update_active_mapping_set(self,context):
    gamepad = self.gamepad_number
    if not self.active:
        return
    for ms in bpy.context.scene.johnnygizmo_puppetstrings_mapping_sets:
        if ms == self:
            continue
        if self.active and ms.gamepad_number == gamepad:
            ms.active = False

class MappingSet(bpy.types.PropertyGroup):
    active: bpy.props.BoolProperty(name="Enabled", default=False, update=update_active_mapping_set) # type: ignore
    name: bpy.props.StringProperty(name="Name", default="New Mapping Set") # type: ignore
    gamepad_number: bpy.props.IntProperty(
        name="Controller Number",
        default=0,
        update=update_active_mapping_set
    ) #type: ignore
    button_mappings: bpy.props.CollectionProperty(type=ButtonMapping) # type: ignore
    active_button_mapping_index: bpy.props.IntProperty(name="Active Button Mapping Index", default=0) # type: ignore

def register():
    bpy.utils.register_class(ButtonSetting)
    bpy.utils.register_class(ButtonMapping)
    bpy.utils.register_class(MappingSet)
    
    bpy.types.Scene.johnnygizmo_puppetstrings_mapping_sets = bpy.props.CollectionProperty(type=MappingSet)
    bpy.types.Scene.johnnygizmo_puppetstrings_buttons_settings =  bpy.props.CollectionProperty(type=ButtonSetting)
    bpy.types.Scene.johnnygizmo_puppetstrings_active_mapping_set = bpy.props.IntProperty(name="Active Mapping Set", default=0)


def unregister():
    del bpy.types.Scene.johnnygizmo_puppetstrings_mapping_sets
    del bpy.types.Scene.johnnygizmo_puppetstrings_active_mapping_set
    del bpy.types.Scene.johnnygizmo_puppetstrings_buttons_settings

    bpy.utils.unregister_class(MappingSet)
    bpy.utils.unregister_class(ButtonMapping)
    bpy.utils.unregister_class(ButtonSetting)

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
import math
from . import rumble
from pathlib import Path
from . import mapping_data

extension_dir = Path(__file__).parent
if str(extension_dir) not in sys.path:
    sys.path.insert(0, str(extension_dir))
if hasattr(os, 'add_dll_directory') and os.name == 'nt':
    os.add_dll_directory(str(extension_dir))

from . import fastgamepad
from . import mapping_data

class FG_OT_StartController(bpy.types.Operator):
    """Start polling the gamepad"""

    bl_idname = "fg.start_controller"
    bl_label = "Start Gamepad Controller"

    _timer = None
    _punch_in = None
    _punch_out = None
    _pre_roll = 0

    action: bpy.props.EnumProperty(
        name="Action",
        description="Action to perform",
        default="START",
        items=[
            ("START", "Start", "Start the gamepad controller"),
            ("STOP", "Stop", "Stop the gamepad controller"),
        ],) # type: ignore

    def modal(self, context, event):
        scene = context.scene
        settings = scene.johnnygizmo_puppetstrings_settings
        settings.controller_running = fastgamepad.initialized()
        if not settings.controller_running:
            self.cancel(context)
            return {"CANCELLED"}

        if event.type == "TIMER":
            axes = fastgamepad.get_axes()
            buttons = fastgamepad.get_buttons()

            ob = bpy.context.active_object
            mapping_sets = context.scene.johnnygizmo_puppetstrings_mapping_sets
            active_mapping_set = None
            if len(mapping_sets) > 0:
                active_mapping_set = mapping_sets[context.scene.johnnygizmo_puppetstrings_active_mapping_set]

            if buttons.get("start", 0) == 1:
                if not context.screen.is_animation_playing:
                    bpy.ops.puppetstrings.playback(action="PLAY")
                        
            if buttons.get("back", 0) == 1:
                if context.screen.is_animation_playing:
                    bpy.ops.puppetstrings.playback(action="STOP")
                    return {"PASS_THROUGH"}
                else:
                    scene.frame_current = scene.frame_start
                    return {"PASS_THROUGH"}
                
            combined = {**axes, **buttons}            

            if ob and active_mapping_set and active_mapping_set.active :
                for mapping in active_mapping_set.button_mappings:
                    if not mapping.enabled or mapping.object == "":
                        continue
                    
                    op = mapping.operation
                    value = combined.get(mapping.button)                
                    if mapping.input_easing == "linear":
                        pass
                    elif mapping.input_easing == "x2":
                        value = value**2 * (1 if value >= 0 else -1)
                    elif mapping.input_easing == "x3":
                        value = value**3
                    elif mapping.input_easing == "sqrt":
                        value = math.sqrt(math.fabs(value)) * (1 if value >= 0 else -1)
                    elif mapping.input_easing == "cubet":
                        value = math.pow(math.fabs(value),.333) * (1 if value >= 0 else -1)
                    elif mapping.input_easing == "sin":
                        value = math.sin(value * math.pi / 2)
                    elif mapping.input_easing == "log":
                        if value == 0:
                            value = 0
                        else:
                            value = math.copysign(math.log1p(math.fabs(value) * (math.e - 1)), value)
                    elif mapping.input_easing == "smoothstep":
                        x = (value + 1) / 2
                        s = 3*x * x - 2 * x * x * x
                        value = 2 * s -1
                    ob = bpy.data.objects.get(mapping.object)

                    command = " = " + str(value)
                    pre_command = ""
                    if mapping.operation == "curve":
                        mapped = mapping.curve_owner.curve.evaluate(mapping.curve_owner.curve.curves[0],value)
                        command = " = " + str(round(mapped,6))
                    if mapping.operation == "expression":
                        command = mapping.expression
                    elif mapping.operation == "invertb":
                        command = " = " + str(1 - value)
                    elif mapping.operation == "inverta":
                        command = " = " + str(-value)

                    if mapping.mapping_type == "location":
                        if ob.type != 'ARMATURE':
                            command = "ob.location." + mapping.axis + command
                        else:                            
                            command = "ob.pose.bones[\""+ mapping.sub_data_path +"\"].location." + mapping.axis + command

                    elif mapping.mapping_type == "rotation_euler":                        
                        if ob.type != 'ARMATURE':
                            pre_command = "ob.rotation_mode = 'XYZ'"
                            command = "ob.rotation_euler." + mapping.axis + command
                        else:            
                            pre_command = "ob.pose.bones[\""+ mapping.sub_data_path +"\"].rotation_mode = 'XYZ'"                
                            command = "ob.pose.bones[\""+ mapping.sub_data_path +"\"].rotation_euler." + mapping.axis + command            

                    elif mapping.mapping_type == "scale":                        
                        if ob.type != 'ARMATURE':
                            command = "ob.scale." + mapping.axis + command
                        else:                            
                            command = "ob.pose.bones[\""+ mapping.sub_data_path +"\"].scale." + mapping.axis + command            


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
                    
                    try:         
                        if pre_command != "":
                            exec(pre_command)          
                        exec(command)
                    except Exception as e:
                        pass
                    

                    if ob.type=="ARMATURE" and mapping.sub_data_path != "":
                        ob = ob.pose.bones[mapping.sub_data_path]
                        
                    if context.scene.johnnygizmo_puppetstrings_settings.enable_record and context.screen.is_animation_playing and not context.screen.is_scrubbing:
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
                        else:                        
                            index_map = {"x": 0, "y": 1, "z": 2}
                            if mapping.mapping_type == "location":
                                ob.keyframe_delete(data_path="location", index=index_map.get(mapping.data_path, -1))                              
                            elif mapping.mapping_type == "rotation_euler":
                                ob.keyframe_delete(data_path="rotation_euler", index=index_map.get(mapping.data_path, -1))
                            elif mapping.mapping_type == "scale":
                                ob.keyframe_delete(data_path="scale", index=index_map.get(mapping.data_path, -1))
                            elif mapping.mapping_type == "shape_key":
                                if ob.data.shape_keys:
                                    key = ob.data.shape_keys.key_blocks.get(mapping.data_path)
                                    if key:
                                        key.keyframe_delete(data_path="value")
                            elif mapping.mapping_type == "modifier":
                                if ob and ob.modifiers:
                                    mod = ob.modifiers.get(mapping.data_path)
                                    if mod and mapping.sub_data_path:
                                        mod.keyframe_delete(data_path=mapping.sub_data_path)                

        # Cancel on ESC
        if event.type == "ESC":
            settings.controller_running = False
            #print("Cancelling gamepad controller...")
            self.cancel(context)
            return {"CANCELLED"}
        return {"PASS_THROUGH"}

    def execute(self, context):   
        if len(bpy.context.scene.johnnygizmo_puppetstrings_buttons_settings)==0:
            mapping_data.create_buttons()
        if self.action == "STOP":               
            #print("Stopping gamepad controller...")         
            self.cancel(context)
            return {"FINISHED"}
        else:
            #print("Starting gamepad controller...")
            fastgamepad.init()
            fastgamepad.set_smoothing(context.scene.johnnygizmo_puppetstrings_settings.smoothing)
            wm = context.window_manager
            fps = context.scene.johnnygizmo_puppetstrings_settings.controller_fps
            interval = 1.0 / fps if fps > 0 else 0.03
            self._timer = wm.event_timer_add(interval, window=context.window)
            wm.modal_handler_add(self)
            context.scene.johnnygizmo_puppetstrings_settings.controller_running = True
            return {"RUNNING_MODAL"}

    def cancel(self, context):
        scene = context.scene
        settings  = scene.johnnygizmo_puppetstrings_settings
        settings.controller_running = False
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)
        context.scene.johnnygizmo_puppetstrings_settings.controller_running = False
        fastgamepad.quit()
        return {"CANCELLED"}


def post_playback_handler(scene,depsgrap):
    settings = scene.johnnygizmo_puppetstrings_settings 
    mapping_sets = scene.johnnygizmo_puppetstrings_mapping_sets
    active_mapping_set = mapping_sets[scene.johnnygizmo_puppetstrings_active_mapping_set]

    if active_mapping_set.active == True:
        for mapping in active_mapping_set.button_mappings:
            if not mapping.enabled or mapping.object == "":
                continue
            curve = getCurve(mapping,settings)
            if curve: curve.mute = False

    if settings.auto_simplify == "rec" and (settings.use_punch or settings.enable_record):
        scene.render.use_simplify = False
    elif settings.auto_simplify == "play":
        scene.render.use_simplify = False 

def pre_playback_handler(scene,depsgrap):
    settings = scene.johnnygizmo_puppetstrings_settings 
    mapping_sets = scene.johnnygizmo_puppetstrings_mapping_sets
    active_mapping_set = mapping_sets[scene.johnnygizmo_puppetstrings_active_mapping_set]

    if settings.auto_simplify == "rec" and (settings.use_punch or settings.enable_record):
        scene.render.use_simplify = True
    elif settings.auto_simplify == "play":
        scene.render.use_simplify = True 

    if active_mapping_set.active == True:
        for mapping in active_mapping_set.button_mappings:
            if not mapping.enabled or mapping.object == "":
                continue   
            curve = getCurve(mapping,settings)
            if settings.enable_record or settings.use_punch:         
                if curve: curve.mute = True 
            else:
                if curve: curve.mute = False 
    if settings.enable_record:
        rumble.rumble_async(0xFFFF,0xFFFF,250)

def getCurve(mapping,settings):
    axis_map = {
        "x":0,
        "y":1,
        "z":2
    }
    
    ob = bpy.data.objects.get(mapping.object) 

    if mapping.mapping_type in [ "location" , "rotation_euler","scale"]:
        if(not ob or not ob.animation_data):
            return None
        action = ob.animation_data.action
        for layer in action.layers:                            
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for curve in cb.fcurves:   
                        if ob.type != 'ARMATURE':                                     
                            curve = next((curve for curve in cb.fcurves if curve.data_path ==  mapping.mapping_type and curve.array_index == axis_map[mapping.axis]), None)
                        else:
                            dp = f'pose.bones["{mapping.sub_data_path}"].{mapping.mapping_type}'
                            curve = next((curve for curve in cb.fcurves if curve.data_path ==  dp  and curve.array_index == axis_map[mapping.axis]), None)
                        if curve != None:
                            return curve                 


    elif mapping.mapping_type == "shape_key":
        if not ob or not ob.data or not ob.data.shape_keys or not ob.data.shape_keys.animation_data:
            return None
        if ob.data.shape_keys:
            key = ob.data.shape_keys.key_blocks.get(mapping.data_path)                    
            if key:
                action = ob.data.shape_keys.animation_data.action                        
                for layer in action.layers:                            
                    for strip in layer.strips:
                        for cb in strip.channelbags:
                            for curve in cb.fcurves:           
                                dp ="key_blocks[\""+mapping.data_path+"\"].value"                           
                                curve = next((curve for curve in cb.fcurves if curve.data_path == dp), None)         
                                if curve != None:
                                    return curve 
    return None
       
def pre_frame_change_handler(scene,depsgrap):
    settings = scene.johnnygizmo_puppetstrings_settings
    settings.controller_running = fastgamepad.initialized()
    punch_in_marker = getattr(settings, "punch_in_marker","")
    punch_out_marker = getattr(settings, "punch_out_marker","")        
    punch_in = scene.timeline_markers.get(punch_in_marker, None)
    punch_out = scene.timeline_markers.get(punch_out_marker, None)
            
    pre_roll = settings.pre_roll
    punch_in_frame = scene.frame_start
    if punch_in:
        punch_in_frame = punch_in.frame
    punch_out_frame = scene.frame_end
    if punch_out:
        punch_out_frame = punch_out.frame  


    if scene.frame_current == punch_in_frame and not settings.enable_record and settings.use_punch:
        settings.enable_record = True 
        rumble.rumble_async(0xFFFF,0xFFFF,250)
        
    if scene.frame_current == punch_out_frame and settings.enable_record and settings.use_punch:
        settings.enable_record = False
        rumble.rumble_async(0xFFFF,0xFFFF,250)

    if settings.use_punch and scene.frame_current > punch_out_frame + pre_roll:
        bpy.ops.puppetstrings.playback(action="STOP")
 
    if scene.frame_current == scene.frame_end and settings.one_shot:
        bpy.ops.screen.animation_cancel() 


def register(): 
    bpy.utils.register_class(FG_OT_StartController)
    bpy.app.handlers.animation_playback_pre.append(pre_playback_handler)
    bpy.app.handlers.animation_playback_post.append(post_playback_handler)
    bpy.app.handlers.frame_change_post.append(pre_frame_change_handler)

def unregister():
    bpy.app.handlers.frame_change_post.remove(pre_frame_change_handler)
    bpy.app.handlers.animation_playback_pre.remove(pre_playback_handler)
    bpy.app.handlers.animation_playback_post.remove(post_playback_handler)
    bpy.utils.unregister_class(FG_OT_StartController)

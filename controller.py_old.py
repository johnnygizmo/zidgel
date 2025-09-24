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
from . import handlers

extension_dir = Path(__file__).parent
if str(extension_dir) not in sys.path:
    sys.path.insert(0, str(extension_dir))
if hasattr(os, 'add_dll_directory') and os.name == 'nt':
    os.add_dll_directory(str(extension_dir))

from . import fastgamepad
from . import mapping_data


def easing(value, easing_type):
    if easing_type == "linear":
        return value
    elif easing_type == "x2":
        return value**2 * (1 if value >= 0 else -1)
    elif easing_type == "x3":
        return value**3
    elif easing_type == "sqrt":
        return math.sqrt(math.fabs(value)) * (1 if value >= 0 else -1)
    elif easing_type == "cubet":
        return math.pow(math.fabs(value),.333) * (1 if value >= 0 else -1)
    elif easing_type == "sin":
        return math.sin(value * math.pi / 2)
    elif easing_type == "log":
        if value == 0:
            return 0
        else:
            return math.copysign(math.log1p(math.fabs(value) * (math.e - 1)), value)
    elif easing_type == "smoothstep":
        x = (value + 1) / 2
        s = 3*x * x - 2 * x * x * x
        return 2 * s -1
    return value


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
            sensors = fastgamepad.get_sensors()

            ob = bpy.context.active_object
            mapping_sets = context.scene.johnnygizmo_puppetstrings_mapping_sets
            active_mapping_set = None
            if len(mapping_sets) > 0:
                active_mapping_set = mapping_sets[context.scene.johnnygizmo_puppetstrings_active_mapping_set]


            # Handle Start/Stop
            if buttons.get("start", 0) == 1:
                if not context.screen.is_animation_playing:
                    bpy.ops.puppetstrings.playback(action="PLAY")
                else:
                    settings.enable_record = not settings.enable_record
                                                    
            if buttons.get("back", 0) == 1:
                if context.screen.is_animation_playing:
                    bpy.ops.puppetstrings.playback(action="STOP")
                else:
                    scene.frame_current = scene.frame_start
                
            combined = {**axes, **buttons} #, **sensors}            

            if ob and active_mapping_set and active_mapping_set.active :
                for mapping in active_mapping_set.button_mappings:
                    if not mapping.enabled or mapping.object == "":
                        continue
                    
                    op = mapping.operation
                    raw_value = combined.get(mapping.button)
                    value = raw_value

                    value = easing(value, mapping.input_easing)  
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

                    #keyframe_rate = context.scene.johnnygizmo_puppetstrings_settings.keyframe_interval
                    # if mapping.keyframe_rate_override > 0:
                    #     keyframe_rate = mapping.keyframe_rate_override



                    keyframe_rate = context.scene.johnnygizmo_puppetstrings_settings.keyframe_interval  
                    if context.scene.johnnygizmo_puppetstrings_settings.enable_record and context.screen.is_animation_playing and not context.screen.is_scrubbing:                                   
                    
                    
                        if(context.scene.frame_current % keyframe_rate ) == 0:# or first:
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
            self.cancel(context)
            return {"CANCELLED"}
        return {"PASS_THROUGH"}

    def execute(self, context):   
        if len(bpy.context.scene.johnnygizmo_puppetstrings_buttons_settings)==0:
            mapping_data.create_buttons()
        if self.action == "STOP":                     
            self.cancel(context)
            return {"FINISHED"}
        else:
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




def register(): 
    bpy.utils.register_class(FG_OT_StartController)
    bpy.app.handlers.animation_playback_pre.append(handlers.pre_playback_handler)
    bpy.app.handlers.animation_playback_post.append(handlers.post_playback_handler)
    bpy.app.handlers.frame_change_post.append(handlers.pre_frame_change_handler)

def unregister():
    bpy.app.handlers.frame_change_post.remove(handlers.pre_frame_change_handler)
    bpy.app.handlers.animation_playback_pre.remove(handlers.pre_playback_handler)
    bpy.app.handlers.animation_playback_post.remove(handlers.post_playback_handler)
    bpy.utils.unregister_class(FG_OT_StartController)

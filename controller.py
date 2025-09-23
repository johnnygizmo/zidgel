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
import time
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
    _session_start = 0.0

    action: bpy.props.EnumProperty(
        name="Action",
        description="Action to perform",
        default="START",
        items=[
            ("START", "Start", "Start the gamepad controller"),
            ("STOP", "Stop", "Stop the gamepad controller"),
        ],) # type: ignore

    
    def playback_controls(self, context, buttons):
        if buttons.get("start", 0) == 1:
            if not context.screen.is_animation_playing:                
                bpy.ops.puppetstrings.playback(action="PLAY")
            
                                                
        if buttons.get("back", 0) == 1:
            if context.screen.is_animation_playing:
                bpy.ops.puppetstrings.playback(action="STOP")
            else:
                context.scene.frame_current = context.scene.frame_start

        # if buttons.get("guide", 0) == 1:
        #     bpy.ops.puppetstrings.playback(action="STOP")
        #     self.cancel(context)

    def modify_keyframe(self, context, mapping, ob, insert):
        index_map = {"x": 0, "y": 1, "z": 2}
        if mapping.mapping_type == "location":
            if insert:
                ob.keyframe_insert(data_path="location", index=index_map.get(mapping.axis, -1))                              
            else:
                ob.keyframe_delete(data_path="location", index=index_map.get(mapping.axis, -1))
        elif mapping.mapping_type == "rotation_euler":
            if insert:
                ob.keyframe_insert(data_path="rotation_euler", index=index_map.get(mapping.axis, -1))
            else:
                ob.keyframe_delete(data_path="rotation_euler", index=index_map.get(mapping.axis, -1))
        elif mapping.mapping_type == "scale":
            if insert:
                ob.keyframe_insert(data_path="scale", index=index_map.get(mapping.axis, -1))
            else:
                ob.keyframe_delete(data_path="scale", index=index_map.get(mapping.axis, -1))
        elif mapping.mapping_type == "shape_key":
            if ob.data.shape_keys:
                key = ob.data.shape_keys.key_blocks.get(mapping.data_path)
                if key:
                    if insert:
                        key.keyframe_insert(data_path="value")
                    else:
                        key.keyframe_delete(data_path="value")
        elif mapping.mapping_type == "modifier":
            if ob and ob.modifiers:
                mod = ob.modifiers.get(mapping.data_path)
                if mod and mapping.sub_data_path:
                    if insert:
                        mod.keyframe_insert(data_path=mapping.sub_data_path)
                    else:
                        mod.keyframe_delete(data_path=mapping.sub_data_path)

    def get_active_mapping_set(self, context):
        mapping_sets = context.scene.johnnygizmo_puppetstrings_mapping_sets
        active_mapping_set = None
        if len(mapping_sets) > 0:
            return mapping_sets[context.scene.johnnygizmo_puppetstrings_active_mapping_set]
        else:
            return None

    def modal(self, context, event):
        scene = context.scene
        settings = scene.johnnygizmo_puppetstrings_settings
        settings.controller_running = fastgamepad.initialized()
        if not settings.controller_running:
            self.cancel(context)
            return {"CANCELLED"}

        if event.type == "TIMER":
            buttons_list = [4,5,6]
            m = scene.johnnygizmo_puppetstrings_mapping_sets[scene.johnnygizmo_puppetstrings_active_mapping_set]
            for mapping in m.button_mappings:
                bmd = next((b for b in mapping_data.BUTTON_DATA if b[1] == mapping.button), None)
                if bmd[0] not in buttons_list:                    
                    buttons_list.append(bmd[0])

            combined = fastgamepad.get_button_list(buttons_list)

            ob = bpy.context.active_object
            active_mapping_set = self.get_active_mapping_set(context)
            
            # Handle Start/Stop
            self.playback_controls(context, combined)

            if ob and active_mapping_set and active_mapping_set.active :
                for mapping in active_mapping_set.button_mappings:
                    if not mapping.enabled or mapping.object == "":
                        continue
                    
                    op = mapping.operation
                    raw_value = combined.get(mapping.button)
                    value = None
                    if mapping.is_trigger:                        
                        if raw_value == 0 and mapping.trigger_start_time == mapping_data.UNTRIGGERED:
                            continue

                        action_time = time.time() - self._session_start
                        # Triggered and No Current Action - Start Action
                        if raw_value == 1 and mapping.trigger_start_time == mapping_data.UNTRIGGERED:
                            mapping.trigger_start_time = action_time

                        # Running Action Finished, clean up                        
                        if action_time - mapping.trigger_start_time > mapping.trigger_duration:
                            mapping.trigger_start_time = mapping_data.UNTRIGGERED
                            #print("resetting" + str(action_time) + " " + str(mapping.trigger_start_time) + " " +str(mapping.trigger_duration   ))
                            continue
                        # Maybe scrubbed to past, clean up future presses
                        elif mapping.trigger_start_time > action_time:
                            #print("no great")
                            mapping.trigger_start_time = mapping_data.UNTRIGGERED
                            continue

                        # Running action, get value
                        action_elapsed = action_time - mapping.trigger_start_time
                        map_point = action_elapsed / mapping.trigger_duration                        
                        value = mapping.curve_owner.curve.evaluate(mapping.curve_owner.curve.curves[0],map_point)                        
                        print(str(map_point)+ " "+str(value))
                        #print("value " + str(action_frame) + " " + str(value))
                    else:
                        raw_value = raw_value * mapping.scaling
                        raw_value = round(raw_value, mapping.rounding)

                        if mapping.use_input_clipping:
                            raw_value = max(mapping.input_clip_min, min(mapping.input_clip_max, raw_value))

                        value = raw_value
                        value = easing(value, mapping.input_easing)  
                    
                    ob = bpy.data.objects.get(mapping.object)
                    if ob.type == 'ARMATURE' and mapping.mapping_type == "shape_key":
                        continue

                    scale = 1.0
                    assign = " = "
                    lvalue = ""
                    rvalue = value
                    pre_command = ""
                    retrieve_command = ""
                    final_command = ""
                    existing_value = 0.0
                    temp = 0.0

                    if mapping.assignment == "add":
                        assign = " += "
                        scale = 1 / scene.render.fps
                        
                    elif mapping.assignment == "subtract":
                        assign = " -= "
                        scale = 1 / scene.render.fps
                    elif mapping.assignment == "multiply":
                        assign = " *= "
                        scale = 1 / scene.render.fps

                    #command = assign + str(value*scale)
                    if mapping.operation == "curve" or mapping.is_trigger:
                        mapped = mapping.curve_owner.curve.evaluate(mapping.curve_owner.curve.curves[0],value)
                        #command = assign + str(round(mapped*scale,6)*mapping.output_scaling)
                        rvalue  = str(round(mapped*scale,6)*mapping.output_scaling)
                    elif mapping.operation == "expression":
                        #command = mapping.expression
                        rvalue = mapping.expression
                        assign = " = "
                    elif mapping.operation == "invertb":
                        #command = " = " + str(1 - value)
                        rvalue = str(1 - value)
                        assign = " = "
                    elif mapping.operation == "inverta":
                        #command = " = " + str(-value)
                        rvalue = str(-value)
                        assign = " = "


                    if mapping.mapping_type == "location":
                        if ob.type != 'ARMATURE' or mapping.sub_data_path == "" :
                         #   command = "ob.location." + mapping.axis + command
                            lvalue = "ob.location." + mapping.axis
                        else:                            
                          #  command = "ob.pose.bones[\""+ mapping.sub_data_path +"\"].location." + mapping.axis + command
                            lvalue = "ob.pose.bones[\""+ mapping.sub_data_path +"\"].location." + mapping.axis

                    elif mapping.mapping_type == "rotation_euler":                        
                        if ob.type != 'ARMATURE' or mapping.sub_data_path == "":
                            pre_command = "ob.rotation_mode = 'XYZ'"
                           # command = "ob.rotation_euler." + mapping.axis + command
                            lvalue = "ob.rotation_euler." + mapping.axis
                        else:            
                            pre_command = "ob.pose.bones[\""+ mapping.sub_data_path +"\"].rotation_mode = 'XYZ'"                
                            #command = "ob.pose.bones[\""+ mapping.sub_data_path +"\"].rotation_euler." + mapping.axis + command            
                            lvalue = "ob.pose.bones[\""+ mapping.sub_data_path +"\"].rotation_euler." + mapping.axis

                    elif mapping.mapping_type == "scale":                        
                        if ob.type != 'ARMATURE' or mapping.sub_data_path == "":
                            #command = "ob.scale." + mapping.axis + command
                            lvalue = "ob.scale." + mapping.axis
                        else:                            
                            #command = "ob.pose.bones[\""+ mapping.sub_data_path +"\"].scale." + mapping.axis + command            
                            lvalue = "ob.pose.bones[\""+ mapping.sub_data_path +"\"].scale." + mapping.axis

                    elif mapping.mapping_type == "shape_key":
                        if ob.data.shape_keys:
                            if ob.data.shape_keys.key_blocks.get(mapping.data_path):
                             #   command = "ob.data.shape_keys.key_blocks[\"" + mapping.data_path + "\"].value" + command
                                lvalue = "ob.data.shape_keys.key_blocks[\"" + mapping.data_path + "\"].value"
                            else:
                                continue
                        else:
                            continue
                    elif mapping.mapping_type == "modifier":
                        if ob and ob.modifiers:
                            mod = ob.modifiers.get(mapping.data_path)
                            if mod and mapping.sub_data_path:                                
                              #  command = "ob.modifiers[\"" + mapping.data_path + "\"]" + mapping.sub_data_path + command
                                lvalue = "ob.modifiers[\"" + mapping.data_path + "\"]" + mapping.sub_data_path
                            else:
                                continue
                        else:
                            continue
                    else:
                        command = "ob." + mapping.data_path + " = " + str(value)                               
                        lvalue = "ob." + mapping.data_path
                        rvalue = str(value)
                    # try:         
                    if 1:
                        if pre_command != "":                            
                            exec(pre_command)   

                        if not mapping.use_clipping:
                                final_command = lvalue + assign + str(rvalue)
                        else:
                            if mapping.assignment == "equal":
                                final_command = lvalue + assign + "max(" + str(mapping.clip_min) + ", min(" + str(mapping.clip_max) + "," + str(rvalue) + "))"
                            else:
                                existing_value = eval(str(lvalue))
                                temp = 0.0
                                if mapping.assignment == "add":
                                    temp = existing_value + float(rvalue)
                                elif mapping.assignment == "subtract":
                                    temp = existing_value - float(rvalue)
                                elif mapping.assignment == "multiply":                                  
                                    temp = existing_value * float(rvalue)                                                                    
                                clamp_value = max(mapping.clip_min, min(mapping.clip_max,temp))
                                final_command = lvalue + " = " + str(clamp_value)
                                
                        if final_command == "":
                            #print("Cmd: "+command)
                            exec(command)
                        else:

                            #print("Fcmd: "+final_command + "    " + str(existing_value))
                            exec(final_command)
                    # except Exception as e:
                    #     print(dir(e))
                    #     print(e.__context__)
                    #     pass
                    

                    if ob.type=="ARMATURE" and mapping.sub_data_path != "":
                        ob = ob.pose.bones[mapping.sub_data_path]

                    keyframe_rate = context.scene.johnnygizmo_puppetstrings_settings.keyframe_interval
                    if mapping.keyframe_rate_override > 0:
                        keyframe_rate = mapping.keyframe_rate_override

                    #keyframe_rate = context.scene.johnnygizmo_puppetstrings_settings.keyframe_interval  
                    if context.scene.johnnygizmo_puppetstrings_settings.enable_record and context.screen.is_animation_playing and not context.screen.is_scrubbing:
                        if (context.scene.frame_current % keyframe_rate) == 0:  # or first:
                            self.modify_keyframe(context, mapping, ob, True)
                        else:
                            self.modify_keyframe(context, mapping, ob, False)
                                    
        # Cancel on ESC
        if event.type == "ESC":
            settings.controller_running = False
            self.cancel(context)
            return {"CANCELLED"}
        return {"PASS_THROUGH"}


    def ensure_handler(self,handler_list, handler_func):
        if handler_func not in handler_list:
            handler_list.append(handler_func)


    def execute(self, context):   
        self._session_start = time.time()
        if self.action == "STOP":                     
            self.cancel(context)
            return {"FINISHED"}
        else:

            self.ensure_handler(bpy.app.handlers.animation_playback_pre, handlers.pre_playback_handler)
            self.ensure_handler(bpy.app.handlers.animation_playback_post, handlers.post_playback_handler)
            self.ensure_handler(bpy.app.handlers.frame_change_post, handlers.pre_frame_change_handler)
        
            fastgamepad.init()
            fastgamepad.set_smoothing(context.scene.johnnygizmo_puppetstrings_settings.smoothing)
            wm = context.window_manager
            fps = context.scene.johnnygizmo_puppetstrings_settings.controller_fps
            interval = 1 / fps if fps > 0 else 0.03

            if self._timer:
                wm.event_timer_remove(self._timer)
                self._timer = None
            else:
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
            self._timer = None
        context.scene.johnnygizmo_puppetstrings_settings.controller_running = False
        fastgamepad.quit()
        return None




def register(): 
    bpy.utils.register_class(FG_OT_StartController)
    bpy.app.handlers.animation_playback_pre.append(handlers.pre_playback_handler)
    bpy.app.handlers.animation_playback_post.append(handlers.post_playback_handler)
    bpy.app.handlers.frame_change_post.append(handlers.pre_frame_change_handler)
    bpy.app.handlers.load_post.append(handlers.load_file_handler)

def unregister():
    bpy.app.handlers.load_post.remove(handlers.load_file_handler)
    bpy.app.handlers.frame_change_post.remove(handlers.pre_frame_change_handler)
    bpy.app.handlers.animation_playback_pre.remove(handlers.pre_playback_handler)
    bpy.app.handlers.animation_playback_post.remove(handlers.post_playback_handler)
    bpy.utils.unregister_class(FG_OT_StartController)

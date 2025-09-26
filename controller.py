bl_info = {
    "name": "Fast Gamepad Control",
    "blender": (4, 2, 0),
    "category": "Animation",
    "version": (0, 1, 0),
    "description": "Use gamepad to control rigs",
}

from multiprocessing import context
import bpy
import math
#from . import rumble
from . import mapping_data
from . import handlers
from . import fastgamepad
from . import mapping_data
from .function_lib import easing


class FG_OT_StartController(bpy.types.Operator):
    """Start polling the gamepad"""

    bl_idname = "fg.start_controller"
    bl_label = "Start Gamepad Controller"

    _timer = None
    _punch_in = None
    _punch_out = None
    _pre_roll = 0
    previous_button_list = {}
    current_button_list = {}
    axis_map = {"x": 0, "y": 1, "z": 2}

    action: bpy.props.EnumProperty(
        name="Action",
        description="Action to perform",
        default="START",
        items=[
            ("START", "Start", "Start the gamepad controller"),
            ("STOP", "Stop", "Stop the gamepad controller"),
        ],) # type: ignore

    
    def playback_controls(self, context, buttons, prev):
        settings = context.scene.johnnygizmo_puppetstrings_settings
        start = buttons.get("start", 0)
        pstart =prev.get("start",0)

        guide = buttons.get("guide",0)
        pguide =prev.get("guide",0)

        back = buttons.get("back", 0)
        pback =prev.get("back",0)

        if guide == 1 and pguide == 0:            
            settings.mute_controller = not settings.mute_controller

        if not context.screen.is_animation_playing:
            if start == 1 and pstart == 0:                           
                bpy.ops.puppetstrings.playback(action="PLAY")
            if back == 1 and pback == 0:
                context.scene.frame_current = context.scene.frame_start
        else:
             if start == 1 and pstart == 0 and not settings.enable_record:                           
                settings.enable_record = True
             elif start == 1 and pstart == 0 and settings.enable_record:
                settings.enable_record = False
             if back == 1 and pback == 0:
                bpy.ops.puppetstrings.playback(action="STOP")

                

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
                    if "[" in mapping.sub_data_path and mapping.sub_data_path.endswith("]"):
                        prop_name, idx = mapping.sub_data_path[:-1].split("[")
                        if insert:
                            mod.keyframe_insert(data_path=prop_name)
                        else:
                            mod.keyframe_delete(data_path=prop_name)                            
                    else:
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

    def set_mapping_value(self,mapping, rvalue):
        
        ob = mapping.object_target
        if mapping.mapping_type == "location":
            if ob and ob.type != 'ARMATURE' or mapping.sub_data_path == "" :
                ob.location[self.axis_map[mapping.axis]] = rvalue
            else:
                ob.pose.bones[mapping.sub_data_path].location[self.axis_map[mapping.axis]] = rvalue
            return
        elif mapping.mapping_type == "rotation_euler":                        
            if ob and ob.type != 'ARMATURE' or mapping.sub_data_path == "":
                ob.rotation_mode = 'XYZ'
                ob.rotation_euler[self.axis_map[mapping.axis]] = rvalue
            else:  
                ob.pose.bones[mapping.sub_data_path].rotation_mode = 'XYZ'
                ob.pose.bones[mapping.sub_data_path].rotation_euler[self.axis_map[mapping.axis]] = rvalue
            return
        elif mapping.mapping_type == "scale":                        
            if ob and ob.type != 'ARMATURE' or mapping.sub_data_path == "":
                ob.scale[self.axis_map[mapping.axis]] = rvalue
            else:                            
                ob.pose.bones[mapping.sub_data_path].scale[self.axis_map[mapping.axis]] = rvalue
            return
        elif mapping.mapping_type == "shape_key":
            if ob and ob.data.shape_keys:
                if ob.data.shape_keys.key_blocks.get(mapping.data_path):
                    ob.data.shape_keys.key_blocks[mapping.data_path].value = rvalue
                return
        elif mapping.mapping_type == "modifier":
            if ob and ob.modifiers:
                mod = ob.modifiers.get(mapping.data_path)
                if mod and mapping.sub_data_path:    
                                                
                    if "[" in mapping.sub_data_path and mapping.sub_data_path.endswith("]"):
                        prop_name, idx = mapping.sub_data_path[:-1].split("[")
                        idx = int(idx)
                        arr = getattr(mod, prop_name, None)
                        if arr is not None and hasattr(arr, "__getitem__"):
                            arr[idx] = rvalue
                    else:
                        prop = mod.bl_rna.properties.get(mapping.sub_data_path)
                        if prop is None:
                            return
                        if prop.type == 'INT':
                            rvalue = int(rvalue)
                        elif prop.type == 'BOOL':
                            rvalue = bool(rvalue)
                        setattr(mod, mapping.sub_data_path, rvalue)                            
                        return


    def get_mapping_value(self,mapping):
        ob = mapping.object_target
        if mapping.mapping_type == "location":
            if ob and ob.type != 'ARMATURE' or mapping.sub_data_path == "" :
                return ob.location[self.axis_map[mapping.axis]]
            else:
                return ob.pose.bones[mapping.sub_data_path].location[self.axis_map[mapping.axis]]
            return
        elif mapping.mapping_type == "rotation_euler":                        
            if ob and ob.type != 'ARMATURE' or mapping.sub_data_path == "":                
                return ob.rotation_euler[self.axis_map[mapping.axis]]
            else: 
                return ob.pose.bones[mapping.sub_data_path].rotation_euler[self.axis_map[mapping.axis]]
            return
        elif mapping.mapping_type == "scale":                        
            if ob and ob.type != 'ARMATURE' or mapping.sub_data_path == "":
                return ob.scale[self.axis_map[mapping.axis]] 
            else:                            
                return ob.pose.bones[mapping.sub_data_path].scale[self.axis_map[mapping.axis]]
            return
        elif mapping.mapping_type == "shape_key":
            if ob and ob.data.shape_keys:
                if ob.data.shape_keys.key_blocks.get(mapping.data_path):
                    return ob.data.shape_keys.key_blocks[mapping.data_path].value
                return
        elif mapping.mapping_type == "modifier":
            if ob and ob.modifiers:
                mod = ob.modifiers.get(mapping.data_path)
                if mod and mapping.sub_data_path:                                                    
                    if "[" in mapping.sub_data_path and mapping.sub_data_path.endswith("]"):
                        prop_name, idx = mapping.sub_data_path[:-1].split("[")
                        idx = int(idx)
                        arr = getattr(mod, prop_name, None)
                        if arr is not None and hasattr(arr, "__getitem__"):
                            return arr[idx]
                    else:
                        prop = mod.bl_rna.properties.get(mapping.sub_data_path)
                        rvalue = getattr(mod, mapping.sub_data_path)                                                
                        if prop is None:
                            return
                        if prop.type == 'INT':
                            return int(rvalue)
                        elif prop.type == 'BOOL':
                            return bool(rvalue)
        return




    def modal(self, context, event):
        if not hasattr(self, "previous_button_list"):
            self.previous_button_list = {}

        scene = context.scene
        settings = scene.johnnygizmo_puppetstrings_settings
        settings.controller_running = fastgamepad.initialized()
        if not settings.controller_running:
            self.report({'WARNING'}, "Controller not running")
            self.cancel(context)
            return {"CANCELLED"}

        if event.type == "TIMER":
            buttons_list = [4,5,6]
            if len(scene.johnnygizmo_puppetstrings_mapping_sets) == 0:
                self.report({'WARNING'}, "No mapping sets found")
                self.cancel(context)
                return {"CANCELLED"}               

            m = scene.johnnygizmo_puppetstrings_mapping_sets[scene.johnnygizmo_puppetstrings_active_mapping_set]
            if len(m.button_mappings) == 0:
                self.report({'WARNING'}, "No mappings defined in set")
                self.cancel(context)
                return {"CANCELLED"}  
                       
            for mapping in m.button_mappings:
                bmd = next((b for b in mapping_data.BUTTON_DATA if b[1] == mapping.button), None)
                if bmd[0] not in buttons_list:                    
                    buttons_list.append(bmd[0])

            self.previous_button_list = self.current_button_list.copy()
            self.current_button_list = fastgamepad.get_button_list(buttons_list)
            active_mapping_set = self.get_active_mapping_set(context)
            
            # Handle Start/Stop
            self.playback_controls(context, self.current_button_list, self.previous_button_list)

            if settings.mute_controller:
                return {"PASS_THROUGH"}       

            if active_mapping_set and active_mapping_set.active :
                for mapping in active_mapping_set.button_mappings:
                    # if not mapping.enabled or mapping.object == "":
                    #     continue
                    if not mapping.enabled or not mapping.object_target:
                        continue

                    ob = mapping.object_target
                    if not ob:
                        continue
                    if ob and ob.type == 'ARMATURE' and mapping.mapping_type == "shape_key":
                        continue

                    raw_value = self.current_button_list.get(mapping.button)
                    raw_value = raw_value * mapping.scaling
                    raw_value = round(raw_value, mapping.rounding)

                    if mapping.use_input_clipping:
                        raw_value = max(mapping.input_clip_min, min(mapping.input_clip_max, raw_value))

                    value = raw_value
                    value = easing(value, mapping.input_easing)  

                    scale = 1.0
                    rvalue = raw_value

                    if mapping.assignment == "add":
                        scale = 1 / scene.render.fps                        
                    elif mapping.assignment == "subtract":
                        scale = 1 / scene.render.fps
                    elif mapping.assignment == "multiply":
                        scale = 1 / scene.render.fps

                    if mapping.operation == "curve":
                        mapped = mapping.curve_owner.curve.evaluate(mapping.curve_owner.curve.curves[0],value)
                        rvalue = round(mapped*scale,6)
                    elif mapping.operation == "expression":
                        rvalue = mapping.expression
                    elif mapping.operation == "invertb":                        
                        rvalue = 1 - value
                    elif mapping.operation == "inverta":                        
                        rvalue = -value

                    
                    if mapping.rounding == 0:
                        rvalue = int(rvalue)                    
                    
                    
                    if mapping.assignment == "add":
                        rvalue = self.get_mapping_value(mapping) + rvalue
                    elif mapping.assignment == "subtract":
                        rvalue = self.get_mapping_value(mapping) - rvalue
                    elif mapping.assignment == "multiply":
                        rvalue = self.get_mapping_value(mapping) * rvalue
                    
                    if mapping.use_clipping:
                            rvalue = max(mapping.clip_min, min(mapping.clip_max,rvalue))

                    self.set_mapping_value(mapping,rvalue)                                          
                   

                    # HANDLE KEYFRAMES
                    if ob.type=="ARMATURE" and mapping.sub_data_path != "":
                        ob = ob.pose.bones[mapping.sub_data_path]

                    keyframe_rate = settings.keyframe_interval
                    if mapping.keyframe_rate_override > 0:
                        keyframe_rate = mapping.keyframe_rate_override

                    #keyframe_rate = context.scene.johnnygizmo_puppetstrings_settings.keyframe_interval  
                    if settings.enable_record and context.screen.is_animation_playing and not context.screen.is_scrubbing:
                        try:
                            if (context.scene.frame_current % keyframe_rate) == 0:  # or first:
                                self.modify_keyframe(context, mapping, ob, True)
                            else:
                                self.modify_keyframe(context, mapping, ob, False)
                        except:
                            pass          
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

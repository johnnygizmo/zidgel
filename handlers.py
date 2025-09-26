import bpy
from . import fastgamepad
from . import rumble

def post_playback_handler(scene,depsgrap):
    if len(scene.johnnygizmo_puppetstrings_mapping_sets) == 0:
        return
    if len(scene.johnnygizmo_puppetstrings_mapping_sets[scene.johnnygizmo_puppetstrings_active_mapping_set].button_mappings) == 0:
        return
    settings = scene.johnnygizmo_puppetstrings_settings 
    mapping_sets = scene.johnnygizmo_puppetstrings_mapping_sets
    active_mapping_set = mapping_sets[scene.johnnygizmo_puppetstrings_active_mapping_set]

    fastgamepad.set_led(0,0,0)
    if active_mapping_set.active == True:
        for mapping in active_mapping_set.button_mappings:
            if not mapping.enabled or not mapping.object_target:
                continue
            curve = getCurve(mapping,settings)
            if curve: 
                curve.mute = False

    if settings.auto_simplify == "rec" and (settings.use_punch or settings.enable_record):
        scene.render.use_simplify = False
    elif settings.auto_simplify == "play":
        scene.render.use_simplify = False 


def channel_mute_toggle(mapping,settings):
    curve = getCurve(mapping,settings)
    if settings.mute_controller:
        curve.mute = False
    elif settings.enable_record or settings.use_punch:         
        if curve: 
            curve.mute = True 
    else:
        if curve: 
            curve.mute = False 


def pre_playback_handler(scene,depsgrap):
    if len(scene.johnnygizmo_puppetstrings_mapping_sets) == 0:
        return
    if len(scene.johnnygizmo_puppetstrings_mapping_sets[scene.johnnygizmo_puppetstrings_active_mapping_set].button_mappings) == 0:
        return
    for m in scene.johnnygizmo_puppetstrings_mapping_sets[scene.johnnygizmo_puppetstrings_active_mapping_set].button_mappings:
        m.is_last_value_captured = False
    settings = scene.johnnygizmo_puppetstrings_settings 
    mapping_sets = scene.johnnygizmo_puppetstrings_mapping_sets
    active_mapping_set = mapping_sets[scene.johnnygizmo_puppetstrings_active_mapping_set]

    if settings.auto_simplify == "rec" and (settings.use_punch or settings.enable_record):
        scene.render.use_simplify = True
    elif settings.auto_simplify == "play":
        scene.render.use_simplify = True 



    if active_mapping_set.active == True:        
        for mapping in active_mapping_set.button_mappings:
            if not mapping.enabled or not mapping.object_target:
                continue   
            # curve = getCurve(mapping,settings)
            # if settings.enable_record or settings.use_punch:         
            #     if curve: 
            #         curve.mute = True 
            # else:
            #     if curve: 
            #         curve.mute = False 


    if settings.enable_record:
        #rumble.rumble_async(0xFFFF,0xFFFF,250)
        fastgamepad.set_led(255,0,0)
        bpy.ops.ed.undo_push()
    else:
        fastgamepad.set_led(0,255,0)

def getCurve(mapping,settings):
    axis_map = {
        "x":0,
        "y":1,
        "z":2
    }
    
    ob = mapping.object_target
    if mapping.mapping_type in [ "location" , "rotation_euler","scale"]:
        if(not ob or not ob.animation_data):
            return None
        action = ob.animation_data.action
        for layer in action.layers:                            
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for curve in cb.fcurves:   
                        if ob.type != 'ARMATURE' or mapping.sub_data_path == "":                                     
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

    for m in scene.johnnygizmo_puppetstrings_mapping_sets[scene.johnnygizmo_puppetstrings_active_mapping_set].button_mappings:
        channel_mute_toggle(m ,settings)    



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
        for m in scene.johnnygizmo_puppetstrings_mapping_sets[scene.johnnygizmo_puppetstrings_active_mapping_set].button_mappings:
            m.is_last_value_captured = False

        settings.enable_record = True 
        bpy.ops.ed.undo_push()
        #rumble.rumble_async(0xFFFF,0xFFFF,250)
        fastgamepad.set_led(255,0,0)
        
    if scene.frame_current == punch_out_frame and settings.enable_record and settings.use_punch:
        settings.enable_record = False
        #rumble.rumble_async(0xFFFF,0xFFFF,250)
        fastgamepad.set_led(0,255,0)

    if settings.use_punch and scene.frame_current > punch_out_frame + pre_roll:
        bpy.ops.puppetstrings.playback(action="STOP")
 
    if scene.frame_current == scene.frame_end and settings.one_shot:
        bpy.ops.screen.animation_cancel() 


def load_file_handler(dummy):
    scene = bpy.context.scene
    settings = scene.johnnygizmo_puppetstrings_settings
    settings.controller_running = False
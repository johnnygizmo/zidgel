import bpy

from . import fastgamepad

class PuppetStrings_OT_PlayWithPunch(bpy.types.Operator):
    bl_idname = "puppetstrings.playback"
    bl_label = "Playback functions"
    bl_description = "Playback functions with punch in/out support"

    action: bpy.props.EnumProperty(
        name="Action",
        description="Action to perform",
        items=[
            ("PLAY", "Play", "Start playback"),
            ("STOP", "Stop", "Stop playback"),
        ],
        default="PLAY",
    )  # type: ignore

    def execute(self, context):
        scene = context.scene
        screen = context.screen
        settings = scene.johnnygizmo_puppetstrings_settings

        if self.action == "PLAY":
            if fastgamepad.initialized():
                fastgamepad.set_smoothing(settings.smoothing)
                fastgamepad.set_debounce(settings.debounce_time)

            if screen.is_animation_playing:
                return {'CANCELLED'}
        
            if getattr(settings, "use_punch", False):
                punch_in = scene.frame_start
                punch_in_marker = getattr(settings, "punch_in_marker","")
                if punch_in_marker != "":                
                    punch_in_marker = scene.timeline_markers.get(punch_in_marker, None)
                    if punch_in_marker:
                        punch_in = punch_in_marker.frame                      
                    
                preroll = getattr(settings, "pre_roll", 0)
                start_frame = scene.frame_start
                if punch_in_marker:
                    start_frame = max(1, punch_in - preroll)
                if preroll > 0:
                    settings.enable_record = False
                else: 
                    settings.enable_record = True
                
                #print(f"Starting playback at frame {start_frame} (punch-in {punch_in} minus preroll {preroll})")
                scene.frame_current = start_frame
 
            bpy.ops.screen.animation_play()
            return {'FINISHED'}
        elif self.action == "STOP":
            if not screen.is_animation_playing:
                return {'CANCELLED'}
            bpy.ops.screen.animation_cancel()            
            return {'FINISHED'}
        else :
            #print("Unknown action")
            return {'CANCELLED'}

def register():
    bpy.utils.register_class(PuppetStrings_OT_PlayWithPunch)

def unregister():
    bpy.utils.unregister_class(PuppetStrings_OT_PlayWithPunch)
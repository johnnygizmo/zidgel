import bpy

class FG_OT_PlayWithPunch(bpy.types.Operator):
    bl_idname = "fg.play_with_punch"
    bl_label = "Play With Punch"
    bl_description = "Start playback at punch-in minus preroll if enabled"

    def execute(self, context):
        scene = context.scene
        settings = scene.johnnygizmo_puppetstrings_settings

        if getattr(settings, "use_punch", False):
            punch_in = getattr(settings, "punch_in", scene.frame_start)
            preroll = getattr(settings, "pre_roll", 0)
            start_frame = max(1, punch_in - preroll)
            if preroll > 0:
                settings.enable_record = False
            else: 
                settings.enable_record = True
            
            print(f"Starting playback at frame {start_frame} (punch-in {punch_in} minus preroll {preroll})")
            scene.frame_current = start_frame
 
        bpy.ops.screen.animation_play()
        return {'FINISHED'}

def register():
    bpy.utils.register_class(FG_OT_PlayWithPunch)

def unregister():
    bpy.utils.unregister_class(FG_OT_PlayWithPunch)
import bpy
from . import fastgamepad

class FG_PT_MappingSetsPanel(bpy.types.Panel):
    bl_label = "Mapping Sets"
    bl_idname = "FG_PT_mapping_sets"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Gamepad"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings  = scene.johnnygizmo_puppetstrings_settings
        
        
        if not fastgamepad.initialized():
            layout.operator("fg.start_controller", text="Enable Controller", icon="STRIP_COLOR_01").action = "START"
        else:
            layout.operator("fg.start_controller", text="Controller Running (esc to stop)", icon="STRIP_COLOR_04").action = "STOP"


        if context.screen.is_animation_playing:
            if settings.enable_record:
                layout.prop(settings, "enable_record",text="Recording", icon="RECORD_ON")
            elif settings.use_punch and not settings.enable_record:
                layout.prop(settings, "enable_record",text="Punched Out", icon="RECORD_OFF")
            elif not settings.use_punch and not settings.enable_record:
                layout.prop(settings, "enable_record",text="Playing", icon="NODE_SOCKET_SHADER")
        else:
            if settings.enable_record and not settings.use_punch:
                layout.prop(settings, "enable_record",text="Recording Armed", icon="RECORD_ON")
            elif settings.use_punch:
                layout.prop(settings, "enable_record",text="Recording Armed (punch armed)", icon="RECORD_ON")
            else:
                 layout.prop(settings, "enable_record",text="Recording Disarmed", icon="RECORD_OFF")


        # Timeline marker dropdowns for punch in/out
        row = layout.row()
        if settings.use_punch:
            row.prop(context.scene.johnnygizmo_puppetstrings_settings, "use_punch", text="", icon="RECORD_ON")
        else:
            row.prop(context.scene.johnnygizmo_puppetstrings_settings, "use_punch", text="",icon="RECORD_OFF")

        row.prop_search(context.scene.johnnygizmo_puppetstrings_settings, "punch_in_marker", context.scene, "timeline_markers", text="In", icon='IMPORT')
        row.prop_search(context.scene.johnnygizmo_puppetstrings_settings, "punch_out_marker", context.scene, "timeline_markers", text="Out", icon='EXPORT')

        row.prop(context.scene.johnnygizmo_puppetstrings_settings, "pre_roll")
        # row.prop(context.scene.johnnygizmo_puppetstrings_settings, "punch_in")
        # row.prop(context.scene.johnnygizmo_puppetstrings_settings, "punch_out")

        row = layout.row()
        row.prop(context.scene.johnnygizmo_puppetstrings_settings, "one_shot", text="Prevent Looping Animation")
        
        row = layout.row()
        row.operator("puppetstrings.playback", text="Play", icon="PLAY").action = "PLAY"

        row = layout.row()
        row.prop(context.scene.johnnygizmo_puppetstrings_settings, "controller_fps")
        row.prop(context.scene.johnnygizmo_puppetstrings_settings, "keyframe_interval")
        row = layout.row()
        row.prop(context.scene.johnnygizmo_puppetstrings_settings, "smoothing")
        row.prop(context.scene.johnnygizmo_puppetstrings_settings, "debounce_time")
        layout.label(text="Select Mapping Set:")
        row = layout.row()
        row.template_list(
            "FG_UL_MappingSetList", "", 
            scene, "johnnygizmo_puppetstrings_mapping_sets", 
            scene, "johnnygizmo_puppetstrings_active_mapping_set"
        )
        col = row.column(align=True)
        col.operator("fg.add_mapping_set", icon='ADD', text="")
        col.operator("fg.remove_mapping_set", icon='REMOVE', text="")

class FG_PT_ButtonMappingsPanel(bpy.types.Panel):
    bl_label = "Button Mappings"
    bl_idname = "FG_PT_button_mappings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Gamepad"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        if len(scene.johnnygizmo_puppetstrings_mapping_sets) == 0:
            layout.label(text="No mapping sets defined.")
            return
        ms = scene.johnnygizmo_puppetstrings_mapping_sets[scene.johnnygizmo_puppetstrings_active_mapping_set]
        layout.label(text=f"Mappings for: {ms.name}")
        row = layout.row()
        row.template_list(
            "FG_UL_ButtonMappingList", "",
            ms, "button_mappings",
            ms, "active_button_mapping_index"
        )
        col = row.column(align=True)
        col.operator("fg.add_button_mapping", icon='ADD', text="")
        col.operator("fg.remove_button_mapping", icon='REMOVE', text="")        
        col = row.column(align=True)
       

class PUPPETSTRINGS_PT_buttons(bpy.types.Panel):
    bl_label = "Puppet Strings Buttons"
    bl_idname = "PUPPETSTRINGS_PT_buttons"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Gamepad"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        col = layout.column()
        for item in scene.johnnygizmo_puppetstrings_buttons_settings:
            box = col.box()
            row = box.row()
            row.label(text=item.full_name or item.name)
            box.prop(item, "smooth")
            box.prop(item, "debounce")
   

class FG_UL_MappingSetList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        ms = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if ms.active:
                layout.prop(ms, "active", text="", icon="CHECKBOX_HLT")
            else:
                layout.prop(ms, "active", text="", icon="CHECKBOX_DEHLT")

            layout.prop(ms, "name", text="", emboss=False)
            
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text=ms.name)

class FG_UL_ButtonMappingList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        bm = item
                
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            col = layout.column()
            row = col.row(align=True)
           
            if bm.enabled:
                row.prop(bm, "enabled", text="", icon="CHECKBOX_HLT")
            else:
                row.prop(bm, "enabled", text="", icon="CHECKBOX_DEHLT")
            if bm.show_panel:
                row.prop(bm, "show_panel", text="", icon="HIDE_OFF")
            else:
                row.prop(bm, "show_panel", text="", icon="HIDE_ON")
            row.prop(bm, "button", text="")
            #layout.prop(bm, "invert", icon="ARROW_LEFTRIGHT", text="")

            #layout.prop(bm, "scale", text="")
            row.prop_search(bm, "object", bpy.data, "objects", text="")
            
            ob = bpy.data.objects.get(bm.object)
            if ob and ob.type == "ARMATURE":
                row.prop_search(
                bm,
                "sub_data_path",
                ob.pose,
                "bones",
                text=""
            )
            
            if bm.show_panel:
            
                row = col.row(align=True)
                row.separator(factor=3)
                row.prop(bm, "mapping_type", text="")
                
                if bm.mapping_type in ("location", "rotation_euler", "scale")  :
                    row.prop(bm, "axis", text="")
                elif bm.mapping_type == "shape_key":
                    ob = bpy.data.objects.get(bm.object)
                    #layout.template_path_builder(bm, "data_path", root=ob, text="")
                    if ob and ob.type == 'MESH' and ob.data.shape_keys:
                        row.prop_search(bm, "data_path", text="", search_data=ob.data.shape_keys, search_property="key_blocks")
                    else:
                        row.prop(bm, "data_path", text="")
                elif bm.mapping_type == "modifier":
                    ob = bpy.data.objects.get(bm.object)
                    if ob:
                        row.prop_search(bm, "data_path", text="", search_data=ob, search_property="modifiers")
                        mod = ob.modifiers.get(bm.data_path)
                        if mod:
                            row.prop(bm, "sub_data_path", text="")
                else:
                    row.prop(bm, "data_path", text="")
                row = col.row(align=True)
                row.separator(factor=3)

                row.prop(bm, "operation", text="Operation", emboss=True)
                row.prop(bm, "input_easing", text="Easing")
                if bm.operation == "expression":
                    row.prop(bm, "expression", text="Expression", emboss=True)
                
                if bm.operation == "curve":
                    row = col.row(align=True)
                    col = row.column()
                    box = col.box()
                    box.template_curve_mapping(bm.curve_owner,"curve")
                row = col.row(align=True)
                # row.prop(bm,"smoothing_ms")
                # row.prop(bm,"debounce_ms")
                
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text=bm.name)

class FG_OT_AddMappingSet(bpy.types.Operator):

    bl_idname = "fg.add_mapping_set"
    bl_label = "Add Mapping Set"
    def execute(self, context):
        context.scene.johnnygizmo_puppetstrings_mapping_sets.add()
        return {'FINISHED'}

class FG_OT_RemoveMappingSet(bpy.types.Operator):
    bl_idname = "fg.remove_mapping_set"
    bl_label = "Remove Mapping Set"
    def execute(self, context):
        idx = context.scene.johnnygizmo_puppetstrings_active_mapping_set
        sets = context.scene.johnnygizmo_puppetstrings_mapping_sets
        if sets and 0 <= idx < len(sets):
            sets.remove(idx)
            context.scene.johnnygizmo_puppetstrings_active_mapping_set = max(0, idx-1)
        return {'FINISHED'}

class FG_OT_AddButtonMapping(bpy.types.Operator):
    bl_idname = "fg.add_button_mapping"
    bl_label = "Add Button Mapping"
    def execute(self, context):
        ms = context.scene.johnnygizmo_puppetstrings_mapping_sets[context.scene.johnnygizmo_puppetstrings_active_mapping_set]
        mapping = ms.button_mappings.add()
        if not mapping.curve_owner:
            brush = bpy.data.brushes.new("ButtonMappingCurve", mode='TEXTURE_PAINT')
            brush.curve_preset = 'SMOOTH'
            brush.curve.clip_min_x = -1
            brush.curve.clip_max_x = 1
            brush.curve.reset_view()
            mapping.curve_owner = brush
        return {'FINISHED'}

class FG_OT_RemoveButtonMapping(bpy.types.Operator):
    bl_idname = "fg.remove_button_mapping"
    bl_label = "Remove Button Mapping"
    def execute(self, context):
        ms = context.scene.johnnygizmo_puppetstrings_mapping_sets[context.scene.johnnygizmo_puppetstrings_active_mapping_set]
        idx = ms.active_button_mapping_index
        if ms.button_mappings and 0 <= idx < len(ms.button_mappings):
            ms.button_mappings.remove(idx)
            ms.active_button_mapping_index = max(0, idx-1)
        return {'FINISHED'}


def register():
    #bpy.utils.register_class(PUPPETSTRINGS_PT_buttons)
    bpy.utils.register_class(FG_UL_MappingSetList)
    bpy.utils.register_class(FG_UL_ButtonMappingList)
    bpy.utils.register_class(FG_PT_MappingSetsPanel)
    bpy.utils.register_class(FG_PT_ButtonMappingsPanel)
    bpy.utils.register_class(FG_OT_AddMappingSet)
    bpy.utils.register_class(FG_OT_RemoveMappingSet)
    bpy.utils.register_class(FG_OT_AddButtonMapping)
    bpy.utils.register_class(FG_OT_RemoveButtonMapping)
   
def unregister():
    bpy.utils.unregister_class(FG_OT_RemoveButtonMapping)
    bpy.utils.unregister_class(FG_OT_AddButtonMapping)
    bpy.utils.unregister_class(FG_OT_RemoveMappingSet)
    bpy.utils.unregister_class(FG_OT_AddMappingSet)
    bpy.utils.unregister_class(FG_PT_ButtonMappingsPanel)
    bpy.utils.unregister_class(FG_PT_MappingSetsPanel)
    bpy.utils.unregister_class(FG_UL_ButtonMappingList)
    bpy.utils.unregister_class(FG_UL_MappingSetList)
    #bpy.utils.unregister_class(PUPPETSTRINGS_PT_buttons)


import bpy

class FG_PT_MappingSetsPanel(bpy.types.Panel):
    bl_label = "Mapping Sets"
    bl_idname = "FG_PT_mapping_sets"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Gamepad"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.operator("fg.start_controller", text="Start Controller", icon="PLAY")
       
        if scene.controller_running:
            layout.label(text="Controller Running: Press ESC to cancel", icon="CANCEL")
       
        layout.label(text="Select Mapping Set:")
        row = layout.row()
        row.template_list(
            "FG_UL_MappingSetList", "", 
            scene, "mapping_sets", 
            scene, "active_mapping_set"
        )
        col = row.column(align=True)
        col.operator("fg.add_mapping_set", icon='ADD', text="")
        col.operator("fg.remove_mapping_set", icon='REMOVE', text="")
        
        layout.prop(context.scene, "controller_fps")
        layout.prop(context.scene, "keyframe_interval")

class FG_PT_ButtonMappingsPanel(bpy.types.Panel):
    bl_label = "Button Mappings"
    bl_idname = "FG_PT_button_mappings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Gamepad"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        if len(scene.mapping_sets) == 0:
            layout.label(text="No mapping sets defined.")
            return
        ms = scene.mapping_sets[scene.active_mapping_set]
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

            row.prop(bm, "button", text="")
            #layout.prop(bm, "invert", icon="ARROW_LEFTRIGHT", text="")

            #layout.prop(bm, "scale", text="")
            row.prop(bm, "object", text="")
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
            else:
                row.prop(bm, "data_path", text="")
            row = col.row(align=True)
            row.separator(factor=3)

            row.prop(bm, "operation", text="Operation", emboss=True)
            if bm.operation == "expression":
                row.prop(bm, "expression", text="Expression", emboss=True)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text=bm.name)

class FG_OT_AddMappingSet(bpy.types.Operator):

    bl_idname = "fg.add_mapping_set"
    bl_label = "Add Mapping Set"
    def execute(self, context):
        context.scene.mapping_sets.add()
        return {'FINISHED'}

class FG_OT_RemoveMappingSet(bpy.types.Operator):
    bl_idname = "fg.remove_mapping_set"
    bl_label = "Remove Mapping Set"
    def execute(self, context):
        idx = context.scene.active_mapping_set
        sets = context.scene.mapping_sets
        if sets and 0 <= idx < len(sets):
            sets.remove(idx)
            context.scene.active_mapping_set = max(0, idx-1)
        return {'FINISHED'}

class FG_OT_AddButtonMapping(bpy.types.Operator):
    bl_idname = "fg.add_button_mapping"
    bl_label = "Add Button Mapping"
    def execute(self, context):
        ms = context.scene.mapping_sets[context.scene.active_mapping_set]
        ms.button_mappings.add()
        return {'FINISHED'}

class FG_OT_RemoveButtonMapping(bpy.types.Operator):
    bl_idname = "fg.remove_button_mapping"
    bl_label = "Remove Button Mapping"
    def execute(self, context):
        ms = context.scene.mapping_sets[context.scene.active_mapping_set]
        idx = ms.active_button_mapping_index
        if ms.button_mappings and 0 <= idx < len(ms.button_mappings):
            ms.button_mappings.remove(idx)
            ms.active_button_mapping_index = max(0, idx-1)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(FG_UL_MappingSetList)
    bpy.utils.register_class(FG_UL_ButtonMappingList)
    bpy.utils.register_class(FG_PT_MappingSetsPanel)
    bpy.utils.register_class(FG_PT_ButtonMappingsPanel)
    bpy.utils.register_class(FG_OT_AddMappingSet)
    bpy.utils.register_class(FG_OT_RemoveMappingSet)
    bpy.utils.register_class(FG_OT_AddButtonMapping)
    bpy.utils.register_class(FG_OT_RemoveButtonMapping)
    bpy.types.Scene.controller_running = bpy.props.BoolProperty(name="Controller Running", default=False)

def unregister():
    bpy.utils.unregister_class(FG_PT_ButtonMappingsPanel)
    bpy.utils.unregister_class(FG_PT_MappingSetsPanel)
    bpy.utils.unregister_class(FG_UL_ButtonMappingList)
    bpy.utils.unregister_class(FG_UL_MappingSetList)
    bpy.utils.unregister_class(FG_OT_AddMappingSet)
    bpy.utils.unregister_class(FG_OT_RemoveMappingSet)
    bpy.utils.unregister_class(FG_OT_AddButtonMapping)
    bpy.utils.unregister_class(FG_OT_RemoveButtonMapping)


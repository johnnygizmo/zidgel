import bpy
import json
from . import mapping_data

class EXPORT_OT_mapping_set(bpy.types.Operator):
    bl_idname = "mapping.export_set"
    bl_label = "Export Mapping Set"
    filename_ext = ".json"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.json")

    def execute(self, context):
        scene = context.scene
        sets = scene.johnnygizmo_puppetstrings_mapping_sets
        idx = scene.johnnygizmo_puppetstrings_active_mapping_set
        if idx >= len(sets):
            self.report({'ERROR'}, "No active mapping set")
            return {'CANCELLED'}
        mapping_set = sets[idx]
        data = {
            "name": mapping_set.name,
            "active": mapping_set.active,
            "button_mappings": []
        }
        for bm in mapping_set.button_mappings:
            bm_data = {}
            for k in bm.__annotations__.keys():
                v = getattr(bm, k)
                if k == "curve_owner":
                    curve_data = None
                    if bm.curve_owner and bm.curve_owner.curve:
                        curve = bm.curve_owner.curve
                        # Export all points for the first curve (usually only one)
                        points = []
                        for pt in curve.curves[0].points:
                            points.append({"x": pt.location[0], "y": pt.location[1],"handle":pt.handle_type})
                        curve_data = {
                            "clip_min_x": curve.clip_min_x,
                            "clip_max_x": curve.clip_max_x,
                            "clip_min_y": curve.clip_min_y,
                            "clip_max_y": curve.clip_max_y,
                            "points": points,
                        }
                    bm_data["curve_data"] = curve_data
                    
                elif hasattr(v, "name"):
                    bm_data[k] = v.name
                else:
                    try:
                        json.dumps(v)  # Test if serializable
                        bm_data[k] = v
                    except TypeError:
                        pass  # Skip non-serializable fields
            data["button_mappings"].append(bm_data)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self.report({'INFO'}, f"Mapping set exported to {self.filepath}")
        return {'FINISHED'}

    def invoke(self, context, event):
        scene = context.scene
        sets = scene.johnnygizmo_puppetstrings_mapping_sets
        idx = scene.johnnygizmo_puppetstrings_active_mapping_set
        if idx < len(sets):
            group_name = sets[idx].name
            # Sanitize filename (remove/replace illegal characters if needed)
            safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in group_name)
            self.filepath = safe_name + ".json"
        else:
            self.filepath = "mapping_set.json"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    

class IMPORT_OT_mapping_set(bpy.types.Operator):
    bl_idname = "mapping.import_set"
    bl_label = "Import Mapping Set"
    filename_ext = ".json"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH",default="")
    filter_glob: bpy.props.StringProperty(default="*.json")

    def execute(self, context):
        scene = context.scene
        sets = scene.johnnygizmo_puppetstrings_mapping_sets
        with open(self.filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        new_set = sets.add()
        new_set.name = data.get("name", "Imported Mapping Set")
        new_set.active = data.get("active", False)
        for bm_data in data.get("button_mappings", []):
            bm = new_set.button_mappings.add()
            for k, v in bm_data.items():
                if k == "object_target":
                    bm.object_target = bpy.data.objects.get(v, None)

                elif k == "curve_data":
                    curve_data = bm_data.get("curve_data")
                    if curve_data:
                        # Create a new brush for this mapping
                        brush = bpy.data.brushes.new(name="ImportedCurve", mode='TEXTURE_PAINT')
                        curve = brush.curve                        
                        curve.clip_min_x = curve_data.get("clip_min_x", -1)
                        curve.clip_max_x = curve_data.get("clip_max_x", 1)
                        curve.clip_min_y = curve_data.get("clip_min_y", -1)
                        curve.clip_max_y = curve_data.get("clip_max_y", 1)
                        # Remove existing points except the first two (Blender always creates 2 by default)
                        points = curve.curves[0].points
                        while len(points) > 2:
                            points.remove(points[2])
                        # Add points from saved data
                        i = len(curve_data["points"])-2
                        for j in range(i):
                            points.new(.5, .5)
                        for j in range(len(curve_data["points"])):

                            pt = curve_data["points"][j]
                            points[j].location = (pt["x"], pt["y"])
                            points[j].handle_type = pt["handle"]
                                                   
                        bm.curve_owner = brush
                        bm.curve_owner.curve.reset_view()
                        bm.curve_owner.curve.update()
                    else:
                        brush = bpy.data.brushes.new(name="ImportedCurve", mode='TEXTURE_PAINT')
                        bm.curve_owner = brush
                elif hasattr(bm, k):
                    setattr(bm, k, v)
                    
        scene.johnnygizmo_puppetstrings_active_mapping_set = len(sets) - 1
        self.report({'INFO'}, f"Mapping set imported from {self.filepath}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}    
    

class DUPLICATE_OT_mapping_set(bpy.types.Operator):
    bl_idname = "mapping.duplicate_set"
    bl_label = "Duplicate Mapping Set"

    def execute(self, context):
        scene = context.scene
        sets = scene.johnnygizmo_puppetstrings_mapping_sets
        idx = scene.johnnygizmo_puppetstrings_active_mapping_set
        if idx >= len(sets):
            self.report({'ERROR'}, "No active mapping set to duplicate")
            return {'CANCELLED'}
        src_set = sets[idx]
        new_set = sets.add()
        new_set.name = src_set.name + " Copy"
        new_set.active = False
        # Copy all button mappings
        for src_bm in src_set.button_mappings:
            bm = new_set.button_mappings.add()
            for k in src_bm.__annotations__.keys():
                v = getattr(src_bm, k)
                if k == "object_target":
                    bm.object_target = v
                elif k == "curve_owner":
                    if src_bm.curve_owner and src_bm.curve_owner.curve:
                        brush = bpy.data.brushes.new(name="DuplicatedCurve", mode='TEXTURE_PAINT')
                        src_curve = src_bm.curve_owner.curve
                        dst_curve = brush.curve
                        dst_curve.clip_min_x = src_curve.clip_min_x
                        dst_curve.clip_max_x = src_curve.clip_max_x
                        dst_curve.clip_min_y = src_curve.clip_min_y
                        dst_curve.clip_max_y = src_curve.clip_max_y
                        # Remove extra points
                        points = dst_curve.curves[0].points
                        while len(points) > 2:
                            points.remove(points[2])
                        # Add points to match source
                        i = len(src_curve.curves[0].points) - 2
                        for j in range(i):
                            points.new(.5, .5)
                        for j, src_pt in enumerate(src_curve.curves[0].points):
                            points[j].location = src_pt.location
                            points[j].handle_type = src_pt.handle_type
                        bm.curve_owner = brush
                        bm.curve_owner.curve.reset_view()
                        bm.curve_owner.curve.update()
                    else:
                        bm.curve_owner = None
                else:
                    try:
                        setattr(bm, k, v)
                    except Exception:
                        pass
        scene.johnnygizmo_puppetstrings_active_mapping_set = len(sets) - 1
        self.report({'INFO'}, "Mapping set duplicated")
        return {'FINISHED'}

class DUPLICATE_OT_button_mapping(bpy.types.Operator):
    bl_idname = "mapping.duplicate_button_mapping"
    bl_label = "Duplicate Button Mapping"

    def execute(self, context):
        scene = context.scene
        sets = scene.johnnygizmo_puppetstrings_mapping_sets
        set_idx = scene.johnnygizmo_puppetstrings_active_mapping_set
        if set_idx >= len(sets):
            self.report({'ERROR'}, "No active mapping set")
            return {'CANCELLED'}
        mapping_set = sets[set_idx]
        bm_idx = mapping_set.active_button_mapping_index
        if bm_idx >= len(mapping_set.button_mappings):
            self.report({'ERROR'}, "No active button mapping to duplicate")
            return {'CANCELLED'}
        src_bm = mapping_set.button_mappings[bm_idx]
        bm = mapping_set.button_mappings.add()
        # Copy all properties
        for k in src_bm.__annotations__.keys():
            v = getattr(src_bm, k)
            if k == "object_target":
                bm.object_target = v
            elif k == "curve_owner":
                if src_bm.curve_owner and src_bm.curve_owner.curve:
                    brush = bpy.data.brushes.new(name="DuplicatedCurve", mode='TEXTURE_PAINT')
                    src_curve = src_bm.curve_owner.curve
                    dst_curve = brush.curve
                    dst_curve.clip_min_x = src_curve.clip_min_x
                    dst_curve.clip_max_x = src_curve.clip_max_x
                    dst_curve.clip_min_y = src_curve.clip_min_y
                    dst_curve.clip_max_y = src_curve.clip_max_y
                    points = dst_curve.curves[0].points
                    while len(points) > 2:
                        points.remove(points[2])
                    i = len(src_curve.curves[0].points) - 2
                    for j in range(i):
                        points.new(.5, .5)
                    for j, src_pt in enumerate(src_curve.curves[0].points):
                        points[j].location = src_pt.location
                        points[j].handle_type = src_pt.handle_type
                    bm.curve_owner = brush
                    bm.curve_owner.curve.reset_view()
                    bm.curve_owner.curve.update()
                else:
                    bm.curve_owner = None
            else:
                try:
                    setattr(bm, k, v)
                except Exception:
                    pass
        # Move the new mapping right after the original
        mapping_set.button_mappings.move(len(mapping_set.button_mappings)-1, bm_idx+1)
        mapping_set.active_button_mapping = bm_idx+1
        self.report({'INFO'}, "Button mapping duplicated")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(EXPORT_OT_mapping_set)
    bpy.utils.register_class(IMPORT_OT_mapping_set)
    bpy.utils.register_class(DUPLICATE_OT_mapping_set)
    bpy.utils.register_class(DUPLICATE_OT_button_mapping)


def unregister():
    bpy.utils.unregister_class(DUPLICATE_OT_button_mapping)
    bpy.utils.unregister_class(DUPLICATE_OT_mapping_set)
    bpy.utils.unregister_class(IMPORT_OT_mapping_set)
    bpy.utils.unregister_class(EXPORT_OT_mapping_set)

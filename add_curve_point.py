import bpy # type: ignore
import sys
from .mapping_data import ButtonMapping
from . import controller
class FG_OT_AddCurvePointFromCurrent(bpy.types.Operator):
    bl_idname = "fg.add_curve_point_from_current"
    bl_label = "Add Curve Point From Current"

    #mapping: bpy.props.PointerProperty(type=ButtonMapping) # type: ignore
    lidx: bpy.props.IntProperty(name='list index') # type: ignore
    midx: bpy.props.IntProperty(name='mapping index') # type: ignore

    def execute(self, context):

        scene = context.scene
        sets = scene.johnnygizmo_puppetstrings_mapping_sets
        mapping_set = sets[self.lidx]
        mapping = mapping_set.button_mappings[self.midx]

        y_value = controller.get_mapping_value(mapping)
        if y_value:
            if mapping.curve_owner and mapping.curve_owner.curve:
                curve = mapping.curve_owner.curve.curves[0]
                
                updated = False
                for p in curve.points:
                    if round(p.location.x,2) == round(mapping.curve_x_input,2):
                        p.location.y = y_value
                        updated = True
                if not updated:
                    curve.points.new(round(mapping.curve_x_input,2), y_value)

                minx = sys.float_info.max
                miny = sys.float_info.max
                maxx = sys.float_info.min
                maxy=  sys.float_info.min

                for p in curve.points:
                    if p.location.x > maxx:
                        maxx = p.location.x
                    if p.location.x < minx:
                        minx = p.location.x
                    if p.location.y > maxy:
                        maxy =p.location.y
                    if p.location.y < miny:
                        miny = p.location.y                
                mapping.curve_owner.curve.clip_min_x = minx
                mapping.curve_owner.curve.clip_max_x = maxx
                mapping.curve_owner.curve.clip_min_y = miny
                mapping.curve_owner.curve.clip_max_y = maxy

                mapping.curve_owner.curve.update()
                mapping.curve_owner.curve.reset_view()
               
            else:
                return {'CANCELLED'}
        return {'FINISHED'}

def register():
    bpy.utils.register_class(FG_OT_AddCurvePointFromCurrent)
    

def unregister():

    bpy.utils.unregister_class(FG_OT_AddCurvePointFromCurrent)
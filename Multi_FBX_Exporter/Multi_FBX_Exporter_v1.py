bl_info = {
    "name": "Multi Fbx Exporter",
    "author": "Lazy Onigiri / bTro (Updated from original by nekorushi)",
    "version": (1, 0, 4),
    "blender": (4, 5, 4),
    "location": "View3D > Sidebar > Lazy Onigiri",
    "description": "Export selected objects into separate FBX files using presets.",
    "warning": "",
    "category": "Import-Export",
}

import bpy
import os

ADDON_VERSION = ".".join(str(number) for number in bl_info["version"])
GITHUB_URL = "https://github.com/beetron/blender-addons"

def find_fbx_presets(self, context):
    items = [("NONE", "None (Default Settings)", "Do not apply any saved preset configuration")]
    preset_directories = bpy.utils.preset_paths("operator/export_scene.fbx/")
    
    registered_names = set()
    for folder in preset_directories:
        if not os.path.exists(folder):
            continue
        for filename in os.listdir(folder):
            if filename.endswith(".py"):
                preset_identifier = filename[:-3]
                if preset_identifier not in registered_names:
                    registered_names.add(preset_identifier)
                    absolute_path = os.path.join(folder, filename)
                    readable_label = preset_identifier.replace("_", " ").title()
                    items.append((absolute_path, readable_label, f"Apply the saved {readable_label} preset rules"))
    return items

class MultiFbxExporterProperties(bpy.types.PropertyGroup):
    export_path: bpy.props.StringProperty(
        name="Folder",
        description="Directory to export FBX files",
        default="",
        maxlen=1024,
        subtype='DIR_PATH'
    )
    
    export_preset: bpy.props.EnumProperty(
        name="Preset",
        description="Select FBX export preset rules to apply",
        items=find_fbx_presets
    )
    
    create_subfolders: bpy.props.BoolProperty(
        name="Create Subfolders",
        description="Export each object into its own named subfolder",
        default=False
    )

class WM_OT_RefreshFbxPresets(bpy.types.Operator):
    bl_idname = "wm.refresh_fbx_presets"
    bl_label = "Refresh Presets"
    bl_description = "Scan for available FBX export presets"

    def execute(self, context):
        return {'FINISHED'}

class OBJECT_OT_BatchFbxExport(bpy.types.Operator):
    bl_idname = "object.batch_fbx_export"
    bl_label = "Export Selected"
    bl_description = "Export all selected objects as individual FBX files"

    def execute(self, context):
        scene = context.scene
        props = scene.multi_fbx_exporter_props
        
        if not props.export_path:
            self.report({'ERROR'}, "Export path is not set.")
            return {'CANCELLED'}
            
        target_dir = bpy.path.abspath(props.export_path)
        if not os.path.exists(target_dir):
            self.report({'ERROR'}, f"Directory does not exist: {target_dir}")
            return {'CANCELLED'}

        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not selected_objects:
            self.report({'WARNING'}, "No mesh objects selected.")
            return {'CANCELLED'}

        # Parse preset rules if an option is active
        preset_arguments = {}
        if props.export_preset and props.export_preset != "NONE" and os.path.exists(props.export_preset):
            try:
                class PresetOperatorCapture:
                    def __init__(self):
                        self.captured_rules = {}
                    def __setattr__(self, key, val):
                        if key == "captured_rules":
                            super().__setattr__(key, val)
                        else:
                            self.captured_rules[key] = val

                class PresetContextCapture:
                    def __init__(self, capture_operator):
                        self.active_operator = capture_operator

                class PresetBpyCapture:
                    def __init__(self, capture_operator):
                        self.context = PresetContextCapture(capture_operator)

                capture_instance = PresetOperatorCapture()
                sandbox_environment = {
                    "bpy": PresetBpyCapture(capture_instance)
                }
                
                with open(props.export_preset, 'r') as preset_file:
                    exec(preset_file.read(), sandbox_environment)
                
                preset_arguments = capture_instance.captured_rules
            except Exception as error_exception:
                self.report({'WARNING'}, f"Could not read preset configuration: {str(error_exception)}")

        # Cache initial state
        active_object = context.view_layer.objects.active
        original_selection = context.selected_objects[:]

        for obj in selected_objects:
            # Clear current selection
            bpy.ops.object.select_all(action='DESELECT')
            
            # Select individual object and make it active
            obj.select_set(True)
            context.view_layer.objects.active = obj
            
            # Cache location to center pivot to world origin temporarily if needed
            # (Ensures game engines read the pivot point at center room scale coordinates)
            original_location = obj.location.copy()
            obj.location = (0, 0, 0)
            
            # Formulate destination pathways
            safe_name = bpy.path.clean_name(obj.name)
            if props.create_subfolders:
                object_folder = os.path.join(target_dir, safe_name)
                os.makedirs(object_folder, exist_ok=True)
                file_path = os.path.join(object_folder, f"{safe_name}.fbx")
            else:
                file_path = os.path.join(target_dir, f"{safe_name}.fbx")
            
            # Assemble core configurations required for batch splitting
            final_arguments = {
                "filepath": file_path,
                "use_selection": True,
                "object_types": {'MESH'}
            }
            
            # Inject preset configurations if available
            if preset_arguments:
                final_arguments.update(preset_arguments)
                
            # Enforce priority overrides to protect loop iteration processing
            final_arguments["filepath"] = file_path
            final_arguments["use_selection"] = True
            
            try:
                bpy.ops.export_scene.fbx(**final_arguments)
            except Exception as e:
                self.report({'ERROR'}, f"Failed to export {obj.name}: {str(e)}")
            finally:
                # Restore original placement
                obj.location = original_location

        # Restore original user selection context states
        bpy.ops.object.select_all(action='DESELECT')
        for obj in original_selection:
            obj.select_set(True)
        context.view_layer.objects.active = active_object

        self.report({'INFO'}, f"Successfully batch exported {len(selected_objects)} meshes.")
        return {'FINISHED'}

class VIEW3D_PT_MultiFbxExporterPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Lazy Onigiri'  
    bl_label = "Multi Fbx Exporter"

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.multi_fbx_exporter_props

        # Header titles custom text injection
        header_box = layout.box()
        column = header_box.column(align=True)
        column.label(text=f"Multi Fbx Exporter (v.{ADDON_VERSION})", icon='EXPORT')
        column.label(text="by Lazy Onigiri / bTro", icon='USER')
        header_box.operator("wm.url_open", text="GitHub", icon='URL').url = GITHUB_URL

        # Properties interface
        main_column = layout.column(align=True)
        main_column.prop(props, "export_path")
        main_column.prop(props, "export_preset")
        main_column.prop(props, "create_subfolders")
        
        # Action execution layout placement
        layout.separator()
        layout.operator("object.batch_fbx_export", icon='PLAY', text="Batch Export Selected")

classes = (
    MultiFbxExporterProperties,
    WM_OT_RefreshFbxPresets,
    OBJECT_OT_BatchFbxExport,
    VIEW3D_PT_MultiFbxExporterPanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.multi_fbx_exporter_props = bpy.props.PointerProperty(type=MultiFbxExporterProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.multi_fbx_exporter_props

if __name__ == "__main__":
    register()
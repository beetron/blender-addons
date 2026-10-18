bl_info = {
    "name": "Object Grouper",
    "author": "Lazy Onigiri / bTro",
    "version": (1, 0, 2),
    "blender": (4, 5, 0),
    "location": "View3D > Sidebar > Lazy Onigiri",
    "description": "Save named lists of objects and select them in one click. The last object in a list becomes the active object.",
    "warning": "",
    "category": "Object",
}

import bpy

ADDON_VERSION = ".".join(str(number) for number in bl_info["version"])
GITHUB_URL = "https://github.com/beetron/blender-addons"

OBJECT_TYPE_ICONS = {
    'MESH': 'OUTLINER_OB_MESH',
    'ARMATURE': 'OUTLINER_OB_ARMATURE',
    'EMPTY': 'OUTLINER_OB_EMPTY',
    'CURVE': 'OUTLINER_OB_CURVE',
    'SURFACE': 'OUTLINER_OB_SURFACE',
    'META': 'OUTLINER_OB_META',
    'FONT': 'OUTLINER_OB_FONT',
    'LATTICE': 'OUTLINER_OB_LATTICE',
    'LIGHT': 'OUTLINER_OB_LIGHT',
    'CAMERA': 'OUTLINER_OB_CAMERA',
}


def get_active_group(props):
    if 0 <= props.active_group_index < len(props.groups):
        return props.groups[props.active_group_index]
    return None


def is_in_view_layer(context, obj):
    # A deleted object can still be referenced by the list, so check it is really in this view layer
    return obj is not None and context.view_layer.objects.get(obj.name) is obj


def ensure_object_mode(context):
    if context.mode != 'OBJECT' and context.view_layer.objects.active is not None:
        bpy.ops.object.mode_set(mode='OBJECT')


class ObjectGrouperItem(bpy.types.PropertyGroup):
    obj: bpy.props.PointerProperty(
        name="Object",
        description="Object in this group",
        type=bpy.types.Object
    )


class ObjectGrouperGroup(bpy.types.PropertyGroup):
    # "name" is provided by PropertyGroup and is used as the group name
    items: bpy.props.CollectionProperty(type=ObjectGrouperItem)
    active_item_index: bpy.props.IntProperty(default=0)


class ObjectGrouperProperties(bpy.types.PropertyGroup):
    groups: bpy.props.CollectionProperty(type=ObjectGrouperGroup)
    active_group_index: bpy.props.IntProperty(default=0)

    unhide_objects: bpy.props.BoolProperty(
        name="Unhide Hidden Objects",
        description="Unhide hidden group objects so they can be selected. When off, hidden objects are skipped with a warning",
        default=True
    )


class OBJECTGROUPER_OT_GroupAdd(bpy.types.Operator):
    bl_idname = "object_grouper.group_add"
    bl_label = "Add Group"
    bl_description = "Create a new group"
    bl_options = {'REGISTER', 'UNDO'}

    from_selection: bpy.props.BoolProperty(
        name="From Selection",
        description="Fill the new group with the selected objects, active object last",
        default=False
    )

    def execute(self, context):
        props = context.scene.object_grouper_props
        group = props.groups.add()
        group.name = f"Group {len(props.groups)}"
        props.active_group_index = len(props.groups) - 1

        if self.from_selection:
            added = add_selected_to_group(context, group)
            if context.view_layer.objects.active and context.view_layer.objects.active.select_get():
                group.name = context.view_layer.objects.active.name + "_Group"
            self.report({'INFO'}, f"Created '{group.name}' with {added} objects.")
        return {'FINISHED'}


class OBJECTGROUPER_OT_GroupRemove(bpy.types.Operator):
    bl_idname = "object_grouper.group_remove"
    bl_label = "Remove Group"
    bl_description = "Remove the active group. The objects themselves are not affected"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return get_active_group(context.scene.object_grouper_props) is not None

    def execute(self, context):
        props = context.scene.object_grouper_props
        props.groups.remove(props.active_group_index)
        props.active_group_index = min(props.active_group_index, len(props.groups) - 1)
        return {'FINISHED'}


class OBJECTGROUPER_OT_GroupMove(bpy.types.Operator):
    bl_idname = "object_grouper.group_move"
    bl_label = "Move Group"
    bl_description = "Move the active group up or down"
    bl_options = {'REGISTER', 'UNDO'}

    direction: bpy.props.EnumProperty(items=[('UP', "Up", ""), ('DOWN', "Down", "")])

    @classmethod
    def poll(cls, context):
        return get_active_group(context.scene.object_grouper_props) is not None

    def execute(self, context):
        props = context.scene.object_grouper_props
        index = props.active_group_index
        target = index - 1 if self.direction == 'UP' else index + 1
        if 0 <= target < len(props.groups):
            props.groups.move(index, target)
            props.active_group_index = target
        return {'FINISHED'}


def add_selected_to_group(context, group):
    existing = {item.obj for item in group.items if item.obj is not None}
    active = context.view_layer.objects.active

    # Selection order is not stored by Blender, so sort by name and put the active object last
    new_objects = [obj for obj in sorted(context.selected_objects, key=lambda o: o.name)
                   if obj not in existing and obj is not active]
    if active is not None and active.select_get() and active not in existing:
        new_objects.append(active)

    # Keep a trailing armature (the rig) at the bottom when adding more objects later
    insert_at = len(group.items)
    last_obj = group.items[-1].obj if group.items else None
    if last_obj is not None and last_obj.type == 'ARMATURE' and not any(o.type == 'ARMATURE' for o in new_objects):
        insert_at -= 1

    for obj in new_objects:
        item = group.items.add()
        item.obj = obj
        group.items.move(len(group.items) - 1, insert_at)
        insert_at += 1

    if new_objects:
        group.active_item_index = insert_at - 1
    return len(new_objects)


class OBJECTGROUPER_OT_ItemAddSelected(bpy.types.Operator):
    bl_idname = "object_grouper.item_add_selected"
    bl_label = "Add Selected"
    bl_description = "Add the selected objects to the active group (active object last; an armature already at the bottom stays at the bottom)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return get_active_group(context.scene.object_grouper_props) is not None and bool(context.selected_objects)

    def execute(self, context):
        group = get_active_group(context.scene.object_grouper_props)
        added = add_selected_to_group(context, group)
        if not added:
            self.report({'INFO'}, "Selected objects are already in the group.")
        else:
            self.report({'INFO'}, f"Added {added} objects to '{group.name}'.")
        return {'FINISHED'}


class OBJECTGROUPER_OT_ItemRemove(bpy.types.Operator):
    bl_idname = "object_grouper.item_remove"
    bl_label = "Remove Object"
    bl_description = "Remove the highlighted object from the group. The object itself is not affected"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        group = get_active_group(context.scene.object_grouper_props)
        return group is not None and 0 <= group.active_item_index < len(group.items)

    def execute(self, context):
        group = get_active_group(context.scene.object_grouper_props)
        group.items.remove(group.active_item_index)
        group.active_item_index = min(group.active_item_index, len(group.items) - 1)
        return {'FINISHED'}


class OBJECTGROUPER_OT_ItemMove(bpy.types.Operator):
    bl_idname = "object_grouper.item_move"
    bl_label = "Move Object"
    bl_description = "Move the highlighted object up or down. The last object becomes the active object when selecting"
    bl_options = {'REGISTER', 'UNDO'}

    direction: bpy.props.EnumProperty(items=[
        ('UP', "Up", ""),
        ('DOWN', "Down", ""),
        ('BOTTOM', "Bottom", ""),
    ])

    @classmethod
    def poll(cls, context):
        group = get_active_group(context.scene.object_grouper_props)
        return group is not None and 0 <= group.active_item_index < len(group.items)

    def execute(self, context):
        group = get_active_group(context.scene.object_grouper_props)
        index = group.active_item_index
        if self.direction == 'UP':
            target = index - 1
        elif self.direction == 'DOWN':
            target = index + 1
        else:
            target = len(group.items) - 1
        if 0 <= target < len(group.items) and target != index:
            group.items.move(index, target)
            group.active_item_index = target
        return {'FINISHED'}


class OBJECTGROUPER_OT_ItemClean(bpy.types.Operator):
    bl_idname = "object_grouper.item_clean"
    bl_label = "Remove Missing"
    bl_description = "Remove empty entries and objects that no longer exist in this scene"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return get_active_group(context.scene.object_grouper_props) is not None

    def execute(self, context):
        group = get_active_group(context.scene.object_grouper_props)
        removed = 0
        for index in reversed(range(len(group.items))):
            if not is_in_view_layer(context, group.items[index].obj):
                group.items.remove(index)
                removed += 1
        group.active_item_index = min(group.active_item_index, len(group.items) - 1)
        self.report({'INFO'}, f"Removed {removed} missing entries.")
        return {'FINISHED'}


class OBJECTGROUPER_OT_SelectGroup(bpy.types.Operator):
    bl_idname = "object_grouper.select_group"
    bl_label = "Select Group"
    bl_description = "Select every object in the group and make the last one active.\nShift+Click: add to the current selection"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty(default=-1)
    extend: bpy.props.BoolProperty(name="Extend", default=False)

    def invoke(self, context, event):
        self.extend = event.shift
        return self.execute(context)

    def execute(self, context):
        props = context.scene.object_grouper_props
        index = self.index if self.index >= 0 else props.active_group_index
        if not 0 <= index < len(props.groups):
            self.report({'WARNING'}, "No group to select.")
            return {'CANCELLED'}
        group = props.groups[index]
        props.active_group_index = index

        ensure_object_mode(context)
        if not self.extend:
            for obj in context.view_layer.objects:
                obj.select_set(False)

        selected = []
        skipped = []
        for item in group.items:
            obj = item.obj
            if not is_in_view_layer(context, obj):
                skipped.append(obj.name if obj else "<empty>")
                continue
            if props.unhide_objects:
                if obj.hide_get():
                    obj.hide_set(False)
                if obj.hide_viewport:
                    obj.hide_viewport = False
            if obj.hide_select or not obj.visible_get():
                skipped.append(obj.name)
                continue
            obj.select_set(True)
            selected.append(obj)

        if not selected:
            self.report({'WARNING'}, f"Nothing in '{group.name}' could be selected.")
            return {'CANCELLED'}

        # The last object counts as the last Shift+Clicked one
        context.view_layer.objects.active = selected[-1]

        last_item = group.items[-1].obj if group.items else None
        if skipped:
            message = f"Selected {len(selected)} objects, skipped {len(skipped)}: {', '.join(skipped)}"
            if last_item is not selected[-1]:
                message += f". Active object is '{selected[-1].name}' instead of the last list entry"
            self.report({'WARNING'}, message)
        else:
            self.report({'INFO'}, f"Selected {len(selected)} objects. Active: '{selected[-1].name}'")
        return {'FINISHED'}


class OBJECTGROUPER_UL_Groups(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "name", text="", emboss=False, icon='OUTLINER_COLLECTION')
        # Right-aligned so the count only takes the space it needs and the name gets the rest
        count = row.row(align=True)
        count.alignment = 'RIGHT'
        count.label(text=str(len(item.items)))
        op = row.operator("object_grouper.select_group", text="", icon='RESTRICT_SELECT_OFF', emboss=False)
        op.index = index


class OBJECTGROUPER_UL_Items(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        obj = item.obj
        if obj is None:
            row.alert = True
            row.prop(item, "obj", text="", icon='ERROR')
            return
        row.alert = not is_in_view_layer(context, obj)
        row.prop(item, "obj", text="", emboss=False, icon=OBJECT_TYPE_ICONS.get(obj.type, 'OBJECT_DATA'))
        if index == len(data.items) - 1:
            row.label(text="Active", icon='PINNED')


class VIEW3D_PT_ObjectGrouperPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Lazy Onigiri'
    bl_label = "Object Grouper"
    bl_order = 1

    def draw(self, context):
        layout = self.layout
        props = context.scene.object_grouper_props

        header_box = layout.box()
        column = header_box.column(align=True)
        column.label(text=f"Object Grouper (v.{ADDON_VERSION})", icon='GROUP')
        column.label(text="by Lazy Onigiri / bTro", icon='USER')
        header_box.operator("wm.url_open", text="GitHub", icon='URL').url = GITHUB_URL

        # Groups list
        row = layout.row()
        row.template_list("OBJECTGROUPER_UL_Groups", "groups", props, "groups",
                          props, "active_group_index", rows=4)
        column = row.column(align=True)
        column.operator("object_grouper.group_add", icon='ADD', text="").from_selection = False
        column.operator("object_grouper.group_remove", icon='REMOVE', text="")
        column.separator()
        column.operator("object_grouper.group_move", icon='TRIA_UP', text="").direction = 'UP'
        column.operator("object_grouper.group_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

        layout.operator("object_grouper.group_add", icon='RESTRICT_SELECT_OFF',
                        text="New Group From Selection").from_selection = True

        group = get_active_group(props)
        if group is None:
            return

        # Select button for the active group
        layout.separator()
        select_row = layout.row()
        select_row.scale_y = 1.4
        select_row.operator("object_grouper.select_group", icon='RESTRICT_SELECT_OFF',
                            text=f"Select '{group.name}'").index = props.active_group_index

        # Objects in the active group
        box = layout.box()
        box.label(text="Objects (last one becomes active)", icon='OBJECT_DATA')
        row = box.row()
        row.template_list("OBJECTGROUPER_UL_Items", "items", group, "items",
                          group, "active_item_index", rows=6)
        column = row.column(align=True)
        column.operator("object_grouper.item_add_selected", icon='ADD', text="")
        column.operator("object_grouper.item_remove", icon='REMOVE', text="")
        column.separator()
        column.operator("object_grouper.item_move", icon='TRIA_UP', text="").direction = 'UP'
        column.operator("object_grouper.item_move", icon='TRIA_DOWN', text="").direction = 'DOWN'
        column.operator("object_grouper.item_move", icon='TRIA_DOWN_BAR', text="").direction = 'BOTTOM'
        column.separator()
        column.operator("object_grouper.item_clean", icon='BRUSH_DATA', text="")

        # Warnings
        missing = sum(1 for item in group.items if not is_in_view_layer(context, item.obj))
        if missing:
            box.label(text=f"{missing} missing object(s). Use the brush button to clean up.", icon='ERROR')
        objects = [item.obj for item in group.items if item.obj is not None]
        if any(obj.type == 'ARMATURE' for obj in objects) and objects[-1].type != 'ARMATURE':
            box.label(text="The rig is not last. Move it to the bottom.", icon='ERROR')

        layout.prop(props, "unhide_objects")


classes = (
    ObjectGrouperItem,
    ObjectGrouperGroup,
    ObjectGrouperProperties,
    OBJECTGROUPER_OT_GroupAdd,
    OBJECTGROUPER_OT_GroupRemove,
    OBJECTGROUPER_OT_GroupMove,
    OBJECTGROUPER_OT_ItemAddSelected,
    OBJECTGROUPER_OT_ItemRemove,
    OBJECTGROUPER_OT_ItemMove,
    OBJECTGROUPER_OT_ItemClean,
    OBJECTGROUPER_OT_SelectGroup,
    OBJECTGROUPER_UL_Groups,
    OBJECTGROUPER_UL_Items,
    VIEW3D_PT_ObjectGrouperPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.object_grouper_props = bpy.props.PointerProperty(type=ObjectGrouperProperties)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.object_grouper_props


if __name__ == "__main__":
    register()

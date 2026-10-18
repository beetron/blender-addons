**English** | [日本語](README.ja.md)

# Object Grouper

**Version:** 1.0.2 · **Author:** Lazy Onigiri / bTro · **Blender:** 4.5+

Save named lists of objects and **select a whole list in one click**, with no more Ctrl/Shift-clicking the same objects every time. The **last object in the list becomes the active object**, just as if you had Shift-clicked it last. Put the rig at the bottom of the list, and exporters that need the armature active (such as Auto-Rig Pro's export) work right away.

Typical uses:
- A character's body parts plus its rig, ready for export.
- Different sets of body-part or outfit variants.
- Any set of objects you select often.

## Installation

1. Download `Object_Grouper_v1.py`.
2. In Blender, open **Edit → Preferences → Add-ons**, click the **⌄** menu in the top-right corner and choose **Install from Disk...**.
3. Select the file and enable **Object Grouper**.
4. The panel is in the 3D Viewport sidebar (`N`) under the **Lazy Onigiri** tab.

## Quick start

1. Select the objects you want, and **Shift-click the rig last** so it is the active object.
2. Click **New Group From Selection**. A group is created with the active object at the bottom of the list, named after it (for example `rig_Group`).
3. Double-click the group name to rename it, for example `Character_Base`.
4. From now on, click **Select 'Character_Base'** to select the whole group with the rig active.

## Panel

### Group list
| Control | Description |
|---|---|
| **Group row** | Shows the group name and how many objects it contains. Double-click the name to rename it. |
| **Arrow icon on a row** | Selects that group. |
| **+ / −** | Adds an empty group / removes the highlighted group. The objects themselves are not affected. |
| **▲ / ▼** | Moves the highlighted group up or down. |
| **New Group From Selection** | Creates a group from the selected objects, with the active object last. |
| **Select '…'** | Selects every object in the highlighted group and makes the last one active. |

### Object list (for the highlighted group)
| Control | Description |
|---|---|
| **Active** marker | Shows which object (the last one) becomes active when selecting. |
| **+** | Adds the selected objects, with the active object last. If the list already ends with an armature, new objects are inserted **above** it, so the rig stays last. |
| **−** | Removes the highlighted object from the group. The object itself is not deleted. |
| **▲ / ▼** | Moves the highlighted object up or down. |
| **⤓** | Moves the highlighted object to the bottom, which makes it the active object. |
| **Brush** | Removes entries for objects that no longer exist in the scene. |

### Options
| Option | Description |
|---|---|
| **Unhide Hidden Objects** | On by default. Hidden group members are unhidden so they can be selected. When off, hidden objects are skipped and listed in a warning. |
| **GitHub** | Opens this repository in your web browser. |

## Tips

- **Shift-click** a Select button to add the group to your current selection instead of replacing it.
- Selecting a group switches Blender to **Object Mode** first, for example when you are in Pose Mode.
- **Renaming objects is safe.** Groups store references to the objects, not their names.
- Groups are **saved in the .blend file**, per scene.

## Warnings in the panel

- **Red rows:** the object was deleted or is no longer in the scene. Click the brush button to clean up.
- **"The rig is not last. Move it to the bottom.":** the group contains an armature that isn't the last entry. Highlight the rig and click **⤓**.
- Objects in hidden or excluded collections, and objects that are not selectable, are skipped when selecting. The status bar lists which ones.

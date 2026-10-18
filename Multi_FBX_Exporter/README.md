**English** | [日本語](README.ja.md)

# Multi Fbx Exporter

**Version:** 1.0.4 · **Author:** Lazy Onigiri / bTro (updated from the original by nekorushi) · **Blender:** 4.5+

Export every selected mesh to its **own FBX file** in one click. You can apply one of your saved FBX export presets, so every file uses the same settings. This is useful for exporting many props or modular pieces to a game engine.

## Installation

1. Download `Multi_FBX_Exporter_v1.py`.
2. In Blender, open **Edit → Preferences → Add-ons**, click the **⌄** menu in the top-right corner and choose **Install from Disk...**.
3. Select the file and enable **Multi Fbx Exporter**.
4. The panel is in the 3D Viewport sidebar (`N`) under the **Lazy Onigiri** tab.

## Panel

| Setting | Description |
|---|---|
| **Folder** | The folder the FBX files are written to. It must already exist. |
| **Preset** | An FBX export preset to apply. **None (Default Settings)** uses Blender's default FBX settings. |
| **Create Subfolders** | When on, each object is exported into its own subfolder: `Folder/ObjectName/ObjectName.fbx`. |
| **Batch Export Selected** | Exports each selected mesh as a separate FBX file. |
| **GitHub** | Opens this repository in your web browser. |

## How to use

1. Set **Folder** to where the files should go.
2. Choose a **Preset**, or leave it on **None** for default settings.
3. Select the mesh objects you want to export.
4. Click **Batch Export Selected**.

Each file is named after its object, for example `Crate_01.fbx`.

## Creating an FBX preset

1. Open **File → Export → FBX (.fbx)**.
2. Adjust the settings you want, such as scale, axes and what to include.
3. Next to **Operator Presets** at the top of the settings, click **+** and give the preset a name.
4. The preset now appears in the add-on's **Preset** list.

## Good to know

- **Only mesh objects** are exported. Other selected objects, such as armatures, empties or lights, are ignored.
- **Each object is exported at the world origin.** During export, the object's location is temporarily set to `0, 0, 0`, so the pivot ends up at the center in the game engine. The original location is restored afterwards. Rotation and scale are not changed.
- **Existing files with the same name are overwritten.**
- Characters in object names that are not allowed in file names are replaced with `_`.
- Your selection and active object are restored after the export.
- If the export fails for one object, the others still export, and the error is shown in Blender's status bar.

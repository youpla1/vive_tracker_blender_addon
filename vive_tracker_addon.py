import bpy
from bpy.types import (Panel, Operator)

try:
    import openvr
except:
    print("OpenVR is not installed for bundled python!")

    import os
    if os.name=="nt":
        print("Trying to install it, if this does not work please restart blender as admin")

        import subprocess as sp
        import sys

        python_exe = os.path.join(sys.prefix, 'bin', 'python.exe')
        target = os.path.join(sys.prefix, 'lib', 'site-packages')

        sp.call([python_exe, '-m', 'ensurepip'])
        sp.call([python_exe, '-m', 'pip', 'install', '--upgrade', 'pip'])
        sp.call([python_exe, '-m', 'pip', 'install', '--upgrade', 'openvr', '-t', target])


bpy.openvr=openvr
bpy.openvr.STARTED=0


def toggle_openvr(self, context):
    if self.toggle_openvr:
        print("Initializing OpenVR")
        print(bpy.openvr.init(bpy.openvr.VRApplication_Scene)) # should be an object
        bpy.openvr.STARTED=1
    else:
        print("Shutting OpenVR down")
        print(bpy.openvr.shutdown()) # should be None
        bpy.openvr.STARTED=0
    return

bpy.types.WindowManager.toggle_openvr = bpy.props.BoolProperty(default=False, update=toggle_openvr)
bpy.types.Scene.vive_tracker_kx = bpy.props.FloatProperty(
        description='Displacement factor on X: Object_in_Blender.position.x = (Actual_Vive_Tracker.position.x-x0)*this',
        default=1.0
        )
bpy.types.Scene.vive_tracker_ky = bpy.props.FloatProperty(
        description='Displacement factor on Y: Object_in_Blender.position.y = (Actual_Vive_Tracker.position.y-y0)*this',
        default=1.0
        )
bpy.types.Scene.vive_tracker_kz = bpy.props.FloatProperty(
        description='Displacement factor on Z: Object_in_Blender.position.z = (Actual_Vive_Tracker.position.z-z0)*this',
        default=1.0
        )

bpy.types.Scene.vive_tracker_x0 = bpy.props.FloatProperty(
        description='Offset on X: Object_in_Blender.position.x = (Actual_Vive_Tracker.position.x-this)*kx',
        default=0.0
        )
bpy.types.Scene.vive_tracker_y0 = bpy.props.FloatProperty(
        description='Offset on Y: Object_in_Blender.position.y = (Actual_Vive_Tracker.position.y-this)*ky',
        default=0.0
        )
bpy.types.Scene.vive_tracker_z0 = bpy.props.FloatProperty(
        description='Offset on Z: Object_in_Blender.position.z = (Actual_Vive_Tracker.position.z-this)*kz',
        default=0.0
        )

bpy.types.Scene.vive_tracker_moved_object = bpy.props.StringProperty()


class OBJECT_PT_CustomPanel(Panel):
    bl_idname = "OBJECT_PT_CustomPanel"
    bl_label = "Vive Tracker"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Vive Tracker"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout

        layout.separator()
        wm = context.window_manager
        label = "Click to stop OpenVR" if wm.toggle_openvr else "Click to start OpenVR"
        layout.prop(wm, 'toggle_openvr', text=label, toggle=True)

        layout.label(text="IMPORTANT: Tracking is only done when animation is playing!")

        layout.separator()
        layout.label(text="Apply Pose to:")
        layout.prop_search(context.scene, 'vive_tracker_moved_object', context.scene, "objects", text="")


        layout.separator()
        layout.label(text="Offset:")
        layout.prop(bpy.context.scene, 'vive_tracker_x0', text="X")
        layout.prop(bpy.context.scene, 'vive_tracker_y0', text="Y")
        layout.prop(bpy.context.scene, 'vive_tracker_z0', text="Z")

        layout.separator()
        layout.label(text="Displacement factor:")
        layout.prop(bpy.context.scene, 'vive_tracker_kx', text="X")
        layout.prop(bpy.context.scene, 'vive_tracker_ky', text="Y")
        layout.prop(bpy.context.scene, 'vive_tracker_kz', text="Z")


# Actual tracking function

def set_pose_from_openvr(scene):
    """Set the Pose of an object based on the Vive Tracker data"""
    if bpy.openvr.STARTED!=1:
        return
    poses = []
    poses, _ = bpy.openvr.VRCompositor().waitGetPoses(poses, None)
    p = poses[1].mDeviceToAbsoluteTracking

    x0=bpy.context.scene.vive_tracker_x0
    y0=bpy.context.scene.vive_tracker_y0
    z0=bpy.context.scene.vive_tracker_z0
    kx=bpy.context.scene.vive_tracker_kx
    ky=bpy.context.scene.vive_tracker_ky
    kz=bpy.context.scene.vive_tracker_kz
    tf = [[-p[0][0], p[2][0], p[1][0], 1],
          [-p[0][1], p[2][1], p[1][1], 0],
          [-p[0][2], p[2][2], p[1][2], 0],
          [(-p[0][3]-x0)*kx, (p[2][3]-y0)*ky, (p[1][3]-z0)*kz, 1]]
    bpy.context.scene.objects[bpy.context.scene.vive_tracker_moved_object].matrix_world = tf


# Registration

bl_info = {
    "name": "Vive Tracker",
    "blender": (3, 2, 0),
    "category": "Animation",
    "author": "Quentin Delamare",
}

def register():
    bpy.utils.register_class(OBJECT_PT_CustomPanel)
    # remove any previous version of the handler:
    for h in bpy.app.handlers.frame_change_pre:
        if h.__qualname__=="set_pose_from_openvr":
            bpy.app.handlers.frame_change_pre.remove(h)
    bpy.app.handlers.frame_change_pre.append(set_pose_from_openvr)


def unregister():
    bpy.utils.unregister_class(OBJECT_PT_CustomPanel)
    # remove the handler based on function name:
    for h in bpy.app.handlers.frame_change_pre:
        if h.__qualname__=="set_pose_from_openvr":
            bpy.app.handlers.frame_change_pre.remove(h)


if __name__ == "__main__":
    register()

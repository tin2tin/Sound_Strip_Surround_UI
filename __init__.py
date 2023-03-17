bl_info = {
    "name": "Sound Strip Channel UI",
    "author": "tintwotin",
    "version": (1, 0),
    "blender": (3, 40, 0),
    "location": "Seqeuncer > Sidebar > Sound",
    "description": "Expose channel settings",
    "warning": "",
    "doc_url": "",
    "category": "Sequencer",
}

import os
import bpy
import bpy.utils.previews
from bpy.types import Operator
from bpy.props import EnumProperty


class SequencerPanPresets(Operator):
    """Pan Presets"""
    bl_idname = "sequencer.pan_presets"
    bl_label = "Pan Preset"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = context.active_sequence_strip
        if not strip:
            return False

        return strip.type == 'SOUND'

    mono: EnumProperty(
        items=(
            ('NONE', 'None', 'None avalible'),
        ),
        name="Mono Presets",
        description="Mono Presets",
        default='NONE')

    stereo_items = (
        ('FRONTLEFT', 'Front Left', 'Pan to the left'),
        ('FRONTCENTER', 'Front Center', 'Pan to the center'),
        ('FRONTRIGHT', 'Front Right', 'Pan to the right'),
    )

    stereo: EnumProperty(
        items=stereo_items,
        name="Stereo",
        description="Pan the audio",
        default='FRONTCENTER')

    surround4_items = stereo_items + (
        ('SIDELEFT', 'Side Left', 'Pan to the side left'),
        ('SIDERIGHT', 'Side Right', 'Pan to the side right'),
    )

    surround4: EnumProperty(
        items=surround4_items,
        name="4 Channel Presets",
        description="Pan the audio",
        default='FRONTCENTER')

    surround51: EnumProperty(
        items=surround4_items,
        name="5.1 Surround Presets",
        description="Pan the audio",
        default='FRONTCENTER')

    surround71_items = surround4_items + (
        ('REARLEFT', 'Rear Left', 'Pan to the rear left'),
        ('REARRIGHT', 'Rear Right', 'Pan to the rear right'),
    )

    surround71: EnumProperty(
        items=surround71_items,
        name="7.1 Surround Presets",
        description="Pan the audio",
        default='FRONTCENTER')

    @classmethod
    def poll(cls, context):
        strip = context.active_sequence_strip
        if not strip:
            return False

        return strip.type == 'SOUND' and context.scene and context.scene.sequence_editor and context.scene.sequence_editor.active_strip

    def set_pan(self, sequence, audio_channels):
        pan_stereo = {
            'FRONTLEFT': - 1.0,
            'FRONTCENTER': 0,
            'FRONTRIGHT': 1.0,
        }
        pan_surround4 = {
            'FRONTLEFT': - 0.5,
            'FRONTCENTER': 0.0,
            'FRONTRIGHT': 0.5,
            'SIDELEFT': -1.5,
            'SIDERIGHT': 1.5,
        }
        pan_surround51 = {
            'FRONTLEFT': - 0.33335,
            'FRONTCENTER': 0.0,
            'FRONTRIGHT': 0.33335,
            'SIDELEFT': -1.2225,
            'SIDERIGHT': 1.2225,
        }
        pan_surround71 = {
            'FRONTLEFT': - 0.33335,
            'FRONTCENTER': 0.0,
            'FRONTRIGHT': 0.33335,
            'SIDELEFT': -1.2225,
            'SIDERIGHT': 1.2225,
            'REARLEFT': -1.66667,
            'REARRIGHT': 1.66667,
        }

        if audio_channels == 'STEREO':
            sequence.pan = pan_stereo[self.stereo]
        elif audio_channels == 'SURROUND4':
            sequence.pan = pan_surround4[self.surround4]
        elif audio_channels == 'SURROUND51':
            sequence.pan = pan_surround51[self.surround51]
        elif audio_channels == 'SURROUND71':
            sequence.pan = pan_surround71[self.surround71]

    def execute(self, context):
        audio_channels = context.scene.render.ffmpeg.audio_channels
        sequences = context.selected_sequences
        if not sequences and context.scene.sequence_editor.active_strip:
            self.set_pan(
                context.scene.sequence_editor.active_strip, audio_channels)
            if context.scene.tool_settings.use_keyframe_insert_auto == True:
                sequence.keyframe_insert("pan")
            return {'FINISHED'}

        for sequence in context.selected_sequences:
            self.set_pan(sequence, audio_channels)
            if context.scene.tool_settings.use_keyframe_insert_auto == True:
                sequence.keyframe_insert("pan")
        return {'FINISHED'}


class SEQUENCER_PT_adjust_sound(bpy.types.Panel):
    bl_idname = "SEQUENCER_PT_adjust_sound"
    bl_label = "Sound"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Strip"


    def draw(self, context):
        global custom_icons
        
        st = context.space_data
        strip = context.active_sequence_strip
        sound = strip.sound
        layout = self.layout
        audio_channels = context.scene.render.ffmpeg.audio_channels.lower()
        overlay_settings = st.timeline_overlay
        layout.active = not strip.mute
        layout.use_property_split = True
        layout.use_property_decorate = True
        col = self.layout.column(align=True)
        
        col.prop(strip, "volume", text="Volume")

        if overlay_settings.waveform_display_type == 'DEFAULT_WAVEFORMS':
            col = col.column(heading="Display")
            col.prop(strip, "show_waveform", text="Waveform")

        col = layout.column(heading="Mono")
        col.prop(sound, "use_mono", text="")

        if audio_channels != 'mono':
            col = layout
            col = col.split(factor=0.3, align=True)
            col.label(text="")
            col = col.box()
            col = col.box()

            prefs = context.preferences
            enum_def = prefs.system.bl_rna.properties["audio_channels"]
            lut = {i.identifier : i.name for i in enum_def.enum_items}
            channel_str = str(lut[context.scene.render.ffmpeg.audio_channels])

            cen = col.row()
            cen.scale_y = .8
            cen.alignment = 'CENTER'
            cen.label(text=channel_str)
            cen.enabled = sound is not None and sound.use_mono

            col = col.column(align=True)
            row = col.row()
            row.scale_y = 1.8
            row.scale_x = 1.5
            row.label(text="")
            col.enabled = sound is not None and sound.use_mono
        if audio_channels == 'stereo':
            pan_values = [-1, 0, 1]
            for i, value in enumerate(pan_values):
                pan_values[i] = 1 if value == round(strip.pan, 1) else 0
            props = row.operator('sequencer.pan_presets', text="", emboss=pan_values[0], icon_value=custom_icons["left_front"].icon_id)
            props.stereo = 'FRONTLEFT'
            row.label(text="")
            props = row.operator('sequencer.pan_presets', text="", emboss=pan_values[1], icon_value=custom_icons["center_front"].icon_id)
            props.stereo = 'FRONTCENTER'
            row.label(text="")
            props = row.operator('sequencer.pan_presets', text="", emboss=pan_values[2], icon_value=custom_icons["right_front"].icon_id)
            props.stereo = 'FRONTRIGHT'
            row.label(text="")
            col.label(text="")

        if audio_channels == 'surround4':
            pan_values = [-0.5, 0.5, -1.5, 1.5]
            for i, value in enumerate(pan_values):
                pan_values[i] = 1 if value == round(strip.pan, 1) else 0
            row.scale_y = 1.8
            row.scale_x = 1.5
            props = row.operator('sequencer.pan_presets', text="", emboss=pan_values[0], icon_value=custom_icons["left_front"].icon_id)
            props.surround4 = 'FRONTLEFT'
            row.label(text="")
            row.label(text="")
            props = row.operator('sequencer.pan_presets', text="", emboss=pan_values[1], icon_value=custom_icons["right_front"].icon_id)
            props.surround4 = 'FRONTRIGHT'
            row.label(text="")
            col = col.column()
            row = col.row(align=True)
            row.scale_y = 1.8
            row.scale_x = 1.5
            row.label(text="")
            props = row.operator('sequencer.pan_presets', text="", emboss=pan_values[2], icon_value=custom_icons["left_rear"].icon_id)
            props.surround4 = 'SIDELEFT'
            row.label(text="")
            row.label(text="")
            row.label(text="")
            props = row.operator('sequencer.pan_presets', text="", emboss=pan_values[3], icon_value=custom_icons["right_rear"].icon_id)
            props.surround4 = 'SIDERIGHT'
            row.label(text="")

        if audio_channels == 'surround51':
            pan_values = [-0.3, 0, 0.3, -1.2, 1.2]
            for i, value in enumerate(pan_values):
                pan_values[i] = 1 if value == round(strip.pan, 1) else 0
            row.scale_y = 1.8
            row.scale_x = 1.5
            props = row.operator('sequencer.pan_presets', text="", emboss=pan_values[0], icon_value=custom_icons["left_front"].icon_id)
            props.surround51 = 'FRONTLEFT'
            row.label(text="")
            props = row.operator('sequencer.pan_presets', text="", emboss=pan_values[1], icon_value=custom_icons["center_front"].icon_id)
            props.surround51 = 'FRONTCENTER'
            row.label(text="")
            props = row.operator('sequencer.pan_presets', text="", emboss=pan_values[2], icon_value=custom_icons["right_front"].icon_id)
            props.surround51 = 'FRONTRIGHT'
            row.label(text="")
            col = col.column()
            row = col.row(align=True)
            row.scale_y = 1.8
            row.scale_x = 1.5
            row.label(text="")
            props = row.operator('sequencer.pan_presets', text="", emboss=pan_values[3], icon_value=custom_icons["left_rear"].icon_id)
            props.surround51 = 'SIDELEFT'
            row.label(text="")
            row.label(text="")
            row.label(text="")
            row.label(text="")
            props = row.operator('sequencer.pan_presets', text="", emboss=pan_values[4], icon_value=custom_icons["right_rear"].icon_id)
            props.surround51 = 'SIDERIGHT'
            row.label(text="")

        if audio_channels == 'surround71':
            pan_values = [-0.3, 0, 0.3, -1.2, 1.2, -1.7, 1.7]
            for i, value in enumerate(pan_values):
                pan_values[i] = 1 if value == round(strip.pan, 1) else 0
            row.scale_y = 1.8
            row.scale_x = 1.5
            props = row.operator('sequencer.pan_presets', text="", emboss=pan_values[0], icon_value=custom_icons["left_front"].icon_id)
            props.surround71 = 'FRONTLEFT'
            row.label(text="")
            props = row.operator('sequencer.pan_presets', text="", emboss=pan_values[1], icon_value=custom_icons["center_front"].icon_id)
            props.surround71 = 'FRONTCENTER'
            row.label(text="")
            props = row.operator('sequencer.pan_presets', text="", emboss=pan_values[2], icon_value=custom_icons["right_front"].icon_id)
            props.surround71 = 'FRONTRIGHT'
            row.label(text="")
            col = col.column()
            row = col.row(align=True)
            row.scale_y = 1.8
            row.scale_x = 1.5

            props = row.operator('sequencer.pan_presets', text="", emboss=pan_values[3], icon_value=custom_icons["left_side"].icon_id)
            props.surround71 = 'SIDELEFT'
            row.label(text="")
            props = row.operator('sequencer.pan_presets', text="", emboss=pan_values[4], icon_value=custom_icons["right_side"].icon_id)
            props.surround71 = 'SIDERIGHT'
            row = col.row(align=True)
            row.scale_y = 1.8
            row.scale_x = 1.5
            props = row.operator('sequencer.pan_presets', text="", emboss=pan_values[5], icon_value=custom_icons["left_rear"].icon_id)
            props.surround71 = 'REARLEFT'
            row.label(text="")
            props = row.operator('sequencer.pan_presets', text="", emboss=pan_values[6], icon_value=custom_icons["right_rear"].icon_id)
            props.surround71 = 'REARRIGHT'

        if audio_channels != 'mono':
            cen = col.row()
            cen.alignment = 'CENTER'            

            pan_text = "%.2f°" % (strip.pan * 90)
            cen.label(text=pan_text) 
            
            col = layout.column(align=True)
            col.prop(strip, "pan")
            col.enabled = sound is not None and sound.use_mono

# global variable to store icons in
custom_icons = None


def register():
    global custom_icons
    custom_icons = bpy.utils.previews.new()
    addon_path =  os.path.dirname(__file__)
    icons_dir = os.path.join(addon_path, "icons")
    
    custom_icons.load("left_front", os.path.join(icons_dir, "left_front.png"), 'IMAGE')
    custom_icons.load("right_front", os.path.join(icons_dir, "right_front.png"), 'IMAGE')
    custom_icons.load("center_front", os.path.join(icons_dir, "center_front.png"), 'IMAGE')
    custom_icons.load("left_side", os.path.join(icons_dir, "left_side.png"), 'IMAGE')
    custom_icons.load("right_side", os.path.join(icons_dir, "right_side.png"), 'IMAGE')
    custom_icons.load("left_rear", os.path.join(icons_dir, "left_rear.png"), 'IMAGE')
    custom_icons.load("right_rear", os.path.join(icons_dir, "right_rear.png"), 'IMAGE')
    bpy.utils.register_class(SequencerPanPresets)
    bpy.utils.register_class(SEQUENCER_PT_adjust_sound)

def unregister():
    global custom_icons
    bpy.utils.previews.remove(custom_icons)
    bpy.utils.unregister_class(SEQUENCER_PT_adjust_sound)
    bpy.utils.unregister_class(SequencerPanPresets)

if __name__ == "__main__":
    __file__ = bpy.context.space_data.text.filepath
    register()

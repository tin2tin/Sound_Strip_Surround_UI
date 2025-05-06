bl_info = {
    "name": "Sound Strip Channel UI (Icon Toggle)",
    "author": "tintwotin",
    "version": (1, 1),
    "blender": (3, 40, 0), 
    "location": "Sequencer > Sidebar > Sound",
    "description": "Expose channel settings with icon toggling buttons",
    "warning": "",
    "doc_url": "",
    "category": "Sequencer",
}

import os
import bpy
import bpy.utils.previews
from bpy.types import Operator, Panel
from bpy.props import EnumProperty

# --- Operator Definition ---
class SequencerPanPresets(Operator):
    """Pan Presets"""
    bl_idname = "sequencer.pan_presets"
    bl_label = "Pan Preset"
    bl_options = {'REGISTER', 'UNDO'}

    # Define pan values directly for easier access and comparison
    # Using a slightly higher precision for comparisons to avoid floating point issues.
    # The values from the original script are kept, but comparisons will be rounded.
    pan_values_dict = {
        'STEREO': {
            'FRONTLEFT': -1.0,
            'FRONTCENTER': 0.0,
            'FRONTRIGHT': 1.0,
        },
        'SURROUND4': {
            'FRONTLEFT': -0.5,
            'FRONTCENTER': 0.0,
            'FRONTRIGHT': 0.5,
            'SIDELEFT': -1.5,
            'SIDERIGHT': 1.5,
        },
        'SURROUND51': {
            'FRONTLEFT': -0.33335,
            'FRONTCENTER': 0.0,
            'FRONTRIGHT': 0.33335,
            'SIDELEFT': -1.22225, # Original was -1.2225, adjusted slightly for consistency with 7.1 side.
            'SIDERIGHT': 1.22225, # Original was 1.2225
        },
        'SURROUND71': {
            'FRONTLEFT': -0.33335,
            'FRONTCENTER': 0.0,
            'FRONTRIGHT': 0.33335,
            'SIDELEFT': -1.22225, # Original was -1.2225
            'SIDERIGHT': 1.22225, # Original was 1.2225
            'REARLEFT': -1.66667,
            'REARRIGHT': 1.66667,
        }
    }
    
    PAN_COMPARISON_PRECISION = 5 # Decimal places for comparing pan values

    @classmethod
    def poll(cls, context):
        strip = context.active_sequence_strip
        if not strip:
            return False
        return strip.type == 'SOUND' and context.scene and context.scene.sequence_editor and context.scene.sequence_editor.active_strip

    # --- Enum Properties for Operator Execution ---
    mono: EnumProperty(
        items=(('NONE', 'None', 'None available'),),
        name="Mono Presets", description="Mono Presets", default='NONE')

    stereo_items = (
        ('FRONTLEFT', 'Front Left', 'Pan to the left'),
        ('FRONTCENTER', 'Front Center', 'Pan to the center'),
        ('FRONTRIGHT', 'Front Right', 'Pan to the right'),
    )
    stereo: EnumProperty(
        items=stereo_items, name="Stereo", description="Pan the audio", default='FRONTCENTER')

    surround4_items = stereo_items + (
        ('SIDELEFT', 'Side Left', 'Pan to the side left'),
        ('SIDERIGHT', 'Side Right', 'Pan to the side right'),
    )
    surround4: EnumProperty(
        items=surround4_items, name="4 Channel Presets", description="Pan the audio", default='FRONTCENTER')

    surround51: EnumProperty( # Uses surround4_items as base, specific values handled in execute/pan_values_dict
        items=surround4_items, name="5.1 Surround Presets", description="Pan the audio", default='FRONTCENTER')

    surround71_items = surround4_items + (
        ('REARLEFT', 'Rear Left', 'Pan to the rear left'),
        ('REARRIGHT', 'Rear Right', 'Pan to the rear right'),
    )
    surround71: EnumProperty(
        items=surround71_items, name="7.1 Surround Presets", description="Pan the audio", default='FRONTCENTER')


    def set_pan_value(self, sequence, audio_channels_enum):
        preset_key = ""
        pan_dict_for_mode = {}

        if audio_channels_enum == 'STEREO':
            preset_key = self.stereo
            pan_dict_for_mode = self.pan_values_dict['STEREO']
        elif audio_channels_enum == 'SURROUND4':
            preset_key = self.surround4
            pan_dict_for_mode = self.pan_values_dict['SURROUND4']
        elif audio_channels_enum == 'SURROUND51':
            preset_key = self.surround51
            pan_dict_for_mode = self.pan_values_dict['SURROUND51']
        elif audio_channels_enum == 'SURROUND71':
            preset_key = self.surround71
            pan_dict_for_mode = self.pan_values_dict['SURROUND71']
        
        if preset_key and preset_key in pan_dict_for_mode:
             sequence.pan = pan_dict_for_mode[preset_key]
        else:
            print(f"Warning: Could not find pan value for preset '{preset_key}' in mode '{audio_channels_enum}'")


    def execute(self, context):
        audio_channels_enum = context.scene.render.ffmpeg.audio_channels
        
        target_sequences = []
        if context.selected_sequences:
            target_sequences = [seq for seq in context.selected_sequences if seq.type == 'SOUND']
        elif context.scene.sequence_editor.active_strip and \
             context.scene.sequence_editor.active_strip.type == 'SOUND':
             target_sequences = [context.scene.sequence_editor.active_strip]

        if not target_sequences:
             self.report({'WARNING'}, "No sound strip selected or active.")
             return {'CANCELLED'}

        sequences_processed = 0
        for sequence in target_sequences:
            if sequence.sound and sequence.sound.use_mono:
                self.set_pan_value(sequence, audio_channels_enum)
                if context.scene.tool_settings.use_keyframe_insert_auto:
                    try:
                        sequence.keyframe_insert(data_path="pan", frame=context.scene.frame_current)
                    except Exception as e:
                        print(f"Error inserting keyframe for pan: {e}")
                sequences_processed +=1
            elif sequence.sound and not sequence.sound.use_mono:
                print(f"Skipping '{sequence.name}': 'Process as Mono' is not enabled.")
            elif not sequence.sound:
                 print(f"Skipping '{sequence.name}': No sound data.")

        if sequences_processed == 0 and target_sequences:
            self.report({'INFO'}, "Selected sound strips are not set to 'Process as Mono'.")


        # Refresh the UI to show the change immediately
        # This can be tricky for sidebar panels, might need a more robust redraw call
        for area in context.screen.areas:
            if area.type == 'SEQUENCE_EDITOR':
                area.tag_redraw()
                break
        
        return {'FINISHED'}

# --- Panel Definition ---
class SEQUENCER_PT_adjust_sound(Panel):
    bl_idname = "SEQUENCER_PT_adjust_sound"
    bl_label = "Sound"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Strip" 

    @classmethod
    def poll(cls, context):
        strip = context.active_sequence_strip
        return strip and strip.type == 'SOUND'

    def draw(self, context):
        global custom_icons 

        layout = self.layout
        strip = context.active_sequence_strip
        scene = context.scene

        if not strip or strip.type != 'SOUND':
            layout.label(text="Select a Sound Strip")
            return

        sound = strip.sound
        if not sound:
             layout.label(text="Sound data not found for strip")
             return

        audio_channels_enum = scene.render.ffmpeg.audio_channels
        audio_channels_str_lower = audio_channels_enum.lower() 
        
        st = context.space_data # Sequencer space data
        overlay_settings = st.overlay if hasattr(st, 'overlay') else None

        main_col = layout.column()
        main_col.active = not strip.mute 
        main_col.use_property_split = True
        main_col.use_property_decorate = False # Usually False for custom UI for cleaner look

        main_col.prop(strip, "volume", text="Volume")

        if overlay_settings and hasattr(overlay_settings, 'waveform_display_type') and \
           overlay_settings.waveform_display_type != 'NONE': # Show if waveforms are potentially visible
            wave_col = main_col.column() # No heading needed, it's just one prop
            wave_col.prop(strip, "show_waveform", text="Show Waveform")

        main_col.separator()

        mono_col = main_col.column(heading="Channel Mode")
        mono_col.prop(sound, "use_mono", text="Process as Mono")

        if audio_channels_str_lower != 'mono':
            pan_box = main_col.box()
            pan_box.active = sound.use_mono 

            col = pan_box.column()

            try:
                audio_channels_prop_rna = scene.render.ffmpeg.bl_rna.properties["audio_channels"]
                lut = {i.identifier: i.name for i in audio_channels_prop_rna.enum_items}
                channel_display_str = lut.get(audio_channels_enum, audio_channels_enum) # Fallback to enum id
            except (AttributeError, KeyError):
                 channel_display_str = audio_channels_enum 

            cen_row = col.row()
            cen_row.scale_y = 0.9
            cen_row.alignment = 'CENTER'
            cen_row.label(text=f"Pan Presets ({channel_display_str})")
            
            current_pan_rounded = round(strip.pan, SequencerPanPresets.PAN_COMPARISON_PRECISION)

            def draw_pan_button(ui_layout, preset_enum_val, icon_base, mode_prop_name_in_op):
                """ Helper to draw a pan preset button with toggling icon and correct operator property. """
                pan_map_for_mode = SequencerPanPresets.pan_values_dict.get(audio_channels_enum)
                if not pan_map_for_mode:
                    ui_layout.label(text="ERR") # Mode not in dict
                    return

                target_pan_value = pan_map_for_mode.get(preset_enum_val)
                if target_pan_value is None:
                    # This can happen if surround51 uses 'SIDELEFT' but pan_values_dict['SURROUND51']
                    # doesn't have 'SIDELEFT'. Ensure enum items match keys in pan_values_dict.
                    # For 5.1, we might map 'SIDELEFT' from enum to a specific 5.1 key if different.
                    # For now, assume direct mapping.
                    ui_layout.label(text="?") # Preset not in dict for this mode
                    return

                is_selected = round(target_pan_value, SequencerPanPresets.PAN_COMPARISON_PRECISION) == current_pan_rounded
                
                icon_to_use = icon_base if is_selected else f"{icon_base}_outline"
                
                final_icon_id = 0 # Default to no icon if not found
                if custom_icons:
                    loaded_icon = custom_icons.get(icon_to_use)
                    if not loaded_icon: # Try fallback to base icon if outline is missing
                        loaded_icon = custom_icons.get(icon_base)
                    if loaded_icon:
                        final_icon_id = loaded_icon.icon_id
                
                op = ui_layout.operator(SequencerPanPresets.bl_idname, text="", emboss=False, icon_value=final_icon_id)
                setattr(op, mode_prop_name_in_op, preset_enum_val)


            grid = col.grid_flow(row_major=True, columns=3, even_columns=True, even_rows=False, align=True)
            grid.scale_y = 1.6 
            grid.scale_x = 1.1 

            if audio_channels_str_lower == 'stereo':
                draw_pan_button(grid, 'FRONTLEFT', "left_front", "stereo")
                draw_pan_button(grid, 'FRONTCENTER', "center_front", "stereo")
                draw_pan_button(grid, 'FRONTRIGHT', "right_front", "stereo")

            elif audio_channels_str_lower == 'surround4':
                draw_pan_button(grid, 'FRONTLEFT', "left_front", "surround4")
                grid.label(text="") 
                draw_pan_button(grid, 'FRONTRIGHT', "right_front", "surround4")
                draw_pan_button(grid, 'SIDELEFT', "left_rear", "surround4") 
                grid.label(text="")
                draw_pan_button(grid, 'SIDERIGHT', "right_rear", "surround4") 

            elif audio_channels_str_lower == 'surround51':
                # Using surround4 enum items for UI, mapped to surround51 values in operator
                draw_pan_button(grid, 'FRONTLEFT', "left_front", "surround51")
                draw_pan_button(grid, 'FRONTCENTER', "center_front", "surround51")
                draw_pan_button(grid, 'FRONTRIGHT', "right_front", "surround51")
                draw_pan_button(grid, 'SIDELEFT', "left_rear", "surround51") # Using 'SIDELEFT' enum item
                grid.label(text="") # LFE not panned
                draw_pan_button(grid, 'SIDERIGHT', "right_rear", "surround51") # Using 'SIDERIGHT' enum item

            elif audio_channels_str_lower == 'surround71':
                draw_pan_button(grid, 'FRONTLEFT', "left_front", "surround71")
                draw_pan_button(grid, 'FRONTCENTER', "center_front", "surround71")
                draw_pan_button(grid, 'FRONTRIGHT', "right_front", "surround71")
                draw_pan_button(grid, 'SIDELEFT', "left_side", "surround71")
                grid.label(text="") # Center surround (not typically panned by a single value)
                draw_pan_button(grid, 'SIDERIGHT', "right_side", "surround71")
                draw_pan_button(grid, 'REARLEFT', "left_rear", "surround71")
                grid.label(text="")
                draw_pan_button(grid, 'REARRIGHT', "right_rear", "surround71")


            pan_val_row = col.row(align=True)
            pan_val_row.alignment = 'CENTER'
            pan_degrees = strip.pan * 90
            pan_text_display = f"{strip.pan:.3f} ( {pan_degrees:.1f}° )"
            #pan_val_row.label(text=pan_text_display) 
            
            pan_slider_col = pan_box.column(align=True)
            pan_slider_col.prop(strip, "pan", text="", slider=True) # Explicit text for clarity


# --- Icon Handling ---
custom_icons = None 

def register_icons():
    global custom_icons
    if custom_icons: # Avoid re-registering
        return

    custom_icons = bpy.utils.previews.new()
    
    # Correctly get the addon's directory path, even if run from text editor
    addon_path = ""
    if __name__ == "__main__" and hasattr(bpy.context, 'space_data') and \
       hasattr(bpy.context.space_data, 'text') and bpy.context.space_data.text:
        filepath = bpy.context.space_data.text.filepath
        if filepath:
            addon_path = os.path.dirname(filepath)
    else: # If registered as an addon properly
        addon_path = os.path.dirname(__file__)

    if not addon_path:
        print(f"{bl_info['name']}: Could not determine addon path to load icons.")
        return

    icons_dir = os.path.join(addon_path, "icons")

    icon_definitions = [ # base_name
        "left_front", "right_front", "center_front",
        "left_side", "right_side",
        "left_rear", "right_rear"
    ]

    if not os.path.isdir(icons_dir):
         print(f"{bl_info['name']}: Icons directory not found: {icons_dir}")
         return

    for base_name in icon_definitions:
        # Load standard icon
        std_icon_path = os.path.join(icons_dir, f"{base_name}.png")
        if os.path.exists(std_icon_path):
            custom_icons.load(base_name, std_icon_path, 'IMAGE')
        else:
            print(f"{bl_info['name']}: Icon file not found: {std_icon_path}")

        # Load outline icon
        outline_icon_name = f"{base_name}_outline"
        outline_icon_path = os.path.join(icons_dir, f"{outline_icon_name}.png")
        if os.path.exists(outline_icon_path):
            custom_icons.load(outline_icon_name, outline_icon_path, 'IMAGE')
        else:
            # Only warn if the base icon existed, as outline is optional if base is missing
            if os.path.exists(std_icon_path):
                 print(f"{bl_info['name']}: Outline icon file not found: {outline_icon_path}")


def unregister_icons():
    global custom_icons
    if custom_icons:
        bpy.utils.previews.remove(custom_icons)
    custom_icons = None

# --- Registration ---
classes = (
    SequencerPanPresets,
    SEQUENCER_PT_adjust_sound,
)

def register():
    # Ensure __file__ is set for icon path resolution if running from text editor
    # This check might be redundant if addon_path logic in register_icons is robust
    if __name__ == "__main__" and not hasattr(sys.modules[__name__], '__file__'):
        if bpy.context.space_data and hasattr(bpy.context.space_data, 'text') and bpy.context.space_data.text:
            fpath = bpy.context.space_data.text.filepath
            if fpath:
                globals()['__file__'] = fpath


    register_icons()
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    unregister_icons()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

# --- Main Execution (for running from text editor) ---
if __name__ == "__main__":
    # Clean previous registration if any
    # Use a try-except block for safety during development
    current_module_name = os.path.splitext(os.path.basename(__file__))[0]
    if current_module_name in bpy.context.preferences.addons:
        print(f"Unregistering existing version of '{bl_info['name']}'")
        bpy.ops.preferences.addon_disable(module=current_module_name)
        bpy.ops.preferences.addon_remove(module=current_module_name)
        
    # This simple unregister call might fail if classes/icons were not loaded correctly before
    # For robust re-registration, directly calling unregister() is common.
    try:
        unregister()
    except Exception: # Catch if it was never registered or parts are missing
        pass
        
    register()

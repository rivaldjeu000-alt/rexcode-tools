from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.lang import Builder
from kivy.clock import Clock

import os
import sys
import json
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))
from decoder import decode_full
from encoder import encode_full
from editor import (
    set_stat, read_stats, read_currency, read_resource,
    STATS_VARS, CURRENCY_VARS, RESOURCE_VARS
)

Window.clearcolor = get_color_from_hex('#0A0A0F')

CONFIG_PATH = '/storage/emulated/0/RexCodeTools/config.json'
DEFAULT_PATH = '/data/data/com.playrix.township/saves/mGameInfo.xml'


class RexRoot(BoxLayout):
    pass


class RexCodeTools(App):
    current_xml = None
    current_path = None
    current_tab = 'stats'
    config = {'path': DEFAULT_PATH, 'backup': True, 'lang': 'auto'}

    def build(self):
        self.title = 'RexCode Tools'
        self.load_config()
        return Builder.load_file(os.path.join(os.path.dirname(__file__), 'rexcode.kv'))

    def load_config(self):
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r') as f:
                    self.config.update(json.load(f))
        except:
            pass

    def save_config(self):
        try:
            with open(CONFIG_PATH, 'w') as f:
                json.dump(self.config, f, indent=2)
        except:
            pass

    def log(self, msg):
        def update(dt):
            lbl = self.root.ids.log_label
            lbl.text += f'\n> {msg}'
        Clock.schedule_once(update)

    def pilih_file(self):
        content = BoxLayout(orientation='vertical')
        filechooser = FileChooserListView(path='/storage/emulated/0', filters=['*.xml'])
        content.add_widget(filechooser)

        btn_layout = BoxLayout(size_hint_y=0.15, spacing=5)
        btn_pilih = Button(text='PILIH', background_color=get_color_from_hex('#FF1744'))
        btn_batal = Button(text='BATAL', background_color=get_color_from_hex('#7B1FA2'))
        btn_layout.add_widget(btn_pilih)
        btn_layout.add_widget(btn_batal)
        content.add_widget(btn_layout)

        popup = Popup(title='Pilih File mGameInfo.xml', content=content, size_hint=(0.95, 0.95))

        def on_pilih(instance):
            if filechooser.selection:
                self.current_path = filechooser.selection[0]
                popup.dismiss()
                self.proses_decode()

        btn_pilih.bind(on_press=on_pilih)
        btn_batal.bind(on_press=popup.dismiss)
        popup.open()

    def proses_decode(self):
        try:
            with open(self.current_path, 'rb') as f:
                raw = f.read()
            self.current_xml = decode_full(raw).decode('utf-8', errors='replace')

            self.root.ids.status_label.text = 'READY'
            self.root.ids.btn_decode.text = '2. DONE'
            self.root.ids.btn_decode.background_color = get_color_from_hex('#00E5FF')
            self.root.ids.btn_decode.color = get_color_from_hex('#000000')
            self.root.ids.btn_encode.disabled = False
            self.root.ids.btn_encode.background_color = get_color_from_hex('#FF1744')
            self.root.ids.btn_encode.color = get_color_from_hex('#FFFFFF')

            self.log(f'File: {os.path.basename(self.current_path)}')
            self.log(f'Decoded: {len(self.current_xml)} chars')
            self.log('Statistik dimuat, siap edit!')

            self.render_tab()
        except Exception as e:
            self.log(f'ERROR: {e}')

    def switch_tab(self, tab):
        self.current_tab = tab
        self.render_tab()

    def render_tab(self):
        if not self.current_xml:
            return

        content = self.root.ids.content_box
        content.clear_widgets()

        if self.current_tab == 'stats':
            data = read_stats(self.current_xml)
            vars_map = STATS_VARS
        elif self.current_tab == 'currency':
            data = read_currency(self.current_xml)
            vars_map = CURRENCY_VARS
        elif self.current_tab == 'resource':
            data = read_resource(self.current_xml)
            vars_map = RESOURCE_VARS
        else:
            return

        for label, var_name in vars_map.items():
            row = BoxLayout(size_hint_y=None, height='55dp', spacing=5)

            lbl = Label(
                text=f'{label}\n(current: {data.get(label, "0")})',
                font_size='10sp',
                color=get_color_from_hex('#B0B0C0'),
                halign='left',
                size_hint_x=0.4
            )
            row.add_widget(lbl)

            inp = TextInput(
                text='',
                hint_text=data.get(label, '0'),
                multiline=False,
                font_size='14sp',
                background_color=get_color_from_hex('#1A0B1F'),
                foreground_color=get_color_from_hex('#FFFFFF'),
                cursor_color=get_color_from_hex('#FF1744'),
                size_hint_x=0.4
            )
            inp.varname = var_name
            row.add_widget(inp)

            btn = Button(
                text='APPLY',
                font_size='10sp',
                background_normal='',
                background_color=get_color_from_hex('#FF1744'),
                size_hint_x=0.2
            )

            def make_apply(v, i):
                def on_apply(inst):
                    if i.text:
                        self.current_xml, ok, msg = set_stat(self.current_xml, v, i.text)
                        self.log(msg)
                        i.text = ''
                        self.render_tab()
                return on_apply

            btn.bind(on_press=make_apply(var_name, inp))
            row.add_widget(btn)

            content.add_widget(row)

    def proses_save(self):
        if not self.current_xml:
            self.log('Belum ada data!')
            return

        try:
            encoded = encode_full(self.current_xml.encode('utf-8'), use_lz4=True)
            out_path = self.current_path.replace('.xml', '_edited.xml')

            if self.config.get('backup'):
                shutil.copy(self.current_path, self.current_path + '.bak')
                self.log('Backup dibuat')

            with open(out_path, 'wb') as f:
                f.write(encoded)

            self.log(f'Saved: {os.path.basename(out_path)}')
            self.log(f'Size: {len(encoded)} bytes')
        except Exception as e:
            self.log(f'ERROR save: {e}')

    def buka_settings(self):
        self.log('Buka Settings (belum diimplementasi)')


if __name__ == '__main__':
    RexCodeTools().run()

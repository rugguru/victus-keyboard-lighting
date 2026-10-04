#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Victus RGB color bridge; brightness remains managed by UPower/PowerDevil."""
import os
import re
import json
import logging
import time
from pathlib import Path
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

IFACE = 'org.local.VictusKeyboard'
LED = Path('/sys/class/leds/hp::kbd_backlight')
STATE = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config'))) / 'victus-keyboard/color'
BRIGHTNESS_STATE = STATE.with_name('brightness.json')
PRESETS_STATE = STATE.with_name('presets.json')
DEFAULT_PRESETS = ['#ffffff', '#ff3030', '#ff9600', '#fff030', '#30e050', '#30dfff', '#3060ff', '#ad40ff', '#ff40b0']
GATE_STATE = Path('/sys/devices/platform/hp-wmi/keyboard_backlight_state')
HARDWARE_OFF = 'Klavye donanım tarafından kapalı kaldı. Fn + F4 ile açılması gerekiyor.'
logging.basicConfig(level=logging.INFO, format='%(message)s')

class Keyboard(dbus.service.Object):
    def __init__(self, bus):
        super().__init__(bus, '/org/local/VictusKeyboard')
        self.error = ''
        self.presets = self.load_presets()
        self.previous = None
        self.restored_identity = None
        self.cached_brightness = None
        self.sleeping = False
        self.gate_retry_after = 0
        self.system_bus = dbus.SystemBus()
        self.system_bus.add_signal_receiver(self.prepare_sleep, signal_name='PrepareForSleep', dbus_interface='org.freedesktop.login1.Manager', path='/org/freedesktop/login1')
        self.system_bus.add_signal_receiver(self.brightness_changed, signal_name='BrightnessChanged', dbus_interface='org.freedesktop.UPower.KbdBacklight', path='/org/freedesktop/UPower/KbdBacklight')
        GLib.timeout_add_seconds(2, self.poll)
        self.poll()

    @staticmethod
    def validate_presets(values):
        if not isinstance(values, (list, tuple)) or len(values) != len(DEFAULT_PRESETS):
            raise ValueError('Dokuz hazır renk kodu girilmeli.')
        result = [str(value).lower() for value in values]
        if not all(re.fullmatch(r'#[0-9a-f]{6}', value) for value in result):
            raise ValueError('Renk kodları #RRGGBB biçiminde olmalı.')
        return result

    @staticmethod
    def load_presets():
        try:
            return Keyboard.validate_presets(json.loads(PRESETS_STATE.read_text()))
        except (OSError, ValueError, TypeError):
            return DEFAULT_PRESETS.copy()

    def properties(self):
        available = (LED/'multi_intensity').is_file() and os.access(LED/'multi_intensity', os.W_OK)
        color = '#ffffff'
        try:
            channels = dict(zip((LED/'multi_index').read_text().split(), map(int, (LED/'multi_intensity').read_text().split())))
            color = '#{:02x}{:02x}{:02x}'.format(*(channels[c] for c in ('red','green','blue')))
        except (OSError, ValueError, KeyError):
            pass
        brightness = maximum = 0
        try:
            brightness = int((LED/'brightness').read_text())
            maximum = int((LED/'max_brightness').read_text())
        except (OSError, ValueError):
            pass
        return {'Available': dbus.Boolean(available), 'Color': dbus.String(color), 'Error': dbus.String(self.error),
                'Brightness': dbus.Int32(brightness), 'MaximumBrightness': dbus.Int32(maximum),
                'Presets': dbus.Array(getattr(self, 'presets', DEFAULT_PRESETS), signature='s')}

    def identity(self):
        stat = (LED/'multi_intensity').stat()
        return (stat.st_dev, stat.st_ino)

    def publish(self):
        props = self.properties()
        if props != self.previous:
            self.previous = props
            self.PropertiesChanged(IFACE, props, [])

    def save_brightness(self, value):
        value = int(value)
        if value == self.cached_brightness:
            return
        BRIGHTNESS_STATE.parent.mkdir(parents=True, exist_ok=True)
        tmp = BRIGHTNESS_STATE.with_suffix('.tmp')
        tmp.write_text(json.dumps({'brightness': value})+'\n')
        tmp.replace(BRIGHTNESS_STATE)
        self.cached_brightness = value

    def set_brightness(self, value):
        obj = self.system_bus.get_object('org.freedesktop.UPower', '/org/freedesktop/UPower/KbdBacklight')
        api = dbus.Interface(obj, 'org.freedesktop.UPower.KbdBacklight')
        if int(api.GetMaxBrightness()) <= 0:
            raise OSError('UPower klavye sürücüsünün hazır olmasını bekliyor.')
        api.SetBrightness(int(value))

    def verify_brightness(self, value):
        # LED sysfs queues a blocking driver callback; UPower returning does
        # not mean that the firmware gate has opened yet.
        deadline = time.monotonic() + 0.6
        while True:
            level = int((LED/'brightness').read_text())
            try:
                enabled = bool(int(GATE_STATE.read_text()) & 0x80)
            except (OSError, ValueError):
                enabled = None
            if level == value and (value == 0 or enabled is not False):
                return
            if time.monotonic() >= deadline:
                if value > 0 and enabled is False:
                    raise OSError(HARDWARE_OFF)
                raise OSError('Klavye parlaklığı uygulanamadı; yeniden deneyin.')
            time.sleep(0.03)

    def prepare_sleep(self, sleeping):
        if sleeping:
            self.poll()
        self.sleeping = bool(sleeping)
        if not sleeping:
            self.restored_identity = None
            self.poll()

    def brightness_changed(self, value):
        if self.sleeping:
            return
        try:
            if self.restored_identity == self.identity():
                self.save_brightness(value)
        except (OSError, ValueError):
            pass

    def poll(self):
        if self.sleeping:
            return True
        try:
            if not self.properties()['Available']:
                self.restored_identity = None
            else:
                identity = self.identity()
                if identity != self.restored_identity:
                    desired = self.cached_brightness
                    if desired is None and BRIGHTNESS_STATE.is_file():
                        desired = int(json.loads(BRIGHTNESS_STATE.read_text())['brightness'])
                    if desired is not None:
                        maximum = int((LED/'max_brightness').read_text())
                        self.set_brightness(max(0,min(desired,maximum)))
                    if STATE.is_file():
                        self.apply(STATE.read_text().strip(), save=False, notify=False)
                    # Mark restoration complete only after every write succeeded.
                    self.restored_identity = identity
                    self.error = ''
                self.save_brightness(int((LED/'brightness').read_text()))
                # Keep a failed write visible; a routine timer must not
                # erase it just because the device still exists.
                if self.error == HARDWARE_OFF:
                    try:
                        if int(GATE_STATE.read_text()) & 0x80:
                            self.error = ''
                    except (OSError, ValueError):
                        pass
        except (OSError, ValueError, KeyError, dbus.DBusException) as exc:
            self.error = str(exc)
        self.publish()
        return True

    def apply(self, color, save=True, notify=True):
        if not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
            raise dbus.DBusException('Renk #RRGGBB biçiminde olmalı.', name=IFACE+'.InvalidColor')
        if not self.properties()['Available']:
            raise dbus.DBusException('Klavye renk kontrolüne erişilemiyor.', name=IFACE+'.Unavailable')
        channels = dict(zip(('red','green','blue'), (int(color[i:i+2],16) for i in (1,3,5))))
        order = (LED/'multi_index').read_text().split()
        if sorted(order) != ['blue','green','red']:
            raise dbus.DBusException('Beklenmeyen LED renk kanalları.', name=IFACE+'.UnsupportedChannels')
        try:
            (LED/'multi_intensity').write_text(' '.join(str(channels[c]) for c in order)+'\n')
            if save:
                STATE.parent.mkdir(parents=True,exist_ok=True)
                tmp = STATE.with_suffix('.tmp')
                tmp.write_text(color.lower()+'\n')
                tmp.replace(STATE)
            self.error = ''
        except OSError as exc:
            self.error = str(exc)
            raise dbus.DBusException(str(exc),name=IFACE+'.WriteFailed') from exc
        if notify:
            self.publish()

    @dbus.service.method('org.freedesktop.DBus.Introspectable',in_signature='',out_signature='s',path_keyword='object_path',connection_keyword='connection')
    def Introspect(self,object_path,connection):
        xml = super().Introspect(object_path,connection)
        marker = '<interface name="'+IFACE+'">'
        props = '<property name="Brightness" type="i" access="read"/><property name="MaximumBrightness" type="i" access="read"/><property name="Available" type="b" access="read"/><property name="Color" type="s" access="read"/><property name="Error" type="s" access="read"/><property name="Presets" type="as" access="read"/>'
        return xml.replace(marker, marker+props)

    @dbus.service.method(IFACE,in_signature='i',out_signature='')
    def SetBrightness(self, value):
        maximum = int(self.properties()['MaximumBrightness'])
        if maximum <= 0 or not self.properties()['Available']:
            raise dbus.DBusException('Klavye ışığına erişilemiyor.', name=IFACE+'.Unavailable')
        value = int(value)
        if not 0 <= value <= maximum:
            raise dbus.DBusException('Geçersiz klavye parlaklığı.', name=IFACE+'.InvalidBrightness')
        try:
            if value > 0 and time.monotonic() < getattr(self, 'gate_retry_after', 0):
                try:
                    closed = not (int(GATE_STATE.read_text()) & 0x80)
                except (OSError, ValueError):
                    closed = False
                if closed:
                    raise OSError(HARDWARE_OFF)
            logging.info('Parlaklık isteği: %d; mevcut=%d; renk=%s', value,
                         int(self.properties()['Brightness']), self.properties()['Color'])
            self.set_brightness(value)
            self.verify_brightness(value)
            self.save_brightness(value)
            self.error = ''
            self.publish()
            try:
                gate = GATE_STATE.read_text().strip()
            except OSError:
                gate = 'bilinmiyor'
            logging.info('Parlaklık sonucu: %d; BIOS=%s', int(self.properties()['Brightness']), gate)
        except (OSError, dbus.DBusException) as exc:
            if str(exc) == HARDWARE_OFF:
                self.gate_retry_after = time.monotonic() + 1
            self.error = str(exc)
            logging.warning('Parlaklık uygulanamadı: %s', self.error)
            self.publish()
            raise dbus.DBusException(str(exc), name=IFACE+'.BrightnessFailed') from exc

    @dbus.service.method(IFACE,in_signature='s',out_signature='')
    def SetColor(self,color):
        self.apply(str(color))

    @dbus.service.method(IFACE, in_signature='s', out_signature='')
    def SetPresets(self, presets_json):
        try:
            normalized = self.validate_presets(json.loads(str(presets_json)))
            PRESETS_STATE.parent.mkdir(parents=True, exist_ok=True)
            temporary = PRESETS_STATE.with_suffix('.tmp')
            temporary.write_text(json.dumps(normalized)+'\n')
            temporary.replace(PRESETS_STATE)
        except (ValueError, OSError) as exc:
            raise dbus.DBusException(str(exc), name=IFACE+'.InvalidPresets') from exc
        self.presets = normalized
        self.publish()

    @dbus.service.method('org.freedesktop.DBus.Properties',in_signature='s',out_signature='a{sv}')
    def GetAll(self,iface):
        if iface != IFACE:
            raise dbus.DBusException('Bilinmeyen arayüz.',name=IFACE+'.InvalidInterface')
        return self.properties()

    @dbus.service.method('org.freedesktop.DBus.Properties',in_signature='ss',out_signature='v')
    def Get(self,iface,name):
        return self.GetAll(iface)[name]

    @dbus.service.signal('org.freedesktop.DBus.Properties',signature='sa{sv}as')
    def PropertiesChanged(self,iface,props,invalidated):
        pass

def main():
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    name = dbus.service.BusName(IFACE,bus=bus,do_not_queue=True)
    keyboard = Keyboard(bus)
    GLib.MainLoop().run()

if __name__ == '__main__':
    main()

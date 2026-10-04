# SPDX-License-Identifier: GPL-2.0-or-later
import importlib.util,json,tempfile
from pathlib import Path
spec=importlib.util.spec_from_file_location('rgb',Path(__file__).resolve().parents[1] / 'service/keyboard-service.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def make_led():
 m.LED.mkdir(exist_ok=True)
 for n,v in {'multi_index':'red green blue','multi_intensity':'255 255 255','brightness':'255','max_brightness':'255'}.items():(m.LED/n).write_text(v+'\n')

def keyboard():
 k=m.Keyboard.__new__(m.Keyboard)
 k.error='';k.previous=None;k.restored_identity=None;k.cached_brightness=None;k.sleeping=False
 k.PropertiesChanged=lambda *args:None
 k.set_brightness=lambda v:(m.LED/'brightness').write_text(str(v)+'\n')
 return k

with tempfile.TemporaryDirectory() as d:
 m.LED=Path(d)/'led';m.STATE=Path(d)/'prefs/color';m.BRIGHTNESS_STATE=m.STATE.with_name('brightness.json')
 make_led();k=keyboard();k.poll();k.apply('#3060ff');k.save_brightness(77)
 (m.LED/'brightness').write_text('77\n')
 # Fast recreation: no intermediate poll sees an unavailable device.
 old=m.LED/'multi_intensity';replacement=m.LED/'replacement';replacement.write_text('255 255 255\n');replacement.replace(old)
 (m.LED/'brightness').write_text('255\n');k.poll()
 assert old.read_text().strip()=='48 96 255'
 assert (m.LED/'brightness').read_text().strip()=='77'
 print('Fast device recreation restores saved color/brightness: PASS')
 # A failed write must leave the restoration pending, then retry.
 replacement.write_text('255 255 255\n');replacement.replace(old)
 setter=k.set_brightness
 def fail(v):raise OSError('UPower not ready')
 k.set_brightness=fail;k.poll();assert k.error and k.identity()!=k.restored_identity
 k.set_brightness=setter;k.poll();assert not k.error and k.identity()==k.restored_identity
 print('Delayed UPower availability and restoration retry: PASS')
 # Restart and resume honor off instead of turning the keyboard on.
 k.save_brightness(0);(m.LED/'brightness').write_text('0\n')
 k=keyboard();k.poll();assert (m.LED/'brightness').read_text().strip()=='0'
 k.prepare_sleep(True)
 old.write_text('255 255 255\n');(m.LED/'brightness').write_text('255\n')
 k.prepare_sleep(False)
 assert old.read_text().strip()=='48 96 255' and (m.LED/'brightness').read_text().strip()=='0'
 print('Service restart and resume preserve color and off state: PASS')
 # Unavailable device returns later.
 old.unlink();k.poll();assert k.restored_identity is None
 old.write_text('255 255 255\n');k.poll();assert old.read_text().strip()=='48 96 255'
 print('Device disappearance/reappearance: PASS')

# SPDX-License-Identifier: GPL-2.0-or-later
import importlib.util, tempfile
from pathlib import Path
spec=importlib.util.spec_from_file_location('rgb',Path(__file__).resolve().parents[1] / 'service/keyboard-service.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
# Use a virtual monotonic clock; firmware can acknowledge without opening.
tick=[0.0]
def now():tick[0]+=0.04;return tick[0]
m.time.monotonic=now;m.time.sleep=lambda t:None
with tempfile.TemporaryDirectory() as tmp:
 m.LED=Path(tmp)/'led';m.LED.mkdir();m.GATE_STATE=Path(tmp)/'gate'
 m.STATE=Path(tmp)/'prefs/color';m.BRIGHTNESS_STATE=m.STATE.with_name('brightness.json')
 for n,v in {'multi_index':'red green blue','multi_intensity':'255 255 255','brightness':'0','max_brightness':'255'}.items():(m.LED/n).write_text(v)
 k=m.Keyboard.__new__(m.Keyboard);k.error='';k.cached_brightness=None;k.gate_retry_after=0;k.publish=lambda:None
 calls=[]
 def setter(v):calls.append(v);(m.LED/'brightness').write_text(str(v))
 k.set_brightness=setter;m.GATE_STATE.write_text('100')
 try:k.SetBrightness(255)
 except m.dbus.DBusException as e:assert e.get_dbus_name()==m.IFACE+'.BrightnessFailed'
 else:raise AssertionError('Acknowledged but closed firmware was reported as success')
 assert k.error==m.HARDWARE_OFF
 before=len(calls)
 try:k.SetBrightness(200)
 except m.dbus.DBusException:pass
 assert len(calls)==before,'Continuous drag retried failing hardware too rapidly'
 m.GATE_STATE.write_text('228');k.SetBrightness(200)
 assert not k.error and int((m.LED/'brightness').read_text())==200
 m.GATE_STATE.write_text('100');k.SetBrightness(0);assert not k.error
 # Simulate the queued kernel callback completing after several reads.
 (m.LED/'brightness').write_text('0');m.GATE_STATE.write_text('228')
 old=now;started=[0]
 def delayed():
  started[0]+=1
  if started[0]==4:(m.LED/'brightness').write_text('80')
  return old()
 m.time.monotonic=delayed;k.verify_brightness(80)
print('Closed firmware is detected; drag requests bounded; Fn-on recovers; zero accepted; queued callback awaited: PASS')

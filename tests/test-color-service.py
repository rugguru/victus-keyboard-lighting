# SPDX-License-Identifier: GPL-2.0-or-later
import importlib.util, tempfile
from pathlib import Path
spec=importlib.util.spec_from_file_location('rgb',Path(__file__).resolve().parents[1] / 'service/keyboard-service.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
    m.LED=Path(d)/'led';m.LED.mkdir()
    m.STATE=Path(d)/'saved/color'
    (m.LED/'multi_index').write_text('green blue red\n')
    (m.LED/'multi_intensity').write_text('255 255 255\n')
    obj=m.Keyboard.__new__(m.Keyboard);obj.error='';obj.publish=lambda: None
    obj.apply('#3060ff')
    assert (m.LED/'multi_intensity').read_text()=='96 255 48\n'
    assert obj.properties()['Color']=='#3060ff'
    assert m.STATE.read_text()=='#3060ff\n'
    for invalid in ['red','#fff','#12345678','#gg0000','../../file','255 0 0']:
        try:obj.apply(invalid)
        except m.dbus.DBusException:pass
        else:raise AssertionError(invalid)
    (m.LED/'multi_index').write_text('red white blue\n')
    try:obj.apply('#ffffff')
    except m.dbus.DBusException:pass
    else:raise AssertionError('unsupported channels accepted')
    (m.LED/'multi_intensity').unlink()
    try:obj.apply('#ffffff')
    except m.dbus.DBusException:pass
    else:raise AssertionError('unavailable device accepted')
print('Color channel ordering, save/read, malformed input, unsupported channels and unavailable device: PASS')

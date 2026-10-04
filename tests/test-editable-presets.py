# SPDX-License-Identifier: GPL-2.0-or-later
import importlib.util,json,tempfile
from pathlib import Path
spec=importlib.util.spec_from_file_location('rgb',Path(__file__).resolve().parents[1] / 'service/keyboard-service.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as tmp:
    m.PRESETS_STATE=Path(tmp)/'prefs/presets.json'
    assert m.Keyboard.load_presets()==m.DEFAULT_PRESETS
    obj=m.Keyboard.__new__(m.Keyboard)
    obj.presets=m.DEFAULT_PRESETS.copy()
    published=[]
    obj.publish=lambda:published.append(obj.presets.copy())
    changed=m.DEFAULT_PRESETS.copy();changed[0]='#AABBCC'
    obj.SetPresets(json.dumps(changed))
    assert obj.presets[0]=='#aabbcc'
    assert m.Keyboard.load_presets()==obj.presets
    original=m.PRESETS_STATE.read_bytes()
    for invalid in ['{',json.dumps(['#ffffff']),json.dumps([None]*9),json.dumps(['#fff']*9),json.dumps(['#xyz123']*9),json.dumps({'0':'#ffffff'}),json.dumps('not a list')]:
        try:obj.SetPresets(invalid)
        except m.dbus.DBusException:pass
        else:raise AssertionError(invalid)
        assert m.PRESETS_STATE.read_bytes()==original
        assert obj.presets==published[-1]
    assert not m.PRESETS_STATE.with_suffix('.tmp').exists()
    m.PRESETS_STATE.write_text('bad file')
    assert m.Keyboard.load_presets()==m.DEFAULT_PRESETS
print('Preset validation, uppercase normalization, atomic persistence, restart load and malformed input: PASS')

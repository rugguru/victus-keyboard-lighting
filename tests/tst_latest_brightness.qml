import QtQuick
import QtTest
import "../applet/contents/ui" as Victus
TestCase {
    id: test
    name: "LatestKeyboardBrightness"
    property var calls: []
    QtObject { id: bridge; property var properties: ({Available: true, Brightness: 42, MaximumBrightness: 255}) }
    Victus.VictusKeyboardBrightnessControl {
        id: control
        bridge: bridge
        sendRequest: (value, success, failure) => test.calls.push({value: value, success: success, failure: failure})
    }
    function init() {
        calls = [];
        control.busy = false;
        control.pendingValue = -1;
        control.requestedValue = -1;
        control.error = "";
        bridge.properties = {Available: true, Brightness: 42, MaximumBrightness: 255};
    }
    function acknowledge(index) {
        bridge.properties = {Available: true, Brightness: calls[index].value, MaximumBrightness: 255};
        calls[index].success();
    }
    function test_fast_drag_keeps_latest() {
        control.setBrightness(10);
        for (let i = 0; i < 1000; ++i)
            control.setBrightness(i % 256);
        compare(calls.length, 1);
        compare(control.brightness, 999 % 256);
        acknowledge(0);
        compare(calls.length, 2);
        compare(calls[1].value, 999 % 256);
        compare(control.brightness, 999 % 256);
        acknowledge(1);
        compare(control.busy, false);
        compare(control.requestedValue, -1);
        compare(control.brightness, 999 % 256);
    }
    function test_delayed_properties_do_not_rewind_handle() {
        control.setBrightness(10);
        control.setBrightness(200);
        calls[0].success();
        compare(calls.length, 2);
        bridge.properties = {Available: true, Brightness: 10, MaximumBrightness: 255};
        compare(control.brightness, 200);
        calls[1].success();
        compare(control.brightness, 200);
        bridge.properties = {Available: true, Brightness: 200, MaximumBrightness: 255};
        compare(control.requestedValue, -1);
        bridge.properties = {Available: true, Brightness: 0, MaximumBrightness: 255};
        compare(control.brightness, 0);
    }
    function test_duplicate_pending_value_not_replayed() {
        control.setBrightness(255);
        control.setBrightness(255);
        acknowledge(0);
        compare(calls.length, 1);
        compare(control.busy, false);
    }
    function test_error_and_recovery() {
        control.setBrightness(100);
        control.setBrightness(200);
        calls[0].failure({message: "hardware failure"});
        compare(control.brightness, 42);
        compare(control.error, "hardware failure");
        compare(control.pendingValue, -1);
        control.setBrightness(255);
        acknowledge(1);
        compare(control.error, "");
        compare(control.brightness, 255);
    }
    function test_range_and_unavailable() {
        control.setBrightness(300.2);
        compare(calls[0].value, 255);
        acknowledge(0);
        control.setBrightness(-20);
        compare(calls[1].value, 0);
        acknowledge(1);
        bridge.properties = {Available: false, Brightness: 0, MaximumBrightness: 255};
        control.setBrightness(255);
        compare(calls.length, 2);
    }
}

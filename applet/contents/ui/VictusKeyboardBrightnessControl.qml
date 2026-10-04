// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import org.kde.plasma.workspace.dbus as DBus

QtObject {
    id: root
    required property QtObject bridge
    readonly property bool isBrightnessAvailable: Boolean(bridge.properties.Available)
    readonly property int hardwareBrightness: Number(bridge.properties.Brightness || 0)
    readonly property int brightnessMax: Number(bridge.properties.MaximumBrightness || 0)
    readonly property int brightness: requestedValue >= 0 ? requestedValue : hardwareBrightness
    property string error: ""
    property int requestedValue: -1
    property int pendingValue: -1
    property bool busy: false

    // One hardware command at a time. Dragging replaces the waiting value,
    // so old slider positions cannot build up into a delayed brightness ramp.
    property var sendRequest: function(value, success, failure) {
        DBus.SessionBus.asyncCall({service: "org.local.VictusKeyboard", path: "/org/local/VictusKeyboard",
            iface: "org.local.VictusKeyboard", member: "SetBrightness",
            arguments: [new DBus.int32(value)]}, success, failure);
    }

    function setBrightness(value) {
        if (!isBrightnessAvailable || brightnessMax <= 0)
            return;
        const rounded = Math.max(0, Math.min(brightnessMax, Math.round(value)));
        requestedValue = rounded;
        pendingValue = rounded;
        if (!busy)
            dispatch();
    }

    function dispatch() {
        const value = pendingValue;
        pendingValue = -1;
        busy = true;
        sendRequest(value, () => {
            busy = false;
            error = "";
            if (pendingValue >= 0 && pendingValue !== value) {
                dispatch();
            } else {
                pendingValue = -1;
                if (hardwareBrightness === requestedValue)
                    requestedValue = -1;
            }
        }, failure => {
            busy = false;
            pendingValue = -1;
            requestedValue = -1;
            error = failure.message;
        });
    }

    onHardwareBrightnessChanged: {
        if (!busy && pendingValue < 0 && hardwareBrightness === requestedValue)
            requestedValue = -1;
    }
}

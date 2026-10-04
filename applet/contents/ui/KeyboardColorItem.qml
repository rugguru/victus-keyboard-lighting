// SPDX-License-Identifier: GPL-2.0-or-later
pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import QtQuick.Dialogs
import QtQuick.Controls as QQC2
import org.kde.plasma.components as PlasmaComponents3
import org.kde.kirigami as Kirigami
import org.kde.plasma.workspace.dbus as DBus

PlasmaComponents3.ItemDelegate {
    id: root
    background.visible: highlighted
    hoverEnabled: false
    property string failure: ""
    readonly property bool available: Boolean(bridge.properties.Available)
    readonly property color currentColor: String(bridge.properties.Color || "#ffffff")
    readonly property var defaultPresets: ["#ffffff", "#ff3030", "#ff9600", "#fff030", "#30e050", "#30dfff", "#3060ff", "#ad40ff", "#ff40b0"]
    readonly property var presets: bridge.properties.Presets || defaultPresets
    property var draftPresets: []
    property bool savingPresets: false
    readonly property bool draftValid: draftPresets.length === 9 && draftPresets.every(value => /^#[0-9a-fA-F]{6}$/.test(value))
    visible: available

    DBus.Properties {
        id: bridge
        busType: DBus.BusType.Session
        service: "org.local.VictusKeyboard"
        path: "/org/local/VictusKeyboard"
        iface: "org.local.VictusKeyboard"
    }
    function applyColor(color) {
        const hex = String(color).slice(0, 7);
        DBus.SessionBus.asyncCall({service: "org.local.VictusKeyboard", path: "/org/local/VictusKeyboard",
            iface: "org.local.VictusKeyboard", member: "SetColor", arguments: [hex]},
            () => root.failure = "", error => root.failure = error.message);
    }
    function setDraft(index, value) {
        const copy = draftPresets.slice();
        copy[index] = value;
        draftPresets = copy;
    }
    function resetDraft(values) {
        draftPresets = Array.from(values);
        for (let i = 0; i < presetFields.count; ++i) {
            const row = presetFields.itemAt(i);
            if (row)
                row.field.text = draftPresets[i];
        }
    }
    function savePresets() {
        if (!draftValid || savingPresets)
            return;
        savingPresets = true;
        DBus.SessionBus.asyncCall({service: "org.local.VictusKeyboard", path: "/org/local/VictusKeyboard",
            iface: "org.local.VictusKeyboard", member: "SetPresets", arguments: [JSON.stringify(draftPresets)]},
            () => { root.savingPresets = false; root.failure = ""; presetEditor.close(); },
            error => { root.savingPresets = false; root.failure = error.message; });
    }
    PlasmaComponents3.Dialog {
        id: presetEditor
        objectName: "victusPresetEditor"
        parent: QQC2.Overlay.overlay
        anchors.centerIn: parent
        width: Math.min(440, parent ? parent.width - 24 : 440)
        implicitHeight: contentItem.implicitHeight + footer.implicitHeight + topPadding + bottomPadding
        title: "Hazır klavye renklerini düzenle"
        modal: true
        Kirigami.Theme.inherit: false
        Kirigami.Theme.textColor: root.Kirigami.Theme.textColor
        Kirigami.Theme.backgroundColor: root.Kirigami.Theme.backgroundColor
        contentItem: ColumnLayout {
            PlasmaComponents3.Label {
                text: presetEditor.title
                font.bold: true
                color: root.Kirigami.Theme.textColor
                Layout.fillWidth: true
            }
            PlasmaComponents3.Label {
                text: "Dokuz renk kodunu değiştirebilirsin. Kaydetmek klavyenin seçili rengini değiştirmez."
                color: root.Kirigami.Theme.textColor
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
            Repeater {
                id: presetFields
                model: 9
                delegate: RowLayout {
                    id: presetRow
                    required property int index
                    property alias field: presetField
                    Layout.fillWidth: true
                    Rectangle {
                        implicitWidth: 20; implicitHeight: 20; radius: 10
                        color: /^#[0-9a-fA-F]{6}$/.test(root.draftPresets[presetRow.index] || "") ? root.draftPresets[presetRow.index] : "transparent"
                        border.color: Kirigami.Theme.textColor
                    }
                    PlasmaComponents3.Label { text: "Renk " + (presetRow.index + 1); color: root.Kirigami.Theme.textColor }
                    PlasmaComponents3.TextField {
                        id: presetField
                        objectName: "victusPresetCode" + presetRow.index
                        Layout.fillWidth: true
                        text: root.draftPresets[presetRow.index] || ""
                        color: root.Kirigami.Theme.textColor
                        placeholderText: "#RRGGBB"
                        maximumLength: 7
                        validator: RegularExpressionValidator { regularExpression: /#[0-9a-fA-F]{6}/ }
                        Accessible.name: "Hazır renk " + (presetRow.index + 1) + " kodu"
                        onTextEdited: root.setDraft(presetRow.index, text)
                    }
                }
            }
            PlasmaComponents3.Label {
                text: root.failure
                visible: root.failure !== ""
                wrapMode: Text.Wrap
                Layout.fillWidth: true
                color: Kirigami.Theme.negativeTextColor
            }
        }
        footer: PlasmaComponents3.DialogButtonBox {
            PlasmaComponents3.Button {
                text: "Varsayılanlar"
                Kirigami.Theme.textColor: root.Kirigami.Theme.textColor
                enabled: !root.savingPresets
                PlasmaComponents3.DialogButtonBox.buttonRole: PlasmaComponents3.DialogButtonBox.ResetRole
                onClicked: root.resetDraft(root.defaultPresets)
            }
            PlasmaComponents3.Button {
                text: "Vazgeç"
                Kirigami.Theme.textColor: root.Kirigami.Theme.textColor
                enabled: !root.savingPresets
                PlasmaComponents3.DialogButtonBox.buttonRole: PlasmaComponents3.DialogButtonBox.RejectRole
                onClicked: presetEditor.close()
            }
            PlasmaComponents3.Button {
                objectName: "victusSavePresets"
                text: "Kaydet"
                Kirigami.Theme.textColor: root.Kirigami.Theme.textColor
                enabled: root.draftValid && !root.savingPresets
                PlasmaComponents3.DialogButtonBox.buttonRole: PlasmaComponents3.DialogButtonBox.AcceptRole
                onClicked: root.savePresets()
            }
        }
    }
    ColorDialog {
        id: picker
        title: "Klavye ışık rengini seç"
        options: ColorDialog.DontUseNativeDialog
        onAccepted: root.applyColor(selectedColor)
    }
    contentItem: RowLayout {
        spacing: Kirigami.Units.gridUnit
        Kirigami.Icon {
            Layout.alignment: Qt.AlignTop
            Layout.preferredWidth: Kirigami.Units.iconSizes.medium
            Layout.preferredHeight: Kirigami.Units.iconSizes.medium
            source: "input-keyboard-color"
        }
        ColumnLayout {
            Layout.fillWidth: true
            RowLayout {
                PlasmaComponents3.Label { text: "Klavye Rengi"; Layout.fillWidth: true }
                PlasmaComponents3.Button {
                    text: "Renk seç…"
                    onClicked: { picker.selectedColor = root.currentColor; picker.open(); }
                    contentItem: RowLayout {
                        Rectangle { implicitWidth: 18; implicitHeight: 18; radius: 9; color: root.currentColor; border.color: "#808080" }
                        PlasmaComponents3.Label { text: "Renk seç…" }
                    }
                }
                PlasmaComponents3.ToolButton {
                    objectName: "victusEditPresets"
                    icon.name: "configure"
                    Accessible.name: "Hazır renkleri düzenle"
                    QQC2.ToolTip.text: "Hazır renkleri düzenle"
                    QQC2.ToolTip.visible: hovered
                    onClicked: {
                        root.failure = "";
                        root.resetDraft(root.presets);
                        presetEditor.open();
                    }
                }
            }
            RowLayout {
                Repeater {
                    model: root.presets
                    delegate: PlasmaComponents3.ToolButton {
                        id: swatch
                        required property string modelData
                        Layout.fillWidth: true
                        implicitWidth: 26
                        implicitHeight: 30
                        Accessible.name: "Klavye rengi " + modelData
                        onClicked: root.applyColor(swatch.modelData)
                        contentItem: Rectangle {
                            implicitWidth: 20; implicitHeight: 20; radius: 10
                            color: swatch.modelData
                            border.width: String(root.currentColor) === swatch.modelData ? 2 : 1
                            border.color: String(root.currentColor) === swatch.modelData ? Kirigami.Theme.textColor : "#808080"
                        }
                    }
                }
            }
            RowLayout {
                PlasmaComponents3.TextField {
                    id: hexInput
                    Layout.fillWidth: true
                    text: String(root.currentColor)
                    placeholderText: "#RRGGBB"
                    maximumLength: 7
                    validator: RegularExpressionValidator { regularExpression: /#[0-9a-fA-F]{6}/ }
                    onAccepted: if (acceptableInput) root.applyColor(text)
                }
                PlasmaComponents3.Button { text: "Uygula"; enabled: hexInput.acceptableInput; onClicked: root.applyColor(hexInput.text) }
            }
            PlasmaComponents3.Label {
                visible: root.failure !== ""
                text: root.failure
                wrapMode: Text.Wrap
                Layout.fillWidth: true
                color: Kirigami.Theme.negativeTextColor
            }
        }
    }
}

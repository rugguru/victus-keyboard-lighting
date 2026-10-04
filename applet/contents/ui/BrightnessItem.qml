/*
    SPDX-FileCopyrightText: 2012-2013 Daniel Nicoletti <dantti12@gmail.com>
    SPDX-FileCopyrightText: 2013, 2015 Kai Uwe Broulik <kde@privat.broulik.de>

    SPDX-License-Identifier: LGPL-2.0-or-later
*/

import QtQuick
import QtQuick.Layouts

import org.kde.plasma.components as PlasmaComponents3
import org.kde.kirigami as Kirigami

PlasmaComponents3.ItemDelegate {
    id: root

    enum Type {
        Screen,
        Keyboard
    }

    property alias slider: control
    property real value
    property alias minimumValue: control.from
    property alias maximumValue: control.to
    property alias stepSize: control.stepSize
    required property /*BrightnessItem.Type*/ int type

    readonly property real percentage: maximumValue > 0 ? Math.round(100 * control.value / maximumValue) : 0
    readonly property string brightnessLevelOff: i18n("Kapalı")
    readonly property string brightnessLevelLow: i18n("Düşük")
    readonly property string brightnessLevelMedium: i18n("Orta")
    readonly property string brightnessLevelHigh: i18n("Yüksek")
    readonly property string brightnessLevelOn: i18n("Açık")
    readonly property string labelText: {
        if (maximumValue == 1) {
            const levels = [brightnessLevelOff, brightnessLevelOn];
            return levels[control.value];
        } else if (maximumValue == 2) {
            const levels = [brightnessLevelOff, brightnessLevelLow, brightnessLevelHigh];
            return levels[control.value];
        } else if (maximumValue == 3) {
            const levels = [brightnessLevelOff, brightnessLevelLow, brightnessLevelMedium, brightnessLevelHigh];
            return levels[control.value];
        } else {
            return i18n("%​%1", percentage);
        }
    }

    signal moved(real value)

    background.visible: highlighted
    highlighted: activeFocus
    hoverEnabled: false

    Accessible.name: root.text
    Accessible.description: root.labelText
    Keys.forwardTo: [slider]

    contentItem: RowLayout {
        spacing: Kirigami.Units.gridUnit

        Kirigami.Icon {
            id: image
            Layout.alignment: Qt.AlignTop
            Layout.preferredWidth: Kirigami.Units.iconSizes.medium
            Layout.preferredHeight: Kirigami.Units.iconSizes.medium
            source: root.icon.name
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            spacing: 0

            RowLayout {
                Layout.fillWidth: true
                spacing: Kirigami.Units.smallSpacing

                PlasmaComponents3.Label {
                    id: title
                    Layout.fillWidth: true
                    text: root.text
                    textFormat: Text.PlainText
                    elide: Text.ElideRight
                    Accessible.ignored: true
                }

                PlasmaComponents3.Label {
                    id: hint
                    text: i18n("Parlaklık")
                    textFormat: Text.PlainText
                    opacity: 0.75
                    visible: root.labelText != root.brightnessLevelOff && root.labelText != root.brightnessLevelOn
                }

                PlasmaComponents3.Label {
                    id: brightnessValue
                    Layout.alignment: Qt.AlignRight
                    text: root.labelText
                    textFormat: Text.PlainText
                    font.features: { "tnum": 1 }
                    Accessible.ignored: true
                }
            }

            PlasmaComponents3.Slider {
                id: control
                Layout.fillWidth: true

                activeFocusOnTab: false
                from: 0
                stepSize: 1
                value: root.value
                live: true
                snapMode: root.type === BrightnessItem.Type.Keyboard ? PlasmaComponents3.Slider.SnapAlways : PlasmaComponents3.Slider.SnapOnRelease

                Accessible.name: root.type === BrightnessItem.Type.Screen ? i18n("Görüntü Parlaklığı — %1", root.text) : root.text
                Accessible.description: brightnessValue.text
                Accessible.ignored: true
                Accessible.onPressAction: this.moved(value)

                // while pressed, don't update in response to outside changes, as it can cause
                // problems if the backend is reporting intermediate values while changing
                onPressedChanged: value = pressed ? value : Qt.binding(() => root.value)

                onMoved: {
                    root.moved(value)
                }
            }
        }
    }
}

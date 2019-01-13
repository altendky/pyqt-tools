import QtQuick 2.0
import examples 1.0

Item {
    width: 300
    height: 100

    ExampleQmlItem {
        id: piglet
        width: 300
        height: 300
        anchors.centerIn: parent
        other_value: test_value
    }
}

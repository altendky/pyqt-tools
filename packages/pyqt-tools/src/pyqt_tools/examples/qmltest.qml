import QtQuick 2.0
import QtTest 1.2
import examples 1.0

Item {
    width: 300
    height: 100

    ExampleQmlItem {
        id: piglet
        width: 300
        height: 300
        anchors.centerIn: parent
    }

    TestCase {
        name: "TextTests"
        function test_piglet(){
            compare(piglet.test_value, "pass the test")
        }
    }
}

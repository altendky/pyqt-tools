import QtQuick 2.0
import QtTest 1.2
import examples 1.0

Item {
    width: 300
    height: 100

    Text {
        id: foo
        width: 300
        height: 300
        anchors.centerIn: parent
    }

    TestCase {
        name: "TextTests"
        function testfooText(){
            compare(foo.test_value, "pass the test")
        }
    }
}

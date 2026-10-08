import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui

Panel {
  id: root
  moduleName: "seraph.warp"
  ipcTarget: "seraph.warp"
  readonly property string helper: Qt.resolvedUrl("bin/warp").toString().replace(/^file:\/\//, "")
  readonly property color foreground: Color.popups.text
  property bool connected: false
  property bool available: false
  property string status: "Checking WARP…"
  property string message: ""
  property bool failed: false
  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  function refresh() {
    if (!statusProcess.running && !actionProcess.running) statusProcess.running = true
  }
  function act(action) {
    if (actionProcess.running) return
    message = ""
    failed = false
    actionProcess.command = [root.helper, action]
    actionProcess.running = true
  }
  function registerWarp() {
    if (!available) {
      failed = true
      message = "Registration requires Cloudflare WARP (warp-cli). Install the Cloudflare client first; the installed Warp file-sharing app cannot register or connect to Cloudflare."
      return
    }
    failed = false
    message = "Opening registration in your terminal…"
    Quickshell.execDetached(["omarchy", "launch", "terminal", root.helper, "register"])
    root.close()
  }
  Component.onCompleted: refresh()
  onOpenedChanged: if (opened) refresh()
  Timer { interval: 5000; running: true; repeat: true; onTriggered: root.refresh() }
  Process {
    id: statusProcess
    command: [root.helper, "status"]
    stdout: StdioCollector {
      onStreamFinished: {
        try {
          var data = JSON.parse(text)
          root.connected = data.connected === true
          root.available = data.available === true
          root.status = data.message
        } catch (e) {
          root.connected = false
          root.status = "Unable to read WARP status"
        }
      }
    }
  }
  Process {
    id: actionProcess
    stdout: StdioCollector {
      onStreamFinished: {
        try {
          var data = JSON.parse(text)
          root.failed = !data.ok
          root.message = data.message
        } catch (e) {
          root.failed = true
          root.message = "Unable to run WARP command"
        }
      }
    }
    onExited: root.refresh()
  }
  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: "WARP"
    active: root.connected
    activeColor: Color.accent
    tooltipText: "Cloudflare WARP · " + root.status
    onPressed: root.toggle()
  }
  KeyboardPanel {
    id: popup
    anchorItem: button
    owner: root
    bar: root.bar
    open: root.opened
    contentWidth: popup.fittedContentWidth(Style.space(360))
    contentHeight: popup.fittedContentHeight(content.implicitHeight)
    Flickable {
      anchors.fill: parent
      contentHeight: content.implicitHeight
      clip: true
      Column {
        id: content
        width: parent.width
        spacing: Style.space(8)
        PanelHero {
          width: parent.width
          title: "Cloudflare WARP"
          meta: !root.available ? "Client missing" : root.connected ? "Connected" : "Disconnected"
          foreground: root.foreground
        }
        Text {
          width: parent.width
          text: root.status
          textFormat: Text.PlainText
          wrapMode: Text.Wrap
          color: root.foreground
          font.family: Style.font.family
          font.pixelSize: Style.font.bodySmall
        }
        Repeater {
          model: [
            {label: "Connect", action: "connect"},
            {label: "Disconnect", action: "disconnect"},
            {label: "DNS only (DoH)", action: "doh"},
            {label: "WARP + DNS (DoH)", action: "warp+doh"},
            {label: "Block malware", action: "malware"},
            {label: "Block malware + adult content", action: "full"},
            {label: "Turn off family filtering", action: "off"},
            {label: "Check connection", action: "check"}
          ]
          delegate: Button {
            required property var modelData
            width: content.width
            text: modelData.label
            bordered: true
            focusable: true
            foreground: root.foreground
            enabled: !actionProcess.running && (root.available || modelData.action === "check")
            onClicked: root.act(modelData.action)
          }
        }
        PanelSeparator { foreground: root.foreground }
        Button {
          width: parent.width
          text: root.available ? "Register WARP (first time)" : "Register WARP — client required"
          bordered: true
          focusable: true
          foreground: root.foreground
          enabled: !actionProcess.running
          onClicked: root.registerWarp()
        }
        Text {
          width: parent.width
          visible: actionProcess.running || root.message !== ""
          text: actionProcess.running ? "Working…" : root.message
          textFormat: Text.PlainText
          wrapMode: Text.Wrap
          color: root.failed ? Color.urgent : root.foreground
          font.family: Style.font.family
          font.pixelSize: Style.font.bodySmall
        }
      }
    }
  }
}

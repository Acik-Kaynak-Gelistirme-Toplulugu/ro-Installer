import sys
import os
from PyQt6.QtCore import Qt, QUrl, QObject, pyqtSlot
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel

from installer_backend import BackendBridge

# WebEngine'in root (sudo) yetkisiyle de sorunsuz çalışabilmesi için:
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--no-sandbox"

class InstallerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Tam Ekran ve Çerçevesiz Pencere Ayarları
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Web Motoru Kurulumu
        self.browser = QWebEngineView()
        self.browser.page().setBackgroundColor(Qt.GlobalColor.transparent)
        
        # Python-JS İletişim Kanalı (WebChannel)
        self.channel = QWebChannel()
        self.backend = BackendBridge(self)
        self.channel.registerObject("backend", self.backend)
        self.browser.page().setWebChannel(self.channel)
        
        # HTML dosyasını yükle
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "index.html")
        self.browser.setUrl(QUrl.fromLocalFile(ui_path))
        
        self.setCentralWidget(self.browser)
        
        # Sayfa yüklendiğinde JavaScript'e backend objesini tanıt
        self.browser.loadFinished.connect(self.on_load_finished)
        
    def on_load_finished(self, ok):
        if ok:
            # QWebChannel.js kütüphanesi html içinde yüklü olduğu varsayılır.
            # Backend objesini window.backend olarak Javascript tarafına kaydeder.
            init_js = """
            new QWebChannel(qt.webChannelTransport, function (channel) {
                window.backend = channel.objects.backend;
                window.backend.logMessage('WebChannel başarıyla bağlandı.');

                // Python'dan Gelecek Sinyalleri JS Fonksiyonlarıyla Eşleştir
                window.backend.progressChanged.connect(function(val) {
                    const pb = document.getElementById('mainProgressBar');
                    if (pb) pb.style.width = val + '%';
                });

                window.backend.logMessageSignal.connect(function(msg) {
                    if (typeof addLog === "function") {
                        addLog(msg);
                    } else {
                        console.log(msg);
                    }
                });

                window.backend.statusChangedSignal.connect(function(statusMsg) {
                    const statusText = document.getElementById('installStatusText');
                    if(statusText) statusText.innerHTML = statusMsg;
                });

                window.backend.installFinished.connect(function(status, msg) {
                    const statusText = document.getElementById('installStatusText');
                    if (status) {
                        if (statusText) statusText.innerHTML = "Kurulum Tamamlandı! Sistemi yeniden başlatabilirsiniz.";
                        const rebootBtn = document.getElementById('reboot-row');
                        if (rebootBtn) rebootBtn.style.display = 'flex';
                    } else {
                        if (statusText) statusText.innerHTML = "Kurulum Başarısız: " + msg;
                    }
                });

                window.backend.wifiListSignal.connect(function(jsonStr) {
                    if (typeof receiveWifiList === "function") {
                        receiveWifiList(jsonStr);
                    }
                });

                window.backend.wifiConnectStatus.connect(function(status, msg) {
                    if (typeof receiveWifiStatus === "function") {
                        receiveWifiStatus(status, msg);
                    }
                });

                window.backend.osDetectedSignal.connect(function(found, msg) {
                    if (typeof receiveOsDetection === "function") {
                        receiveOsDetection(found, msg);
                    }
                });
            });
            """
            self.browser.page().runJavaScript(init_js)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = InstallerWindow()
    window.showFullScreen()
    
    sys.exit(app.exec())

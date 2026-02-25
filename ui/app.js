// Installer UI Interactions
let currentStep = 1;
const totalSteps = 7;

// Root Parola Alanını Göster/Gizle
function toggleRootFields() {
    const sudoSwitch = document.getElementById('sudoSwitch');
    const rootPassContainer = document.getElementById('rootPassContainer');
    if (sudoSwitch && rootPassContainer) {
        if (!sudoSwitch.checked) {
            rootPassContainer.style.display = 'block';
        } else {
            rootPassContainer.style.display = 'none';
        }
    }
}

// Hata Mesajı Gösterme (Toast)
function showError(msg) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.innerText = msg;
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3500);
}

// İleri Sayfa
function nextPage() {
    // === SAYFA 3 (Kullanıcı Formu) Doğrulama ===
    if (currentStep === 3) {
        const name = document.getElementById('inputName').value.trim();
        const surname = document.getElementById('inputSurname').value.trim();
        const username = document.getElementById('inputUsername').value.trim();
        const pass = document.getElementById('inputPassword').value;
        const passConf = document.getElementById('inputPasswordConfirm').value;

        if (!name || !surname || !username || !pass || !passConf) {
            showError("Lütfen tüm alanları doldurun, boş alan bırakılamaz!");
            return; // İlerlemeyi durdur ve hata ver
        }

        if (pass !== passConf) {
            showError("Kullanıcı şifreleri birbiriyle eşleşmiyor. Lütfen iki şifreyi de aynı giriniz!");
            return; // İlerlemeyi durdur
        }

        const sudoSwitch = document.getElementById('sudoSwitch');
        if (sudoSwitch && !sudoSwitch.checked) {
            const rootPass = document.getElementById('inputRootPassword').value;
            const rootPassConf = document.getElementById('inputRootPasswordConfirm').value;

            if (!rootPass || !rootPassConf) {
                showError("Root (Yönetici) olabilmek için Root (su) şifresi alanlarının doldurulması zorunludur!");
                return;
            }
            if (rootPass !== rootPassConf) {
                showError("Root şifreleri hatalı (Birbiriyle uyuşmuyor)!");
                return;
            }
        }
    }

    if (currentStep < totalSteps) {

        // Yeni sayfaya geçmeden önceki hooklar:
        if (currentStep === 1) { // 1. sayfadan 2. (Ağ) sayfasına geçişte wifi tara
            scanNetworks();
        }

        if (currentStep === 4) { // 4. (Sys/Kurulum Modeli) sayfadan 5. (Disk) sayfasına geçerken OS tara
            scanForOtherOS();
            scanTargetDisks();
        }

        // Önceki sayfayı gizle
        document.getElementById(`page-${currentStep}`).classList.remove('active');

        // Sidebar'da önceki adımı 'completed' yap
        document.getElementById(`step${currentStep}`).classList.add('completed');
        document.getElementById(`step${currentStep}`).classList.remove('active');

        currentStep++;

        // Yeni sayfayı göster
        const nextPageEl = document.getElementById(`page-${currentStep}`);
        if (nextPageEl) {
            nextPageEl.classList.add('active');
        }

        // Sidebar'ı güncelle
        document.getElementById(`step${currentStep}`).classList.add('active');
    }
}

// Geri Sayfa
function prevPage() {
    if (currentStep > 1) {
        // Şu anki sayfayı gizle
        document.getElementById(`page-${currentStep}`).classList.remove('active');
        document.getElementById(`step${currentStep}`).classList.remove('active');

        currentStep--;

        // Önceki sayfayı göster
        const prevPageEl = document.getElementById(`page-${currentStep}`);
        if (prevPageEl) {
            prevPageEl.classList.add('active');
        }

        // Sidebar'ı düzelt
        document.getElementById(`step${currentStep}`).classList.remove('completed');
        document.getElementById(`step${currentStep}`).classList.add('active');
    }
}

// Çıkış ve Live Desktop'a Dönüş
function exitInstaller() {
    if (confirm("Kurulumdan çıkmak ve Live Masaüstüne dönmek istediğinize emin misiniz?")) {
        // Python Backend'ine sinyal gönder
        if (window.backend) {
            window.backend.exitInstaller();
        } else {
            console.log("Python Backend signal: EXIT");
        }
    }
}

// Kernel Seçimi (Aktif Sınıfını Değiştirme)
function selectKernel(type) {
    // Tüm kartlardaki active sınıfını kaldır
    const cards = document.querySelectorAll('#page-4 .selection-card');
    cards.forEach(c => c.classList.remove('active'));

    // Tıklanana active ekle
    event.currentTarget.classList.add('active');

    // Deneysel Seçildiyse -> Disk Bölümlemedeki "Elle Bölümle" Kartını Göster
    const manualCard = document.getElementById('manual-partition-card');
    if (manualCard) {
        if (type === 'deneysel') {
            manualCard.style.display = 'block';
        } else {
            // Standart ise gizle
            manualCard.style.display = 'none';

            // Eğer Elle bölümleme aktifken Standart menüye dönüldüyse Disk seçimini zorla sıfırla ("Tamamen"e çek)
            const manualBox = document.getElementById('manual-partitioning-box');
            if (manualBox && manualBox.style.display === 'block') {
                const diskCards = document.querySelectorAll('#page-5 .selection-card');
                diskCards.forEach(c => c.classList.remove('active'));
                if (diskCards.length > 0) diskCards[0].classList.add('active'); // Tamamen Kur aktive edildi

                // Form elementlerini sıfırla
                document.getElementById('custom-disk-options').style.display = 'none';
                manualBox.style.display = 'none';
                const fsSelect = document.getElementById('fs-selection');
                if (fsSelect) fsSelect.style.display = 'block';
            }
        }
    }
}

// Wi-Fi Seçimi
document.addEventListener('click', function (e) {
    if (e.target.closest('.wifi-item')) {
        const item = e.target.closest('.wifi-item');
        const items = document.querySelectorAll('.wifi-item');
        items.forEach(i => i.classList.remove('selected'));
        item.classList.add('selected');

        const wifiPwdBox = document.getElementById('wifi-password-box');
        if (wifiPwdBox) {
            const isSecure = item.getAttribute('data-security') && item.getAttribute('data-security') !== '--';
            const isActive = item.getAttribute('data-active') === 'true';

            if (isActive) {
                wifiPwdBox.style.display = 'none'; // Zaten bağlıysa şifre sorma
            } else if (isSecure) {
                wifiPwdBox.style.display = 'block';
                document.getElementById('wifiInputPassword').value = '';
                document.getElementById('wifiInputPassword').focus();
            } else {
                wifiPwdBox.style.display = 'none';
            }
        }
    }
});

// === Wi-Fi Backend Fonksiyonları ===
function scanNetworks() {
    const listbox = document.querySelector('.wifi-list-box');
    if (listbox) {
        listbox.innerHTML = '<div style="text-align:center; padding: 20px;">Ağlar aranıyor... Lütfen bekleyin.</div>';
    }
    const wifiPwdBox = document.getElementById('wifi-password-box');
    if (wifiPwdBox) wifiPwdBox.style.display = 'none';

    if (window.backend) {
        window.backend.scanWifi();
    }
}

// Python'dan wifi listesi (JSON) buraya düşer
window.receiveWifiList = function (jsonStr) {
    const listbox = document.querySelector('.wifi-list-box');
    if (!listbox) return;
    listbox.innerHTML = ''; // Temizle

    try {
        const parsedData = JSON.parse(jsonStr);
        let networks = [];
        let ethActive = false;

        if (Array.isArray(parsedData)) {
            networks = parsedData;
        } else {
            networks = parsedData.networks || [];
            ethActive = parsedData.ethernet_active || false;
        }

        if (ethActive) {
            listbox.innerHTML = `
                <div style="text-align:center; padding: 20px;">
                    <div style="font-size: 40px; margin-bottom: 10px;">🔌</div>
                    <h3 style="color: var(--accent-green);">Kablolu İnternet (Ethernet) Aktif</h3>
                    <p style="font-size: 13px; opacity: 0.8; margin-top:10px;">Hazır bir internet bağlantısı algılandı. Kuruluma dilediğiniz gibi devam edebilirsiniz.</p>
                </div>`;

            const btn = document.getElementById('wifiConnectBtn');
            if (btn) {
                btn.style.display = 'block';
                btn.innerText = 'Devam Et';
                btn.onclick = function () { nextPage(); };
            }

            return;
        }

        if (networks.length === 0) {
            listbox.innerHTML = '<div style="text-align:center; padding: 20px;">Hiçbir Wi-Fi ağı bulunamadı. Lütfen cihazınızda Wi-Fi açık mı kontrol edin.</div>';
            return;
        }

        const btn = document.getElementById('wifiConnectBtn');
        if (btn) btn.style.display = 'block';

        networks.forEach(net => {
            const div = document.createElement('div');
            div.className = 'wifi-item';
            if (net.active) div.classList.add('selected');
            div.setAttribute('data-ssid', net.ssid);
            div.setAttribute('data-security', net.security);
            div.setAttribute('data-active', net.active);

            const signalLevel = net.signal > 70 ? '🟢' : (net.signal > 40 ? '🟡' : '🔴');
            const secIcon = (net.security && net.security !== '--') ? '🔒' : '🔓';
            const statusTxt = net.active ? 'Bağlı' : (net.signal + '%');

            div.innerHTML = `
                <span>${signalLevel} ${secIcon} ${net.ssid}</span>
                <span class="wifi-status" style="${net.active ? 'color: var(--accent-green); font-weight: bold;' : ''}">${statusTxt}</span>
            `;
            listbox.appendChild(div);
        });

    } catch (e) {
        console.error("WiFi JSON Parse hatası:", e);
        listbox.innerHTML = '<div style="text-align:center;">Ağ listesi çözümlenemedi.</div>';
    }
};

function connectSelectedWifi() {
    const selectedItem = document.querySelector('.wifi-item.selected');
    if (!selectedItem) {
        showError("Lütfen bağlanmak veya teyit etmek için bir Wi-Fi ağı seçin.");
        return;
    }

    const ssid = selectedItem.getAttribute('data-ssid');
    const isActive = selectedItem.getAttribute('data-active') === 'true';

    // Eğer zaten bağlıysa direkt sonraki sayfaya geç
    if (isActive) {
        nextPage();
        return;
    }

    const isSecure = selectedItem.getAttribute('data-security') && selectedItem.getAttribute('data-security') !== '--';
    let pwd = '';

    if (isSecure) {
        pwd = document.getElementById('wifiInputPassword').value;
        if (!pwd) {
            showError("Bu ağ şifreli. Lütfen şifre giriniz!");
            return;
        }
    }

    // Ağa bağlanma isteği
    document.getElementById('wifiConnectBtn').innerText = "Bağlanıyor...";
    document.getElementById('wifiConnectBtn').disabled = true;

    if (window.backend) {
        window.backend.connectWifi(ssid, pwd);
    } else {
        // Simülasyon
        setTimeout(() => {
            receiveWifiStatus(true, ssid);
        }, 2000);
    }
}

// Python'dan gelen bağlantı sonucu
window.receiveWifiStatus = function (status, msg) {
    const btn = document.getElementById('wifiConnectBtn');
    if (btn) {
        btn.innerText = "Ağı Onayla ve İlerle";
        btn.disabled = false;
    }

    if (status) {
        // Başarılıysa ilerle
        nextPage();
    } else {
        showError(msg);
    }
};

// === İşletim Sistemi (OS) Tespiti JS Bridge ===
function scanForOtherOS() {
    const alongsideCard = document.getElementById('alongside-card');
    // Baştan gizleyelim ki, eğer önceki sayfaya dönülmüşse sahte pozitif olmasın.
    if (alongsideCard) alongsideCard.style.display = 'none';

    if (window.backend) {
        window.backend.detectOS();
    } else {
        console.log("OS Tarayıcı (os-prober) başlatıldı. [SIMULATION]");
        setTimeout(() => {
            receiveOsDetection(true, "Simüle Windows Bulundu");
        }, 1500);
    }
}

window.receiveOsDetection = function (found, msg) {
    const alongsideCard = document.getElementById('alongside-card');
    if (found && alongsideCard) {
        alongsideCard.style.display = 'block'; // DÜZELTİLDİ: Flex yerine block olmalı
        console.log("OS Bulundu: " + msg);
        // İsterseniz bu aşamada 'addLog' veya notification kullanılabilir.
    } else {
        console.log("OS Bulunamadı, Yanına Kur inaktif.");
    }
};

// === Disk Tespiti JS Bridge ===
function scanTargetDisks() {
    const lbl = document.getElementById('lblTargetDisk');
    if (lbl) lbl.innerText = "Disk Sürücüleri Taranıyor...";

    if (window.backend) {
        window.backend.scanDisks();
    } else {
        setTimeout(() => {
            receiveDiskList(JSON.stringify([
                { name: "/dev/sda", size: "500G", model: "Simüle SSD" },
                { name: "/dev/nvme0n1", size: "1T", model: "Simüle NVMe" }
            ]));
        }, 1000);
    }
}

window.receiveDiskList = function (jsonStr) {
    try {
        const disks = JSON.parse(jsonStr);
        const select = document.getElementById('targetDiskSelect');
        const lbl = document.getElementById('lblTargetDisk');
        if (!select) return;

        if (lbl) {
            lbl.innerHTML = 'Kurulum Yapılacak Disk (Hedef Sürücü) <span class="tooltip-icon" style="text-transform: none; cursor: help;" data-title="ro-ASD\'nin ve sistem çekirdeklerinin kalıcı olarak yükleneceği donanım. Lütfen doğru diski seçtiğinizden emin olun!">?</span>';
        }

        select.innerHTML = '';
        if (disks.length === 0) {
            const opt = document.createElement('option');
            opt.value = "";
            opt.text = "Kurulabilir disk bulunamadı!";
            select.appendChild(opt);
        } else {
            disks.forEach((d, idx) => {
                const opt = document.createElement('option');
                opt.value = d.name;
                opt.text = `${d.name} (${d.size}) - ${d.model}`;
                opt.setAttribute('data-size', parseDiskSize(d.size));
                if (idx === 0) opt.selected = true;
                select.appendChild(opt);
            });

            // Adjust slider for first initially selected disk
            if (select.options.length > 0) {
                updateSliderLimits(parseFloat(select.options[0].getAttribute('data-size')));
            }
        }

        // Custom Dropdown Görselliğini Güncelle (Sıfırdan inşa et)
        const wrapper = select.closest('.custom-select-wrapper');
        if (wrapper) {
            const oldCustomSelect = wrapper.querySelector('.custom-select');
            const oldOptionsList = wrapper.querySelector('.custom-select-options');
            if (oldCustomSelect) oldCustomSelect.remove();
            if (oldOptionsList) oldOptionsList.remove();

            const customSelect = document.createElement('div');
            customSelect.className = 'custom-select';
            let selectedOpt = select.options[select.selectedIndex];
            customSelect.innerHTML = selectedOpt ? selectedOpt.text : '';
            wrapper.appendChild(customSelect);

            const optionsList = document.createElement('div');
            optionsList.className = 'custom-select-options';
            Array.from(select.options).forEach((opt) => {
                const optionDiv = document.createElement('div');
                optionDiv.className = 'custom-option';
                if (opt.selected) optionDiv.classList.add('selected');
                optionDiv.innerHTML = opt.text;

                optionDiv.addEventListener('click', function (e) {
                    e.stopPropagation();
                    customSelect.innerHTML = this.innerHTML;
                    select.value = opt.value;

                    if (opt.hasAttribute('data-size')) {
                        updateSliderLimits(parseFloat(opt.getAttribute('data-size')));
                    }

                    select.dispatchEvent(new Event('change'));

                    optionsList.querySelectorAll('.custom-option').forEach(o => o.classList.remove('selected'));
                    this.classList.add('selected');
                    customSelect.classList.remove('open');
                });
                optionsList.appendChild(optionDiv);
            });
            wrapper.appendChild(optionsList);

            customSelect.addEventListener('click', function (e) {
                e.stopPropagation();
                document.querySelectorAll('.custom-select.open').forEach(s => {
                    if (s !== customSelect) s.classList.remove('open');
                });
                this.classList.toggle('open');
            });
        }

    } catch (e) {
        console.log("Disk listesi islenirken hata:", e);
    }
};

// Disk Seçim Tipi
function selectDiskType(type) {
    const cards = document.querySelectorAll('#page-5 .selection-card');
    cards.forEach(c => c.classList.remove('active'));
    event.currentTarget.classList.add('active');

    const customOptions = document.getElementById('custom-disk-options');
    const fsSelection = document.getElementById('fs-selection');
    const manualBox = document.getElementById('manual-partitioning-box');

    // Hepsini varsayılan olarak gizle
    if (customOptions) customOptions.style.display = 'none';
    if (fsSelection) fsSelection.style.display = 'none';
    if (manualBox) manualBox.style.display = 'none';

    if (type === 'tamamen') {
        if (fsSelection) fsSelection.style.display = 'block';
    }
    else if (type === 'yanina') {
        if (fsSelection) fsSelection.style.display = 'block';
        if (customOptions) customOptions.style.display = 'block';
    }
    else if (type === 'elle') {
        if (manualBox) manualBox.style.display = 'block';
    }
}

function openKPMcore() {
    alert("KPMcore gelişmiş bölümleme aracı veya GParted bağlantısı simülasyonu çalıştırılıyor...");
}

// Slider Değerini Kutucuğa Aktarma
function updateDiskText(val) {
    document.getElementById('diskInput').value = val;
}

// Kutucuktan Rakam Girildiğinde Slider'ı Güncelleme
function updateDiskSlider(val) {
    const slider = document.querySelector('.glass-slider');
    if (!slider) return;
    let num = parseInt(val);
    if (isNaN(num)) num = 30;
    if (num > parseInt(slider.max)) num = parseInt(slider.max);
    if (num < parseInt(slider.min)) num = parseInt(slider.min);

    slider.value = num;
}

// Lsblk'dan Gelen Size Bilgisini Numerik (GB) Olarak Parse Et
function parseDiskSize(sizeStr) {
    if (!sizeStr || sizeStr === 'Bilinmiyor') return 500;
    let val = parseFloat(sizeStr.replace(/,/g, '.'));
    if (sizeStr.includes('T')) return val * 1024;
    if (sizeStr.includes('M')) return Math.max(0, val / 1024);
    return val;
}

// Yeni Bir Disk Seçildiğinde Slider Max/Min Sınırlarını Hesapla
function updateSliderLimits(maxGb) {
    const slider = document.querySelector('.glass-slider');
    const diskInput = document.getElementById('diskInput');
    if (!slider || !diskInput) return;

    const minGb = 30;
    let maxVal = Math.floor(maxGb);
    let calculatedMax = maxVal > minGb ? maxVal - 20 : maxVal; // 20GB buffer for host OS
    if (calculatedMax < minGb) calculatedMax = minGb;

    slider.min = minGb;
    slider.max = calculatedMax;

    if (parseInt(slider.value) > calculatedMax) {
        slider.value = calculatedMax;
        diskInput.value = calculatedMax;
    }
    if (parseInt(slider.value) < minGb) {
        slider.value = minGb;
        diskInput.value = minGb;
    }
}

// Terminal (Log) Gizle/Göster
function toggleLogTerminal() {
    const term = document.getElementById('logTerminal');
    if (term.style.display === 'none') {
        term.style.display = 'block';
    } else {
        term.style.display = 'none';
    }
}

// Log'a yeni yazı ekle
function addLog(text) {
    const list = document.getElementById('logList');
    const li = document.createElement('li');
    li.textContent = text;
    list.appendChild(li);
    // Auto scroll
    const term = document.getElementById('logTerminal');
    term.scrollTop = term.scrollHeight;
}

// Python Sistem Kurulumunu Başlatma (Gerçek/Simülasyon Aktarımı)
function startInstallationJob() {
    // 1. Kurulum Parametrelerini (JSON) Topla
    const sudoElement = document.getElementById('sudoSwitch');
    const kernelElement = document.querySelector('#page-4 .selection-card.active h3');
    const diskElement = document.querySelector('#page-5 .selection-card.active h3');
    const fsElement = document.querySelector('#fs-selection select');

    // Region & Localization Elements
    const regionVal = document.getElementById('regionSelect') ? document.getElementById('regionSelect').value : 'Europe/Istanbul';
    const localeVal = document.getElementById('localeSelect') ? document.getElementById('localeSelect').value : 'tr_TR.UTF-8';
    const keyboardVal = document.getElementById('keyboardSelect') ? document.getElementById('keyboardSelect').value : 'tr';

    const config = {
        name: document.getElementById('inputName') ? document.getElementById('inputName').value : '',
        surname: document.getElementById('inputSurname') ? document.getElementById('inputSurname').value : '',
        username: document.getElementById('inputUsername') ? document.getElementById('inputUsername').value : 'ro-user',
        password: document.getElementById('inputPassword') ? document.getElementById('inputPassword').value : '1234',
        rootPassword: document.getElementById('inputRootPassword') ? document.getElementById('inputRootPassword').value : '1234',
        sudo: sudoElement ? sudoElement.checked : true,
        kernelType: kernelElement ? kernelElement.innerText : 'Standart',
        diskType: diskElement ? diskElement.innerText : 'Tamamen',
        targetDisk: document.getElementById('targetDiskSelect') ? document.getElementById('targetDiskSelect').value : '/dev/sda',
        fsType: fsElement ? fsElement.value : 'ext4',
        region: regionVal,
        locale: localeVal,
        keyboard: keyboardVal
    };

    nextPage(); // Page 7'ye (Progress) geçis

    // UI Animasyon Tetikleniyor: Slayt genişlesin
    setTimeout(() => {
        const slideshowBox = document.getElementById('installSlideshow');
        if (slideshowBox) slideshowBox.classList.add('show');
        startSlideshow();
    }, 800);

    // Python Backend Sinyali
    if (window.backend) {
        addLog("[Backend] Python kurulum sistemine startInstall sinyali gönderiliyor...");
        window.backend.startInstall(JSON.stringify(config));
    } else {
        addLog("[HATA] Python backend bağlantısı bulunamadı!");
        document.getElementById('installStatusText').innerHTML = "Bağlantı Hatası: Python backend'i yok.";
    }
}

// Otomatik Slayt Gösterisi
let slideInterval;
function startSlideshow() {
    if (slideInterval) clearInterval(slideInterval);
    let currentSlide = 0;
    const slides = document.querySelectorAll('.slide-img');
    if (slides.length === 0) return;

    slideInterval = setInterval(() => {
        slides[currentSlide].classList.remove('active');
        currentSlide = (currentSlide + 1) % slides.length;
        slides[currentSlide].classList.add('active');
    }, 4000); // Her 4 saniyede bir değiştir
}

// Sistemi Yeniden Başlat Metodu
function rebootSystem() {
    if (confirm("Kurulum başarıyla tamamlandı. Sistem yeniden başlatılacak. Emin misiniz?")) {
        // Python'a sinyal gönderilir -> os.system("reboot")
        addLog("[Sistem] Yeniden başlatılıyor...");
        alert("Bağlantı başarılı: Simgesel Reboot (Sistem yeniden başlatılıyor...)");
        if (window.backend) {
            window.backend.exitInstaller(); // veya ayrı bağlanan reboot()
        }
    }
}

// Parallax Effect (Fare hareketlerine göre arkaplan ve camın tepki vermesi)
document.addEventListener('mousemove', (e) => {
    const x = (e.clientX / window.innerWidth - 0.5) * 20; // -10px to +10px
    const y = (e.clientY / window.innerHeight - 0.5) * 20;

    // Arkaplanın zıt yöne kayması
    const bgSlider = document.getElementById('bg-slider');
    if (bgSlider) {
        bgSlider.style.transform = `translate(${-x}px, ${-y}px) scale(1.05)`;
    }

    // Aktif sayfa kartının çok hafif sallanması (Derinlik - Z-Axis efekti)
    const activePage = document.querySelector('.page.active .glass-container');
    if (activePage) {
        activePage.style.transform = `translate(${x * 0.5}px, ${y * 0.5}px)`;
    }
});


// === Tema Yönetimi ===
function toggleTheme() {
    document.body.classList.toggle('light-mode');
}

// Canlı Klavye Değiştirme
function changeKeyboardEvent(val) {
    if (window.backend) {
        window.backend.changeLiveKeyboard(val);
    } else {
        console.log("Simulating live keyboard change to:", val);
    }
}

// === Dil Yönetimi ===
const translations = {
    tr: {
        topTitle: "ro-ASD Kurulumuna Hoşgeldiniz",
        welcomeDesc: "Modern, hızlı ve güvenilir işletim sistemi kurulum aracı. İşlemler sırasında lütfen bilgisayarınızı kapatmayınız.",
        startBtn: "Kurulumu Başlat",
        step1: "Karşılama", step2: "Ağ ve Bağlantı", step3: "Kullanıcı Bilgileri",
        step4: "Kurulum Türü", step5: "Disk Bölümleme", step6: "Zaman ve Bölge", step7: "Kurulum İlerlemesi",
        btnBack: "Geri", btnContinue: "Devam Et",

        p2Title: "Ağ Bağlantısı",
        p2Desc: "Kurulum süresince güncellemeleri ve gerekli kernel paketlerini indirebilmek için internete bağlanmanız gerekmektedir.",
        p2Btn: "Ağı Onayla ve İlerle",

        p3Title: "Sistem Kullanıcı Bilgileri",
        p3Desc: "Sisteminizi ve ana yetkili oturumunuzu kişiselleştirin.",
        p3LblName: "Adınız",
        p3LblSurname: "Soyadınız",
        p3LblUser: "Kullanıcı Adı (Sistem Girişi)",
        p3LblPass: "Şifre",
        p3LblPassConf: "Şifre Tekrar",
        p3SpanSudo: 'Bu kullanıcıyı "Yönetici" (sudo/wheel) yap',
        p3DescSudo: 'Yönetici hesabı sisteme program yükleme ve kritik değişiklikler yapma hakkına sahiptir. (Tiki kaldırırsanız sistem için ayrı bir "Root" (Süper Kullanıcı) şifresi oluşturmanız istenecek)',
        p3LblRoot: "Root (Su) Şifresi",
        p3LblRootConf: "Root Şifresi Tekrar",

        p4Title: "Kurulum Türü ve Çekirdek (Kernel) Seçimi",
        p4Desc: "Sistemin kalbini ve kurulum tipini belirleyin.",
        p4Opt1Title: "Standart Kurulum",
        p4Opt1Desc: "Mevcut Fedora deposundan orijinal, güncel ve kararlı çekirdek.<br><b>(Kurulum medyası veya internetten yüklenir)</b>",
        p4Opt2Title: "Gelişmiş-Deneysel",
        p4Opt2Desc: "ro-ASD özel, yamalı ve performans odaklı çekirdek <br><b>(Yerel kurulum paketinden gömülür)</b>",

        p5Title: "Sistem Kurulum Diski ve Biçimlendirme",
        p5Desc: "ro-ASD'yi kurmak istediğiniz hedef diski ve kurulum yöntemini seçin.",
        p5Opt1Title: "Tüm Diske Kur",
        p5Opt1Desc: "Seçtiğiniz diskteki <b>tüm veriler ve işletim sistemleri kalıcı olarak silinir.</b> Depolama alanının tamamı ro-ASD için optimize edilerek sıfırdan oluşturulur. Sıfır bir başlangıç isteyenler için en temiz ve önerilen yöntemdir.",
        p5Opt2Title: `Yanına Kur <span class="tooltip-icon" data-title="Bu seçenek mevcut Windows veya diğer Linux dağıtımlarınıza dokunmadan diskinizde boş bir alan açarak (Shrinking) ro-ASD'yi o alana güvenle kurmanızı sağlar. Sistem açılışında hangi işletim sistemine gireceğinizi seçebilirsiniz (Dual Boot).">?</span>`,
        p5Opt2Desc: "Mevcut Windows veya Diğer Sistemlerinize (Verilerinize) <b>dokunulmadan</b> yanlarına ek bir partition açılarak güvenli şekilde (Dual Boot) kurulum yapılır.",
        p5Opt3Title: "Elle Bölümleme",
        p5Opt3Desc: "Diskleri siz ayarlayın.",
        p5LblFs: `Kurulum Dosya Sistemi (Format) <span class="tooltip-icon" style="text-transform: none; cursor: help;" data-title="Linux diskinizin (Partition) okuma/yazma mimarisini belirler. Ext4 (Standart), BTRFS (Snapshot/Yedekleme destekli, SSD dostu) veya XFS (Yüksek kapasite/Sunucu) seçebilirsiniz.">?</span>`,
        p5LblSpace: "ro-ASD İçin Ayrılacak Kurulum Alanı:",
        p5ManDesc: "Devam ettiğinizde disk bölümlerini, dosya sistemlerini (Ext4, BTRFS vb.) ve bağlama noktalarını dilediğiniz gibi oluşturabilirsiniz.",
        p5ManBtn: "Gelişmiş Bölümleme Aracı (KPMcore)",
        p5GrubInfo: "ℹ️ <b>Sistem Önyükleyicisi:</b> Kurulum tamamlandığında diskinize ro-ASD'yi başlatmaktan sorumlu olan <b>GRUB2 (Bootloader)</b> kurulacak ve yapılandırılacaktır.",

        p6Title: "Zaman ve Bölge Ayarları",
        p6Desc: "Sistemin konum ve saat bilgilerini ayarlayın.",
        p6LblRegion: "Bölge / Şehir",
        p6LblLang: "Sistem Dili (Locale)",
        p6StartInstall: "Sistemi Kurmaya Başla",

        p7Title: "Kurulum Gerçekleştiriliyor...",
        p7ToggleLog: "Kurulum Loglarını Göster / Gizle",
        p7Reboot: "Sistemi Yeniden Başlat"
    },
    en: {
        topTitle: "Welcome to ro-ASD Installer",
        welcomeDesc: "Modern, fast, and reliable OS installer. Please do not turn off your machine during the process.",
        startBtn: "Start Installation",
        step1: "Welcome", step2: "Network", step3: "User Details",
        step4: "Install Type", step5: "Partitions", step6: "Time & Region", step7: "Progress",
        btnBack: "Back", btnContinue: "Continue",

        p2Title: "Network Connection",
        p2Desc: "You need to connect to the internet during installation to download updates and necessary kernel packages.",
        p2Btn: "Confirm Network & Continue",

        p3Title: "System User Details",
        p3Desc: "Personalize your system and main administrative account.",
        p3LblName: "First Name",
        p3LblSurname: "Last Name",
        p3LblUser: "Username (System Login)",
        p3LblPass: "Password",
        p3LblPassConf: "Confirm Password",
        p3SpanSudo: 'Make this user an "Administrator" (sudo/wheel)',
        p3DescSudo: 'Admin account has permissions to install programs and make critical changes. (If unchecked, you must set a separate "Root" password)',
        p3LblRoot: "Root (Su) Password",
        p3LblRootConf: "Confirm Root Password",

        p4Title: "Installation Type & Kernel Selection",
        p4Desc: "Determine the heart of your system and the installation type.",
        p4Opt1Title: "Standard Installation",
        p4Opt1Desc: "Original, up-to-date and stable kernel from Fedora repository.<br><b>(Installed from media or internet)</b>",
        p4Opt2Title: "Advanced / Experimental",
        p4Opt2Desc: "ro-ASD custom, patched, and performance-oriented kernel <br><b>(Embedded from local disk)</b>",

        p5Title: "Installation Disk & Formatting",
        p5Desc: "Select the target disk and installation method for ro-ASD.",
        p5Opt1Title: "Erase Entire Disk",
        p5Opt1Desc: "<b>All data and operating systems on the selected disk will be permanently deleted.</b> The entire storage space will be optimized for ro-ASD from scratch. This is the cleanest and recommended method for a fresh start.",
        p5Opt2Title: `Install Alongside <span class="tooltip-icon" data-title="This option allows you to safely install ro-ASD in a new empty space (Shrinking) on your disk without touching your existing Windows or other Linux distributions. You can choose which OS to boot into at startup (Dual Boot).">?</span>`,
        p5Opt2Desc: "Installs safely (Dual Boot) by creating an additional partition <b>without touching</b> your existing Windows or other systems (data).",
        p5Opt3Title: "Manual Partitioning",
        p5Opt3Desc: "Configure the disks yourself.",
        p5LblFs: `Installation File System (Format) <span class="tooltip-icon" style="text-transform: none; cursor: help;" data-title="Determines the read/write architecture of your Linux disk (Partition). You can choose Ext4 (Standard), BTRFS (Snapshot/Backup supported, SSD friendly) or XFS (High capacity/Server).">?</span>`,
        p5LblSpace: "Installation Space Allocated for ro-ASD:",
        p5ManDesc: "When you continue, you can create disk partitions, file systems (Ext4, BTRFS etc.), and mount points as you wish.",
        p5ManBtn: "Advanced Partition Tool (KPMcore)",
        p5GrubInfo: "ℹ️ <b>Bootloader:</b> When the installation is complete, GRUB2 (Bootloader) will be installed and configured on your disk.",

        p6Title: "Time and Region Settings",
        p6Desc: "Configure system location and clock.",
        p6LblRegion: "Region / City",
        p6LblLang: "System Language (Locale)",
        p6StartInstall: "Start System Installation",

        p7Title: "Installation in Progress...",
        p7ToggleLog: "Show / Hide Installation Logs",
        p7Reboot: "Reboot System"
    }
};

function changeLanguage(lang) {
    const t = translations[lang];
    if (!t) return;

    // Top Bar & Welcome
    safelySetText('topTitle', t.topTitle);
    safelySetText('welcomeDesc', t.welcomeDesc);
    safelySetText('startBtn', t.startBtn);
    safelySetText('welcomeTitle', 'ro-Installer');

    // Sidebar
    safelySetText('spStep1', t.step1); safelySetText('spStep2', t.step2);
    safelySetText('spStep3', t.step3); safelySetText('spStep4', t.step4);
    safelySetText('spStep5', t.step5); safelySetText('spStep6', t.step6);
    safelySetText('spStep7', t.step7);

    // Global Buttons
    document.querySelectorAll('.btn-secondary[onclick="prevPage()"]').forEach(b => b.innerText = t.btnBack);
    document.querySelectorAll('.btn-primary[onclick="nextPage()"]').forEach(b => {
        if (b.id !== 'startBtn') b.innerText = t.btnContinue;
    });

    // Page 2
    document.querySelector('#page-2 h2').innerText = t.p2Title;
    document.querySelector('#page-2 p').innerText = t.p2Desc;
    document.querySelector('#page-2 .btn-primary').innerText = t.p2Btn;

    // Page 3
    document.querySelector('#page-3 h2').innerText = t.p3Title;
    document.querySelector('#page-3 > div > p').innerText = t.p3Desc;

    const p3Labels = [t.p3LblName, t.p3LblSurname, t.p3LblUser, t.p3LblPass, t.p3LblPassConf, t.p3LblRoot, t.p3LblRootConf];
    // Sadece doğrudan form-group içindeki label'ları seç (switch container label'ını hatayla almasına engel ol)
    const p3LabelEls = document.querySelectorAll('#page-3 .form-group > label');
    p3LabelEls.forEach((el, index) => { if (p3Labels[index] && el) el.innerText = p3Labels[index]; });

    document.querySelector('#page-3 .toggle-group span').innerText = t.p3SpanSudo;
    document.querySelector('#page-3 .toggle-group p').innerText = t.p3DescSudo;

    // Page 4
    document.querySelector('#page-4 h2').innerText = t.p4Title;
    document.querySelector('#page-4 > div > p').innerText = t.p4Desc;

    const p4Cards = document.querySelectorAll('#page-4 .selection-card');
    p4Cards[0].querySelector('h3').innerText = t.p4Opt1Title;
    p4Cards[0].querySelector('p').innerHTML = t.p4Opt1Desc;
    p4Cards[1].querySelector('h3').innerText = t.p4Opt2Title;
    p4Cards[1].querySelector('p').innerHTML = t.p4Opt2Desc;

    // Page 5
    document.querySelector('#page-5 h2').innerText = t.p5Title;
    document.querySelector('#page-5 > div > p').innerText = t.p5Desc;

    const p5Cards = document.querySelectorAll('#page-5 .selection-card');
    p5Cards[0].querySelector('h3').innerHTML = t.p5Opt1Title; p5Cards[0].querySelector('p').innerHTML = t.p5Opt1Desc;
    p5Cards[1].querySelector('h3').innerHTML = t.p5Opt2Title; p5Cards[1].querySelector('p').innerHTML = t.p5Opt2Desc;
    p5Cards[2].querySelector('h3').innerHTML = t.p5Opt3Title; p5Cards[2].querySelector('p').innerHTML = t.p5Opt3Desc;

    document.querySelector('#fs-selection label').innerHTML = t.p5LblFs;
    document.querySelector('#custom-disk-options label').innerText = t.p5LblSpace;
    document.querySelector('#manual-partitioning-box p').innerText = t.p5ManDesc;
    document.querySelector('#manual-partitioning-box button').innerText = t.p5ManBtn;

    const grubInfo = document.querySelector('#page-5 div[style*="border-left"]');
    if (grubInfo) grubInfo.innerHTML = t.p5GrubInfo;

    // Page 6
    document.querySelector('#page-6 h2').innerText = t.p6Title;
    document.querySelector('#page-6 > div > p').innerText = t.p6Desc;
    const p6Labels = document.querySelectorAll('#page-6 label');
    if (p6Labels[0]) p6Labels[0].innerText = t.p6LblRegion;
    if (p6Labels[1]) p6Labels[1].innerText = t.p6LblLang;

    document.querySelector('#page-6 .btn-primary').innerText = t.p6StartInstall;

    // Page 7
    document.querySelector('#page-7 h2').innerText = t.p7Title;
    document.querySelector('#page-7 button.btn-secondary').innerText = t.p7ToggleLog;
    document.querySelector('#reboot-row button').innerText = t.p7Reboot;
}

function safelySetText(id, text) {
    const el = document.getElementById(id);
    if (el) el.innerText = text;
}

// --- BUG FIX: QtWebEngine Translucent Native Dropdown Fix ---
function setupCustomSelects() {
    const selects = document.querySelectorAll('select.custom-dropdown');
    selects.forEach(select => {
        select.classList.add('select-hidden');

        const wrapper = document.createElement('div');
        wrapper.className = 'custom-select-wrapper';
        select.parentNode.insertBefore(wrapper, select);
        wrapper.appendChild(select);

        const customSelect = document.createElement('div');
        customSelect.className = 'custom-select';

        let selectedOpt = select.options[select.selectedIndex];
        customSelect.innerHTML = selectedOpt ? selectedOpt.text : '';
        wrapper.appendChild(customSelect);

        const optionsList = document.createElement('div');
        optionsList.className = 'custom-select-options';

        Array.from(select.options).forEach((opt, idx) => {
            const optionDiv = document.createElement('div');
            optionDiv.className = 'custom-option';
            if (opt.selected) optionDiv.classList.add('selected');
            optionDiv.innerHTML = opt.text;

            optionDiv.addEventListener('click', function (e) {
                e.stopPropagation();
                customSelect.innerHTML = this.innerHTML;
                select.value = opt.value;
                select.dispatchEvent(new Event('change'));

                optionsList.querySelectorAll('.custom-option').forEach(o => o.classList.remove('selected'));
                this.classList.add('selected');

                customSelect.classList.remove('open');
            });
            optionsList.appendChild(optionDiv);
        });

        wrapper.appendChild(optionsList);

        customSelect.addEventListener('click', function (e) {
            e.stopPropagation();
            document.querySelectorAll('.custom-select.open').forEach(s => {
                if (s !== customSelect) s.classList.remove('open');
            });
            this.classList.toggle('open');
        });
    });

    document.addEventListener('click', function () {
        document.querySelectorAll('.custom-select.open').forEach(s => {
            s.classList.remove('open');
        });
    });
}

document.addEventListener("DOMContentLoaded", setupCustomSelects);

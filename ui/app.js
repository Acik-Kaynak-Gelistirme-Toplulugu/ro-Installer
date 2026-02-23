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
        const items = document.querySelectorAll('.wifi-item');
        items.forEach(i => i.classList.remove('selected'));
        e.target.closest('.wifi-item').classList.add('selected');
    }
});

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

    const config = {
        name: document.getElementById('inputName') ? document.getElementById('inputName').value : '',
        surname: document.getElementById('inputSurname') ? document.getElementById('inputSurname').value : '',
        username: document.getElementById('inputUsername') ? document.getElementById('inputUsername').value : 'ro-user',
        sudo: sudoElement ? sudoElement.checked : true,
        kernelType: kernelElement ? kernelElement.innerText : 'Standart',
        diskType: diskElement ? diskElement.innerText : 'Tamamen',
        fsType: fsElement ? fsElement.value : 'ext4'
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
        p4Opt1Desc: "Orijinal ve Kararlı Fedora 43 deposundan çekirdek <br><b>(İnternet bağlantısı ile DNF üzerinden indirilir)</b>",
        p4Opt2Title: "Gelişmiş-Deneysel",
        p4Opt2Desc: "ro-ASD özel, yamalı ve performans odaklı çekirdek <br><b>(Yerel kurulum paketinden gömülür)</b>",

        p5Title: "Sistem Kurulum Diski ve Biçimlendirme",
        p5Desc: "ro-ASD'yi kurmak istediğiniz hedef diski ve kurulum yöntemini seçin.",
        p5Opt1Title: "Tüm Diske Kur",
        p5Opt1Desc: "Disk tamamen silinir.",
        p5Opt2Title: "Yanına Kur",
        p5Opt2Desc: "Sistemlere dokunulmaz.",
        p5Opt3Title: "Elle Bölümleme",
        p5Opt3Desc: "Diskleri siz ayarlayın.",
        p5LblFs: "Kurulum Dosya Sistemi (Format)",
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
        p4Opt1Desc: "Original and stable OS kernel from Fedora 43 repository <br><b>(Requires internet, via DNF)</b>",
        p4Opt2Title: "Advanced / Experimental",
        p4Opt2Desc: "ro-ASD custom, patched, and performance-oriented kernel <br><b>(Embedded from local disk)</b>",

        p5Title: "Installation Disk & Formatting",
        p5Desc: "Select the target disk and installation method for ro-ASD.",
        p5Opt1Title: "Erase Entire Disk",
        p5Opt1Desc: "The disk will be completely erased.",
        p5Opt2Title: "Install Alongside",
        p5Opt2Desc: "Existing OS systems will remain intact.",
        p5Opt3Title: "Manual Partitioning",
        p5Opt3Desc: "Configure the disks yourself.",
        p5LblFs: "Installation File System (Format)",
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
    p5Cards[0].querySelector('h3').innerText = t.p5Opt1Title; p5Cards[0].querySelector('p').innerText = t.p5Opt1Desc;
    p5Cards[1].querySelector('h3').innerText = t.p5Opt2Title; p5Cards[1].querySelector('p').innerText = t.p5Opt2Desc;
    p5Cards[2].querySelector('h3').innerText = t.p5Opt3Title; p5Cards[2].querySelector('p').innerText = t.p5Opt3Desc;

    document.querySelector('#fs-selection label').innerText = t.p5LblFs;
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

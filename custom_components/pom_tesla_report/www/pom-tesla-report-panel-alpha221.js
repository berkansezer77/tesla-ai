class PomTeslaReportPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._frontendBuild = "alpha221-entities-render-safe-autofind-banner";
    this._manualDebugSnapshot = null;
    this._panelMigrationOutput = null;
    this._lastClickDebug = {};
    this.shadowRoot.addEventListener("pointerdown", (ev) => this._handleDelegatedPointerDown(ev), true);
    this.shadowRoot.addEventListener("click", (ev) => this._handleDelegatedClick(ev));
    this.shadowRoot.addEventListener("keydown", (ev) => this._handleDelegatedKeydown(ev));
    ["keydown", "keyup", "keypress"].forEach((type) => {
      this.shadowRoot.addEventListener(type, (ev) => {
        const path = typeof ev.composedPath === "function" ? ev.composedPath() : [];
        if (path.some((node) => node?.classList?.contains?.("entity-picker-modal") || node?.id === "entity_picker_search")) {
          // Keep Home Assistant global shortcuts from seeing picker typing, but do
          // not stop immediate propagation here. The search input's own listener
          // still has to receive input events so filtering can work.
          ev.stopPropagation();
        }
      }, true);
    });
    this._hass = null;
    this._activeTab = "charge";
    this._activeSettingsTab = "general";
    this._activeEntitiesTab = "ai";
    this._aiEntityDraft = null;
    this._reportEntityDraft = null;
    this._entityPickerTarget = "";
    this._entityPickerSearch = "";
    this._autoFindNotice = null;
    this._chargeData = null;
    this._tripData = null;
    this._settingsData = null;
    this._telegramDiagnostics = null;
    this._aiDiagnostics = null;
    this._liveTripDiagnostics = null;
    this._selectedChargeId = "";
    this._selectedTripId = "";
    this._selectedManualTrackingId = "";
    this._selectedStationIndex = -1;
    this._editingCharge = null;
    this._editingTrip = null;
    this._editingManualTracking = null;
    this._editingStation = null;
    this._chargeMapPreview = null;
    this._tripMapPreview = null;
    this._manualTrackingMapPreview = null;
    this._chargeMapRequestId = 0;
    this._tripMapRequestId = 0;
    this._manualTrackingMapRequestId = 0;
    const initialMonthKey = this._monthKeyFromDate(new Date());
    const initialDateKey = this._dateKeyFromDate(new Date());
    this._chargeFilter = "month";
    this._tripFilter = "month";
    this._manualTrackingFilter = "month";
    this._chargeSelectedMonth = initialMonthKey;
    this._tripSelectedMonth = initialMonthKey;
    this._manualTrackingSelectedMonth = initialMonthKey;
    this._chargeRangeStart = initialDateKey;
    this._chargeRangeEnd = initialDateKey;
    this._tripRangeStart = initialDateKey;
    this._tripRangeEnd = initialDateKey;
    this._manualTrackingRangeStart = initialDateKey;
    this._manualTrackingRangeEnd = initialDateKey;
    this._chargeDatePanelOpen = false;
    this._tripDatePanelOpen = false;
    this._manualTrackingDatePanelOpen = false;
    this._tripSettingsSection = "tracking";
    this._dashboardSettingsSection = "general";
    this._status = "";
    this._error = "";
    this._loading = false;
    this._debugEvents = [];
    this._lastApiResults = [];
    this._lastSettingsSaveSummary = {};
    this._initialActiveLoadStarted = false;
    this._lazyLoadMode = true;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._initialActiveLoadStarted && !this._loading) {
      this._initialActiveLoadStarted = true;
      window.setTimeout(() => this._ensureActiveLoaded(), 450);
    }
    // Home Assistant calls the hass setter very frequently. Do not re-render
    // the panel on every hass update after the initial API load. Data is now
    // loaded lazily per active tab instead of by a startup Promise.all burst.
  }

  set panel(panel) {
    this._panel = panel;
  }

  connectedCallback() {
    this._render();
  }

  get _data() {
    if (this._activeTab === "settings") return this._settingsData;
    if (this._activeTab === "trip" || this._activeTab === "manual") return this._tripData;
    return this._chargeData;
  }

  get _lang() {
    const lang = this._settingsData?.language || this._chargeData?.language || this._tripData?.language || "tr";
    return lang === "en" ? "en" : "tr";
  }

  get _currency() {
    return this._settingsData?.currency || this._chargeData?.currency || this._tripData?.currency || "TL";
  }

  _t(key) {
    const dict = {
      tr: {
        title: "POM Tesla Report",
        subtitle: "Şarj, sürüş ve rapor ayarlarını Options menüsüne girmeden canlı yönet.",
        chargeTab: "Şarj Kayıtları",
        tripTab: "Sürüş Kayıtları",
        manualTrackingTab: "Manuel Takip",
        settingsTab: "Ayarlar",
        chargeRecords: "Şarj Kayıtları",
        tripRecords: "Sürüş Kayıtları",
        manualTrackingRecords: "Manuel Takip Kayıtları",
        manualTrackingDetails: "Manuel Takip Detayı",
        manualTrackingRecordsSub: "Manuel takip düğmesi açılıp kapandığında oluşan aktiviteler.",
        manualTrackingEmpty: "Manuel takip kaydı yok.",
        activitySource: "Aktivite",
        settings: "Ayarlar",
        chargingSettings: "Şarj Raporu Ayarları",
        chargingSettingsSub: "Para birimi, rapor modu, yerleşik fiyatlar ve şarj istasyonu presetleri.",
        stationPresets: "Şarj İstasyonu Presetleri",
        stationPresetsSub: "Soldaki listeden kayıtlı istasyona basınca ayarları burada açılır. Yeni istasyon için alanları doldurup Kaydet’e bas.",
        savedStationPresets: "Kayıtlı istasyon presetleri",
        stationEditor: "İstasyon ayarı",
        stationEditorSub: "İsim, birim fiyat ve para birimini düzenle. Kaydet doğrudan ayarlara yazar.",
        currentMonth: "Bu ay",
        allRecords: "Tümü",
        todayRecords: "Bugün",
        dateRange: "Tarih aralığı",
        startDate: "Başlangıç tarihi",
        endDate: "Bitiş tarihi",
        applyRange: "Aralığı uygula",
        selectedMonth: "Seçili ay",
        invalidDateRange: "Tarih aralığı hatalı.",
        refresh: "Yenile",
        addNew: "Yeni kayıt",
        saveNew: "Yeni kayıt ekle",
        saveUpdate: "Kaydı güncelle",
        delete: "Kaydı sil",
        provider: "Provider",
        date: "Tarih",
        energy: "Enerji (kWh)",
        usedEnergy: "Kullanılan enerji (kWh)",
        totalCost: "Toplam maliyet",
        unitPrice: "Birim fiyat",
        currency: "Para birimi",
        source: "Kaynak",
        selectChargeHint: "Soldaki listeden bir şarj kaydı seç. Alanlar anında dolar.",
        selectTripHint: "Soldaki listeden bir sürüş kaydı seç. Alanlar anında dolar.",
        empty: "Kayıt yok.",
        summary: "Aylık özet",
        count: "Kayıt",
        totalEnergy: "Toplam enerji",
        totalCostByCurrency: "Para birimine göre toplam",
        totalDistance: "Toplam mesafe",
        totalDuration: "Toplam süre",
        avgConsumption: "Ortalama tüketim",
        averageSpeed: "Ortalama hız",
        movingAverageSpeed: "Hareket ort. hızı",
        overallAverageSpeed: "Genel ort. hız",
        movingDuration: "Hareket süresi",
        nonMovingDuration: "Durma / mola süresi",
        maxSpeed: "Maksimum hız",
        speedSamples: "Hız örneği",
        speedSamplerInterval: "Hız örnekleme aralığı",
        trafficBreakdown: "Trafik ayrımı",
        stoppedInDrive: "D’de bekleme",
        slowTraffic: "Yavaş trafik",
        normalDrive: "Normal sürüş",
        parkedPause: "Park / mola",
        finalParkWait: "Son Park beklemesi",
        totalElapsed: "Toplam oturum",
        reportDuration: "Rapor süresi",
        lastTrafficClass: "Son trafik sınıfı",
        movingThreshold: "Hareket eşiği",
        loaded: "Kayıtlar yüklendi.",
        saved: "Kaydedildi.",
        deleted: "Silindi.",
        settingsSaved: "Şarj ayarları kaydedildi.",
        confirmChargeDelete: "Bu şarj kaydı silinsin mi?",
        confirmTripDelete: "Bu sürüş kaydı silinsin mi?",
        confirmStationDelete: "Bu şarj istasyonu silinsin mi?",
        missingProvider: "Provider boş olamaz.",
        missingStation: "İstasyon adı ve birim fiyat gerekli.",
        missingTripFields: "Başlangıç/bitiş boş olabilir ama mesafe sayısal ve 0'dan büyük olmalı.",
        invalidChargeNumbers: "Enerji, toplam maliyet ve birim fiyat sayısal olmalı.",
        invalidTripNumbers: "Mesafe, süre, enerji, tüketim ve maliyet sayısal olmalı.",
        loading: "Yükleniyor...",
        noSelection: "Önce bir kayıt seç.",
        panelNote: "Bu panel Options Flow sınırlarını aşmak için eklendi. Satıra tıklayınca alanlar beklemeden dolar.",
        startAddress: "Başlangıç adresi",
        endAddress: "Bitiş adresi",
        distance: "Mesafe (km)",
        durationMinutes: "Süre (dakika)",
        durationText: "Süre metni",
        consumption: "Tüketim (kWh/100 km)",
        autoCalcHint: "Tüketim boş/0 bırakılırsa mesafe ve enerjiye göre yeniden hesaplanır.",
        locationMap: "Konum haritası",
        routeMap: "Rota haritası",
        fullTripMap: "Tüm trip haritası",
        fullAddress: "Tam açık adres",
        loadingMap: "Harita yükleniyor...",
        mapUnavailable: "Bu kayıt için harita üretilemedi.",
        noAddressAvailable: "Bu kayıt için açık adres bulunamadı.",
        reportCurrency: "Rapor para birimi",
        reportMode: "Şarj raporu modu",
        promptMode: "Telegram soru akışı",
        directMode: "Direkt rapor",
        builtInPrices: "Kayıtlı istasyon presetleri",
        builtInPricesSub: "Üstteki ilk üç istasyon raporlarda ve şarj popup tahmini maliyet kartlarında kullanılır. Alttaki istasyonlardan birini 1/2/3 slotuna taşıyabilirsin.",
        reportCostSlots: "Rapor maliyet slotları",
        reportCostSlotsSub: "Bu üç sıra şarj popup ve görsel raporlardaki tahmini maliyet kartlarıdır.",
        savedStationPool: "Diğer kayıtlı istasyonlar",
        moveToReportSlot: "Rapor slotuna taşı",
        setReportSlot: "Raporda göster",
        poolOrder: "Sıra",
        reportSlot: "Rapor slotu",
        reportSlotUpdated: "Rapor maliyet sırası güncellendi.",
        chargeTelegramTests: "Telegram Şarj Testleri",
        chargeTelegramTestsSub: "Aşağıdaki butonlar şarj kayıtlarına veri eklemeden test raporları üretir ve Telegram’a gönderir.",
        sendTestChargeCostReport: "Telegram’a test şarj maliyet özeti gönder",
        sendTestChargeCompletionReport: "Telegram’a test şarj tamamlandı raporu gönder",
        testChargeCostSent: "Test şarj maliyet özeti Telegram’a gönderildi.",
        testChargeCompletionSent: "Test şarj tamamlandı raporu Telegram’a gönderildi.",
        testChargeNoLedger: "Bu işlemler şarj kayıtlarına veri eklemez.",
        superchargerPrice: "Supercharger fiyatı",
        zesPrice: "ZES fiyatı",
        astorPrice: "Astor fiyatı",
        saveChargingSettings: "Şarj ayarlarını kaydet",
        stationName: "İstasyon adı",
        stationCurrency: "İstasyon para birimi",
        stationUnitPrice: "İstasyon birim fiyatı",
        addStation: "İstasyon ekle",
        updateStation: "İstasyonu güncelle",
        saveStation: "Kaydet",
        newStation: "Yeni istasyon",
        deleteStation: "İstasyonu sil",
        clearStationSelection: "Seçimi temizle",
        noStations: "Henüz istasyon preset’i yok.",
        settingsNote: "Ayarlar artık modüler panel mimarisine taşınıyor. Bu ekrana sırayla Şarj, Sürüş, Harita, Rapor ve Veri bölümleri eklenecek.",
        settingsOnline: "SİSTEM ONLINE",
        settingsGeneralNav: "GENEL",
        generalSettings: "Genel Ayarlar",
        generalSettingsSub: "Uygulama dili, debug/diagnostics, ayar dışa/içe aktarma ve sistem özeti.",
        appLanguage: "Uygulama dili",
        languageTurkish: "Türkçe",
        languageEnglish: "English",
        defaultOpenTab: "Varsayılan açılış sekmesi",
        defaultOpenSettings: "Ayarlar",
        defaultOpenCharges: "Şarj Kayıtları",
        defaultOpenTrips: "Sürüş Kayıtları",
        debugDiagnosticsMode: "Debug / diagnostics modu",
        debugDiagnosticsSub: "Hata detaylarını ve destek bilgilerini görünür tutmak için kullanılır.",
        debugDiagnosticsDetails: "Debug çıktısı",
        debugRuntime: "Panel runtime",
        debugApiResults: "Son API çağrıları",
        debugRecentEvents: "Son olaylar",
        debugCopy: "Debug çıktısını kopyala",
        debugCopied: "Debug çıktısı panoya kopyalandı.",
        debugCopyManual: "Pano API kullanılamıyor. Debug çıktısını ekrandan manuel kopyalayabilirsin.",
        debugFrontend: "Frontend / tarayıcı",
        debugDiagnosticsDetails: "Debug çıktısı",
        exportSettings: "Ayarları dışa aktar",
        importSettings: "Ayarları içe aktar",
        importSettingsPlaceholder: "İçe aktarma hazırlık alanı. Şimdilik sadece dosya seçimini doğrular.",
        selectedImportFile: "Seçilen import dosyası",
        systemSummary: "Sistem özeti",
        resourceSummaryShort: "Resource özeti",
        entityStoreAudit: "Panel entity store audit",
        entityStoreAuditSub: "Rapor, AI ve Dashboard seçimlerinin panel store’dan mı yoksa legacy Flow fallback’ten mi geldiğini gösterir.",
        migratePanelStores: "Panel store migration çalıştır",
        panelStoresMigrated: "Panel entity store migration tamamlandı.",
        saveGeneralSettings: "Genel ayarları kaydet",
        generalSettingsSaved: "Genel ayarlar kaydedildi.",
        exportSettingsDone: "Ayarlar JSON olarak indirildi.",
        settingsChargingNav: "ŞARJ",
        settingsTripNav: "SÜRÜŞ",
        settingsMapNav: "HARİTA",
        settingsReportNav: "RAPOR",
        settingsDataNav: "VERİ",
        settingsAIConfigNav: "AI",
        settingsAutomationsNav: "AUTOMATIONS",
        settingsDashboardNav: "DASHBOARD",
        automationSettings: "Automations",
        automationSettingsSub: "Proaktif AI uyarıları ve her otomasyona ait eşik/gecikme değerleri.",
        saveAutomationSettings: "Automations ayarlarını kaydet",
        automationSettingsSaved: "Automations ayarları kaydedildi.",
        dashboardSettings: "Dashboard Ayarları",
        dashboardResourceStorage: "Lovelace resource storage",
        dashboardResourceSummary: "Özet",
        dashboardResourcesInstallDone: "Dashboard resources kurulum/onarım tamamlandı.",
        dashboardResourcesUpdated: "Dashboard resources kontrol edildi.",
        dashboardCheckPaths: "Kontrol edilen pathler",
        dashboardFoundPath: "Bulunan path",
        dashboardType: "Tip",
        dashboardGithub: "GitHub",
        dashboardMissing: "Eksik",
        dashboardInstalled: "Kurulu",
        dashboardCustomCardInfo: "Gerekli dış kartlar",
        dashboardResourceInfo: "POM resource",
        dashboardShowMissingCards: "Eksik kartları göster",
        dashboardInstallResources: "Resources kur / onar",
        dashboardResourcesSub: "Sadece mevcut dashboard için gereken POM Tesla Live Trip Card resource durumunu gösterir ve onarır.",
        dashboardResourcesTitle: "POM Lovelace Resources",
        dashboardGeneralSettings: "Genel Ayarlar",
        dashboardMenuGeneralSub: "Resources, eksik kartlar ve dashboard sistem bilgileri.",
        dashboardMenuGeneral: "Genel Ayarlar",
        dashboardSettingsSub: "Arka plan görsellerini bilgisayarından seçip yükle. Yol yazmana gerek yok.",
        dashboardBackgrounds: "Arka plan görselleri",
        dashboardAllowedTypes: "Desteklenen dosyalar: PNG, JPG, JPEG, WEBP, GIF",
        dashboardCurrentAsset: "Mevcut görsel",
        dashboardChooseFile: "Dosya seç",
        dashboardUpload: "Yükle",
        dashboardResetDefault: "Varsayılana dön",
        dashboardNoFileSelected: "Henüz dosya seçilmedi.",
        dashboardFileReady: "Seçilen dosya",
        dashboardUploadOk: "Dashboard arka planı güncellendi.",
        dashboardBackgroundParked: "Parked background",
        dashboardBackgroundCharging: "Charging background",
        dashboardBackgroundDriving: "Driving background",
        dashboardYoutubeDrivingTitle: "Tesla Safe YouTube Background",
        dashboardYoutubeDrivingSub: "Shows a YouTube iframe instead of the normal driving background when the vehicle is in D/drive. Experimental.",
        dashboardYoutubeDrivingEnabled: "Enable YouTube driving background",
        dashboardYoutubeVideo: "YouTube video URL / ID",
        dashboardYoutubeStartSeconds: "Start second",
        dashboardYoutubeMute: "Mute",
        dashboardYoutubeLoop: "Loop",
        dashboardYoutubeDrivingTitle: "Tesla Safe YouTube Background",
        dashboardYoutubeDrivingSub: "Araç D/drive durumundayken YouTube kaynağını HTML5 video yerine Canvas2D/JSMpeg olarak arka planda gösterir.",
        dashboardYoutubeDrivingEnabled: "Tesla Safe YouTube background aktif",
        dashboardYoutubeVideo: "YouTube video URL / ID",
        dashboardYoutubeStartSeconds: "Başlangıç saniyesi",
        dashboardYoutubeMute: "Mute",
        dashboardYoutubeLoop: "Loop",
        dashboardMenuFullscreen: "Fullscreen",
        dashboardMenuFullscreenSub: "Tam ekran görünüm davranışını yönet.",
        dashboardMenuTopArea: "Üst Alan",
        dashboardMenuTopAreaSub: "Dashboard üst alan slotlarını seç.",
        dashboardMenuSidebar: "Sidebar",
        dashboardMenuSidebarSub: "8 adet sidebar aksiyon slotunu seç.",
        dashboardMenuBackgrounds: "Background",
        dashboardMenuBackgroundsSub: "Parked, charging ve driving görselleri.",
        dashboardMenuBottomBar: "Bottom Bar",
        dashboardMenuBottomBarSub: "Alt bar görünürlük switchleri. Alt bardaki 3 veri alanı artık dashboard ekranından tıklanarak canlı değişir.",
        bottomSlotsLiveNote: "Bottom slot 1/2/3 artık bu ayar sayfasından değil, Tesla dashboard ekranındaki ilgili alt bar alanına tıklanarak canlı değiştirilir.",
        dashboardMenuMap: "Map",
        dashboardMenuMapSub: "Tesla ve person harita geçmiş süresi.",
        dashboardMenuPersonTrack: "Person Track",
        dashboardMenuPersonTrackSub: "Person takip popup ve kişi ayarları.",
        dashboardBottomBarSettings: "Bottom Bar Ayarları",
        dashboardMapSettings: "Map Ayarları",
        dashboardPersonTrackSettings: "Person Track Ayarları",
        location_display_mode: "Konum gösterim modu",
        bottom_slot_1: "Bottom slot 1",
        bottom_slot_2: "Bottom slot 2",
        bottom_slot_3: "Bottom slot 3",
        tesla_map_hours_to_show: "Tesla harita geçmişi",
        person_map_hours_to_show: "Person harita geçmişi",
        person_track_enabled: "Person track etkin",
        person_track_show_button: "Person track butonunu göster",
        person_track_hours_to_show: "Person track geçmiş saati",
        person_track_1_entity: "Person Track 1 entity",
        person_track_1_name: "Person Track 1 adı",
        person_track_1_enabled: "Person Track 1 etkin",
        person_track_2_entity: "Person Track 2 entity",
        person_track_2_name: "Person Track 2 adı",
        person_track_2_enabled: "Person Track 2 etkin",
        person_track_3_entity: "Person Track 3 entity",
        person_track_3_name: "Person Track 3 adı",
        person_track_3_enabled: "Person Track 3 etkin",
        dashboardFullscreenSettings: "Fullscreen ayarları",
        dashboardTopAreaSettings: "Üst Alan",
        dashboardSidebarSettings: "Sidebar",
        saveDashboardSettings: "Dashboard ayarlarını kaydet",
        dashboardSettingsSaved: "Dashboard ayarları kaydedildi.",
        dashboardSettingsSavedRebuild: "Dashboard ayarları kaydedildi. YAML arka planda yeniden oluşturuluyor; birkaç saniye sonra dashboard sayfasını yenile.",
        fullscreen_enabled: "Fullscreen etkin",
        fullscreen_hide_header: "Header gizle",
        fullscreen_hide_sidebar: "Sidebar gizle",
        fullscreen_disable_scroll: "Scroll devre dışı",
        fullscreen_show_button: "Fullscreen butonu göster",
        rebuild_on_save: "Kaydetmede dashboard'u yeniden oluştur",
        dashboardTopHelp: "Üst alanda seçilmiş dashboard entitylerinin hangi slotlarda görüneceğini seç.",
        dashboardTopFontScales: "Üst alan font boyutları",
        dashboardTopFontGlobal: "Genel üst alan font ölçeği",
        dashboardTopFontLeft: "Sol alan font ölçeği",
        dashboardTopFontCenter: "Orta hız font ölçeği",
        dashboardTopFontRight: "Sağ alan font ölçeği",
        dashboardSidebarHelp: "Sidebar düzeni. Her slotta hangi aksiyonun görüneceğini seç.",
        settingsTelegramNav: "TELEGRAM",
        settingsAiNav: "ENTITIES",
        aiSettings: "AI Ayarları",
        aiSettingsSub: "AI davranışı, OpenAI bağlantısı, adres çözümleme ve proaktif uyarılar.",
        aiBehavior: "Davranış",
        aiConnection: "OpenAI",
        aiAddress: "Adres çözümleme",
        aiTelegramContext: "Telegram / bağlam",
        aiAlerts: "Proaktif AI uyarıları",
        aiEnabled: "AI etkin",
        aiPersonality: "AI kişiliği",
        aiAnswerLength: "Cevap uzunluğu",
        aiContextMode: "Context modu",
        aiName: "AI adı",
        openaiApiKey: "OpenAI API key",
        openaiModel: "OpenAI model",
        reverseGeocodingEnabled: "Reverse geocoding / adres çözümleme",
        reverseGeocodingCacheMinutes: "Adres lookup cache süresi",
        reverseGeocodingUseInAi: "Çözümlenen adresi AI context içinde kullan",
        aiMaxOutputTokens: "Maksimum cevap token",
        aiTelegramIncludeContext: "Telegram cevaplarında araç context’i kullan",
        aiConfirmOptionalControls: "Opsiyonel kontrol komutlarında onay iste",
        aiAlertStyle: "Uyarı stili",
        aiAlertCooldownMinutes: "Uyarı cooldown süresi",
        aiAlertLowBatteryEnabled: "Düşük batarya uyarısı",
        aiAlertLowBatteryThreshold: "Düşük batarya eşiği",
        aiAlertPostTripSummaryEnabled: "Sürüş sonrası özet uyarısı",
        aiAlertChargeFinishedEnabled: "Şarj bitti uyarısı",
        aiAlertChargingStoppedEnabled: "Şarj durdu uyarısı",
        aiAlertTirePressureEnabled: "Lastik basıncı uyarısı",
        aiAlertTirePressureThresholdBar: "Lastik basıncı eşiği",
        aiAlertHighBatteryTempEnabled: "Yüksek batarya sıcaklığı uyarısı",
        aiAlertHighBatteryTempThresholdC: "Yüksek batarya sıcaklığı eşiği",
        aiAlertClimateLeftOnEnabled: "Klima açık kaldı uyarısı",
        aiAlertClimateLeftOnDelayMinutes: "Klima açık kaldı gecikmesi",
        aiAlertUnlockedEnabled: "Araç kilitsiz uyarısı",
        aiAlertUnlockedDelayMinutes: "Kilit açık gecikmesi",
        aiAlertDoorWindowOpenEnabled: "Kapı/cam açık uyarısı",
        aiAlertDoorWindowOpenDelayMinutes: "Kapı/cam açık gecikmesi",
        aiAlertWindowOpenInstantEnabled: "Cam açık anlık uyarı",
        saveAISettings: "AI ayarlarını kaydet",
        aiSettingsSaved: "AI ayarları kaydedildi.",
        minutesShort: "dk",
        percentShort: "%",
        psiBarNote: "Mevcut Options Flow değeri ile aynı formatta kaydedilir.",
        personalityProfessional: "Professional",
        personalityFriendly: "Friendly",
        personalityFunny: "Funny",
        personalityShortDirect: "Short direct",
        personalityPremium: "Premium Tesla Assistant",
        personalityTurkishBuddy: "Turkish Buddy",
        answerShort: "Kısa",
        answerNormal: "Normal",
        answerDetailed: "Detaylı",
        contextBasic: "Basic",
        contextSmartAuto: "Smart auto",
        contextSelectedDevice: "Selected device",
        contextSmartManual: "Smart manual",
        contextManualOnly: "Manual only",
        alertStyleRule: "Rule-based",
        alertStyleAI: "AI",
        entitiesAiTab: "AI",
        entitiesReportTab: "RAPOR",
        entitiesDashboardTab: "DASHBOARD",
        entityCategoryVehicleControls: "Araç Kontrolleri",
        entityCategorySensors: "Sensörler",
        entityCategoryDiagnostics: "Diagnostics",
        entityCategoryTeslamate: "Teslamate",
        entityCategoryOther: "Diğer",
        entityExpectedEntity: "Beklenen entity",
        entityCategoryCount: "{count} slot",
        autoFindEntitiesSub: "Önce exact entity_id ve HA entity registry teknik alanlarını kullanır; friendly name sadece son yedektir.",
        entityPickerExpected: "Bu rol için beklenen entity: {entity}",
        entitiesReportPlaceholder: "Rapor entity manager sonraki adımda burada olacak. Şimdilik rapor için kullanılan entityler ayrı yönetilecek.",
        reportEntityManager: "Entities · Rapor Manager",
        reportEntityManagerSub: "Sürüş, şarj ve harita raporlarının kullanacağı ana entity kaynaklarını seç. Bu alan Options Flow rapor entity ayarlarıyla aynı kayıtları yönetir.",
        reportMainTeslaEntity: "Rapor için örnek Tesla entity",
        reportMainTeslaEntitySub: "Auto Find rapor kaynaklarını aynı cihazdan veya teknik entity_id/registry bilgilerinden bulur.",
        saveReportEntities: "Rapor entity ayarlarını kaydet",
        reportEntitiesSaved: "Rapor entity ayarları kaydedildi.",
        reportAutoFindDone: "Rapor Auto Find tamamlandı ve bulunan entityler kaydedildi.",
        reportEntityCount: "Rapor entity",
        reportRoleSlotCount: "Rapor slotu",
        reportMapCount: "Harita entity",
        reportPrimarySources: "Rapor ana kaynakları",
        reportPrimarySourcesSub: "Bu slotlar Options Flow'daki Report Entity Manager alanlarıyla aynı legacy report key'lerine yazılır.",
        entitiesDashboardPlaceholder: "Dashboard entity manager sonraki adımda burada olacak. Şimdilik dashboard entityleri ayrı yönetilecek.",
        dashboardEntityManager: "Entities · Dashboard Manager",
        dashboardEntityManagerSub: "Dashboard görünümünde kullanılan entityleri üst alan, sidebar, bottom bar, harita ve şarj popup bölümlerine göre seç.",
        dashboardMainTeslaEntity: "Dashboard ana örnek entity",
        dashboardMainTeslaEntitySub: "Auto Find dashboard entitylerini önce eski dashboard canonical entity ID'leriyle, sonra teknik registry bilgileriyle bulur.",
        dashboardPrimarySources: "Dashboard entity haritası",
        dashboardPrimarySourcesSub: "Eski dashboard entegrasyonunda kullanılan entityler burada bölüm bölüm yönetilir.",
        dashboardEntityCount: "Seçili dashboard entity",
        dashboardRoleSlotCount: "Dashboard slotu",
        dashboardMissingCount: "Eksik",
        dashboardEntitiesSaved: "Dashboard entityleri kaydedildi.",
        dashboardAutoFindDone: "Dashboard Auto Find tamamlandı.",
        saveDashboardEntities: "Dashboard entitylerini kaydet",
        entityCategoryDashboardTop: "Üst Alan",
        entityCategoryDashboardSidebar: "Sidebar",
        entityCategoryDashboardBottom: "Bottom Bar",
        entityCategoryDashboardMap: "Harita",
        entityCategoryDashboardChargePopup: "Şarj Popup",
        entityCategoryDashboardPerson: "Person Takip",
        entityCategoryDashboardCustomHome: "Custom Home Assistant Entities",
        entityCategoryDashboardVehicleOpenClose: "Araç Açık/Kapalı Durumları",
        dashboardCustomIcon: "MDI icon",
        dashboardCustomIconSub: "Boş bırakılırsa dashboard varsayılan iconu kullanır. Örnek: mdi:home-lightning-bolt",
        aiEntityManager: "Entities · AI Manager",
        aiEntityManagerSub: "POM AI için kullanılacak entity rollerini seç. Rapor ve Dashboard entityleri ayrı bölümlerde yönetilecek.",
        aiMainTeslaEntity: "Ana Tesla örnek entity",
        aiMainTeslaEntitySub: "Auto Find aynı cihazdaki veya aynı Tesla/POM isim kümesindeki entityleri buradan bulmaya çalışır.",
        autoFindEntities: "Auto Find entityleri bul",
        saveAiEntities: "AI entity ayarlarını kaydet",
        aiEntitiesSaved: "AI entity ayarları kaydedildi.",
        aiAutoFindDone: "Auto Find tamamlandı ve bulunan entityler kaydedildi.",
        autoFindStarted: "Dil bağımsız Auto Find arka planda başlatıldı. Panel açık kalabilir; HA kilitlenmez.",
        autoFindWarningTitle: "Auto Find çalışıyor",
        autoFindWarningText: "Bu ekranda kalmanız önerilir. İşlem birkaç dakika sürebilir ve büyük HA kurulumlarında kısa süreli yavaşlama olabilir.",
        autoFindWarningSub: "X ile kapatabilirsiniz; işlem arka planda devam eder.",
        autoFindWarningDoNotLeave: "Do not leave this place, it may take a few minutes.",
        confidenceVeryHigh: "Çok yüksek",
        confidenceHigh: "Yüksek",
        confidenceMedium: "Kontrol et",
        confidenceLow: "Zayıf",
        confidenceManual: "Manual",
        confidenceReason: "Sebep",
        autoFindRunning: "Auto Find arka planda çalışıyor...",
        autoFindStillRunning: "Auto Find hâlâ çalışıyor. Bu sırada Home Assistant kullanılabilir.",
        autoFindFailed: "Auto Find hata verdi.",
        aiExtraDeduped: "Role atanmış entityler Extra AI listesinden otomatik çıkarılır.",
        aiAutoDiscoverToggle: "Cihaz bazlı otomatik keşfi etkin tut",
        entityRole: "Entity rolü",
        selectedEntity: "Seçili entity",
        entityDescription: "Açıklama",
        aiUseAi: "AI",
        aiUseReport: "Rapor",
        aiUseAlerts: "Uyarı",
        aiUseMap: "Harita",
        aiEntityCount: "Seçili entity",
        aiRoleSlotCount: "Rol slotu",
        aiCustomCount: "Ekstra entity",
        customAiEntities: "Ekstra AI entityleri",
        customAiEntitiesSub: "Sabit rol listesine girmeyen özel entityleri AI bağlamına manuel ekleyebilirsin.",
        addAiEntity: "Ekle",
        removeAiEntity: "Kaldır",
        chooseEntity: "Entity seç",
        entityPickerTitle: "Entity seç",
        entityPickerSearch: "Entity ara",
        entityPickerNoResults: "Sonuç yok.",
        entityPickerHint: "Entity adı, görünen isim veya durum ile arayabilirsin.",
        entityNotSelected: "Seçilmedi",
        unknownEntitySelected: "Bilinmeyen varlık seçildi",
        entityPickerTitle: "Home Assistant entity seç",
        entityPickerSearch: "Entity ara",
        entityPickerHint: "Friendly name, entity_id, domain veya mevcut state değerine göre arayabilirsin.",
        entityPickerDebug: "HA entity: {total} · Sonuç: {count} · Kaynak: hass.states + registry",
        noEntityMatch: "Eşleşen entity bulunamadı.",
        close: "Kapat",
        aiReportCount: "Rapor entity",
        aiMapCount: "Harita entity",
        clearAiRole: "Temizle",
        clearAllAiEntities: "Tümünü temizle",
        clearAllAiConfirm: "Tüm AI entity seçimleri temizlensin mi? Kalıcı olması için ardından Kaydet butonuna basmalısın.",
        clearAllAiDraftDone: "AI entity seçimleri temizlendi. Kalıcı yapmak için kaydet.",
        clearAllDashboardEntities: "Tümünü temizle",
        clearAllDashboardConfirm: "Tüm Dashboard entity seçimleri temizlensin mi? Kalıcı olması için ardından Kaydet butonuna basmalısın.",
        clearAllDashboardDraftDone: "Dashboard entity seçimleri temizlendi. Kalıcı yapmak için kaydet.",
        telegramSettings: "Telegram Ayarları",
        telegramSettingsSub: "Rapor cevapları, grup ID, dahili bot ve AI grup dinleyicisi ayarları.",
        telegramHelpTitle: "Ortak Telegram grubu",
        telegramHelpText: "Rapor cevapları ve grup dinleme için tek bir Telegram grup ID kullanılır. Home Assistant Telegram entegrasyonunu kullanabilir veya dahili Telegram bot modunu açabilirsin.",
        useBuiltInTelegramBot: "Dahili Telegram botu kullan",
        telegramBotToken: "Telegram bot token",
        enableBuiltInTelegramPolling: "Dahili Telegram polling listener",
        telegramPollingInterval: "Polling aralığı",
        enableReplies: "Cevapları etkinleştir",
        telegramGroupId: "Telegram grup ID",
        enableTelegramAiGroupListener: "Telegram AI grup dinleyicisi",
        saveTelegramSettings: "Telegram ayarlarını kaydet",
        telegramSettingsSaved: "Telegram ayarları kaydedildi.",
        telegramDiagnostics: "Telegram Test ve Log",
        telegramDiagnosticsSub: "Panelden doğrudan test mesajı gönder ve Telegram hatalarını burada gör.",
        aiDiagnostics: "AI Test ve Log",
        aiDiagnosticsSub: "Panelden doğrudan OpenAI bağlantı testi çalıştır ve AI hatalarını burada gör.",
        aiServiceState: "AI servis durumu",
        aiTestPrompt: "AI test prompt",
        runAITest: "AI testini çalıştır",
        clearAILogs: "AI loglarını temizle",
        aiLog: "AI Log",
        noAILogs: "Henüz AI log yok.",
        aiTestOk: "AI testi başarılı.",
        aiLogsCleared: "AI logları temizlendi.",
        telegramTestMessage: "Test mesajı",
        sendTelegramTest: "Test mesajı gönder",
        pollTelegramOnce: "Polling testini çalıştır",
        clearTelegramLogs: "Logları temizle",
        telegramLog: "Telegram log",
        telegramServiceState: "Servis durumu",
        telegramTestSent: "Telegram test mesajı gönderildi.",
        telegramPollOk: "Telegram polling testi tamamlandı.",
        telegramLogsCleared: "Telegram logları temizlendi.",
        noTelegramLogs: "Henüz log yok.",
        comingSoon: "Bu bölüm sıradaki ayar taşıma aşamasında aktif edilecek.",
        tripReportSettings: "Sürüş Raporu Ayarları",
        tripReportSettingsSub: "Otomatik sürüş takibi, harita toplama ve görsel sürüş raporunda gösterilecek alanlar.",
        tracking: "Takip",
        trackingEmpty: "Takip",
        trackingEmptySub: "Bu bölüm şimdilik boş. Sürüş başlatma ayarları Canlı Sürüş içinden yönetilir.",
        mapCollection: "Harita",
        visualFields: "Rapor Alanları",
        visualFieldsSub: "Sürüş görsel raporunda hangi bölümlerin görüneceğini seç.",
        enableAutoTripTracking: "Otomatik sürüş takibini etkinleştir",
        liveTripSettings: "Canlı Sürüş",
        liveTripSettingsSub: "Otomatik sürüş başlatma ve canlı sürüş hesaplama ayarları.",
        enableLiveTripEngine: "Canlı sürüş hesaplama motorunu etkinleştir",
        liveTripUpdateIntervalSeconds: "Canlı sürüş güncelleme aralığı",
        liveTripTrafficSpeedThreshold: "Trafik hız eşiği",
        liveTripFinishDelaySeconds: "Park sonrası rapor gecikmesi",
        liveTripMinDistanceKm: "Minimum sürüş mesafesi",
        startSpeedThreshold: "Başlangıç hız eşiği",
        enableTripMapCollection: "Sürüş haritası toplamayı etkinleştir",
        tripMapTrackerEntity: "Sürüş haritası tracker entity",
        mapSampleInterval: "Harita örnekleme aralığı",
        minimumMovementMeters: "Minimum hareket metresi",
        enableSeparateMapPng: "Harita PNG'sini ayrı görsel olarak gönder",
        showDistance: "Mesafeyi göster",
        showDuration: "Süreyi göster",
        showTraffic: "Trafikli süreyi göster",
        showAverageSpeed: "Ortalama hızı göster",
        showEnergy: "Enerjiyi göster",
        showConsumption: "Tüketimi göster",
        showBattery: "Batarya bölümünü göster",
        showCost: "Maliyet bölümünü göster",
        showClimate: "Klima bilgisini göster",
        showElevation: "Rakım bilgisini göster",
        showTripMap: "Sürüş haritasını göster",
        saveTripSettings: "Sürüş ayarlarını kaydet",
        tripSettingsSaved: "Sürüş ayarları kaydedildi.",
        tripTelegramTest: "Telegram Test Sürüşü",
        tripTelegramTestSub: "Aşağıdaki araçlar arabayı sürmeden canlı sürüş akışını test etmeni sağlar. Örnek rapor butonu kayıt oluşturmadan görsel rapor üretir; Live Trip test start/end ise simüle sürüş başlatıp bitirerek gerçek akışa daha yakın test yapar.",
        sendTestTripReport: "Telegram’a örnek test sürüşü gönder",
        startLiveTripTest: "Live Trip test start",
        finishLiveTripTest: "Live Trip test end",
        resetLiveTripTest: "Live Trip test reset",
        liveTripTestStarted: "Live Trip test simülasyonu başlatıldı.",
        liveTripTestFinished: "Live Trip test bitirildi ve rapor gönderimi tetiklendi.",
        liveTripTestReset: "Live Trip test sıfırlandı.",
        liveTripTestSubNote: "Start butonu simüle sürüş başlatır. End butonu testi bitirir ve Telegram raporu gönderimini dener.",
        liveTripDebug: "Live Trip debug",
        refreshLiveTripDebug: "Live Trip debug yenile",
        liveTripDebugSub: "Gerçek otomatik canlı sürüş neden başlamadı veya neden rapor göndermedi sorusunu burada kontrol et.",
        liveTripDebugLoaded: "Live Trip debug güncellendi.",
        testTripSent: "Örnek test sürüş raporu Telegram’a gönderildi.",
        testTripNoLedger: "Bu işlem sürüş kayıtlarına veri eklemez.",
        testTripMapIncluded: "Harita dahil",
        testTripMapExcluded: "Harita kapalı",
        secondsShort: "sn",
        metersShort: "m",
        speedUnit: "km/sa",
      },
      en: {
        title: "POM Tesla Report",
        subtitle: "Manage charge, trip, and report settings live without opening the Options screen.",
        chargeTab: "Charge Records",
        tripTab: "Trip Records",
        manualTrackingTab: "Manual Tracking",
        settingsTab: "Settings",
        chargeRecords: "Charge Records",
        tripRecords: "Trip Records",
        manualTrackingRecords: "Manual Tracking Records",
        manualTrackingDetails: "Manual Tracking Details",
        manualTrackingRecordsSub: "Activities created when the manual tracking switch is turned on and off.",
        manualTrackingEmpty: "No manual tracking records.",
        activitySource: "Activity",
        settings: "Settings",
        chargingSettings: "Charging Report Settings",
        chargingSettingsSub: "Currency, report mode, built-in prices, and charging station presets.",
        stationPresets: "Charging Station Presets",
        stationPresetsSub: "Click a saved station on the left to load it here. To add a new station, fill the fields and click Save.",
        savedStationPresets: "Saved station presets",
        stationEditor: "Station editor",
        stationEditorSub: "Edit name, unit price, and currency. Save writes directly to settings.",
        currentMonth: "This month",
        allRecords: "All",
        todayRecords: "Today",
        dateRange: "Date range",
        startDate: "Start date",
        endDate: "End date",
        applyRange: "Apply range",
        selectedMonth: "Selected month",
        invalidDateRange: "Invalid date range.",
        refresh: "Refresh",
        addNew: "New record",
        saveNew: "Add new record",
        saveUpdate: "Update record",
        delete: "Delete record",
        provider: "Provider",
        date: "Date",
        energy: "Energy (kWh)",
        usedEnergy: "Used energy (kWh)",
        totalCost: "Total cost",
        unitPrice: "Unit price",
        currency: "Currency",
        source: "Source",
        selectChargeHint: "Select a charge record on the left. Fields fill instantly.",
        selectTripHint: "Select a trip record on the left. Fields fill instantly.",
        empty: "No records.",
        summary: "Monthly summary",
        count: "Records",
        totalEnergy: "Total energy",
        totalCostByCurrency: "Total by currency",
        totalDistance: "Total distance",
        totalDuration: "Total duration",
        avgConsumption: "Avg. consumption",
        loaded: "Records loaded.",
        saved: "Saved.",
        deleted: "Deleted.",
        settingsSaved: "Charging settings saved.",
        confirmChargeDelete: "Delete this charge record?",
        confirmTripDelete: "Delete this trip record?",
        confirmStationDelete: "Delete this charging station?",
        missingProvider: "Provider cannot be empty.",
        missingStation: "Station name and unit price are required.",
        missingTripFields: "Start/end may be empty, but distance must be numeric and greater than 0.",
        invalidChargeNumbers: "Energy, total cost, and unit price must be numeric.",
        invalidTripNumbers: "Distance, duration, energy, consumption, and cost must be numeric.",
        loading: "Loading...",
        noSelection: "Select a record first.",
        panelNote: "This panel bypasses Options Flow limits. Click a row and the fields fill immediately.",
        startAddress: "Start address",
        endAddress: "End address",
        distance: "Distance (km)",
        durationMinutes: "Duration (minutes)",
        durationText: "Duration text",
        consumption: "Consumption (kWh/100 km)",
        autoCalcHint: "If consumption is empty/0, it is recalculated from distance and energy.",
        locationMap: "Location map",
        routeMap: "Route map",
        fullTripMap: "Full trip map",
        fullAddress: "Full address",
        loadingMap: "Loading map...",
        mapUnavailable: "A map could not be generated for this record.",
        noAddressAvailable: "No full address is available for this record.",
        reportCurrency: "Report currency",
        reportMode: "Charging report mode",
        promptMode: "Telegram prompt flow",
        directMode: "Direct report",
        builtInPrices: "Saved station presets",
        builtInPricesSub: "The first three stations are used by the visual reports and the charge popup estimated-cost cards. Move a lower station into slot 1/2/3 when needed.",
        reportCostSlots: "Report cost slots",
        reportCostSlotsSub: "These three rows are the cost cards used in charge popup and visual reports.",
        savedStationPool: "Other saved stations",
        moveToReportSlot: "Move to report slot",
        setReportSlot: "Show in report",
        poolOrder: "Order",
        reportSlot: "Report slot",
        reportSlotUpdated: "Report cost order updated.",
        chargeTelegramTests: "Telegram Charge Tests",
        chargeTelegramTestsSub: "The buttons below generate test charge visuals and send them to Telegram without writing to charge records.",
        sendTestChargeCostReport: "Send test charging cost summary to Telegram",
        sendTestChargeCompletionReport: "Send test charge completed report to Telegram",
        testChargeCostSent: "Test charging cost summary sent to Telegram.",
        testChargeCompletionSent: "Test charge completed report sent to Telegram.",
        testChargeNoLedger: "These actions do not write anything to charge records.",
        superchargerPrice: "Supercharger price",
        zesPrice: "ZES price",
        astorPrice: "Astor price",
        saveChargingSettings: "Save charging settings",
        stationName: "Station name",
        stationCurrency: "Station currency",
        stationUnitPrice: "Station unit price",
        addStation: "Add station",
        updateStation: "Update station",
        saveStation: "Save",
        newStation: "New station",
        deleteStation: "Delete station",
        clearStationSelection: "Clear selection",
        noStations: "No station presets yet.",
        settingsNote: "Settings are moving into a modular panel architecture. Charging, Trip, Map, Report, and Data sections will be added here step by step.",
        settingsOnline: "SYSTEM ONLINE",
        settingsGeneralNav: "GENERAL",
        generalSettings: "General Settings",
        generalSettingsSub: "App language, debug/diagnostics, settings export/import, and system summary.",
        appLanguage: "App language",
        languageTurkish: "Türkçe",
        languageEnglish: "English",
        defaultOpenTab: "Default opening tab",
        defaultOpenSettings: "Settings",
        defaultOpenCharges: "Charge Records",
        defaultOpenTrips: "Trip Records",
        debugDiagnosticsMode: "Debug / diagnostics mode",
        debugDiagnosticsSub: "Use this to keep error details and support information visible.",
        debugDiagnosticsDetails: "Debug output",
        debugRuntime: "Panel runtime",
        debugApiResults: "Recent API calls",
        debugRecentEvents: "Recent events",
        debugCopy: "Copy debug info",
        debugCopied: "Debug info copied to clipboard.",
        debugCopyManual: "Clipboard API is unavailable. You can manually copy the debug output from the screen.",
        debugFrontend: "Frontend / browser",
        debugDiagnosticsDetails: "Debug output",
        exportSettings: "Export settings",
        importSettings: "Import settings",
        importSettingsPlaceholder: "Import preparation area. For now it validates file selection only.",
        selectedImportFile: "Selected import file",
        systemSummary: "System summary",
        resourceSummaryShort: "Resource summary",
        entityStoreAudit: "Panel entity store audit",
        entityStoreAuditSub: "Shows whether Report, AI, and Dashboard selections come from panel stores or legacy Flow fallback.",
        migratePanelStores: "Run panel store migration",
        panelStoresMigrated: "Panel entity store migration completed.",
        saveGeneralSettings: "Save general settings",
        generalSettingsSaved: "General settings saved.",
        exportSettingsDone: "Settings downloaded as JSON.",
        settingsChargingNav: "CHARGE",
        settingsTripNav: "TRIP",
        settingsMapNav: "MAP",
        settingsReportNav: "REPORT",
        settingsDataNav: "DATA",
        settingsAIConfigNav: "AI",
        settingsAIConfigNav: "AI",
        settingsAutomationsNav: "AUTOMATIONS",
        settingsDashboardNav: "DASHBOARD",
        automationSettings: "Automations",
        automationSettingsSub: "Proactive AI alerts with each automation's threshold/delay next to its switch.",
        saveAutomationSettings: "Save automation settings",
        automationSettingsSaved: "Automation settings saved.",
        dashboardSettings: "Dashboard Settings",
        dashboardMenuGeneral: "General Settings",
        dashboardMenuGeneralSub: "Resources, missing cards and dashboard system information.",
        dashboardGeneralSettings: "General Settings",
        dashboardResourcesTitle: "POM Lovelace Resources",
        dashboardResourcesSub: "Shows and repairs only the POM Tesla Live Trip Card resource required by the current dashboard.",
        dashboardInstallResources: "Install / repair resources",
        dashboardShowMissingCards: "Show missing cards",
        dashboardResourceInfo: "POM resource",
        dashboardCustomCardInfo: "Required external cards",
        dashboardInstalled: "Installed",
        dashboardMissing: "Missing",
        dashboardGithub: "GitHub",
        dashboardType: "Type",
        dashboardFoundPath: "Found path",
        dashboardCheckPaths: "Checked paths",
        dashboardResourcesUpdated: "Dashboard resources checked.",
        dashboardResourcesInstallDone: "Dashboard resources install/repair completed.",
        dashboardResourceSummary: "Summary",
        dashboardResourceStorage: "Lovelace resource storage",
        dashboardSettingsSub: "Choose and upload background images directly from your computer. No manual path is needed.",
        dashboardBackgrounds: "Background images",
        dashboardAllowedTypes: "Supported files: PNG, JPG, JPEG, WEBP, GIF",
        dashboardCurrentAsset: "Current asset",
        dashboardChooseFile: "Choose file",
        dashboardUpload: "Upload",
        dashboardResetDefault: "Reset to default",
        dashboardNoFileSelected: "No file selected yet.",
        dashboardFileReady: "Selected file",
        dashboardUploadOk: "Dashboard background updated.",
        dashboardBackgroundParked: "Parked background",
        dashboardBackgroundCharging: "Charging background",
        dashboardBackgroundDriving: "Driving background",
        dashboardMenuFullscreen: "Fullscreen",
        dashboardMenuFullscreenSub: "Manage full-screen dashboard behavior.",
        dashboardMenuTopArea: "Top Area",
        dashboardMenuTopAreaSub: "Choose dashboard top-area slots.",
        dashboardMenuSidebar: "Sidebar",
        dashboardMenuSidebarSub: "Choose 8 sidebar action slots.",
        dashboardMenuBackgrounds: "Backgrounds",
        dashboardMenuBackgroundsSub: "Parked, charging and driving images.",
        dashboardMenuBottomBar: "Bottom Bar",
        dashboardMenuBottomBarSub: "Bottom bar visibility switches. The 3 bottom data fields are now changed live by tapping them on the dashboard screen.",
        bottomSlotsLiveNote: "Bottom slots 1/2/3 are no longer configured here; tap the related bottom-bar field on the Tesla dashboard to change it live.",
        dashboardMenuMap: "Map",
        dashboardMenuMapSub: "Tesla and person map history hours.",
        dashboardMenuPersonTrack: "Person Track",
        dashboardMenuPersonTrackSub: "Person tracking popup and person settings.",
        dashboardBottomBarSettings: "Bottom Bar Settings",
        dashboardMapSettings: "Map Settings",
        dashboardPersonTrackSettings: "Person Track Settings",
        location_display_mode: "Location display mode",
        bottom_slot_1: "Bottom slot 1",
        bottom_slot_2: "Bottom slot 2",
        bottom_slot_3: "Bottom slot 3",
        tesla_map_hours_to_show: "Tesla map history hours",
        person_map_hours_to_show: "Person map history hours",
        person_track_enabled: "Person track enabled",
        person_track_show_button: "Show person track button",
        person_track_hours_to_show: "Person track hours to show",
        person_track_1_entity: "Person Track 1 entity",
        person_track_1_name: "Person Track 1 name",
        person_track_1_enabled: "Person Track 1 enabled",
        person_track_2_entity: "Person Track 2 entity",
        person_track_2_name: "Person Track 2 name",
        person_track_2_enabled: "Person Track 2 enabled",
        person_track_3_entity: "Person Track 3 entity",
        person_track_3_name: "Person Track 3 name",
        person_track_3_enabled: "Person Track 3 enabled",
        dashboardFullscreenSettings: "Fullscreen settings",
        dashboardTopAreaSettings: "Top Area",
        dashboardSidebarSettings: "Sidebar",
        saveDashboardSettings: "Save dashboard settings",
        dashboardSettingsSaved: "Dashboard settings saved.",
        dashboardSettingsSavedRebuild: "Dashboard settings saved. YAML is regenerating in the background; refresh the dashboard page after a few seconds.",
        fullscreen_enabled: "Fullscreen enabled",
        fullscreen_hide_header: "Hide header",
        fullscreen_hide_sidebar: "Hide sidebar",
        fullscreen_disable_scroll: "Disable scroll",
        fullscreen_show_button: "Show fullscreen button",
        rebuild_on_save: "Rebuild dashboard on save",
        dashboardTopHelp: "Choose which already-selected dashboard entities appear in each top-area slot.",
        dashboardTopFontScales: "Top area font sizes",
        dashboardTopFontGlobal: "Global top area font scale",
        dashboardTopFontLeft: "Left area font scale",
        dashboardTopFontCenter: "Center speed font scale",
        dashboardTopFontRight: "Right area font scale",
        dashboardSidebarHelp: "Sidebar layout. Pick which action appears in each slot.",
        settingsTelegramNav: "TELEGRAM",
        settingsAiNav: "ENTITIES",
        aiSettings: "AI Settings",
        aiSettingsSub: "AI behavior, OpenAI connection, address lookup, and proactive alerts.",
        aiBehavior: "Behavior",
        aiConnection: "OpenAI",
        aiAddress: "Address lookup",
        aiTelegramContext: "Telegram / context",
        aiAlerts: "Proactive AI alerts",
        aiEnabled: "AI enabled",
        aiPersonality: "AI personality",
        aiAnswerLength: "Answer length",
        aiContextMode: "Context mode",
        aiName: "AI name",
        openaiApiKey: "OpenAI API key",
        openaiModel: "OpenAI model",
        reverseGeocodingEnabled: "Reverse geocoding / address lookup",
        reverseGeocodingCacheMinutes: "Address lookup cache minutes",
        reverseGeocodingUseInAi: "Use resolved address in AI context",
        aiMaxOutputTokens: "Max output tokens",
        aiTelegramIncludeContext: "Use vehicle context in Telegram replies",
        aiConfirmOptionalControls: "Ask confirmation for optional control commands",
        aiAlertStyle: "Alert style",
        aiAlertCooldownMinutes: "Alert cooldown minutes",
        aiAlertLowBatteryEnabled: "Low battery alert",
        aiAlertLowBatteryThreshold: "Low battery threshold",
        aiAlertPostTripSummaryEnabled: "Post-trip summary alert",
        aiAlertChargeFinishedEnabled: "Charge finished alert",
        aiAlertChargingStoppedEnabled: "Charging stopped alert",
        aiAlertTirePressureEnabled: "Tire pressure alert",
        aiAlertTirePressureThresholdBar: "Tire pressure threshold",
        aiAlertHighBatteryTempEnabled: "High battery temperature alert",
        aiAlertHighBatteryTempThresholdC: "High battery temperature threshold",
        aiAlertClimateLeftOnEnabled: "Climate left on alert",
        aiAlertClimateLeftOnDelayMinutes: "Climate left on delay",
        aiAlertUnlockedEnabled: "Unlocked vehicle alert",
        aiAlertUnlockedDelayMinutes: "Unlocked delay",
        aiAlertDoorWindowOpenEnabled: "Door/window open alert",
        aiAlertDoorWindowOpenDelayMinutes: "Door/window open delay",
        aiAlertWindowOpenInstantEnabled: "Window open instant alert",
        saveAISettings: "Save AI settings",
        aiSettingsSaved: "AI settings saved.",
        minutesShort: "min",
        percentShort: "%",
        psiBarNote: "Saved in the same format used by the existing Options Flow.",
        personalityProfessional: "Professional",
        personalityFriendly: "Friendly",
        personalityFunny: "Funny",
        personalityShortDirect: "Short direct",
        personalityPremium: "Premium Tesla Assistant",
        personalityTurkishBuddy: "Turkish Buddy",
        answerShort: "Short",
        answerNormal: "Normal",
        answerDetailed: "Detailed",
        contextBasic: "Basic",
        contextSmartAuto: "Smart auto",
        contextSelectedDevice: "Selected device",
        contextSmartManual: "Smart manual",
        contextManualOnly: "Manual only",
        alertStyleRule: "Rule-based",
        alertStyleAI: "AI",
        aiSettings: "AI Ayarları",
        aiSettingsSub: "AI davranışı, OpenAI bağlantısı, adres çözümleme ve proaktif uyarılar.",
        aiBehavior: "Davranış",
        aiConnection: "OpenAI",
        aiAddress: "Adres çözümleme",
        aiTelegramContext: "Telegram / bağlam",
        aiAlerts: "Proaktif AI uyarıları",
        aiEnabled: "AI etkin",
        aiPersonality: "AI kişiliği",
        aiAnswerLength: "Cevap uzunluğu",
        aiContextMode: "Context modu",
        aiName: "AI adı",
        openaiApiKey: "OpenAI API key",
        openaiModel: "OpenAI model",
        reverseGeocodingEnabled: "Reverse geocoding / adres çözümleme",
        reverseGeocodingCacheMinutes: "Adres lookup cache süresi",
        reverseGeocodingUseInAi: "Çözümlenen adresi AI context içinde kullan",
        aiMaxOutputTokens: "Maksimum cevap token",
        aiTelegramIncludeContext: "Telegram cevaplarında araç context’i kullan",
        aiConfirmOptionalControls: "Opsiyonel kontrol komutlarında onay iste",
        aiAlertStyle: "Uyarı stili",
        aiAlertCooldownMinutes: "Uyarı cooldown süresi",
        aiAlertLowBatteryEnabled: "Düşük batarya uyarısı",
        aiAlertLowBatteryThreshold: "Düşük batarya eşiği",
        aiAlertPostTripSummaryEnabled: "Sürüş sonrası özet uyarısı",
        aiAlertChargeFinishedEnabled: "Şarj bitti uyarısı",
        aiAlertChargingStoppedEnabled: "Şarj durdu uyarısı",
        aiAlertTirePressureEnabled: "Lastik basıncı uyarısı",
        aiAlertTirePressureThresholdBar: "Lastik basıncı eşiği",
        aiAlertHighBatteryTempEnabled: "Yüksek batarya sıcaklığı uyarısı",
        aiAlertHighBatteryTempThresholdC: "Yüksek batarya sıcaklığı eşiği",
        aiAlertClimateLeftOnEnabled: "Klima açık kaldı uyarısı",
        aiAlertClimateLeftOnDelayMinutes: "Klima açık kaldı gecikmesi",
        aiAlertUnlockedEnabled: "Araç kilitsiz uyarısı",
        aiAlertUnlockedDelayMinutes: "Kilit açık gecikmesi",
        aiAlertDoorWindowOpenEnabled: "Kapı/cam açık uyarısı",
        aiAlertDoorWindowOpenDelayMinutes: "Kapı/cam açık gecikmesi",
        aiAlertWindowOpenInstantEnabled: "Cam açık anlık uyarı",
        saveAISettings: "AI ayarlarını kaydet",
        aiSettingsSaved: "AI ayarları kaydedildi.",
        minutesShort: "dk",
        percentShort: "%",
        psiBarNote: "Mevcut Options Flow değeri ile aynı formatta kaydedilir.",
        personalityProfessional: "Professional",
        personalityFriendly: "Friendly",
        personalityFunny: "Funny",
        personalityShortDirect: "Short direct",
        personalityPremium: "Premium Tesla Assistant",
        personalityTurkishBuddy: "Turkish Buddy",
        answerShort: "Kısa",
        answerNormal: "Normal",
        answerDetailed: "Detaylı",
        contextBasic: "Basic",
        contextSmartAuto: "Smart auto",
        contextSelectedDevice: "Selected device",
        contextSmartManual: "Smart manual",
        contextManualOnly: "Manual only",
        alertStyleRule: "Rule-based",
        alertStyleAI: "AI",
        entitiesAiTab: "AI",
        entitiesReportTab: "REPORT",
        entitiesDashboardTab: "DASHBOARD",
        entityCategoryVehicleControls: "Vehicle Controls",
        entityCategorySensors: "Sensors",
        entityCategoryDiagnostics: "Diagnostics",
        entityCategoryTeslamate: "Teslamate",
        entityCategoryOther: "Other",
        entityExpectedEntity: "Expected entity",
        entityCategoryCount: "{count} slots",
        autoFindEntitiesSub: "Uses exact entity IDs and HA entity registry technical fields first; friendly names are only a last-resort fallback.",
        entityPickerExpected: "Expected entity for this role: {entity}",
        entitiesReportPlaceholder: "Report entity manager will be added here next. For now, report entities are managed separately.",
        reportEntityManager: "Entities · Report Manager",
        reportEntityManagerSub: "Select the primary entity sources used by trip, charging, and map reports. This panel manages the same records as the Options Flow report entity step.",
        reportMainTeslaEntity: "Sample Tesla entity for reports",
        reportMainTeslaEntitySub: "Auto Find discovers report sources from the same device or from technical entity_id/registry metadata.",
        saveReportEntities: "Save report entity settings",
        reportEntitiesSaved: "Report entity settings saved.",
        reportAutoFindDone: "Report Auto Find completed and saved the discovered entities.",
        reportEntityCount: "Report entities",
        reportRoleSlotCount: "Report slots",
        reportMapCount: "Map entities",
        reportPrimarySources: "Primary report sources",
        reportPrimarySourcesSub: "These slots write to the same legacy report keys used by the Options Flow Report Entity Manager.",
        entitiesDashboardPlaceholder: "Dashboard entity manager will be added here next. For now, dashboard entities are managed separately.",
        dashboardEntityManager: "Entities · Dashboard Manager",
        dashboardEntityManagerSub: "Select dashboard entities by top area, sidebar, bottom bar, map, and charge popup sections.",
        dashboardMainTeslaEntity: "Dashboard main sample entity",
        dashboardMainTeslaEntitySub: "Auto Find matches dashboard entities using old dashboard canonical entity IDs first, then technical registry metadata.",
        dashboardPrimarySources: "Dashboard entity map",
        dashboardPrimarySourcesSub: "Entities used by the old dashboard integration are managed here section by section.",
        dashboardEntityCount: "Selected dashboard entities",
        dashboardRoleSlotCount: "Dashboard slots",
        dashboardMissingCount: "Missing",
        dashboardEntitiesSaved: "Dashboard entities saved.",
        dashboardAutoFindDone: "Dashboard Auto Find completed.",
        saveDashboardEntities: "Save dashboard entities",
        entityCategoryDashboardTop: "Top Area",
        entityCategoryDashboardSidebar: "Sidebar",
        entityCategoryDashboardBottom: "Bottom Bar",
        entityCategoryDashboardMap: "Map",
        entityCategoryDashboardChargePopup: "Charge Popup",
        entityCategoryDashboardPerson: "Person Tracking",
        entityCategoryDashboardCustomHome: "Custom Home Assistant Entities",
        entityCategoryDashboardVehicleOpenClose: "Vehicle Open/Close Status",
        dashboardCustomIcon: "MDI icon",
        dashboardCustomIconSub: "Leave empty to use the dashboard default icon. Example: mdi:home-lightning-bolt",
        aiEntityManager: "Entities · AI Manager",
        aiEntityManagerSub: "Select entity roles used by POM AI. Report and Dashboard entities will be managed in separate sections.",
        aiMainTeslaEntity: "Main Tesla sample entity",
        aiMainTeslaEntitySub: "Auto Find uses this entity to discover same-device or same Tesla/POM entity groups.",
        autoFindEntities: "Auto Find entities",
        saveAiEntities: "Save AI entity settings",
        aiEntitiesSaved: "AI entity settings saved.",
        aiAutoFindDone: "Auto Find completed and saved discovered entities.",
        autoFindStarted: "Language-independent Auto Find started in the background. The panel can stay open; HA will not be blocked.",
        autoFindWarningTitle: "Auto Find is running",
        autoFindWarningText: "Please stay on this screen. This may take a few minutes and large Home Assistant systems can briefly slow down.",
        autoFindWarningSub: "You can close this warning with X; the background job will continue.",
        autoFindWarningDoNotLeave: "Do not leave this place, it may take a few minutes.",
        confidenceVeryHigh: "Very high",
        confidenceHigh: "High",
        confidenceMedium: "Review",
        confidenceLow: "Weak",
        confidenceManual: "Manual",
        confidenceReason: "Reason",
        autoFindRunning: "Auto Find is running in the background...",
        autoFindStillRunning: "Auto Find is still running. Home Assistant remains usable.",
        autoFindFailed: "Auto Find failed.",
        aiExtraDeduped: "Entities assigned to fixed roles are automatically removed from Extra AI.",
        aiAutoDiscoverToggle: "Keep device-based auto discovery enabled",
        entityRole: "Entity role",
        selectedEntity: "Selected entity",
        entityDescription: "Description",
        aiUseAi: "AI",
        aiUseReport: "Report",
        aiUseAlerts: "Alert",
        aiUseMap: "Map",
        aiEntityCount: "Selected entities",
        aiRoleSlotCount: "Role slots",
        aiCustomCount: "Extra entities",
        customAiEntities: "Extra AI entities",
        customAiEntitiesSub: "Manually add custom context entities that do not fit the fixed role list.",
        addAiEntity: "Add entry",
        removeAiEntity: "Remove",
        chooseEntity: "Choose entity",
        entityPickerTitle: "Choose entity",
        entityPickerSearch: "Search entity",
        entityPickerNoResults: "No results.",
        entityPickerHint: "Search by entity ID, display name, or state.",
        entityNotSelected: "Not selected",
        unknownEntitySelected: "Unknown entity selected",
        entityPickerTitle: "Choose Home Assistant entity",
        entityPickerSearch: "Search entity",
        entityPickerHint: "Search by friendly name, entity ID, domain, or current state.",
        entityPickerDebug: "HA entities: {total} · Results: {count} · Source: hass.states + registry",
        noEntityMatch: "No matching entity found.",
        close: "Close",
        aiReportCount: "Report entities",
        aiMapCount: "Map entities",
        clearAiRole: "Clear",
        clearAllAiEntities: "Clear all",
        clearAllAiConfirm: "Clear all AI entity selections? To make this permanent, press Save afterward.",
        clearAllAiDraftDone: "AI entity selections cleared. Press Save to make it permanent.",
        clearAllDashboardEntities: "Clear all",
        clearAllDashboardConfirm: "Clear all Dashboard entity selections? To make this permanent, press Save afterward.",
        clearAllDashboardDraftDone: "Dashboard entity selections cleared. Press Save to make it permanent.",
        telegramSettings: "Telegram Settings",
        telegramSettingsSub: "Report replies, group ID, built-in bot, and AI group listener settings.",
        telegramHelpTitle: "Shared Telegram group",
        telegramHelpText: "One Telegram group ID is used for report replies and group listening. You can keep using Home Assistant's Telegram integration or enable the built-in Telegram bot mode.",
        useBuiltInTelegramBot: "Use built-in Telegram bot",
        telegramBotToken: "Telegram bot token",
        enableBuiltInTelegramPolling: "Built-in Telegram polling listener",
        telegramPollingInterval: "Polling interval",
        enableReplies: "Enable replies",
        telegramGroupId: "Telegram group ID",
        enableTelegramAiGroupListener: "Telegram AI group listener",
        saveTelegramSettings: "Save Telegram settings",
        telegramSettingsSaved: "Telegram settings saved.",
        telegramDiagnostics: "Telegram Test & Logs",
        telegramDiagnosticsSub: "Send a direct test message from the panel and see Telegram errors here.",
        aiDiagnostics: "AI Test & Logs",
        aiDiagnosticsSub: "Run a direct OpenAI connectivity test from the panel and see AI errors here.",
        aiServiceState: "AI service state",
        aiTestPrompt: "AI test prompt",
        runAITest: "Run AI test",
        clearAILogs: "Clear AI logs",
        aiLog: "AI Log",
        noAILogs: "No AI logs yet.",
        aiTestOk: "AI test succeeded.",
        aiLogsCleared: "AI logs cleared.",
        telegramTestMessage: "Test message",
        sendTelegramTest: "Send test message",
        pollTelegramOnce: "Run polling test",
        clearTelegramLogs: "Clear logs",
        telegramLog: "Telegram log",
        telegramServiceState: "Service state",
        telegramTestSent: "Telegram test message sent.",
        telegramPollOk: "Telegram polling test completed.",
        telegramLogsCleared: "Telegram logs cleared.",
        noTelegramLogs: "No logs yet.",
        comingSoon: "This section will become active in the next settings migration step.",
        tripReportSettings: "Trip Report Settings",
        tripReportSettingsSub: "Automatic trip tracking, map collection, and fields shown in the visual trip report.",
        tracking: "Tracking",
        mapCollection: "Map",
        visualFields: "Report Fields",
        visualFieldsSub: "Choose which sections are shown in the visual trip report.",
        enableAutoTripTracking: "Enable automatic trip tracking",
        liveTripSettings: "Live Trip",
        liveTripSettingsSub: "Automatic trip-start and live trip calculation settings.",
        enableLiveTripEngine: "Enable live trip calculation engine",
        liveTripUpdateIntervalSeconds: "Live trip update interval seconds",
        liveTripTrafficSpeedThreshold: "Traffic speed threshold",
        liveTripFinishDelaySeconds: "Report delay after Park",
        liveTripMinDistanceKm: "Minimum trip distance",
        startSpeedThreshold: "Start speed threshold",
        enableTripMapCollection: "Enable trip map collection",
        tripMapTrackerEntity: "Trip map tracker entity",
        mapSampleInterval: "Map sample interval",
        minimumMovementMeters: "Minimum movement meters",
        enableSeparateMapPng: "Send map PNG as a separate image",
        showDistance: "Show distance",
        showDuration: "Show duration",
        showTraffic: "Show traffic duration",
        showAverageSpeed: "Show average speed",
        showEnergy: "Show energy",
        showConsumption: "Show consumption",
        showBattery: "Show battery section",
        showCost: "Show cost section",
        showClimate: "Show climate info",
        showElevation: "Show elevation info",
        showTripMap: "Show trip map",
        saveTripSettings: "Save trip settings",
        tripSettingsSaved: "Trip settings saved.",
        tripTelegramTest: "Telegram Test Trip",
        tripTelegramTestSub: "These tools let you test the live trip flow without driving the car. The sample report button renders a visual-only report; Live Trip test start/end simulates a trip and is closer to the real report pipeline.",
        sendTestTripReport: "Send sample test trip to Telegram",
        startLiveTripTest: "Live Trip test start",
        finishLiveTripTest: "Live Trip test end",
        resetLiveTripTest: "Live Trip test reset",
        liveTripTestStarted: "Live Trip test simulation started.",
        liveTripTestFinished: "Live Trip test finished and report sending was triggered.",
        liveTripTestReset: "Live Trip test was reset.",
        liveTripTestSubNote: "Start begins a simulated trip. End finishes the test and attempts Telegram report delivery.",
        liveTripDebug: "Live Trip debug",
        refreshLiveTripDebug: "Refresh Live Trip debug",
        liveTripDebugSub: "Use this to see why automatic live trip did not start or did not send a report.",
        liveTripDebugLoaded: "Live Trip debug refreshed.",
        testTripSent: "Sample test trip report sent to Telegram.",
        testTripNoLedger: "This action does not write anything to trip records.",
        testTripMapIncluded: "Map included",
        testTripMapExcluded: "Map hidden",
        secondsShort: "s",
        metersShort: "m",
        speedUnit: "km/h",
      }
    };
    return (dict[this._lang] || dict.tr)[key] || key;
  }

  _formatError(err) {
    if (!err) return "API error";
    if (typeof err === "string") return err.slice(0, 1200);

    const pickString = (value) => {
      if (!value) return "";
      if (typeof value === "string") return value;
      if (typeof value === "object") {
        if (typeof value.error === "string") return value.error;
        if (typeof value.message === "string") return value.message;
        if (typeof value.body === "string") {
          try {
            const parsed = JSON.parse(value.body);
            return pickString(parsed) || value.body;
          } catch (_e) {
            return value.body;
          }
        }
      }
      try { return JSON.stringify(value); } catch (_e) { return String(value); }
    };

    let text = pickString(err.response) || pickString(err.message) || pickString(err.body) || pickString(err);
    if (text.includes("Bad Request: chat not found")) {
      text = "Telegram chat not found. Bot bu gruba ekli değil, bot token yanlış gruba ait veya group ID hatalı.";
    }
    return String(text || "API error").slice(0, 1200);
  }

  _normalizeApiPayload(payload, fallbackCurrency = "") {
    if (!payload || typeof payload !== "object") {
      return { success: false, language: this._lang, currency: fallbackCurrency, records: [], summary: {} };
    }
    const records = Array.isArray(payload.records) ? payload.records : [];
    const summary = payload.summary && typeof payload.summary === "object" ? payload.summary : {};
    return { ...payload, records, summary };
  }


  _deepMergeSettingsObject(base, patch) {
    const output = { ...(base || {}) };
    Object.entries(patch || {}).forEach(([key, value]) => {
      if (value && typeof value === "object" && !Array.isArray(value)) {
        output[key] = this._deepMergeSettingsObject(output[key] || {}, value);
      } else {
        output[key] = value;
      }
    });
    return output;
  }

  _applySettingsSaveResponse(response, localPatch = {}) {
    const current = this._settingsData || this._normalizeSettingsPayload({});
    if (!response || !response.partial_update) {
      return this._normalizeSettingsPayload(response || current);
    }
    let merged = { ...current };
    if (response.language) merged.language = response.language;
    if (response.currency) merged.currency = response.currency;
    if (Array.isArray(response.currency_options)) merged.currency_options = response.currency_options;

    const sections = [
      "general_settings",
      "charging",
      "telegram",
      "trip_reports",
      "ai_settings",
      "dashboard_settings",
      "ai_entity_manager",
      "report_entity_manager",
      "dashboard_entity_manager",
    ];

    sections.forEach((section) => {
      const patchValue = localPatch?.[section];
      const responseValue = response?.[section];
      if (patchValue === undefined && responseValue === undefined) return;
      if (
        ["ai_entity_manager", "report_entity_manager", "dashboard_entity_manager"].includes(section) &&
        responseValue && typeof responseValue === "object"
      ) {
        // Entity-manager save responses are authoritative. This is important
        // for Auto Find: the request payload contains the old/empty draft, but
        // the response contains the newly discovered entries.
        merged[section] = responseValue;
      } else if (Array.isArray(patchValue) || Array.isArray(responseValue)) {
        merged[section] = responseValue !== undefined ? responseValue : patchValue;
      } else if (
        (patchValue && typeof patchValue === "object") ||
        (responseValue && typeof responseValue === "object")
      ) {
        merged[section] = this._deepMergeSettingsObject(
          this._deepMergeSettingsObject(merged[section] || {}, patchValue || {}),
          responseValue || {},
        );
      } else {
        merged[section] = responseValue !== undefined ? responseValue : patchValue;
      }
    });

    merged.success = true;
    return this._normalizeSettingsPayload(merged);
  }


  _normalizeTelegramCommandWord(value, fallback = "") {
    const raw = String(value ?? fallback ?? "").trim();
    const first = raw.split(/\s+/)[0] || "";
    const withoutSlash = first.replace(/^\/+/, "").split("@")[0].replace(/\/+$/g, "");
    const cleaned = withoutSlash.toLowerCase().replace(/[^a-z0-9_\-\u00c0-\u024fğüşöçıİĞÜŞÖÇ]/gi, "");
    return cleaned || String(fallback || "").replace(/^\/+/, "").toLowerCase();
  }

  _defaultTelegramReportCommands() {
    return {
      charge_report: "charge",
      trip_summary: "trip",
      trip_all: "tripall",
      trip_single: "single",
      trip_last: "triplast",
    };
  }

  _telegramReportCommands(input = {}) {
    const defaults = this._defaultTelegramReportCommands();
    const raw = input && typeof input === "object" ? input : {};
    return Object.fromEntries(Object.entries(defaults).map(([key, value]) => [
      key,
      this._normalizeTelegramCommandWord(raw[key], value),
    ]));
  }

  _normalizeSettingsPayload(payload) {
    const currency = payload?.currency || this._currency || "TL";
    const charging = payload?.charging && typeof payload.charging === "object" ? payload.charging : {};
    const provider_presets = Array.isArray(charging.provider_presets) ? charging.provider_presets : [];
    const trip = payload?.trip_reports && typeof payload.trip_reports === "object" ? payload.trip_reports : {};
    const aiManager = payload?.ai_entity_manager && typeof payload.ai_entity_manager === "object" ? payload.ai_entity_manager : {};
    const reportManager = payload?.report_entity_manager && typeof payload.report_entity_manager === "object" ? payload.report_entity_manager : {};
    const dashboardManager = payload?.dashboard_entity_manager && typeof payload.dashboard_entity_manager === "object" ? payload.dashboard_entity_manager : {};
    const aiEntries = Array.isArray(aiManager.entries) ? aiManager.entries : [];
    const aiRoles = Array.isArray(aiManager.roles) ? aiManager.roles : [];
    const reportEntries = Array.isArray(reportManager.entries) ? reportManager.entries : [];
    const reportRoles = Array.isArray(reportManager.roles) ? reportManager.roles : [];
    const dashboardEntries = Array.isArray(dashboardManager.entries) ? dashboardManager.entries : [];
    const dashboardRoles = Array.isArray(dashboardManager.roles) ? dashboardManager.roles : [];
    const entityOptions = Array.isArray(aiManager.entity_options)
      ? aiManager.entity_options
      : (Array.isArray(reportManager.entity_options)
        ? reportManager.entity_options
        : (Array.isArray(dashboardManager.entity_options) ? dashboardManager.entity_options : []));
    return {
      success: Boolean(payload?.success ?? true),
      language: payload?.language || this._lang,
      currency,
      currency_options: Array.isArray(payload?.currency_options) ? payload.currency_options : ["TL", "EUR", "USD", "GBP"],
      general_settings: {
        app_language: payload?.general_settings?.app_language || payload?.language || this._lang || "tr",
        debug_enabled: Boolean(payload?.general_settings?.debug_enabled ?? false),
        default_open_tab: payload?.general_settings?.default_open_tab || "settings",
        resource_summary: payload?.general_settings?.resource_summary || {},
        system: payload?.general_settings?.system || {},
        entity_store_audit: payload?.general_settings?.entity_store_audit || payload?.entity_store_audit || {},
      },
      migration: payload?.migration || {},
      charging: {
        report_currency: charging.report_currency || currency,
        charging_report_mode: charging.charging_report_mode || "prompt",
        supercharger_price: Number(charging.supercharger_price || 9.9),
        zes_price: Number(charging.zes_price || 16.49),
        astor_price: Number(charging.astor_price || 12.49),
        provider_presets: provider_presets.map((p) => ({
          id: p.id || String(p.name || "").toLowerCase(),
          name: p.name || "",
          unit_price: Number(p.unit_price || p.price || 0),
          currency: p.currency || currency,
        })).filter((p) => p.name && p.unit_price > 0),
      },
      ai_entity_manager: {
        main_entity: aiManager.main_entity || "",
        auto_discover_device_entities: Boolean(aiManager.auto_discover_device_entities ?? true),
        entries: aiEntries.map((item) => ({
          entity_id: item.entity_id || "",
          role: item.role || "other",
          label: item.label || "",
          use_ai: Boolean(item.use_ai ?? true),
          use_report: Boolean(item.use_report ?? false),
          use_alerts: Boolean(item.use_alerts ?? false),
          use_map: Boolean(item.use_map ?? false),
          source: item.source || "",
        })).filter((item) => item.entity_id),
        roles: aiRoles,
        entity_options: entityOptions,
        summary: aiManager.summary || {},
      },
      report_entity_manager: {
        main_entity: reportManager.main_entity || "",
        entries: reportEntries.map((item) => ({
          entity_id: item.entity_id || "",
          role: item.role || "other",
          label: item.label || "",
          use_ai: Boolean(item.use_ai ?? true),
          use_report: Boolean(item.use_report ?? true),
          use_alerts: Boolean(item.use_alerts ?? false),
          use_map: Boolean(item.use_map ?? false),
          source: item.source || "",
        })).filter((item) => item.entity_id),
        roles: reportRoles,
        entity_options: Array.isArray(reportManager.entity_options) ? reportManager.entity_options : entityOptions,
        summary: reportManager.summary || {},
      },
      dashboard_entity_manager: {
        main_entity: dashboardManager.main_entity || "",
        entries: dashboardEntries.map((item) => ({
          entity_id: item.entity_id || "",
          role: item.role || "other",
          label: item.label || "",
          icon: item.icon || "",
          name: item.name || "",
          source: item.source || "",
        })).filter((item) => item.entity_id),
        roles: dashboardRoles,
        entity_options: Array.isArray(dashboardManager.entity_options) ? dashboardManager.entity_options : entityOptions,
        summary: dashboardManager.summary || {},
      },
      ai_settings: {
        ...(payload?.ai_settings || {}),
        reverse_geocoding_cache_minutes: Math.max(5, Number(payload?.ai_settings?.reverse_geocoding_cache_minutes ?? 60)),
      },
      dashboard_settings: {
        resources_status: payload?.dashboard_settings?.resources_status || {},
        images: {
          parked: payload?.dashboard_settings?.images?.parked || "",
          charging: payload?.dashboard_settings?.images?.charging || "",
          driving: payload?.dashboard_settings?.images?.driving || "",
        },
        defaults: {
          parked: payload?.dashboard_settings?.defaults?.parked || "",
          charging: payload?.dashboard_settings?.defaults?.charging || "",
          driving: payload?.dashboard_settings?.defaults?.driving || "",
        },
        allowed_extensions: Array.isArray(payload?.dashboard_settings?.allowed_extensions) ? payload.dashboard_settings.allowed_extensions : ["png", "jpg", "jpeg", "webp", "gif"],
        max_bytes: Number(payload?.dashboard_settings?.max_bytes || 25 * 1024 * 1024),
        youtube_driving_background: payload?.dashboard_settings?.youtube_driving_background || {},
        fullscreen: payload?.dashboard_settings?.fullscreen || {},
        top_area: {
          ...(payload?.dashboard_settings?.top_area || {}),
          slots: payload?.dashboard_settings?.top_area?.slots || {},
          font_scales: payload?.dashboard_settings?.top_area?.font_scales || {},
          font_scale_min: Number(payload?.dashboard_settings?.top_area?.font_scale_min ?? 0.7),
          font_scale_max: Number(payload?.dashboard_settings?.top_area?.font_scale_max ?? 1.6),
          font_scale_step: Number(payload?.dashboard_settings?.top_area?.font_scale_step ?? 0.05),
          options: payload?.dashboard_settings?.top_area?.options || {},
          options_list: Array.isArray(payload?.dashboard_settings?.top_area?.options_list) ? payload.dashboard_settings.top_area.options_list : [],
          center_options: payload?.dashboard_settings?.top_area?.center_options || {},
          center_options_list: Array.isArray(payload?.dashboard_settings?.top_area?.center_options_list) ? payload.dashboard_settings.top_area.center_options_list : [],
        },
        sidebar: {
          ...(payload?.dashboard_settings?.sidebar || {}),
          slots: payload?.dashboard_settings?.sidebar?.slots || {},
          options: payload?.dashboard_settings?.sidebar?.options || {},
          options_list: Array.isArray(payload?.dashboard_settings?.sidebar?.options_list) ? payload.dashboard_settings.sidebar.options_list : [],
        },
        bottom_bar: {
          ...(payload?.dashboard_settings?.bottom_bar || {}),
          slots: payload?.dashboard_settings?.bottom_bar?.slots || {},
          toggles: payload?.dashboard_settings?.bottom_bar?.toggles || {},
          location_display_modes: payload?.dashboard_settings?.bottom_bar?.location_display_modes || {},
          location_display_modes_list: Array.isArray(payload?.dashboard_settings?.bottom_bar?.location_display_modes_list) ? payload.dashboard_settings.bottom_bar.location_display_modes_list : [],
          slot_options: payload?.dashboard_settings?.bottom_bar?.slot_options || {},
          slot_options_list: Array.isArray(payload?.dashboard_settings?.bottom_bar?.slot_options_list) ? payload.dashboard_settings.bottom_bar.slot_options_list : [],
        },
        map: payload?.dashboard_settings?.map || {},
        person_track: payload?.dashboard_settings?.person_track || {},
      },
      telegram: {
        builtin_telegram_enabled: Boolean(payload?.telegram?.builtin_telegram_enabled ?? true),
        builtin_telegram_bot_token: payload?.telegram?.builtin_telegram_bot_token || "",
        builtin_telegram_poll_enabled: Boolean(payload?.telegram?.builtin_telegram_poll_enabled ?? false),
        builtin_telegram_poll_interval_seconds: Number(payload?.telegram?.builtin_telegram_poll_interval_seconds ?? 3),
        replies_enabled: Boolean(payload?.telegram?.replies_enabled ?? Boolean(payload?.telegram?.telegram_group_id)),
        telegram_group_id: payload?.telegram?.telegram_group_id || "",
        ai_group_listener_enabled: Boolean(payload?.telegram?.ai_group_listener_enabled ?? true),
        report_commands: this._telegramReportCommands(payload?.telegram?.report_commands || {}),
      },
      trip_reports: {
        auto_trip_tracking: Boolean(trip.auto_trip_tracking ?? true),
        auto_start_speed_threshold: Number(trip.auto_start_speed_threshold ?? 2),
        live_trip_enabled: Boolean(trip.live_trip_enabled ?? true),
        live_trip_update_interval_seconds: Number(trip.live_trip_update_interval_seconds ?? 5),
        live_trip_traffic_speed_threshold: Number(trip.live_trip_traffic_speed_threshold ?? 20),
        live_trip_finish_delay_seconds: Number(trip.live_trip_finish_delay_seconds ?? 90),
        live_trip_min_distance_km: Number(trip.live_trip_min_distance_km ?? 0),
        ai_trip_story_enabled: Boolean(trip.ai_trip_story_enabled ?? payload?.ai_settings?.ai_alert_post_trip_summary_enabled ?? true),
        ai_trip_story_delay_mode: trip.ai_trip_story_delay_mode || "follow_live_trip_report_delay",
        trip_map_enabled: Boolean(trip.trip_map_enabled ?? true),
        trip_map_tracker_entity: trip.trip_map_tracker_entity || "",
        trip_map_sample_interval_seconds: Number(trip.trip_map_sample_interval_seconds ?? 5),
        trip_map_min_movement_meters: Number(trip.trip_map_min_movement_meters ?? 15),
        trip_map_send_separate_png: Boolean(trip.trip_map_send_separate_png ?? true),
        show_distance: Boolean(trip.show_distance ?? true),
        show_duration: Boolean(trip.show_duration ?? true),
        show_traffic: Boolean(trip.show_traffic ?? true),
        show_average_speed: Boolean(trip.show_average_speed ?? true),
        show_energy: Boolean(trip.show_energy ?? true),
        show_consumption: Boolean(trip.show_consumption ?? true),
        show_battery: Boolean(trip.show_battery ?? true),
        show_cost: Boolean(trip.show_cost ?? true),
        show_climate: Boolean(trip.show_climate ?? true),
        show_elevation: Boolean(trip.show_elevation ?? true),
        show_trip_map: Boolean(trip.show_trip_map ?? true),
      },
    };
  }


  _pushDebugEvent(level, message, detail = {}) {
    const item = {
      ts: new Date().toISOString(),
      level,
      message,
      detail,
      active_tab: this._activeTab,
      active_settings_tab: this._activeSettingsTab,
    };
    this._debugEvents = [item, ...(this._debugEvents || [])].slice(0, 30);
  }

  _recordApiResult(name, result, startedAt) {
    const ok = result?.status === "fulfilled";
    const entry = {
      ts: new Date().toISOString(),
      name,
      ok,
      duration_ms: Math.max(0, Math.round(performance.now() - startedAt)),
      error: ok ? "" : this._formatError(result?.reason),
    };
    this._lastApiResults = [entry, ...(this._lastApiResults || [])].slice(0, 20);
    this._pushDebugEvent(ok ? "success" : "error", `${name} ${ok ? "OK" : "ERROR"}`, entry);
  }

  _debugSnapshot() {
    const general = this._settingsData?.general_settings || {};
    const summary = general.resource_summary || {};
    const system = general.system || {};
    return {
      timestamp: new Date().toISOString(),
      active_tab: this._activeTab,
      active_settings_tab: this._activeSettingsTab,
      active_entities_tab: this._activeEntitiesTab,
      active_dashboard_section: this._dashboardSettingsSection,
      active_trip_section: this._tripSettingsSection,
      language: general.app_language || this._lang || "-",
      currency: this._currency || "-",
      default_open_tab: general.default_open_tab || "settings",
      status: this._status || "",
      error: this._error || "",
      loading: Boolean(this._loading),
      system: {
        config_entry: Boolean(system.has_config_entry),
        integration_version: system.integration_version || "",
      },
      frontend: {
        url: window.location?.href || "",
        user_agent: navigator.userAgent || "",
        platform: navigator.platform || "",
        clipboard_api: Boolean(navigator.clipboard?.writeText),
        secure_context: Boolean(window.isSecureContext),
      },
      last_settings_save_summary: this._lastSettingsSaveSummary || {},
      resource_summary: summary || {},
      entity_store_audit: general.entity_store_audit || {},
      api_results: this._lastApiResults || [],
      recent_events: this._debugEvents || [],
      telegram_service_state: this._telegramDiagnostics?.service_state || {},
      ai_service_state: this._aiDiagnostics?.service_state || {},
      counts: {
        charge_records: this._chargeData?.records?.length || 0,
        trip_records: this._tripData?.records?.length || 0,
        ai_entities: this._settingsData?.ai_entity_manager?.entries?.length || 0,
        report_entities: this._settingsData?.report_entity_manager?.entries?.length || 0,
        dashboard_entities: this._settingsData?.dashboard_entity_manager?.entries?.length || 0,
      },
    };
  }

  async _copyDebugInfo() {
    const text = JSON.stringify(this._manualDebugSnapshot || this._debugSnapshot(), null, 2);
    let copied = false;
    let method = "";
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
        copied = true;
        method = "navigator.clipboard";
      }
    } catch (err) {
      this._pushDebugEvent("warning", "navigator.clipboard copy failed, trying textarea fallback", { error: this._formatError(err) });
    }

    if (!copied) {
      try {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.setAttribute("readonly", "readonly");
        textarea.style.position = "fixed";
        textarea.style.left = "-9999px";
        textarea.style.top = "0";
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();
        textarea.setSelectionRange(0, textarea.value.length);
        copied = Boolean(document.execCommand && document.execCommand("copy"));
        document.body.removeChild(textarea);
        method = copied ? "document.execCommand" : "";
      } catch (err) {
        this._pushDebugEvent("warning", "textarea fallback copy failed", { error: this._formatError(err) });
      }
    }

    if (copied) {
      this._error = "";
      this._status = this._t("debugCopied");
      this._pushDebugEvent("success", "Debug info copied to clipboard", { method });
    } else {
      this._error = this._t("debugCopyManual");
      this._status = this._t("debugCopyManual");
      this._pushDebugEvent("warning", "Clipboard API unavailable; user can manually copy debug output", {
        clipboard_api: Boolean(navigator.clipboard?.writeText),
        secure_context: Boolean(window.isSecureContext),
      });
    }
    this._render();
  }

  _runDebugDiagnostics() {
    this._pushDebugEvent("info", "Debug diagnostics refreshed manually");
    this._manualDebugSnapshot = this._debugSnapshot();
    this._status = this._t("debugRunDone");
    this._error = "";
    this._render();
  }

  _clearDebugDiagnostics() {
    this._debugEvents = [];
    this._lastApiResults = [];
    this._lastClickDebug = {};
    this._manualDebugSnapshot = {
      cleared_at: new Date().toISOString(),
      message: this._t("debugCleared"),
    };
    this._status = this._t("debugCleared");
    this._error = "";
    this._render();
  }

  _clearPanelMigrationOutput() {
    this._panelMigrationOutput = {
      cleared_at: new Date().toISOString(),
      message: this._t("panelMigrationOutputCleared"),
    };
    this._status = this._t("panelMigrationOutputCleared");
    this._error = "";
    this._render();
  }



  _hasDataForActiveTab() {
    if (this._activeTab === "settings") return Boolean(this._settingsData);
    if (this._activeTab === "trip" || this._activeTab === "manual") return Boolean(this._tripData);
    return Boolean(this._chargeData);
  }

  _ensureActiveLoaded() {
    if (!this._hass || this._loading || this._hasDataForActiveTab()) return;
    this._loadActive();
  }

  async _loadAll() {
    // Alpha193 safety: keep the old method name for any legacy button/path,
    // but do not run the previous startup Promise.all burst here. Loading is
    // now per active tab.
    await this._loadActive();
  }

  _restoreSelections() {
    let hasCharge = false;
    if (this._selectedChargeId) {
      const rec = (this._chargeData?.records || []).find((r) => r.id === this._selectedChargeId);
      if (rec) {
        this._editingCharge = { ...rec };
        hasCharge = true;
      }
    }
    if (!hasCharge) this._chargeMapPreview = null;
    else this._loadChargeMapPreview(this._selectedChargeId);

    let hasTrip = false;
    if (this._selectedTripId) {
      const rec = (this._tripData?.records || []).find((r) => r.id === this._selectedTripId);
      if (rec) {
        this._editingTrip = { ...rec };
        hasTrip = true;
      }
    }
    if (!hasTrip) this._tripMapPreview = null;
    else this._loadTripMapPreview(this._selectedTripId);

    let hasManual = false;
    if (this._selectedManualTrackingId) {
      const rec = (this._tripData?.records || []).find((r) => r.id === this._selectedManualTrackingId);
      if (rec && this._isManualTrackingRecord(rec)) {
        this._editingManualTracking = { ...rec };
        hasManual = true;
      }
    }
    if (!hasManual) this._manualTrackingMapPreview = null;
    else this._loadManualTrackingMapPreview(this._selectedManualTrackingId);
  }

  async _loadActive() {
    if (!this._hass) return;
    this._loading = true;
    this._error = "";
    this._render();
    try {
      if (this._activeTab === "trip" || this._activeTab === "manual") {
        const trip = await this._hass.callApi("GET", "pom_tesla_report/trip_records");
        this._tripData = this._normalizeApiPayload(trip, this._chargeData?.currency || this._currency || "");
      } else if (this._activeTab === "settings") {
        const settings = await this._hass.callApi("GET", "pom_tesla_report/settings");
        this._settingsData = this._normalizeSettingsPayload(settings);
        this._ensureStationEditor();
      } else {
        const charge = await this._hass.callApi("GET", "pom_tesla_report/charge_records");
        this._chargeData = this._normalizeApiPayload(charge);
      }
      this._restoreSelections();
      this._status = this._t("loaded");
    } catch (err) {
      this._error = this._formatError(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  _number(value) {
    const raw = String(value ?? "").trim();
    if (!raw) return 0;
    let text = raw.replace(/\s/g, "");
    // Accept both Turkish decimal comma and English decimal dot. Also tolerate
    // accidental decorations such as "9,90 TL/kWh" by extracting the first
    // numeric token before normalizing separators.
    const token = text.match(/-?\d+(?:[.,]\d+)*(?:[.,]\d+)?/);
    if (token) text = token[0];
    let normalized = text;
    if (text.includes(",") && text.includes(".")) {
      normalized = text.lastIndexOf(",") > text.lastIndexOf(".")
        ? text.replace(/\./g, "").replace(",", ".")
        : text.replace(/,/g, "");
    } else {
      normalized = text.replace(",", ".");
    }
    const n = Number(normalized);
    return Number.isFinite(n) ? n : NaN;
  }

  _fmtNumber(value, digits = 2) {
    const n = Number(value || 0);
    if (!Number.isFinite(n)) return "0";
    return n.toLocaleString(this._lang === "tr" ? "tr-TR" : "en-US", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });
  }

  _secondsToMinutesValue(seconds, fallbackSeconds = 1800) {
    const raw = Number(seconds ?? fallbackSeconds);
    const safeSeconds = Number.isFinite(raw) ? raw : fallbackSeconds;
    const minutes = safeSeconds / 60;
    return Number.isInteger(minutes) ? String(minutes) : String(Math.round(minutes * 10) / 10);
  }

  _minutesToSecondsValue(minutes, fallbackMinutes = 30) {
    const raw = Number(minutes ?? fallbackMinutes);
    const safeMinutes = Number.isFinite(raw) ? raw : fallbackMinutes;
    return Math.max(0, Math.round(safeMinutes * 60));
  }

  _secondsDurationText(seconds) {
    return this._durationText(Number(seconds || 0) / 60);
  }

  _durationText(minutes) {
    const total = Math.max(0, Math.round(Number(minutes || 0)));
    const hours = Math.floor(total / 60);
    const mins = total % 60;
    if (this._lang === "en") {
      if (hours && mins) return `${hours} hr ${mins} min`;
      if (hours) return `${hours} hr`;
      return `${mins} min`;
    }
    if (hours && mins) return `${hours} sa ${mins} dk`;
    if (hours) return `${hours} sa`;
    return `${mins} dk`;
  }

  _pad2(value) {
    return String(value).padStart(2, "0");
  }

  _dateKeyFromDate(date) {
    if (!(date instanceof Date) || Number.isNaN(date.getTime())) return "";
    return `${date.getFullYear()}-${this._pad2(date.getMonth() + 1)}-${this._pad2(date.getDate())}`;
  }

  _monthKeyFromDate(date) {
    if (!(date instanceof Date) || Number.isNaN(date.getTime())) return "";
    return `${date.getFullYear()}-${this._pad2(date.getMonth() + 1)}`;
  }

  _currentMonthKey() {
    return this._monthKeyFromDate(new Date());
  }

  _todayKey() {
    return this._dateKeyFromDate(new Date());
  }

  _parseRecordDate(record) {
    const candidates = [record?.created_at, record?.started_at, record?.finished_at, record?.display_at, record?.date, record?.report_date];
    for (const raw of candidates) {
      const text = String(raw || "").trim();
      if (!text) continue;
      if (/^\d{4}-\d{2}-\d{2}/.test(text)) {
        const d = new Date(text);
        if (!Number.isNaN(d.getTime())) return d;
        const m = text.match(/^(\d{4})-(\d{2})-(\d{2})/);
        if (m) return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]), 12, 0, 0);
      }
      const tr = text.match(/^(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})(?:\s+(\d{1,2}):(\d{1,2}))?/);
      if (tr) {
        const year = Number(tr[3].length === 2 ? `20${tr[3]}` : tr[3]);
        const month = Number(tr[2]) - 1;
        const day = Number(tr[1]);
        const hour = Number(tr[4] || 12);
        const minute = Number(tr[5] || 0);
        const d = new Date(year, month, day, hour, minute, 0);
        if (!Number.isNaN(d.getTime())) return d;
      }
    }
    if (record?.month_key && /^\d{4}-\d{2}$/.test(String(record.month_key))) {
      const [year, month] = String(record.month_key).split("-").map(Number);
      return new Date(year, month - 1, 1, 12, 0, 0);
    }
    return null;
  }

  _monthOptionsForRecords(records) {
    const months = new Set([this._currentMonthKey()]);
    for (const r of records || []) {
      if (r?.month_key && /^\d{4}-\d{2}$/.test(String(r.month_key))) {
        months.add(String(r.month_key));
        continue;
      }
      const d = this._parseRecordDate(r);
      const key = this._monthKeyFromDate(d);
      if (key) months.add(key);
    }
    return [...months].sort().reverse();
  }

  _monthLabel(monthKey) {
    const key = String(monthKey || "");
    const m = key.match(/^(\d{4})-(\d{2})$/);
    if (!m) return key || this._t("currentMonth");
    const year = Number(m[1]);
    const month = Number(m[2]);
    const namesTr = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"];
    const namesEn = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    const label = (this._lang === "en" ? namesEn : namesTr)[month - 1] || key;
    return `${label} ${year}`;
  }

  _filterLabel(kind) {
    const filter = kind === "manual" ? this._manualTrackingFilter : (kind === "trip" ? this._tripFilter : this._chargeFilter);
    const month = kind === "manual" ? this._manualTrackingSelectedMonth : (kind === "trip" ? this._tripSelectedMonth : this._chargeSelectedMonth);
    if (filter === "today") return this._t("todayRecords");
    if (filter === "all") return this._t("allRecords");
    if (filter === "range") return this._t("dateRange");
    return month === this._currentMonthKey() ? this._t("currentMonth") : this._monthLabel(month);
  }

  _filterRecordsByDate(records, kind) {
    const filter = kind === "manual" ? this._manualTrackingFilter : (kind === "trip" ? this._tripFilter : this._chargeFilter);
    if (filter === "all") return [...records];
    const selectedMonth = kind === "manual" ? this._manualTrackingSelectedMonth : (kind === "trip" ? this._tripSelectedMonth : this._chargeSelectedMonth);
    const rangeStart = kind === "manual" ? this._manualTrackingRangeStart : (kind === "trip" ? this._tripRangeStart : this._chargeRangeStart);
    const rangeEnd = kind === "manual" ? this._manualTrackingRangeEnd : (kind === "trip" ? this._tripRangeEnd : this._chargeRangeEnd);
    const todayKey = this._todayKey();

    return [...records].filter((r) => {
      const date = this._parseRecordDate(r);
      const dateKey = this._dateKeyFromDate(date);
      if (!dateKey) return false;

      if (filter === "today") return dateKey === todayKey;
      if (filter === "range") {
        const start = String(rangeStart || "");
        const end = String(rangeEnd || "");
        if (!start || !end) return false;
        return dateKey >= start && dateKey <= end;
      }

      const monthKey = String(r?.month_key || this._monthKeyFromDate(date) || "");
      return monthKey === selectedMonth;
    });
  }

  _chargeRecords() {
    return this._filterRecordsByDate(this._chargeData?.records || [], "charge");
  }

  _tripRecords() {
    return this._filterRecordsByDate(this._tripData?.records || [], "trip");
  }

  _isManualTrackingRecord(record) {
    const source = String(record?.source || "").toLowerCase();
    return source.includes("manual_tracking") || source === "manual tracking";
  }

  _manualTrackingRecords() {
    const records = (this._tripData?.records || []).filter((r) => this._isManualTrackingRecord(r));
    return this._filterRecordsByDate(records, "manual");
  }

  _chargeSummaryFromRecords(records) {
    const byCurrency = {};
    let totalKwh = 0;
    for (const item of records || []) {
      totalKwh += Number(item?.added_kwh || 0);
      const currency = String(item?.currency_label || this._chargeData?.currency || this._currency || "-");
      byCurrency[currency] = (byCurrency[currency] || 0) + Number(item?.total_cost || 0);
    }
    return {
      count: (records || []).length,
      total_kwh: totalKwh,
      total_cost_by_currency: byCurrency,
    };
  }

  _tripSummaryFromRecords(records) {
    let totalDistance = 0;
    let totalEnergy = 0;
    let totalCost = 0;
    let totalDuration = 0;
    for (const item of records || []) {
      totalDistance += Number(item?.trip_km || 0);
      totalEnergy += Number(item?.used_kwh || 0);
      totalCost += Number(item?.total_cost || 0);
      totalDuration += Number(item?.duration_minutes || 0);
    }
    return {
      count: (records || []).length,
      total_distance_km: totalDistance,
      total_energy_kwh: totalEnergy,
      total_cost: totalCost,
      total_duration_minutes: totalDuration,
      average_consumption_kwh_100km: totalDistance > 0 ? (totalEnergy / totalDistance * 100) : 0,
    };
  }

  _stations() {
    return [...(this._settingsData?.charging?.provider_presets || [])];
  }

  _ensureStationEditor() {
    if (!this._editingStation) {
      this._editingStation = { name: "", unit_price: "", currency: this._settingsData?.charging?.report_currency || this._currency || "TL" };
    }
  }

  async _loadChargeMapPreview(recordId = this._selectedChargeId) {
    if (!this._hass || !recordId) {
      this._chargeMapPreview = null;
      this._render();
      return;
    }
    const requestId = ++this._chargeMapRequestId;
    this._chargeMapPreview = { loading: true, image_url: "", full_address: "", error: "" };
    this._render();
    try {
      const payload = await this._hass.callApi("GET", `pom_tesla_report/record_map?kind=charge&id=${encodeURIComponent(recordId)}`);
      if (requestId !== this._chargeMapRequestId) return;
      this._chargeMapPreview = { ...(payload || {}), loading: false, error: (payload && payload.success === false ? (payload.message || payload.error || "") : "") };
    } catch (err) {
      if (requestId !== this._chargeMapRequestId) return;
      this._chargeMapPreview = { loading: false, image_url: "", full_address: "", error: this._formatError(err) };
    }
    this._render();
  }

  async _loadTripMapPreview(recordId = this._selectedTripId) {
    if (!this._hass || !recordId) {
      this._tripMapPreview = null;
      this._render();
      return;
    }
    const requestId = ++this._tripMapRequestId;
    this._tripMapPreview = { loading: true, image_url: "", error: "" };
    this._render();
    try {
      const payload = await this._hass.callApi("GET", `pom_tesla_report/record_map?kind=trip&id=${encodeURIComponent(recordId)}`);
      if (requestId !== this._tripMapRequestId) return;
      this._tripMapPreview = { ...(payload || {}), loading: false, error: (payload && payload.success === false ? (payload.message || payload.error || "") : "") };
    } catch (err) {
      if (requestId !== this._tripMapRequestId) return;
      this._tripMapPreview = { loading: false, image_url: "", error: this._formatError(err) };
    }
    this._render();
  }

  _selectChargeRecord(id) {
    const rec = (this._chargeData?.records || []).find((r) => r.id === id);
    this._selectedChargeId = id;
    this._editingCharge = rec ? { ...rec } : null;
    this._status = "";
    this._error = "";
    this._loadChargeMapPreview(id);
  }

  _selectTripRecord(id) {
    const rec = (this._tripData?.records || []).find((r) => r.id === id);
    this._selectedTripId = id;
    this._editingTrip = rec ? { ...rec } : null;
    this._status = "";
    this._error = "";
    this._loadTripMapPreview(id);
  }

  _selectManualTrackingRecord(id) {
    const rec = (this._tripData?.records || []).find((r) => r.id === id);
    this._selectedManualTrackingId = id;
    this._editingManualTracking = rec ? { ...rec } : null;
    this._status = "";
    this._error = "";
    this._loadManualTrackingMapPreview(id);
  }

  _selectStation(index) {
    const station = this._stations()[Number(index)];
    this._selectedStationIndex = Number(index);
    this._editingStation = station ? { ...station } : { name: "", unit_price: "", currency: this._currency };
    this._status = "";
    this._error = "";
    this._render();
  }

  _newChargeRecord() {
    const displayAt = this._displayNow();
    this._selectedChargeId = "";
    this._editingCharge = {
      id: "",
      display_at: displayAt,
      provider: "Manual",
      added_kwh: 0,
      total_cost: 0,
      price_per_kwh: 0,
      currency_label: this._chargeData?.currency || this._currency || "TL",
      source: "panel_manual",
    };
    this._chargeMapPreview = null;
    this._status = "";
    this._error = "";
    this._render();
  }

  _newTripRecord() {
    const displayAt = this._displayNow();
    this._selectedTripId = "";
    this._editingTrip = {
      id: "",
      display_at: displayAt,
      start_address: "",
      end_address: "",
      trip_km: 0,
      duration_text: "",
      duration_minutes: 0,
      used_kwh: 0,
      consumption_kwh_100km: 0,
      total_cost: 0,
      currency_label: this._tripData?.currency || this._currency || "TL",
      source: "panel_manual",
    };
    this._tripMapPreview = null;
    this._status = "";
    this._error = "";
    this._render();
  }

  _newStation() {
    this._selectedStationIndex = -1;
    this._editingStation = { name: "", unit_price: "", currency: this._settingsData?.charging?.report_currency || this._currency || "TL" };
    this._status = "";
    this._error = "";
    this._render();
  }

  _displayNow() {
    const now = new Date();
    const pad = (v) => String(v).padStart(2, "0");
    return `${pad(now.getDate())}.${pad(now.getMonth() + 1)}.${now.getFullYear()} ${pad(now.getHours())}:${pad(now.getMinutes())}`;
  }

  _readChargeForm() {
    const root = this.shadowRoot;
    const rec = { ...(this._editingCharge || {}) };
    rec.provider = root.getElementById("charge_provider")?.value?.trim() || "";
    rec.display_at = root.getElementById("charge_display_at")?.value?.trim() || rec.display_at || "";
    rec.added_kwh = this._number(root.getElementById("charge_added_kwh")?.value);
    rec.total_cost = this._number(root.getElementById("charge_total_cost")?.value);
    rec.price_per_kwh = this._number(root.getElementById("charge_price_per_kwh")?.value);
    rec.currency_label = root.getElementById("charge_currency_label")?.value?.trim() || this._chargeData?.currency || this._currency || "TL";
    return rec;
  }

  _readTripForm() {
    const root = this.shadowRoot;
    const rec = { ...(this._editingTrip || {}) };
    rec.display_at = root.getElementById("trip_display_at")?.value?.trim() || rec.display_at || "";
    rec.start_address = root.getElementById("trip_start_address")?.value?.trim() || "";
    rec.end_address = root.getElementById("trip_end_address")?.value?.trim() || "";
    rec.trip_km = this._number(root.getElementById("trip_km")?.value);
    rec.duration_minutes = this._number(root.getElementById("trip_duration_minutes")?.value);
    rec.duration_text = root.getElementById("trip_duration_text")?.value?.trim() || "";
    rec.used_kwh = this._number(root.getElementById("trip_used_kwh")?.value);
    rec.consumption_kwh_100km = this._number(root.getElementById("trip_consumption")?.value);
    rec.total_cost = this._number(root.getElementById("trip_total_cost")?.value);
    rec.currency_label = root.getElementById("trip_currency_label")?.value?.trim() || this._tripData?.currency || this._currency || "TL";
    return rec;
  }

  _readSettingsForm() {
    const root = this.shadowRoot;
    const current = this._settingsData?.charging || {};
    return {
      report_currency: root.getElementById("settings_report_currency")?.value || current.report_currency || this._currency || "TL",
      charging_report_mode: root.getElementById("settings_report_mode")?.value || current.charging_report_mode || "prompt",
      provider_presets: this._stations(),
    };
  }

  _readStationForm() {
    const root = this.shadowRoot;
    return {
      name: root.getElementById("station_name")?.value?.trim() || "",
      unit_price: this._number(root.getElementById("station_unit_price")?.value),
      currency: root.getElementById("station_currency")?.value || this._settingsData?.charging?.report_currency || this._currency || "TL",
    };
  }

  _checked(id) {
    return Boolean(this.shadowRoot.getElementById(id)?.checked);
  }

  _readTripSettingsForm() {
    const root = this.shadowRoot;
    const current = this._settingsData?.trip_reports || {};
    const value = (id, fallback = "") => {
      const el = root.getElementById(id);
      return el ? el.value : fallback;
    };
    const checked = (id, fallback = false) => {
      const el = root.getElementById(id);
      return el ? Boolean(el.checked) : Boolean(fallback);
    };
    const number = (id, fallback) => this._number(value(id, fallback));
    const autoTripTracking = checked("trip_auto_trip_tracking", current.auto_trip_tracking);
    return {
      auto_trip_tracking: autoTripTracking,
      auto_start_speed_threshold: number("trip_auto_start_speed_threshold", current.auto_start_speed_threshold ?? 2),
      live_trip_enabled: autoTripTracking,
      live_trip_update_interval_seconds: number("trip_live_trip_update_interval_seconds", current.live_trip_update_interval_seconds ?? 5),
      live_trip_traffic_speed_threshold: number("trip_live_trip_traffic_speed_threshold", current.live_trip_traffic_speed_threshold ?? 20),
      live_trip_finish_delay_seconds: this._minutesToSecondsValue(value("trip_live_trip_finish_delay_minutes", this._secondsToMinutesValue(current.live_trip_finish_delay_seconds ?? 1800)), 30),
      live_trip_min_distance_km: number("trip_live_trip_min_distance_km", current.live_trip_min_distance_km ?? 0),
      ai_trip_story_enabled: checked("trip_ai_story_enabled", current.ai_trip_story_enabled ?? true),
      ai_trip_story_delay_mode: "follow_live_trip_report_delay",
      trip_map_enabled: checked("trip_map_enabled", current.trip_map_enabled),
      trip_map_tracker_entity: String(value("trip_map_tracker_entity", current.trip_map_tracker_entity || "") || "").trim(),
      trip_map_sample_interval_seconds: number("trip_map_sample_interval_seconds", current.trip_map_sample_interval_seconds ?? 5),
      trip_map_min_movement_meters: number("trip_map_min_movement_meters", current.trip_map_min_movement_meters ?? 15),
      trip_map_send_separate_png: checked("trip_map_send_separate_png", current.trip_map_send_separate_png),
      show_distance: checked("trip_show_distance", current.show_distance),
      show_duration: checked("trip_show_duration", current.show_duration),
      show_traffic: checked("trip_show_traffic", current.show_traffic),
      show_average_speed: checked("trip_show_average_speed", current.show_average_speed),
      show_energy: checked("trip_show_energy", current.show_energy),
      show_consumption: checked("trip_show_consumption", current.show_consumption),
      show_battery: checked("trip_show_battery", current.show_battery),
      show_cost: checked("trip_show_cost", current.show_cost),
      show_climate: checked("trip_show_climate", current.show_climate),
      show_elevation: checked("trip_show_elevation", current.show_elevation),
      show_trip_map: checked("trip_show_trip_map", current.show_trip_map),
    };
  }

  _readTelegramSettingsForm() {
    const root = this.shadowRoot;
    const current = this._settingsData?.telegram || {};
    return {
      builtin_telegram_enabled: this._checked("telegram_builtin_enabled"),
      builtin_telegram_bot_token: root.getElementById("telegram_bot_token")?.value?.trim() || current.builtin_telegram_bot_token || "",
      builtin_telegram_poll_enabled: this._checked("telegram_poll_enabled"),
      builtin_telegram_poll_interval_seconds: this._number(root.getElementById("telegram_poll_interval")?.value || current.builtin_telegram_poll_interval_seconds || 3),
      replies_enabled: this._checked("telegram_replies_enabled"),
      telegram_group_id: root.getElementById("telegram_group_id")?.value?.trim() || "",
      ai_group_listener_enabled: this._checked("telegram_ai_listener_enabled"),
      report_commands: {
        charge_report: this._normalizeTelegramCommandWord(root.getElementById("telegram_cmd_charge_report")?.value, "charge"),
        trip_summary: this._normalizeTelegramCommandWord(root.getElementById("telegram_cmd_trip_summary")?.value, "trip"),
        trip_all: this._normalizeTelegramCommandWord(root.getElementById("telegram_cmd_trip_all")?.value, "tripall"),
        trip_single: this._normalizeTelegramCommandWord(root.getElementById("telegram_cmd_trip_single")?.value, "single"),
        trip_last: this._normalizeTelegramCommandWord(root.getElementById("telegram_cmd_trip_last")?.value, "triplast"),
      },
    };
  }

  _aiEntryForRole(role) {
    const entries = this._settingsData?.ai_entity_manager?.entries || [];
    return entries.find((item) => item.role === role) || null;
  }

  _aiRoleSet() {
    return new Set((this._settingsData?.ai_entity_manager?.roles || []).map((item) => item.role));
  }

  _aiRoleDefinitions() {
    return this._settingsData?.ai_entity_manager?.roles || [];
  }

  _roleDefinition(role) {
    return this._aiRoleDefinitions().find((item) => item.role === role) || null;
  }

  _pickerRoleDefinition() {
    const target = this._entityPickerTarget || "";
    if (target.startsWith("ai_role_")) return this._roleDefinition(target.slice("ai_role_".length));
    if (target.startsWith("report_role_")) return this._reportRoleDefinition(target.slice("report_role_".length));
    if (target.startsWith("dashboard_role_")) return this._dashboardRoleDefinition(target.slice("dashboard_role_".length));
    return null;
  }

  _categoryTranslationKey(category) {
    const map = {
      vehicle_controls: "entityCategoryVehicleControls",
      sensors: "entityCategorySensors",
      diagnostics: "entityCategoryDiagnostics",
      teslamate: "entityCategoryTeslamate",
      dashboard_top: "entityCategoryDashboardTop",
      dashboard_sidebar: "entityCategoryDashboardSidebar",
      dashboard_bottom: "entityCategoryDashboardBottom",
      dashboard_map: "entityCategoryDashboardMap",
      dashboard_charge_popup: "entityCategoryDashboardChargePopup",
      dashboard_person: "entityCategoryDashboardPerson",
      dashboard_custom_home: "entityCategoryDashboardCustomHome",
      dashboard_vehicle_open_close: "entityCategoryDashboardVehicleOpenClose",
      other: "entityCategoryOther",
    };
    return map[category || "other"] || "entityCategoryOther";
  }

  _groupAIRolesByCategory(roles) {
    const order = ["dashboard_top", "dashboard_sidebar", "dashboard_bottom", "dashboard_map", "dashboard_charge_popup", "dashboard_person", "dashboard_vehicle_open_close", "dashboard_custom_home", "vehicle_controls", "sensors", "diagnostics", "teslamate", "other"];
    const groups = new Map();
    roles.forEach((roleDef) => {
      const category = roleDef.category || "other";
      if (!groups.has(category)) groups.set(category, []);
      groups.get(category).push(roleDef);
    });
    const ordered = order.filter((category) => groups.has(category)).map((category) => [category, groups.get(category)]);
    Array.from(groups.keys()).filter((category) => !order.includes(category)).sort().forEach((category) => {
      ordered.push([category, groups.get(category)]);
    });
    return ordered;
  }

  _getAIEntityDraft() {
    const ai = this._settingsData?.ai_entity_manager || {};
    if (this._aiEntityDraft) return this._aiEntityDraft;
    const roleValues = {};
    const custom = [];
    const roleSet = new Set((ai.roles || []).map((item) => item.role));
    const seenCustom = new Set();
    (ai.entries || []).forEach((item) => {
      if (!item?.entity_id) return;
      const role = item.role || "other";
      // The fixed role area can show only one entity per role. If Auto Find or
      // the old Options screen produced multiple entities for the same role,
      // keep the first in the role slot. A fixed-role entity is not an Extra AI
      // Entity, so duplicates are removed from the custom list.
      if (roleSet.has(role) && !roleValues[role]) {
        roleValues[role] = item.entity_id;
        return;
      }
      const key = `${role}|${item.entity_id}`;
      if (seenCustom.has(key)) return;
      seenCustom.add(key);
      custom.push({ entity_id: item.entity_id, role });
    });
    this._aiEntityDraft = this._dedupeAIEntityDraft({
      main_entity: ai.main_entity || "",
      auto_discover_device_entities: Boolean(ai.auto_discover_device_entities ?? true),
      roles: roleValues,
      custom,
    });
    return this._aiEntityDraft;
  }

  _dedupeAIEntityDraft(draft) {
    const roleValues = draft?.roles || {};
    const fixedEntities = new Set(Object.values(roleValues).map((value) => String(value || "").trim()).filter(Boolean));
    const seenCustom = new Set();
    const custom = [];
    (draft?.custom || []).forEach((item) => {
      const entityId = String(item?.entity_id || "").trim();
      if (!entityId || fixedEntities.has(entityId) || seenCustom.has(entityId)) return;
      seenCustom.add(entityId);
      custom.push({ ...item, entity_id: entityId, role: item?.role || "other" });
    });
    draft.custom = custom;
    return draft;
  }

  _reportRoleDefinitions() {
    return this._settingsData?.report_entity_manager?.roles || [];
  }

  _reportRoleDefinition(role) {
    return this._reportRoleDefinitions().find((item) => item.role === role) || null;
  }

  _getReportEntityDraft() {
    const report = this._settingsData?.report_entity_manager || {};
    if (this._reportEntityDraft) return this._reportEntityDraft;
    const roleValues = {};
    const roleSet = new Set((report.roles || []).map((item) => item.role));
    (report.entries || []).forEach((item) => {
      if (!item?.entity_id) return;
      const role = item.role || "other";
      if (roleSet.has(role) && !roleValues[role]) roleValues[role] = item.entity_id;
    });
    this._reportEntityDraft = {
      main_entity: report.main_entity || "",
      roles: roleValues,
    };
    return this._reportEntityDraft;
  }


  _dashboardRoleDefinitions() {
    return this._settingsData?.dashboard_entity_manager?.roles || [];
  }

  _dashboardRoleDefinition(role) {
    return this._dashboardRoleDefinitions().find((item) => item.role === role) || null;
  }

  _getDashboardEntityDraft() {
    const dashboard = this._settingsData?.dashboard_entity_manager || {};
    if (this._dashboardEntityDraft) return this._dashboardEntityDraft;
    const roleValues = {};
    const roleSet = new Set((dashboard.roles || []).map((item) => item.role));
    const roleMeta = {};
    (dashboard.entries || []).forEach((item) => {
      if (!item?.entity_id) return;
      const role = item.role || "other";
      if (roleSet.has(role) && !roleValues[role]) {
        roleValues[role] = item.entity_id;
        roleMeta[role] = { icon: item.icon || "", name: item.name || item.label || "" };
      }
    });
    this._dashboardEntityDraft = {
      main_entity: dashboard.main_entity || "",
      roles: roleValues,
      meta: roleMeta,
    };
    return this._dashboardEntityDraft;
  }

  _allHAEntityOptions() {
    const out = [];
    const seen = new Set();
    const states = this._hass?.states || {};
    Object.entries(states).forEach(([entityId, stateObj]) => {
      if (!entityId || seen.has(entityId)) return;
      seen.add(entityId);
      const attrs = stateObj?.attributes || {};
      const friendly = attrs.friendly_name || entityId;
      const domain = entityId.includes(".") ? entityId.split(".")[0] : "entity";
      out.push({
        entity_id: entityId,
        name: friendly,
        state: stateObj?.state ?? "",
        domain,
        source: "hass",
      });
    });

    // Merge backend registry-derived options as fallback/source of original names.
    const backend = [
      ...(this._settingsData?.ai_entity_manager?.entity_options || []),
      ...(this._settingsData?.report_entity_manager?.entity_options || []),
      ...(this._settingsData?.dashboard_entity_manager?.entity_options || []),
    ];
    const backendById = new Map();
    backend.forEach((item) => {
      if (item?.entity_id) backendById.set(item.entity_id, item);
    });
    out.forEach((item) => {
      const meta = backendById.get(item.entity_id) || {};
      item.role_guess = meta.role_guess || item.role_guess || "";
      item.category = meta.category || item.category || "";
      item.expected_entity = meta.expected_entity || item.expected_entity || "";
      item.original_name = meta.original_name || item.original_name || "";
      item.registry_name = meta.registry_name || item.registry_name || "";
      item.unique_id = meta.unique_id || item.unique_id || "";
      item.translation_key = meta.translation_key || item.translation_key || "";
      item.platform = meta.platform || item.platform || "";
      item.match_text = meta.match_text || item.match_text || "";
      item.has_state = meta.has_state ?? true;
    });
    backend.forEach((item) => {
      const entityId = item?.entity_id || "";
      if (!entityId || seen.has(entityId)) return;
      seen.add(entityId);
      out.push({
        entity_id: entityId,
        name: item.name || entityId,
        state: item.state ?? "",
        domain: item.domain || (entityId.includes(".") ? entityId.split(".")[0] : "entity"),
        source: "registry",
        role_guess: item.role_guess || "",
        category: item.category || "",
        expected_entity: item.expected_entity || "",
        original_name: item.original_name || "",
        registry_name: item.registry_name || "",
        unique_id: item.unique_id || "",
        translation_key: item.translation_key || "",
        platform: item.platform || "",
        match_text: item.match_text || "",
        has_state: item.has_state ?? false,
      });
    });

    const score = (item) => {
      const hay = this._normalizeSearchText(`${item.entity_id || ""} ${item.name || ""}`);
      if (hay.includes("pom tesla") || hay.includes("tesla") || hay.includes("pom_")) return 0;
      if (String(item.entity_id || "").startsWith("sensor.pom")) return 1;
      if (String(item.entity_id || "").startsWith("binary_sensor.pom")) return 2;
      return 10;
    };
    return out.sort((a, b) => score(a) - score(b) || String(a.name || a.entity_id).localeCompare(String(b.name || b.entity_id), "tr"));
  }

  _entityOptionById(entityId) {
    if (!entityId) return null;
    const states = this._hass?.states || {};
    const stateObj = states[entityId];
    if (stateObj) {
      const attrs = stateObj.attributes || {};
      return {
        entity_id: entityId,
        name: attrs.friendly_name || entityId,
        state: stateObj.state ?? "",
        domain: entityId.includes(".") ? entityId.split(".")[0] : "entity",
      };
    }
    const options = [
      ...(this._settingsData?.ai_entity_manager?.entity_options || []),
      ...(this._settingsData?.report_entity_manager?.entity_options || []),
      ...(this._settingsData?.dashboard_entity_manager?.entity_options || []),
    ];
    return options.find((item) => item.entity_id === entityId) || null;
  }

  _entityDisplay(entityId) {
    const opt = this._entityOptionById(entityId);
    if (!entityId) return "";
    if (!opt) return entityId;
    return opt.name || entityId;
  }

  _entityMeta(entityId) {
    const opt = this._entityOptionById(entityId);
    if (!entityId) return "";
    if (!opt) return entityId;
    const bits = [entityId, opt.state].filter((v) => v !== undefined && v !== null && String(v) !== "");
    return bits.join(" · ");
  }

  _renderEntityPickerField(target, value, placeholder = "sensor.pom_battery_level") {
    const opt = this._entityOptionById(value);
    const stateClass = !value ? " empty" : (!opt ? " invalid" : "");
    const display = value ? (opt?.name || value) : this._t("entityNotSelected");
    const meta = !value ? placeholder : (!opt ? this._t("unknownEntitySelected") : this._entityMeta(value));
    return `
      <button type="button" class="entity-picker-field compact-ha-field${stateClass}" data-entity-picker-target="${this._esc(target)}" title="${this._esc(value || this._t("chooseEntity"))}">
        <span class="entity-picker-main">
          <strong class="entity-friendly">${this._esc(display)}</strong>
          <small class="entity-meta-line">${this._esc(meta)}</small>
        </span>
        <span class="entity-picker-arrow">▾</span>
      </button>
    `;
  }

  _syncHAEntityPickers() {
    // We intentionally use the internal picker. Native ha-entity-picker is not
    // reliable inside this custom panel shell on every HA frontend build.
  }

  _normalizeSearchText(value) {
    return String(value || "")
      .toLocaleLowerCase("tr-TR")
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .replace(/ı/g, "i")
      .replace(/İ/g, "i")
      .replace(/ş/g, "s")
      .replace(/ğ/g, "g")
      .replace(/ü/g, "u")
      .replace(/ö/g, "o")
      .replace(/ç/g, "c");
  }

  _normalizeEntitySearchKey(value) {
    return this._normalizeSearchText(value)
      .replace(/[\-. /:\()\[\]{}|+]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  _technicalEntityText(item) {
    return this._normalizeEntitySearchKey([
      item?.entity_id || "",
      item?.original_name || "",
      item?.registry_name || "",
      item?.unique_id || "",
      item?.translation_key || "",
      item?.platform || "",
      item?.match_text || "",
    ].join(" "));
  }

  _expectedObjectId(expected) {
    const value = String(expected || "").trim();
    return value.includes(".") ? value.split(".").slice(1).join(".") : value;
  }

  _roleMatchTokens(roleDef) {
    const expected = String(roleDef?.expected_entity || "").trim();
    const tokens = new Set();
    if (expected) {
      const obj = this._expectedObjectId(expected);
      tokens.add(this._normalizeEntitySearchKey(expected));
      tokens.add(this._normalizeEntitySearchKey(obj));
      const parts = obj.split("_").filter(Boolean);
      for (let size = 2; size <= Math.min(5, parts.length); size += 1) {
        tokens.add(this._normalizeSearchText(parts.slice(-size).join("_")));
      }
    }
    return Array.from(tokens).filter(Boolean);
  }

  _scoreEntityOptionForPicker(item, roleDef) {
    if (!roleDef) return 100;
    const entityId = String(item?.entity_id || "");
    const expected = String(roleDef.expected_entity || "");
    const technical = this._technicalEntityText(item);
    const friendly = this._normalizeSearchText(`${item?.name || ""} ${item?.state || ""}`);
    let score = 1000;
    if (expected && entityId === expected) score -= 950;
    if (expected && entityId.includes(".") && expected.includes(".")) {
      const entityDomain = entityId.split(".")[0];
      const expectedDomain = expected.split(".")[0];
      const entityObj = entityId.split(".").slice(1).join(".");
      const expectedObj = expected.split(".").slice(1).join(".");
      if (entityDomain === expectedDomain) score -= 25;
      if (entityObj === expectedObj) score -= 700;
      else if (entityObj.endsWith(`_${expectedObj}`) || expectedObj.endsWith(`_${entityObj}`)) score -= 250;
    }
    for (const token of this._roleMatchTokens(roleDef)) {
      if (token && technical.includes(token)) score -= 180;
      else if (token && friendly.includes(token)) score -= 15;
    }
    if (item?.role_guess && item.role_guess === roleDef.role) score -= 90;
    if (technical.includes("pom") || technical.includes("tessie")) score -= 30;
    if (technical.includes("teslamate") || entityId.startsWith("sensor.tesla_")) score -= 25;
    if (item?.has_state === false) score += 20;
    return score;
  }

  _scoreEntityOptionForQuery(item, qRaw) {
    const raw = String(qRaw || "").trim();
    if (!raw) return 0;
    const qText = this._normalizeSearchText(raw);
    const qKey = this._normalizeEntitySearchKey(raw);
    const entityId = String(item?.entity_id || "");
    const entityText = this._normalizeSearchText(entityId);
    const entityKey = this._normalizeEntitySearchKey(entityId);
    const friendly = this._normalizeSearchText(`${item?.name || ""} ${item?.state || ""}`);
    const technical = this._technicalEntityText(item);
    if (entityText === qText || entityKey === qKey) return -10000;
    if (entityText.startsWith(qText) || entityKey.startsWith(qKey)) return -9000;
    if (entityText.includes(qText) || entityKey.includes(qKey)) return -8000;
    if (technical.includes(qKey)) return -7000;
    if (friendly.includes(qText) || friendly.includes(qKey)) return -4000;
    return 0;
  }

  _filteredEntityOptions() {
    const all = this._allHAEntityOptions();
    const roleDef = this._pickerRoleDefinition();
    const qRaw = String(this._entityPickerSearch || "").trim();
    const qText = this._normalizeSearchText(qRaw);
    const qKey = this._normalizeEntitySearchKey(qRaw);
    const tokens = qKey.split(/_+/).filter(Boolean);
    let result = all;
    if (qRaw) {
      result = all.filter((item) => {
        const rawHay = this._normalizeSearchText([
          item?.entity_id || "",
          item?.name || "",
          item?.domain || "",
          item?.state || "",
          item?.original_name || "",
          item?.registry_name || "",
          item?.unique_id || "",
          item?.translation_key || "",
          item?.platform || "",
          item?.match_text || "",
        ].join(" "));
        const keyHay = this._normalizeEntitySearchKey(rawHay);
        return rawHay.includes(qText)
          || keyHay.includes(qKey)
          || tokens.every((token) => rawHay.includes(token) || keyHay.includes(token));
      });
    } else if (!roleDef) {
      const preferred = all.filter((item) => {
        const hay = `${this._technicalEntityText(item)} ${this._normalizeEntitySearchKey(item.name || "")}`;
        return hay.includes("tesla") || hay.includes("pom") || hay.includes("tessie") || hay.includes("teslamate");
      });
      result = preferred.length ? preferred : all;
    }
    return result
      .slice()
      .sort((a, b) => this._scoreEntityOptionForQuery(a, qRaw) - this._scoreEntityOptionForQuery(b, qRaw) || this._scoreEntityOptionForPicker(a, roleDef) - this._scoreEntityOptionForPicker(b, roleDef) || String(a.name || a.entity_id).localeCompare(String(b.name || b.entity_id), this._lang === "en" ? "en" : "tr"))
      .slice(0, 180);
  }

  _openEntityPicker(target) {
    this._entityPickerTarget = target || "";
    this._entityPickerSearch = "";
    this._render();
    setTimeout(() => this.shadowRoot.getElementById("entity_picker_search")?.focus(), 0);
  }

  _closeEntityPicker() {
    this._entityPickerTarget = "";
    this._entityPickerSearch = "";
    this._render();
  }

  _setEntityForTarget(target, entityId) {
    const draft = this._getAIEntityDraft();
    const cleanEntityId = String(entityId || "").trim();
    if (target === "report_main_entity") {
      const reportDraft = this._getReportEntityDraft();
      reportDraft.main_entity = cleanEntityId;
      return;
    }
    if (target.startsWith("report_role_")) {
      const reportDraft = this._getReportEntityDraft();
      reportDraft.roles[target.slice("report_role_".length)] = cleanEntityId;
      return;
    }
    if (target === "dashboard_main_entity") {
      const dashboardDraft = this._getDashboardEntityDraft();
      dashboardDraft.main_entity = cleanEntityId;
      return;
    }
    if (target.startsWith("dashboard_role_")) {
      const dashboardDraft = this._getDashboardEntityDraft();
      const role = target.slice("dashboard_role_".length);
      dashboardDraft.roles[role] = cleanEntityId;
      dashboardDraft.meta = dashboardDraft.meta || {};
      dashboardDraft.meta[role] = dashboardDraft.meta[role] || {};
      if (cleanEntityId && !dashboardDraft.meta[role].name) dashboardDraft.meta[role].name = this._entityDisplay(cleanEntityId);
      return;
    }
    if (target === "ai_main_entity") draft.main_entity = cleanEntityId;
    else if (target.startsWith("ai_role_")) {
      draft.roles[target.slice("ai_role_".length)] = cleanEntityId;
      // When an entity is assigned to its fixed role slot, it is no longer an
      // Extra AI Entity. Remove it immediately from the custom list so the UI,
      // saved payload and AI context stay consistent.
      this._dedupeAIEntityDraft(draft);
    } else if (target.startsWith("ai_custom_")) {
      const index = Number(target.slice("ai_custom_".length));
      if (Number.isFinite(index) && draft.custom[index]) draft.custom[index].entity_id = cleanEntityId;
      this._dedupeAIEntityDraft(draft);
    }
  }

  _setEntityForPickerTarget(entityId) {
    const target = this._entityPickerTarget || "";
    this._setEntityForTarget(target, entityId);
    this._entityPickerTarget = "";
    this._entityPickerSearch = "";
    this._render();
  }

  _entityDomain(entityId) {
    return String(entityId || "").includes(".") ? String(entityId).split(".")[0] : "entity";
  }

  _renderEntityOptionItem(item) {
    const entityId = item.entity_id || "";
    const name = item.name || entityId;
    const state = item.state || "";
    const domain = this._entityDomain(entityId);
    const icon = domain.slice(0, 1).toUpperCase();
    return `
      <button type="button" class="entity-option" data-entity-id="${this._esc(entityId)}">
        <span class="entity-option-icon">${this._esc(icon)}</span>
        <span class="entity-option-main">
          <b>${this._esc(name)}</b>
          <small>${this._esc(entityId)}${item.original_name && item.original_name !== name ? ` · ${this._esc(item.original_name)}` : ""}${state ? ` · ${this._esc(state)}` : ""}</small>
        </span>
        <span class="entity-option-domain">${this._esc(domain)}</span>
      </button>
    `;
  }

  _renderEntityPickerListHtml() {
    const all = this._allHAEntityOptions();
    const options = this._filteredEntityOptions();
    const debugText = this._t("entityPickerDebug")
      .replace("{total}", String(all.length))
      .replace("{count}", String(options.length));
    const body = options.length
      ? options.map((item) => this._renderEntityOptionItem(item)).join("")
      : `<div class="note entity-empty">${this._t("entityPickerNoResults")}</div>`;
    return `<div class="entity-picker-debug">${this._esc(debugText)}</div>${body}`;
  }

  _refreshEntityPickerList() {
    const list = this.shadowRoot?.querySelector?.(".entity-picker-list");
    if (list) list.innerHTML = this._renderEntityPickerListHtml();
  }

  _renderEntityPickerOverlay() {
    if (!this._entityPickerTarget) return "";
    return `
      <div class="entity-picker-overlay" data-entity-picker-backdrop="1">
        <div class="entity-picker-modal" role="dialog" aria-modal="true">
          <div class="entity-picker-head">
            <div>
              <h3>${this._t("entityPickerTitle")}</h3>
              <p>${this._t("entityPickerHint")}</p>
              ${this._pickerRoleDefinition()?.expected_entity ? `<p class="entity-picker-expected">${this._esc(this._t("entityPickerExpected").replace("{entity}", this._pickerRoleDefinition().expected_entity))}</p>` : ""}
            </div>
            <button type="button" class="entity-picker-close">×</button>
          </div>
          <input id="entity_picker_search" class="entity-picker-search" autocomplete="off" autocapitalize="off" spellcheck="false" value="${this._esc(this._entityPickerSearch || "")}" placeholder="${this._esc(this._t("entityPickerSearch"))}" />
          <div class="entity-picker-list">${this._renderEntityPickerListHtml()}</div>
        </div>
      </div>
    `;
  }

  _readAIEntityManagerForm() {
    const current = this._settingsData?.ai_entity_manager || {};
    const roles = current.roles || [];
    const draft = this._dedupeAIEntityDraft(this._getAIEntityDraft());
    const entries = [];
    const fixedEntities = new Set();
    roles.forEach((roleDef) => {
      const entity = String(draft.roles?.[roleDef.role] || "").trim();
      if (!entity) return;
      fixedEntities.add(entity);
      entries.push({ role: roleDef.role, entity_id: entity, use_ai: true });
    });
    const seenCustom = new Set();
    (draft.custom || []).forEach((item) => {
      const entity = String(item.entity_id || "").trim();
      if (!entity || fixedEntities.has(entity) || seenCustom.has(entity)) return;
      seenCustom.add(entity);
      entries.push({ role: "other", entity_id: entity, use_ai: true });
    });
    return {
      action: "save",
      replace_all: true,
      main_entity: String(draft.main_entity || current.main_entity || "").trim(),
      auto_discover_device_entities: this._checked("ai_auto_discover_device_entities"),
      entries,
    };
  }

  _showAutoFindNotice(kind) {
    const label = kind === "dashboard"
      ? this._t("dashboardEntityManager")
      : (kind === "report" ? this._t("reportEntityManager") : this._t("aiEntityManager"));
    this._autoFindNotice = { kind, label, closed: false };
  }

  _hideAutoFindNotice() {
    this._autoFindNotice = null;
  }

  _closeAutoFindNotice() {
    if (this._autoFindNotice) this._autoFindNotice.closed = true;
    this._render();
  }

  _renderAutoFindNoticeBanner() {
    const notice = this._autoFindNotice;
    if (!notice || notice.closed) return "";
    const label = notice.label || this._t("autoFindRunning");
    return `
      <div class="autofind-banner" id="autoFindNoticeBanner">
        <div class="autofind-banner-spinner"></div>
        <div class="autofind-banner-main">
          <b>${this._esc(this._t("autoFindWarningTitle"))} · ${this._esc(label)}</b>
          <div>${this._esc(this._t("autoFindWarningDoNotLeave"))}</div>
          <small>${this._esc(this._t("autoFindWarningText"))} ${this._esc(this._t("autoFindWarningSub"))}</small>
        </div>
        <button type="button" class="autofind-banner-close" id="autoFindNoticeClose">×</button>
      </div>
    `;
  }

  _sleep(ms) {
    return new Promise((resolve) => window.setTimeout(resolve, ms));
  }

  async _pollAutoFindJob(kind) {
    const label = kind === "dashboard"
      ? this._t("dashboardEntityManager")
      : (kind === "report" ? this._t("reportEntityManager") : this._t("aiEntityManager"));
    for (let attempt = 0; attempt < 180; attempt += 1) {
      await this._sleep(attempt < 3 ? 800 : 1200);
      let payload = null;
      try {
        payload = await this._hass.callApi("POST", "pom_tesla_report/settings", {
          action: "auto_find_status",
          kind,
        });
      } catch (err) {
        this._error = this._formatError(err);
        this._render();
        return null;
      }

      const job = payload?.auto_find_job || {};
      const status = String(job.status || "idle");
      const countInfo = Number.isFinite(Number(job.found_count)) ? ` · ${job.found_count}` : "";
      this._status = `${label}: ${job.message || this._t("autoFindRunning")}${countInfo}`;
      this._error = job.error || "";
      this._render();

      if (status === "done") {
        const settingsPayload = job.settings || payload.settings || payload;
        this._settingsData = this._applySettingsSaveResponse(settingsPayload, {});
        if (kind === "dashboard") {
          this._dashboardEntityDraft = null;
          this._status = this._t("dashboardAutoFindDone");
        } else if (kind === "report") {
          this._reportEntityDraft = null;
          this._status = this._t("reportAutoFindDone");
        } else {
          this._aiEntityDraft = null;
          this._status = this._t("aiAutoFindDone");
        }
        this._error = "";
        this._hideAutoFindNotice();
        this._render();
        return job;
      }

      if (status === "error") {
        this._error = job.error || this._t("autoFindFailed");
        this._status = "";
        this._hideAutoFindNotice();
        this._render();
        return job;
      }
    }
    this._status = this._t("autoFindStillRunning");
    this._hideAutoFindNotice();
    this._render();
    return null;
  }

  async _saveAIEntityManager() {
    if (!this._hass) return;
    const ai_entity_manager = this._readAIEntityManagerForm();
    this._loading = true;
    this._error = "";
    this._render();
    try {
      this._settingsData = this._applySettingsSaveResponse(await this._hass.callApi("POST", "pom_tesla_report/settings", { ai_entity_manager }), { ai_entity_manager });
      this._aiEntityDraft = null;
      this._status = this._t("aiEntitiesSaved");
    } catch (err) {
      this._error = this._formatError(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _autoFindAIEntities() {
    if (!this._hass) return;
    const ai_entity_manager = this._readAIEntityManagerForm();
    ai_entity_manager.action = "auto_find_async";
    this._loading = false;
    this._error = "";
    this._status = this._t("autoFindStarted");
    this._showAutoFindNotice("ai");
    this._render();
    try {
      const started = await this._hass.callApi("POST", "pom_tesla_report/settings", { ai_entity_manager });
      const job = started?.auto_find_job || {};
      this._status = job.message || this._t("autoFindStarted");
      this._render();
      await this._pollAutoFindJob("ai");
    } catch (err) {
      this._error = this._formatError(err);
      this._hideAutoFindNotice();
      this._render();
    }
  }

  _readReportEntityManagerForm() {
    const current = this._settingsData?.report_entity_manager || {};
    const roles = current.roles || [];
    const draft = this._getReportEntityDraft();
    const entries = [];
    roles.forEach((roleDef) => {
      const entity = String(draft.roles?.[roleDef.role] || "").trim();
      if (!entity) return;
      entries.push({
        role: roleDef.role,
        entity_id: entity,
        use_report: true,
        use_ai: true,
        use_map: roleDef.role === "location_tracker",
      });
    });
    return {
      action: "save",
      main_entity: String(draft.main_entity || current.main_entity || "").trim(),
      entries,
    };
  }

  async _saveReportEntityManager() {
    if (!this._hass) return;
    const report_entity_manager = this._readReportEntityManagerForm();
    this._loading = true;
    this._error = "";
    this._render();
    try {
      this._settingsData = this._applySettingsSaveResponse(await this._hass.callApi("POST", "pom_tesla_report/settings", { report_entity_manager }), { report_entity_manager });
      this._reportEntityDraft = null;
      this._status = this._t("reportEntitiesSaved");
    } catch (err) {
      this._error = this._formatError(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _autoFindReportEntities() {
    if (!this._hass) return;
    const report_entity_manager = this._readReportEntityManagerForm();
    report_entity_manager.action = "auto_find_async";
    this._loading = false;
    this._error = "";
    this._status = this._t("autoFindStarted");
    this._showAutoFindNotice("report");
    this._render();
    try {
      const started = await this._hass.callApi("POST", "pom_tesla_report/settings", { report_entity_manager });
      const job = started?.auto_find_job || {};
      this._status = job.message || this._t("autoFindStarted");
      this._render();
      await this._pollAutoFindJob("report");
    } catch (err) {
      this._error = this._formatError(err);
      this._hideAutoFindNotice();
      this._render();
    }
  }

  _clearReportRole(role) {
    const draft = this._getReportEntityDraft();
    if (draft.roles) draft.roles[role] = "";
    this._render();
  }

  _readDashboardEntityManagerForm() {
    const current = this._settingsData?.dashboard_entity_manager || {};
    const roles = current.roles || [];
    const draft = this._getDashboardEntityDraft();
    const entries = [];
    roles.forEach((roleDef) => {
      const entity = String(draft.roles?.[roleDef.role] || "").trim();
      if (!entity) return;
      const meta = draft.meta?.[roleDef.role] || {};
      entries.push({
        role: roleDef.role,
        entity_id: entity,
        icon: String(meta.icon || "").trim(),
        name: String(meta.name || "").trim(),
      });
    });
    return {
      action: "save",
      main_entity: String(draft.main_entity || current.main_entity || "").trim(),
      entries,
    };
  }

  async _saveDashboardEntityManager() {
    if (!this._hass) return;
    const dashboard_entity_manager = this._readDashboardEntityManagerForm();
    this._loading = true;
    this._error = "";
    this._render();
    try {
      this._settingsData = this._applySettingsSaveResponse(await this._hass.callApi("POST", "pom_tesla_report/settings", { dashboard_entity_manager }), { dashboard_entity_manager });
      this._dashboardEntityDraft = null;
      this._status = this._t("dashboardEntitiesSaved");
    } catch (err) {
      this._error = this._formatError(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _autoFindDashboardEntities() {
    if (!this._hass) return;
    const dashboard_entity_manager = this._readDashboardEntityManagerForm();
    dashboard_entity_manager.action = "auto_find_async";
    this._loading = false;
    this._error = "";
    this._status = this._t("autoFindStarted");
    this._showAutoFindNotice("dashboard");
    this._render();
    try {
      const started = await this._hass.callApi("POST", "pom_tesla_report/settings", { dashboard_entity_manager });
      const job = started?.auto_find_job || {};
      this._status = job.message || this._t("autoFindStarted");
      this._render();
      await this._pollAutoFindJob("dashboard");
    } catch (err) {
      this._error = this._formatError(err);
      this._hideAutoFindNotice();
      this._render();
    }
  }

  _clearDashboardRole(role) {
    const draft = this._getDashboardEntityDraft();
    if (draft.roles) draft.roles[role] = "";
    if (draft.meta?.[role]) draft.meta[role] = { icon: "", name: "" };
    this._render();
  }


  _clearAIRole(role) {
    const draft = this._getAIEntityDraft();
    if (draft.roles) draft.roles[role] = "";
    this._render();
  }

  _clearAllAIEntities() {
    if (!confirm(this._t("clearAllAiConfirm"))) return;
    const draft = this._getAIEntityDraft();
    draft.main_entity = "";
    Object.keys(draft.roles || {}).forEach((key) => { draft.roles[key] = ""; });
    draft.custom = [];
    this._status = this._t("clearAllAiDraftDone");
    this._error = "";
    this._render();
  }

  _clearAllDashboardEntities() {
    if (!confirm(this._t("clearAllDashboardConfirm"))) return;
    const draft = this._getDashboardEntityDraft();
    draft.main_entity = "";
    Object.keys(draft.roles || {}).forEach((key) => { draft.roles[key] = ""; });
    draft.meta = {};
    this._status = this._t("clearAllDashboardDraftDone");
    this._error = "";
    this._render();
  }

  _addCustomAIEntry() {
    const draft = this._getAIEntityDraft();
    draft.custom = Array.isArray(draft.custom) ? draft.custom : [];
    draft.custom.push({ role: "other", entity_id: "" });
    this._render();
  }

  _removeCustomAIEntry(index) {
    const draft = this._getAIEntityDraft();
    draft.custom = (draft.custom || []).filter((_item, idx) => idx !== Number(index));
    this._render();
  }

  _captureStationDraft() {
    const root = this.shadowRoot;
    const nameEl = root.getElementById("station_name");
    const priceEl = root.getElementById("station_unit_price");
    const currencyEl = root.getElementById("station_currency");
    if (!nameEl && !priceEl && !currencyEl) return;
    const current = this._editingStation || {};
    const priceText = priceEl?.value ?? current.unit_price ?? "";
    this._editingStation = {
      ...current,
      name: nameEl?.value ?? current.name ?? "",
      unit_price: priceText === "" ? "" : this._number(priceText),
      currency: currencyEl?.value || current.currency || this._settingsData?.charging?.report_currency || this._currency || "TL",
    };
  }

  async _saveCharge(mode) {
    if (!this._hass) return;
    const rec = this._readChargeForm();
    if (!rec.provider) {
      this._error = this._t("missingProvider");
      this._render();
      return;
    }
    if (![rec.added_kwh, rec.total_cost, rec.price_per_kwh].every(Number.isFinite)) {
      this._error = this._t("invalidChargeNumbers");
      this._render();
      return;
    }
    const action = mode === "add" || !this._selectedChargeId ? "add" : "update";
    const payload = { action, record: rec };
    if (action === "update") payload.id = this._selectedChargeId;
    await this._postRecord("charge", payload, action);
  }

  async _saveTrip(mode) {
    if (!this._hass) return;
    const rec = this._readTripForm();
    if (!Number.isFinite(rec.trip_km) || rec.trip_km <= 0) {
      this._error = this._t("missingTripFields");
      this._render();
      return;
    }
    if (![rec.trip_km, rec.duration_minutes, rec.used_kwh, rec.consumption_kwh_100km, rec.total_cost].every(Number.isFinite)) {
      this._error = this._t("invalidTripNumbers");
      this._render();
      return;
    }
    const action = mode === "add" || !this._selectedTripId ? "add" : "update";
    const payload = { action, record: rec };
    if (action === "update") payload.id = this._selectedTripId;
    await this._postRecord("trip", payload, action);
  }

  async _postRecord(type, payload, action) {
    this._loading = true;
    this._error = "";
    this._render();
    try {
      if (type === "trip") {
        this._tripData = await this._hass.callApi("POST", "pom_tesla_report/trip_records", payload);
        this._status = this._t("saved");
        const saved = action === "update"
          ? this._tripData.records.find((r) => r.id === this._selectedTripId)
          : this._tripData.records[0];
        if (saved) {
          this._selectedTripId = saved.id;
          this._editingTrip = { ...saved };
        }
      } else {
        this._chargeData = await this._hass.callApi("POST", "pom_tesla_report/charge_records", payload);
        this._status = this._t("saved");
        const saved = action === "update"
          ? this._chargeData.records.find((r) => r.id === this._selectedChargeId)
          : this._chargeData.records[0];
        if (saved) {
          this._selectedChargeId = saved.id;
          this._editingCharge = { ...saved };
        }
      }
    } catch (err) {
      this._error = this._formatError(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _moveStationToReportSlot(index, slot) {
    index = Number(index);
    slot = Number(slot);
    const current = { ...(this._settingsData || this._normalizeSettingsPayload({})) };
    current.charging = { ...(current.charging || {}) };
    const list = [...(current.charging.provider_presets || [])];
    if (!Number.isInteger(index) || !Number.isInteger(slot) || index < 0 || index >= list.length || slot < 0 || slot > 2) {
      return;
    }
    const [item] = list.splice(index, 1);
    list.splice(slot, 0, item);
    current.charging.provider_presets = list;
    this._settingsData = current;
    this._selectedStationIndex = slot;
    this._editingStation = { ...item };
    this._status = this._t("reportSlotUpdated");
    this._error = "";
    await this._saveSettings();
  }

  async _addOrUpdateStation() {
    const station = this._readStationForm();
    if (!station.name || !Number.isFinite(station.unit_price) || station.unit_price <= 0) {
      this._error = this._t("missingStation");
      this._render();
      return;
    }
    const current = { ...(this._settingsData || this._normalizeSettingsPayload({})) };
    current.charging = { ...(current.charging || {}) };
    const list = [...(current.charging.provider_presets || [])];
    const normalizedName = station.name.toLocaleLowerCase();
    const existingIndex = this._selectedStationIndex >= 0
      ? this._selectedStationIndex
      : list.findIndex((item) => String(item.name || "").toLocaleLowerCase() === normalizedName);
    const normalized = { id: normalizedName, name: station.name, unit_price: station.unit_price, currency: station.currency };
    if (existingIndex >= 0 && existingIndex < list.length) list[existingIndex] = normalized;
    else list.push(normalized);
    current.charging.provider_presets = list;
    this._settingsData = current;
    this._selectedStationIndex = list.findIndex((item) => item.name === normalized.name);
    this._editingStation = { ...normalized };
    this._status = "";
    this._error = "";
    await this._saveSettings();
  }

  async _deleteStation() {
    if (this._selectedStationIndex < 0) {
      this._error = this._t("noSelection");
      this._render();
      return;
    }
    if (!confirm(this._t("confirmStationDelete"))) return;
    const current = { ...(this._settingsData || this._normalizeSettingsPayload({})) };
    current.charging = { ...(current.charging || {}) };
    const list = [...(current.charging.provider_presets || [])];
    list.splice(this._selectedStationIndex, 1);
    current.charging.provider_presets = list;
    this._settingsData = current;
    this._selectedStationIndex = -1;
    this._editingStation = { name: "", unit_price: "", currency: current.charging.report_currency || this._currency || "TL" };
    this._status = "";
    this._error = "";
    await this._saveSettings();
  }

  async _saveSettings() {
    if (!this._hass) return;
    const charging = this._readSettingsForm();
    const presets = Array.isArray(charging.provider_presets) ? charging.provider_presets : [];
    const hasInvalidPreset = presets.some((item) => !item || !String(item.name || "").trim() || !Number.isFinite(this._number(item.unit_price)) || this._number(item.unit_price) <= 0);
    if (hasInvalidPreset) {
      this._error = this._t("missingStation");
      this._render();
      return;
    }
    this._loading = true;
    this._error = "";
    this._render();
    try {
      this._settingsData = this._applySettingsSaveResponse(await this._hass.callApi("POST", "pom_tesla_report/settings", { charging }), { charging });
      const newCurrency = this._settingsData?.currency || this._currency;
      if (this._chargeData) this._chargeData.currency = newCurrency;
      if (this._tripData) this._tripData.currency = newCurrency;
      this._status = this._t("settingsSaved");
      this._ensureStationEditor();
    } catch (err) {
      this._error = this._formatError(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }


  async _saveTelegramSettings() {
    if (!this._hass) return;
    const telegram = this._readTelegramSettingsForm();
    if (!Number.isFinite(telegram.builtin_telegram_poll_interval_seconds) || telegram.builtin_telegram_poll_interval_seconds < 1) {
      this._error = this._t("invalidTripNumbers");
      this._render();
      return;
    }
    this._loading = true;
    this._error = "";
    this._render();
    try {
      this._settingsData = this._applySettingsSaveResponse(await this._hass.callApi("POST", "pom_tesla_report/settings", { telegram }), { telegram });
      this._status = this._t("telegramSettingsSaved");
      this._ensureStationEditor();
    } catch (err) {
      this._error = this._formatError(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }


  async _loadTelegramDiagnostics() {
    if (!this._hass) return;
    try {
      this._telegramDiagnostics = await this._hass.callApi("GET", "pom_tesla_report/telegram_test");
    } catch (err) {
      this._error = this._formatError(err);
    }
  }

  async _runTelegramTest(action) {
    if (!this._hass) return;
    const telegram = this._readTelegramSettingsForm();
    const target = telegram.telegram_group_id || this._settingsData?.telegram?.telegram_group_id || "";
    const msg = this.shadowRoot.getElementById("telegram_test_message")?.value?.trim() || (this._lang === "en" ? "POM Telegram test message" : "POM Telegram test mesajı");
    this._loading = true;
    this._error = "";
    this._render();
    try {
      this._telegramDiagnostics = await this._hass.callApi("POST", "pom_tesla_report/telegram_test", {
        action,
        target,
        message: msg,
        telegram,
      });
      this._status = action === "poll_once" ? this._t("telegramPollOk") : this._t("telegramTestSent");
    } catch (err) {
      this._error = this._formatError(err);
      try { await this._loadTelegramDiagnostics(); } catch (_e) {}
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _clearTelegramLogs() {
    if (!this._hass) return;
    this._loading = true;
    this._error = "";
    this._render();
    try {
      this._telegramDiagnostics = await this._hass.callApi("POST", "pom_tesla_report/telegram_test", { action: "clear_logs" });
      this._status = this._t("telegramLogsCleared");
    } catch (err) {
      this._error = this._formatError(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _loadAIDiagnostics() {
    if (!this._hass) return;
    try {
      this._aiDiagnostics = await this._hass.callApi("GET", "pom_tesla_report/ai_test");
    } catch (err) {
      this._error = this._formatError(err);
    }
  }

  async _runAITest(sendTelegram = false) {
    if (!this._hass) return;
    const ai_settings = this._readAISettingsForm();
    const prompt = this.shadowRoot.getElementById("ai_test_prompt")?.value?.trim() || (this._lang === "en" ? "Reply briefly: did the POM Tesla AI connectivity test succeed?" : "Kısaca cevap ver: POM Tesla AI bağlantı testi başarılı mı?");
    this._loading = true;
    this._error = "";
    this._render();
    try {
      this._aiDiagnostics = await this._hass.callApi("POST", "pom_tesla_report/ai_test", {
        action: sendTelegram ? "run_test_send_telegram" : "run_test",
        prompt,
        ai_settings,
      });
      this._status = this._t(sendTelegram ? "aiTestTelegramOk" : "aiTestOk");
    } catch (err) {
      this._error = this._formatError(err);
      try { await this._loadAIDiagnostics(); } catch (_e) {}
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _clearAILogs() {
    if (!this._hass) return;
    this._loading = true;
    this._error = "";
    this._render();
    try {
      this._aiDiagnostics = await this._hass.callApi("POST", "pom_tesla_report/ai_test", { action: "clear_logs" });
      this._status = this._t("aiLogsCleared");
    } catch (err) {
      this._error = this._formatError(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _saveTripSettings() {
    if (!this._hass) return;
    const trip_reports = this._readTripSettingsForm();
    const numeric = [
      trip_reports.auto_start_speed_threshold,
      trip_reports.live_trip_update_interval_seconds,
      trip_reports.live_trip_traffic_speed_threshold,
      trip_reports.live_trip_finish_delay_seconds,
      trip_reports.live_trip_min_distance_km,
      trip_reports.trip_map_sample_interval_seconds,
      trip_reports.trip_map_min_movement_meters,
    ];
    if (!numeric.every(Number.isFinite)) {
      this._error = this._t("invalidTripNumbers");
      this._render();
      return;
    }
    this._loading = true;
    this._error = "";
    this._render();
    try {
      this._settingsData = this._applySettingsSaveResponse(await this._hass.callApi("POST", "pom_tesla_report/settings", { trip_reports }), { trip_reports });
      this._status = this._t("tripSettingsSaved");
      this._ensureStationEditor();
    } catch (err) {
      this._error = this._formatError(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }


  async _sendTestTripReport() {
    if (!this._hass) return;
    const trip_reports = this._readTripSettingsForm();
    const numeric = [
      trip_reports.auto_start_speed_threshold,
      trip_reports.live_trip_update_interval_seconds,
      trip_reports.live_trip_traffic_speed_threshold,
      trip_reports.live_trip_finish_delay_seconds,
      trip_reports.live_trip_min_distance_km,
      trip_reports.trip_map_sample_interval_seconds,
      trip_reports.trip_map_min_movement_meters,
    ];
    if (!numeric.every(Number.isFinite)) {
      this._error = this._t("invalidTripNumbers");
      this._render();
      return;
    }
    this._loading = true;
    this._error = "";
    this._render();
    try {
      // Save the currently visible trip toggles first so the test PNG uses the
      // exact values the user is trying from this screen.
      this._settingsData = this._applySettingsSaveResponse(await this._hass.callApi("POST", "pom_tesla_report/settings", { trip_reports }), { trip_reports });
      const result = await this._hass.callApi("POST", "pom_tesla_report/trip_test", {});
      const mapText = result?.map_included ? this._t("testTripMapIncluded") : this._t("testTripMapExcluded");
      this._status = `${this._t("testTripSent")} ${mapText}. ${this._t("testTripNoLedger")}`;
    } catch (err) {
      this._error = this._formatError(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _runLiveTripTestAction(action) {
    if (!this._hass) return;
    const trip_reports = this._readTripSettingsForm();
    const numeric = [
      trip_reports.auto_start_speed_threshold,
      trip_reports.live_trip_update_interval_seconds,
      trip_reports.live_trip_traffic_speed_threshold,
      trip_reports.live_trip_finish_delay_seconds,
      trip_reports.live_trip_min_distance_km,
      trip_reports.trip_map_sample_interval_seconds,
      trip_reports.trip_map_min_movement_meters,
    ];
    if (!numeric.every(Number.isFinite)) {
      this._error = this._t("invalidTripNumbers");
      this._render();
      return;
    }
    this._loading = true;
    this._error = "";
    this._render();
    try {
      this._settingsData = this._applySettingsSaveResponse(await this._hass.callApi("POST", "pom_tesla_report/settings", { trip_reports }), { trip_reports });
      const result = await this._hass.callApi("POST", "pom_tesla_report/live_trip_test", { action });
      const statusMap = {
        start: this._t("liveTripTestStarted"),
        finish: this._t("liveTripTestFinished"),
        reset: this._t("liveTripTestReset"),
      };
      this._status = result?.message || statusMap[action] || "OK";
      try { await this._loadSettings(); } catch (_e) {}
      try { this._liveTripDiagnostics = await this._hass.callApi("GET", "pom_tesla_report/live_trip_debug"); } catch (_e) {}
    } catch (err) {
      this._error = this._formatError(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _loadLiveTripDebug(showStatus = false) {
    if (!this._hass) return;
    this._loading = true;
    this._error = "";
    this._render();
    try {
      this._liveTripDiagnostics = await this._hass.callApi("GET", "pom_tesla_report/live_trip_debug");
      if (showStatus) this._status = this._t("liveTripDebugLoaded");
    } catch (err) {
      this._error = this._formatError(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  _renderLiveTripDebugPanel() {
    const diag = this._liveTripDiagnostics || {};
    const warnings = diag?.derived?.warnings || [];
    const summary = {
      settings: diag.settings || {},
      derived: diag.derived || {},
      bindings: diag.bindings || {},
      live_trip_state: diag.live_trip_state || {},
      entity_states: diag.entity_states || {},
      teslamate_note: diag.teslamate_note || "",
    };
    return `
      <div class="debug-panel live-trip-debug">
        <div class="debug-head">
          <div><b>${this._t("liveTripDebug")}</b><div class="note">${this._t("liveTripDebugSub")}</div></div>
          <button id="refreshLiveTripDebugBtn" class="secondary">${this._t("refreshLiveTripDebug")}</button>
        </div>
        ${warnings.length ? `<div class="error">${warnings.map((w) => this._esc(w)).join(" · ")}</div>` : ""}
        <pre>${this._esc(JSON.stringify(summary, null, 2))}</pre>
      </div>
    `;
  }

  _findActionTarget(ev, selector) {
    const path = typeof ev.composedPath === "function" ? ev.composedPath() : [];
    for (const node of path) {
      if (node && node.matches && node.matches(selector)) return node;
    }
    return ev.target?.closest?.(selector) || null;
  }

  _handlePanelAction(action, ev) {
    if (ev) {
      ev.preventDefault();
      ev.stopPropagation();
      ev.stopImmediatePropagation?.();
    }
    if (action === "charge-test-monthly") {
      this._sendTestChargeReport("monthly_cost");
    } else if (action === "charge-test-completion") {
      this._sendTestChargeReport("completion_report");
    }
  }

  _handleDelegatedPointerDown(ev) {
    const settingsTab = this._findActionTarget(ev, "[data-settings-tab]");
    if (settingsTab) {
      ev.preventDefault();
      ev.stopPropagation();
      const tab = settingsTab.dataset.settingsTab || "general";
      this._lastClickDebug = {
        pointerdown_settings_tab: tab,
        target_id: ev.target?.id || "",
        target_tag: ev.target?.tagName || "",
        active_settings_tab: this._activeSettingsTab,
      };
      this._switchSettingsTabDirect(tab);
      return;
    }

    const dashboardSection = this._findActionTarget(ev, "[data-dashboard-section]");
    if (dashboardSection) {
      ev.preventDefault();
      ev.stopPropagation();
      const section = dashboardSection.dataset.dashboardSection || "general";
      this._lastClickDebug = {
        pointerdown_dashboard_section: section,
        target_id: ev.target?.id || "",
        target_tag: ev.target?.tagName || "",
        active_dashboard_section: this._dashboardSettingsSection,
      };
      this._switchDashboardSectionDirect(section);
      return;
    }
  }


  _handleDelegatedClick(ev) {
    try {
      const path = typeof ev.composedPath === "function" ? ev.composedPath() : [];
      this._lastClickDebug = {
        tag: ev.target?.tagName || "",
        id: ev.target?.id || "",
        cls: ev.target?.className || "",
        text: String(ev.target?.textContent || "").trim().slice(0, 80),
        path: path.slice(0, 8).map((node) => ({
          tag: node?.tagName || "",
          id: node?.id || "",
          cls: node?.className || "",
          settings_tab: node?.dataset?.settingsTab || "",
          dashboard_section: node?.dataset?.dashboardSection || "",
        })),
        active_settings_tab: this._activeSettingsTab,
        active_dashboard_section: this._dashboardSettingsSection,
      };
    } catch (err) {}
    const panelTarget = this._findActionTarget(ev, "[data-panel-action]");
    if (panelTarget) return this._handlePanelAction(panelTarget.dataset.panelAction, ev);
    const settingsTab = this._findActionTarget(ev, "[data-settings-tab]");
    if (settingsTab) {
      ev.preventDefault();
      ev.stopPropagation();
      this._activeSettingsTab = settingsTab.dataset.settingsTab || "general";
      this._status = "";
      this._error = "";
      if (this._activeSettingsTab === "charging") this._ensureStationEditor();
      this._render();
      return;
    }
    const subtab = this._findActionTarget(ev, "[data-entities-subtab]");
    if (subtab) { ev.preventDefault(); this._activeEntitiesTab = subtab.dataset.entitiesSubtab || "ai"; this._render(); return; }
    const tripSection = this._findActionTarget(ev, "[data-trip-section]");
    if (tripSection) { ev.preventDefault(); this._tripSettingsSection = tripSection.dataset.tripSection || "tracking"; this._render(); return; }
    const dashboardSection = this._findActionTarget(ev, "[data-dashboard-section]");
    if (dashboardSection) {
      ev.preventDefault();
      ev.stopPropagation();
      this._dashboardSettingsSection = dashboardSection.dataset.dashboardSection || "fullscreen";
      this._status = "";
      this._error = "";
      this._render();
      return;
    }
    if (this._findActionTarget(ev, ".add-ai-entry")) { ev.preventDefault(); this._addCustomAIEntry(); return; }
    const remove = this._findActionTarget(ev, ".remove-ai-custom-entry");
    if (remove) { ev.preventDefault(); this._removeCustomAIEntry(remove.dataset.index); return; }
    const clearAll = this._findActionTarget(ev, ".clear-all-ai-entities");
    if (clearAll) { ev.preventDefault(); this._clearAllAIEntities(); return; }
    const clearAllDashboard = this._findActionTarget(ev, ".clear-all-dashboard-entities");
    if (clearAllDashboard) { ev.preventDefault(); this._clearAllDashboardEntities(); return; }
    const clearReport = this._findActionTarget(ev, ".clear-report-role");
    if (clearReport) { ev.preventDefault(); this._clearReportRole(clearReport.dataset.role || ""); return; }
    const clearDashboard = this._findActionTarget(ev, ".clear-dashboard-role");
    if (clearDashboard) { ev.preventDefault(); this._clearDashboardRole(clearDashboard.dataset.role || ""); return; }
    const clear = this._findActionTarget(ev, ".clear-ai-role");
    if (clear) { ev.preventDefault(); this._clearAIRole(clear.dataset.role || ""); return; }
    if (this._findActionTarget(ev, "[data-stop-picker]")) return;
    const pickerTarget = this._findActionTarget(ev, "[data-entity-picker-target]");
    if (pickerTarget) { ev.preventDefault(); this._openEntityPicker(pickerTarget.dataset.entityPickerTarget || ""); return; }
    const option = this._findActionTarget(ev, ".entity-option");
    if (option) { ev.preventDefault(); this._setEntityForPickerTarget(option.dataset.entityId || ""); return; }
    if (this._findActionTarget(ev, ".entity-picker-close")) { ev.preventDefault(); this._closeEntityPicker(); return; }
    const backdrop = this._findActionTarget(ev, "[data-entity-picker-backdrop]");
    if (backdrop && ev.target === backdrop) { ev.preventDefault(); this._closeEntityPicker(); return; }
  }

  _switchSettingsTabDirect(tab) {
    this._activeSettingsTab = tab || "general";
    this._status = "";
    this._error = "";
    if (this._activeSettingsTab === "charging") this._ensureStationEditor();
    this._render();
  }

  _switchDashboardSectionDirect(section) {
    this._dashboardSettingsSection = section || "general";
    this._status = "";
    this._error = "";
    this._render();
  }

  _setDateFilter(kind, filter) {
    if (kind === "manual") {
      this._manualTrackingFilter = filter;
      if (filter !== "month") this._manualTrackingDatePanelOpen = false;
    } else if (kind === "trip") {
      this._tripFilter = filter;
      if (filter !== "month") this._tripDatePanelOpen = false;
    } else {
      this._chargeFilter = filter;
      if (filter !== "month") this._chargeDatePanelOpen = false;
    }
    this._status = "";
    this._error = "";
    this._render();
  }

  _toggleMonthPanel(kind) {
    if (kind === "manual") {
      this._manualTrackingFilter = "month";
      this._manualTrackingDatePanelOpen = !this._manualTrackingDatePanelOpen;
    } else if (kind === "trip") {
      this._tripFilter = "month";
      this._tripDatePanelOpen = !this._tripDatePanelOpen;
    } else {
      this._chargeFilter = "month";
      this._chargeDatePanelOpen = !this._chargeDatePanelOpen;
    }
    this._status = "";
    this._error = "";
    this._render();
  }

  _setSelectedMonth(kind, value) {
    const month = String(value || this._currentMonthKey());
    if (kind === "manual") {
      this._manualTrackingSelectedMonth = month;
      this._manualTrackingFilter = "month";
      this._manualTrackingDatePanelOpen = false;
    } else if (kind === "trip") {
      this._tripSelectedMonth = month;
      this._tripFilter = "month";
      this._tripDatePanelOpen = false;
    } else {
      this._chargeSelectedMonth = month;
      this._chargeFilter = "month";
      this._chargeDatePanelOpen = false;
    }
    this._status = "";
    this._error = "";
    this._render();
  }

  _applyDateRange(kind) {
    const root = this.shadowRoot;
    const prefix = kind === "manual" ? "Manual" : (kind === "trip" ? "Trip" : "Charge");
    const start = root.getElementById(`filter${prefix}RangeStart`)?.value || "";
    const end = root.getElementById(`filter${prefix}RangeEnd`)?.value || "";
    if (!start || !end || start > end) {
      this._error = this._t("invalidDateRange");
      this._render();
      return;
    }
    if (kind === "manual") {
      this._manualTrackingRangeStart = start;
      this._manualTrackingRangeEnd = end;
      this._manualTrackingFilter = "range";
      this._manualTrackingDatePanelOpen = false;
    } else if (kind === "trip") {
      this._tripRangeStart = start;
      this._tripRangeEnd = end;
      this._tripFilter = "range";
      this._tripDatePanelOpen = false;
    } else {
      this._chargeRangeStart = start;
      this._chargeRangeEnd = end;
      this._chargeFilter = "range";
      this._chargeDatePanelOpen = false;
    }
    this._status = "";
    this._error = "";
    this._render();
  }

  _handleDelegatedKeydown(ev) {
    if (ev.key !== "Enter" && ev.key !== " ") return;
    const panelTarget = this._findActionTarget(ev, "[data-panel-action]");
    if (panelTarget) return this._handlePanelAction(panelTarget.dataset.panelAction, ev);
    const pickerTarget = this._findActionTarget(ev, "[data-entity-picker-target]");
    if (pickerTarget) { ev.preventDefault(); this._openEntityPicker(pickerTarget.dataset.entityPickerTarget || ""); }
  }


  async _sendTestChargeReport(action) {
    if (!this._hass) return;
    const charging = this._readSettingsForm();
    this._loading = true;
    this._error = "";
    this._status = action === "completion_report"
      ? this._t("sendTestChargeCompletionReport")
      : this._t("sendTestChargeCostReport");
    this._render();
    try {
      this._settingsData = this._applySettingsSaveResponse(await this._hass.callApi("POST", "pom_tesla_report/settings", { charging }), { charging });
      await this._hass.callApi("POST", "pom_tesla_report/charge_test", { action });
      this._status = action === "completion_report"
        ? `${this._t("testChargeCompletionSent")} ${this._t("testChargeNoLedger")}`
        : `${this._t("testChargeCostSent")} ${this._t("testChargeNoLedger")}`;
    } catch (err) {
      this._error = this._formatError(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }


  async _deleteCharge() {
    if (!this._hass || !this._selectedChargeId) {
      this._error = this._t("noSelection");
      this._render();
      return;
    }
    if (!confirm(this._t("confirmChargeDelete"))) return;
    this._loading = true;
    this._error = "";
    this._render();
    try {
      this._chargeData = await this._hass.callApi("POST", "pom_tesla_report/charge_records", {
        action: "delete",
        id: this._selectedChargeId,
      });
      this._selectedChargeId = "";
      this._editingCharge = null;
      this._status = this._t("deleted");
    } catch (err) {
      this._error = this._formatError(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _deleteTrip() {
    if (!this._hass || !this._selectedTripId) {
      this._error = this._t("noSelection");
      this._render();
      return;
    }
    if (!confirm(this._t("confirmTripDelete"))) return;
    this._loading = true;
    this._error = "";
    this._render();
    try {
      this._tripData = await this._hass.callApi("POST", "pom_tesla_report/trip_records", {
        action: "delete",
        id: this._selectedTripId,
      });
      this._selectedTripId = "";
      this._editingTrip = null;
      this._status = this._t("deleted");
    } catch (err) {
      this._error = this._formatError(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  _esc(v) {
    return String(v ?? "").replace(/[&<>'"]/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]));
  }

  _styles() {
    return `
      :host { display:block; min-height:100vh; color:#e5edf6; background:radial-gradient(circle at top left, #11223a 0, #090d13 42%, #05070b 100%); font-family: var(--ha-font-family-body, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif); }
      .wrap { padding:24px; max-width:1560px; margin:0 auto; }
      .top { display:flex; justify-content:space-between; gap:16px; align-items:flex-start; margin-bottom:18px; }
      h1 { margin:0; font-size:28px; letter-spacing:-0.02em; }
      .sub { color:#a8b3c2; margin-top:6px; font-size:14px; }
      .pill { padding:10px 14px; border:1px solid #273244; background:#111822; color:#cbd5e1; border-radius:999px; font-weight:700; }
      .tabs { display:flex; gap:10px; flex-wrap:wrap; margin:0 0 18px; }
      .tab { background:#111827; color:#94a3b8; border:1px solid #273244; border-radius:16px; padding:12px 16px; box-shadow:none; }
      .tab.active { background:#0ea5e9; color:white; border-color:#38bdf8; box-shadow:0 12px 30px rgba(14,165,233,.20); }
      .settings-shell { background:linear-gradient(180deg, rgba(11,15,23,.94), rgba(8,10,16,.98)); border:1px solid #1e293b; border-radius:24px; overflow:hidden; box-shadow:0 22px 70px rgba(0,0,0,.38); }
      .settings-head { display:flex; justify-content:space-between; align-items:center; gap:12px; padding:16px 20px; border-bottom:1px solid #1e293b; background:rgba(2,6,23,.50); }
      .settings-title { display:flex; align-items:center; gap:12px; font-weight:900; font-size:18px; }
      .settings-close { width:46px; height:46px; border-radius:12px; display:grid; place-items:center; background:#0f172a; border:1px solid #253143; color:#818cf8; font-size:24px; box-shadow:none; }
      .online { border:1px solid rgba(20,184,166,.35); background:rgba(13,148,136,.12); color:#5eead4; border-radius:7px; padding:8px 14px; letter-spacing:.35em; font-size:11px; font-weight:900; }
      .settings-nav { display:grid; grid-template-columns:repeat(8, minmax(0,1fr)); border-bottom:1px solid #1e293b; background:rgba(15,23,42,.35); }
      .settings-nav button { background:transparent; color:#667085; border:0; border-radius:0; box-shadow:none; padding:14px 5px; letter-spacing:.14em; font-weight:900; font-size:12px; border-bottom:3px solid transparent; white-space:nowrap; }
      .settings-nav button.active { color:#a78bfa; border-bottom-color:#7c3aed; }
      .settings-content { padding:22px; }
      .grid { display:grid; grid-template-columns:minmax(560px, 1.15fr) minmax(420px, 0.85fr); gap:18px; align-items:start; }
      .settings-grid { display:grid; grid-template-columns:minmax(520px, .95fr) minmax(560px, 1.05fr); gap:18px; align-items:start; }
      .settings-grid.wide { grid-template-columns:minmax(420px, .72fr) minmax(620px, 1.28fr); }
      .module-list { display:grid; gap:12px; }
      .module-card { width:100%; text-align:left; cursor:pointer; appearance:none; -webkit-appearance:none; padding:16px; border:1px solid #273244; border-radius:18px; background:#0f172a; color:inherit; font:inherit; outline:none; }
      .module-card b { display:block; margin-bottom:6px; }
      .module-card:hover, .module-card:focus-visible { border-color:#7dd3fc; } .module-card.active { border-color:#38bdf8; background:linear-gradient(135deg, rgba(14,165,233,.18), rgba(15,23,42,.92)); }
      .test-card { position:relative; z-index:2; margin-top:14px; padding:18px; border-radius:20px; border:1px solid rgba(168,85,247,.38); background:linear-gradient(135deg, rgba(124,58,237,.20), rgba(14,165,233,.10)); box-shadow:0 18px 48px rgba(124,58,237,.10); pointer-events:auto; }
      .test-card h3 { margin:0 0 7px; font-size:17px; }
      .test-card p { margin:0 0 14px; color:#b6c3d5; line-height:1.45; font-size:13px; }
      .test-card button { width:100%; background:linear-gradient(135deg, #7c3aed, #0ea5e9); box-shadow:0 14px 34px rgba(124,58,237,.25); pointer-events:auto; position:relative; z-index:3; }
      .test-card .actions.compact button { flex:1 1 240px; min-height:44px; }
      .charge-test-actions { display:grid; grid-template-columns:repeat(2,minmax(220px,1fr)); gap:16px; margin-top:12px; position:relative; z-index:20; pointer-events:auto; }
      .test-action-card { min-height:62px; display:flex; align-items:center; justify-content:center; text-align:center; padding:14px 18px; border-radius:18px; font-weight:900; color:#fff; cursor:pointer; user-select:none; position:relative; z-index:30; pointer-events:auto; border:1px solid rgba(255,255,255,.08); box-shadow:0 14px 34px rgba(14,165,233,.16); }
      .test-action-card.primary { background:linear-gradient(135deg, #7c3aed, #0ea5e9); }
      .test-action-card.secondary { background:#1f2937; color:#dbeafe; border-color:#334155; box-shadow:none; }
      .test-action-card:hover { filter:brightness(1.12); transform:translateY(-1px); }
      .test-action-card:active { transform:translateY(1px) scale(.995); }
      .test-action-card:focus-visible { outline:2px solid #38bdf8; outline-offset:3px; }
      @media (max-width: 760px) { .charge-test-actions { grid-template-columns:1fr; } }
      .card { background:linear-gradient(180deg, rgba(21,26,34,.96), rgba(13,17,23,.96)); border:1px solid #263143; border-radius:22px; box-shadow:0 18px 50px rgba(0,0,0,.35); overflow:hidden; }
      .card.accent { border-color:rgba(56,189,248,.35); box-shadow:0 20px 60px rgba(14,165,233,.10); }
      .card-h { padding:18px 20px; border-bottom:1px solid #263143; display:flex; justify-content:space-between; gap:12px; align-items:center; }
      .card-h h2 { margin:0; font-size:18px; }
      .card-h .hint { color:#94a3b8; font-size:13px; margin-top:5px; line-height:1.35; }
      .body { padding:18px 20px; }
      button { background:#0ea5e9; color:white; border:0; border-radius:14px; padding:11px 14px; font-weight:800; cursor:pointer; box-shadow:0 10px 30px rgba(14,165,233,.18); }
      button.secondary { background:#1f2937; color:#dbeafe; box-shadow:none; border:1px solid #334155; }
      .file-btn { display:inline-flex; align-items:center; justify-content:center; padding:12px 16px; border-radius:14px; background:#1f2937; color:#dbeafe; border:1px solid #334155; cursor:pointer; font-weight:900; text-decoration:none; min-height:42px; }
      .file-btn:hover { border-color:#38bdf8; color:#fff; background:#243244; }
      .debug-panel { margin-top:14px; border:1px solid rgba(56,189,248,.20); background:rgba(2,6,23,.55); border-radius:16px; padding:12px; }
      .debug-panel pre { white-space:pre-wrap; word-break:break-word; margin:8px 0 0; color:#cbd5e1; font-size:11px; line-height:1.45; }
      .debug-toolbar { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; margin:16px 0 8px; }
      .debug-toolbar b { display:block; font-size:14px; }
      .debug-toolbar .note { margin-top:4px; }
      .debug-toolbar .actions { margin-top:0; justify-content:flex-end; }
      .debug-output-panel { margin-top:8px; }
      .debug-output-panel pre { max-height:560px; overflow:auto; }
      .audit-pre { white-space:pre-wrap; word-break:break-word; margin:10px 0 0; color:#cbd5e1; font-size:11px; line-height:1.45; background:rgba(2,6,23,.55); border:1px solid rgba(56,189,248,.20); border-radius:16px; padding:12px; max-height:420px; overflow:auto; }
      @media (max-width: 760px) { .debug-toolbar { flex-direction:column; } .debug-toolbar .actions { justify-content:flex-start; } }
      button.danger { background:#ef4444; }
      button:disabled { opacity:.55; cursor:not-allowed; }
      .toolbar { display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
      .seg { display:inline-flex; background:#0f172a; border:1px solid #273244; border-radius:14px; padding:4px; }
      .seg button { background:transparent; color:#94a3b8; box-shadow:none; padding:8px 10px; }
      .seg button.active { background:#1e293b; color:white; }
      table { width:100%; border-collapse:separate; border-spacing:0 8px; }
      th { color:#91a0b8; text-align:left; font-size:12px; font-weight:800; padding:0 12px; }
      td { background:#101720; border-top:1px solid #253143; border-bottom:1px solid #253143; padding:13px 12px; font-size:14px; vertical-align:top; }
      tr td:first-child { border-left:1px solid #253143; border-radius:14px 0 0 14px; }
      tr td:last-child { border-right:1px solid #253143; border-radius:0 14px 14px 0; }
      tr.selected td { background:#082f49; border-color:#0ea5e9; }
      tr.record, tr.station { cursor:pointer; }
      .muted { color:#94a3b8; }
      .addr { max-width:360px; line-height:1.25; }
      .summary { display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:12px; margin-bottom:14px; }
      .stat { background:#0f172a; border:1px solid #273244; border-radius:16px; padding:14px; min-width:0; }
      .stat b { display:block; font-size:22px; margin-top:6px; overflow-wrap:anywhere; }
      .settings-hero { background:linear-gradient(135deg, rgba(14,165,233,.16), rgba(16,185,129,.08)); border:1px solid rgba(56,189,248,.25); border-radius:18px; padding:16px; margin-bottom:16px; }
      .settings-hero b { display:block; font-size:16px; margin-bottom:5px; }
      label { display:block; color:#9ca3af; font-size:13px; font-weight:800; margin:14px 0 7px; }
      input, textarea, select { width:100%; box-sizing:border-box; background:#0f172a; border:1px solid #334155; color:#f8fafc; border-radius:14px; padding:13px 14px; font-size:15px; outline:none; font-family:inherit; }
      select { appearance:auto; }
      textarea { min-height:82px; resize:vertical; }
      input:focus, textarea:focus, select:focus { border-color:#38bdf8; box-shadow:0 0 0 3px rgba(56,189,248,.12); }
      .two { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
      .three { display:grid; grid-template-columns:repeat(3, 1fr); gap:12px; }
      .actions { display:flex; gap:10px; flex-wrap:wrap; margin-top:18px; }
      .status { padding:12px 14px; border-radius:14px; margin-bottom:12px; background:#082f49; color:#bae6fd; border:1px solid #0ea5e9; }
      .error { padding:12px 14px; border-radius:14px; margin-bottom:12px; background:#450a0a; color:#fecaca; border:1px solid #ef4444; }
      .note { color:#94a3b8; font-size:13px; margin-top:14px; line-height:1.45; }
      .empty { padding:24px; color:#94a3b8; text-align:center; }
      .station-list { display:flex; flex-direction:column; gap:10px; }
      .station-row { display:grid; grid-template-columns:42px minmax(0,1fr) auto; gap:14px; align-items:center; padding:14px; background:#101720; border:1px solid #253143; border-radius:16px; cursor:pointer; }
      .station-row.report-active { border-color:rgba(34,211,238,.24); background:linear-gradient(135deg, rgba(8,47,73,.52), rgba(15,23,42,.82)); }
      .station-row.selected { background:#082f49; border-color:#0ea5e9; }
      .station-row b { display:block; }
      .station-main-info { min-width:0; }
      .station-order-badge { width:34px; height:34px; border-radius:999px; display:flex; align-items:center; justify-content:center; font-weight:900; border:1px solid rgba(148,163,184,.25); background:rgba(15,23,42,.86); color:#cbd5e1; }
      .station-order-badge.report { border-color:rgba(45,212,191,.38); color:#99f6e4; background:rgba(20,184,166,.13); }
      .station-order-badge.pool { border-color:rgba(56,189,248,.28); color:#bae6fd; }
      .station-row-actions { display:flex; align-items:center; justify-content:flex-end; gap:10px; flex-wrap:wrap; }
      .station-slot-control { display:flex; align-items:center; gap:8px; padding:6px 8px; border:1px solid rgba(56,189,248,.16); border-radius:14px; background:rgba(2,6,23,.34); }
      .station-slot-control span { color:#94a3b8; font-size:11px; font-weight:800; white-space:nowrap; }
      .station-slot-buttons { display:flex; gap:5px; }
      .mini-slot-btn { width:34px; min-width:34px; height:32px; padding:0; border-radius:10px; font-size:12px; font-weight:900; background:rgba(15,23,42,.88); border:1px solid rgba(56,189,248,.38); color:#bae6fd; display:inline-flex; align-items:center; justify-content:center; opacity:1; visibility:visible; }
      .mini-slot-btn:hover { border-color:#38bdf8; color:#fff; background:rgba(14,165,233,.22); }
      .mini-slot-btn.current { color:#99f6e4; border-color:rgba(45,212,191,.55); background:rgba(20,184,166,.16); }
      .report-slot-inline { margin-top:4px; color:#99f6e4; font-size:11px; font-weight:800; }
      .report-cost-slots { margin-bottom:16px; }
      .station-pool-block { margin-top:14px; }
      .small-title { margin-top:12px; }
      .price-badge { background:#0f172a; border:1px solid #334155; color:#dbeafe; padding:8px 10px; border-radius:999px; font-weight:800; white-space:nowrap; }
      @media (max-width: 760px) { .station-row { grid-template-columns:34px minmax(0,1fr); } .station-row-actions { grid-column:1 / -1; justify-content:flex-start; } .station-slot-control { width:100%; justify-content:space-between; } }
      .section-title { margin:22px 0 8px; font-size:14px; color:#cbd5e1; font-weight:900; text-transform:uppercase; letter-spacing:.04em; }
      .toggle-row { display:flex; align-items:center; justify-content:space-between; gap:14px; padding:13px 0; border-bottom:1px solid rgba(148,163,184,.10); }
      .toggle-row:last-child { border-bottom:0; }
      .toggle-row span { font-weight:800; color:#dbeafe; }
      .switch { position:relative; width:54px; height:30px; flex:0 0 auto; }
      .switch input { opacity:0; width:0; height:0; }
      .slider { position:absolute; cursor:pointer; inset:0; background:#1f2937; border:1px solid #334155; border-radius:999px; transition:.18s; }
      .slider:before { content:""; position:absolute; height:24px; width:24px; left:2px; top:2px; background:#94a3b8; border-radius:50%; transition:.18s; }
      .switch input:checked + .slider { background:#075985; border-color:#0ea5e9; }
      .switch input:checked + .slider:before { transform:translateX(24px); background:#38bdf8; }
      .field-grid { display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:12px; }
      .visual-grid { display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:8px 18px; }
      .coming { text-align:center; padding:54px 20px; color:#94a3b8; border:1px dashed #334155; border-radius:20px; background:#0f172a; }

      .ai-manager-grid { grid-template-columns:minmax(360px,.55fr) minmax(740px,1.45fr); }
      .summary-grid.mini { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin:16px 0; }
      .summary-grid.mini div { background:#0f172a; border:1px solid #273244; border-radius:16px; padding:12px; }
      .summary-grid.mini span { display:block; color:#94a3b8; font-size:12px; margin-bottom:6px; }
      .summary-grid.mini b { font-size:22px; }
      .actions.vertical { flex-direction:column; }
      .actions.vertical button, .primary-wide { width:100%; }
      .ai-role-list { display:flex; flex-direction:column; gap:12px; }
      .ai-role-row { display:grid; grid-template-columns:minmax(260px,.45fr) minmax(420px,.55fr); gap:14px; padding:15px; background:#101720; border:1px solid #253143; border-radius:18px; }
      .ai-role-row:hover { border-color:#38bdf8; background:#0b1f2e; }
      .ai-role-title { font-weight:900; color:#f8fafc; margin-bottom:6px; }
      .ai-role-desc { color:#94a3b8; font-size:13px; line-height:1.45; }
      .ai-role-input input { margin-bottom:10px; }
      .role-actions { display:flex; gap:10px; margin-top:8px; }
      .entities-subnav { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin-bottom:16px; background:#0f172a; border:1px solid #273244; border-radius:16px; padding:5px; }
      .entities-subnav button { background:transparent; color:#94a3b8; box-shadow:none; border:0; letter-spacing:.18em; font-size:12px; }
      .entities-subnav button.active { background:linear-gradient(135deg, rgba(124,58,237,.42), rgba(14,165,233,.18)); color:#fff; }
      .entity-picker-field { display:grid; grid-template-columns:1fr auto; gap:8px; align-items:center; padding:8px; background:#0f172a; border:1px solid #334155; border-radius:16px; cursor:pointer; }
      .entity-picker-field:hover { border-color:#38bdf8; }
      .entity-picker-field input { margin:0; border:0; background:transparent; padding:6px 4px; pointer-events:none; }
      .entity-picker-field span { grid-column:1 / -1; color:#94a3b8; font-size:12px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; padding:0 4px 2px; }
      .custom-ai-block { margin-top:16px; border-top:1px solid rgba(148,163,184,.14); padding-top:8px; }
      .entity-picker-overlay { position:fixed; inset:0; z-index:9999; background:rgba(2,6,23,.72); backdrop-filter:blur(8px); display:flex; align-items:center; justify-content:center; padding:24px; }
      .entity-picker-modal { width:min(860px, calc(100vw - 40px)); max-height:min(760px, calc(100vh - 48px)); background:#0b111b; border:1px solid #334155; border-radius:24px; box-shadow:0 28px 90px rgba(0,0,0,.55); padding:18px; display:flex; flex-direction:column; }
      .entity-picker-head { display:flex; justify-content:space-between; gap:14px; align-items:flex-start; margin-bottom:12px; }
      .entity-picker-head h3 { margin:0; font-size:20px; }
      .entity-picker-head p { margin:6px 0 0; color:#94a3b8; }
      .entity-picker-list { overflow:auto; margin-top:12px; display:flex; flex-direction:column; gap:8px; padding-right:4px; }
      .entity-option { padding:12px 14px; border:1px solid #253143; background:#101720; border-radius:14px; cursor:pointer; }
      .entity-option:hover { background:#082f49; border-color:#0ea5e9; }
      .entity-option b { display:block; color:#f8fafc; margin-bottom:4px; }
      .entity-option span { display:block; color:#94a3b8; font-size:12px; }

      .entity-picker-field { display:grid; grid-template-columns:minmax(0,1fr) auto; align-items:center; gap:10px; width:100%; text-align:left; padding:9px 12px; background:#0f172a; border:1px solid #334155; border-radius:14px; cursor:pointer; box-shadow:none; }
      .entity-picker-field:hover { border-color:#38bdf8; background:#122033; }
      .entity-picker-field.empty, .entity-picker-field.invalid { background:linear-gradient(180deg, rgba(56, 8, 8, .92), rgba(36, 7, 7, .88)); border-color:rgba(248, 113, 113, .42); }
      .entity-picker-field.empty:hover, .entity-picker-field.invalid:hover { border-color:rgba(252, 165, 165, .78); background:linear-gradient(180deg, rgba(72, 10, 10, .94), rgba(46, 8, 8, .9)); }
      .entity-picker-field.empty .entity-friendly, .entity-picker-field.invalid .entity-friendly { color:#fee2e2; }
      .entity-picker-field.empty .entity-meta-line, .entity-picker-field.invalid .entity-meta-line, .entity-picker-field.empty .entity-picker-arrow, .entity-picker-field.invalid .entity-picker-arrow { color:#fca5a5; }
      .entity-picker-main { min-width:0; display:flex; flex-direction:column; align-items:flex-start; gap:2px; }
      .entity-friendly { color:#f8fafc; font-size:14px; font-weight:800; max-width:100%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .entity-meta-line { color:#94a3b8; font-size:11px; max-width:100%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .entity-picker-arrow { color:#94a3b8; font-size:15px; }
      .entity-picker-overlay { position:fixed; inset:0; z-index:999999; background:rgba(2,6,23,.72); backdrop-filter:blur(8px); display:flex; align-items:center; justify-content:center; padding:24px; }
      .entity-picker-modal { width:min(920px, calc(100vw - 40px)); max-height:min(780px, calc(100vh - 48px)); background:#0b111b; border:1px solid #334155; border-radius:24px; box-shadow:0 28px 90px rgba(0,0,0,.55); padding:18px; display:flex; flex-direction:column; text-align:left; }
      .entity-picker-head { display:flex; justify-content:space-between; gap:14px; align-items:flex-start; margin-bottom:12px; }
      .entity-picker-head h3 { margin:0; font-size:20px; }
      .entity-picker-head p { margin:6px 0 0; color:#94a3b8; }
      .entity-picker-close { width:44px; height:44px; border-radius:14px; padding:0; display:grid; place-items:center; font-size:24px; }
      .entity-picker-search { flex:0 0 auto; }
      .entity-picker-list { overflow:auto; margin-top:12px; display:flex; flex-direction:column; gap:7px; padding-right:4px; }
      .entity-option { width:100%; display:grid; grid-template-columns:38px minmax(0,1fr) auto; gap:12px; align-items:center; padding:10px 12px; border:1px solid #253143; background:#101720; border-radius:14px; cursor:pointer; text-align:left; box-shadow:none; }
      .entity-option:hover { background:#082f49; border-color:#0ea5e9; }
      .entity-option-icon { width:32px; height:32px; border-radius:10px; display:grid; place-items:center; background:#1e293b; color:#bae6fd; font-weight:900; }
      .entity-option-main { min-width:0; display:flex; flex-direction:column; gap:3px; }
      .entity-option-main b { display:block; color:#f8fafc; font-size:14px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .entity-option-main small { display:block; color:#94a3b8; font-size:12px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .entity-option-domain { color:#94a3b8; font-size:11px; background:#0f172a; border:1px solid #273244; border-radius:999px; padding:5px 8px; }
      .danger-soft { border-color:rgba(239,68,68,.45) !important; color:#fecaca !important; background:#2a1117 !important; }

      .role-flags { display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
      .role-flags label { margin:0; display:inline-flex; align-items:center; gap:6px; font-size:12px; color:#cbd5e1; background:#0f172a; border:1px solid #273244; border-radius:999px; padding:7px 10px; }
      .role-flags input[type="checkbox"] { width:auto; margin:0; }
      button.tiny { padding:7px 10px; font-size:12px; border-radius:999px; background:#1f2937; color:#dbeafe; box-shadow:none; border:1px solid #334155; }

      .compact-ai-manager { grid-template-columns:minmax(360px,.44fr) minmax(620px,.56fr); }
      .compact-ai-card .body.ai-role-list.compact { gap:8px; }
      .ai-role-row.compact { display:grid; grid-template-columns:minmax(210px,.42fr) minmax(360px,.58fr); gap:10px; padding:9px 10px; border-radius:13px; min-height:0; align-items:center; }
      .ai-role-row.compact .ai-role-title { margin-bottom:2px; font-size:14px; }
      .ai-role-row.compact .ai-role-desc { font-size:12px; line-height:1.25; max-height:34px; overflow:hidden; }
      .ai-role-input.compact { display:grid; grid-template-columns:minmax(300px,1fr) auto; gap:8px; align-items:center; }
      .ai-role-input.compact .tiny { white-space:nowrap; min-width:82px; padding:10px 13px; }
      .entity-select-wrap { min-width:0; }

      .entity-picker-debug { position:sticky; top:0; z-index:2; background:#0b111b; color:#7dd3fc; border:1px solid #164e63; border-radius:12px; padding:8px 12px; margin:0 0 8px; font-size:12px; font-weight:700; letter-spacing:.02em; }
      .entity-empty { padding:18px; text-align:center; border:1px dashed #334155; border-radius:14px; }
      .entity-select-wrap ha-entity-picker { width:100%; --mdc-theme-surface:#0f172a; --mdc-theme-on-surface:#f8fafc; --mdc-theme-primary:#38bdf8; --mdc-text-field-fill-color:#0f172a; --mdc-text-field-ink-color:#f8fafc; --mdc-text-field-label-ink-color:#94a3b8; }
      .ai-role-list.compact { display:flex; flex-direction:column; gap:16px; }
      .ai-role-grid.compact-grid { display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:12px; }
      .ai-role-tile { position:relative; min-height:138px; border:1px solid rgba(56,189,248,.18); border-radius:20px; background:linear-gradient(180deg, rgba(5,12,24,.92), rgba(7,18,34,.86)); padding:16px 18px 14px; display:flex; flex-direction:column; gap:12px; text-align:left; cursor:pointer; transition:border-color .18s ease, transform .18s ease, box-shadow .18s ease; overflow:hidden; }
      .ai-role-tile:hover { border-color:#38bdf8; box-shadow:0 10px 26px rgba(2,132,199,.14); transform:translateY(-1px); }
      .ai-role-tile.empty, .ai-role-tile.invalid { border-color:rgba(248, 113, 113, .32); background:linear-gradient(180deg, rgba(40, 8, 12, .94), rgba(28, 6, 10, .90)); }
      .ai-role-tile.empty:hover, .ai-role-tile.invalid:hover { border-color:rgba(252, 165, 165, .70); box-shadow:0 12px 28px rgba(127, 29, 29, .20); }
      .ai-role-tile.empty .ai-role-friendly, .ai-role-tile.invalid .ai-role-friendly { color:#fee2e2; }
      .ai-role-tile.empty .ai-role-meta-line, .ai-role-tile.invalid 

.autofind-banner {
  display: grid;
  grid-template-columns: 42px 1fr 42px;
  gap: 14px;
  align-items: center;
  margin: 14px 0 16px;
  padding: 16px;
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(245,158,11,0.16), rgba(14,165,233,0.12));
  border: 1px solid rgba(245,158,11,0.36);
  box-shadow: 0 14px 42px rgba(0,0,0,0.22);
}
.autofind-banner-spinner {
  width: 34px;
  height: 34px;
  border-radius: 999px;
  border: 4px solid rgba(148,163,184,0.26);
  border-top-color: #38bdf8;
  animation: pomSpin 0.9s linear infinite;
}
@keyframes pomSpin { to { transform: rotate(360deg); } }
.autofind-banner-main b {
  display: block;
  color: #fff7ed;
  font-size: 15px;
  font-weight: 950;
}
.autofind-banner-main div {
  margin-top: 4px;
  color: #fef3c7;
  font-weight: 900;
}
.autofind-banner-main small {
  display: block;
  margin-top: 4px;
  color: #cbd5e1;
  line-height: 1.35;
}
.autofind-banner-close {
  width: 38px;
  height: 38px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.14);
  color: white;
  font-size: 24px;
  line-height: 1;
  padding: 0;
  box-shadow: none;
}

.confidence-badge {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  margin-top: 7px;
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  border: 1px solid rgba(255,255,255,0.14);
  background: rgba(255,255,255,0.07);
  color: rgba(255,255,255,0.82);
}
.confidence-badge.very-high {
  color: #d1fae5;
  background: rgba(16,185,129,0.18);
  border-color: rgba(16,185,129,0.45);
}
.confidence-badge.high {
  color: #dbeafe;
  background: rgba(59,130,246,0.18);
  border-color: rgba(59,130,246,0.42);
}
.confidence-badge.medium {
  color: #fef3c7;
  background: rgba(245,158,11,0.16);
  border-color: rgba(245,158,11,0.42);
}
.confidence-badge.low {
  color: #fee2e2;
  background: rgba(239,68,68,0.16);
  border-color: rgba(239,68,68,0.42);
}
.confidence-badge.manual {
  color: #e9d5ff;
  background: rgba(168,85,247,0.14);
  border-color: rgba(168,85,247,0.36);
}

.ai-role-meta-line { color:#fca5a5; }
      .ai-role-tile.empty .ai-role-chip, .ai-role-tile.invalid .ai-role-chip { border-color:rgba(248, 113, 113, .26); background:rgba(69, 10, 10, .34); }
      .ai-role-tile.empty .ai-role-desc, .ai-role-tile.invalid .ai-role-desc, .ai-role-tile.empty .ai-role-expected, .ai-role-tile.invalid .ai-role-expected { color:#fda4af; }
      .ai-role-tile-head { min-width:0; padding-right:34px; }
      .ai-role-title { font-size:15px; font-weight:800; line-height:1.2; margin:0 0 6px; }
      .ai-role-desc { color:#94a3b8; font-size:12px; line-height:1.45; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
      .ai-role-chip { margin-top:auto; min-width:0; border:1px solid rgba(71,85,105,.55); border-radius:14px; background:#0f172a; padding:10px 12px; }
      .ai-role-friendly { font-size:15px; font-weight:800; line-height:1.25; color:#f8fafc; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
      .ai-role-meta-line { margin-top:4px; color:#94a3b8; font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
      .ai-role-close { position:absolute; top:12px; right:12px; width:28px; height:28px; min-width:28px; padding:0; border-radius:999px; border:1px solid rgba(71,85,105,.6); background:#1e293b; color:#f8fafc; font-size:18px; line-height:1; display:grid; place-items:center; cursor:pointer; }
      .ai-role-close:hover { border-color:#f87171; color:#fff; background:#3f1d24; }
      .custom-ai-block.compact { border-top:1px solid rgba(71,85,105,.35); padding-top:8px; }
      .custom-ai-block.compact .section-title { margin-bottom:4px; }
      .custom-ai-block.compact .note { margin-bottom:10px; }
      .ai-manager-stacked { grid-template-columns:1fr !important; }
      .ai-summary-card .body { padding-bottom:18px; }
      .settings-hero.compact { margin-bottom:12px; padding:13px 15px; }
      .ai-summary-layout { display:grid; grid-template-columns:minmax(420px, 1.05fr) minmax(420px, .95fr); gap:18px; align-items:start; }
      .ai-summary-main, .ai-summary-side { min-width:0; }
      .ai-summary-side { background:rgba(15,23,42,.72); border:1px solid rgba(39,50,68,.95); border-radius:18px; padding:14px; }
      .ai-summary-side .toggle-row { padding-top:0; }
      .summary-grid.mini.ai-summary-stats { margin:12px 0 0; }
      .ai-summary-actions { margin-top:14px; display:grid; grid-template-columns:1fr 1fr; }
      .ai-summary-actions button, .ai-summary-actions .primary-wide { width:100%; }
      .ai-category-list { display:flex; flex-direction:column; gap:18px; }
      .ai-category-block { border:1px solid rgba(51,65,85,.72); background:rgba(15,23,42,.42); border-radius:22px; padding:14px; }
      .ai-category-head { display:flex; align-items:center; justify-content:space-between; gap:12px; margin:0 0 12px; }
      .ai-category-head h3 { margin:0; font-size:16px; letter-spacing:.08em; text-transform:uppercase; color:#e0f2fe; }
      .ai-category-head span { color:#94a3b8; font-size:12px; border:1px solid #273244; background:#0f172a; padding:5px 9px; border-radius:999px; }
      .ai-role-expected { margin-top:6px; color:#7dd3fc; font-size:10px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
      .entity-picker-expected { margin-top:6px !important; color:#7dd3fc !important; font-size:12px; font-weight:800; }
      .ai-four-grid { grid-template-columns:repeat(4, minmax(0, 1fr)) !important; gap:12px; }
      .ai-four-grid .ai-role-tile { min-height:132px; padding:14px 15px 12px; border-radius:18px; }
      .ai-four-grid .ai-role-title { font-size:14px; }
      .ai-four-grid .ai-role-desc { font-size:12px; line-height:1.32; -webkit-line-clamp:2; }
      .ai-four-grid .ai-role-chip { padding:9px 10px; border-radius:13px; }
      .ai-four-grid .ai-role-friendly { font-size:14px; }
      .ai-four-grid .ai-role-close { top:10px; right:10px; width:26px; height:26px; min-width:26px; font-size:17px; }
      .dashboard-custom-icon-row { margin-top:4px; display:flex; flex-direction:column; gap:6px; }
      .dashboard-custom-icon-row label { font-size:11px; color:#cbd5e1; margin:0; }
      .dashboard-custom-icon-row input { min-height:34px; padding:8px 10px; border-radius:12px; font-size:12px; }
      .dashboard-custom-icon-row .note.tiny { font-size:10px; line-height:1.25; margin:0; }
      .automation-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; }
      .automation-card { border:1px solid rgba(56,189,248,.16); border-radius:18px; background:rgba(15,23,42,.55); padding:14px; display:flex; flex-direction:column; gap:12px; }
      .dashboard-upload-grid { display:grid; grid-template-columns:minmax(0,1fr); gap:14px; margin-top:14px; }
      .dashboard-upload-card { border:1px solid rgba(56,189,248,.16); border-radius:18px; background:rgba(15,23,42,.55); padding:16px; display:grid; grid-template-columns:minmax(220px,300px) minmax(260px,1fr) minmax(180px,240px); gap:18px; align-items:start; overflow:hidden; }
      .dashboard-upload-card.youtube-bg-card { grid-template-columns:minmax(0,1fr); }
      .dashboard-upload-media { display:flex; flex-direction:column; gap:10px; min-width:0; }
      .dashboard-upload-main { display:flex; flex-direction:column; gap:12px; min-width:0; }
      .dashboard-upload-side { display:flex; flex-direction:column; gap:10px; min-width:0; }
      .dashboard-upload-title { font-weight:800; font-size:15px; color:#f8fafc; }
      .dashboard-preview { width:100%; aspect-ratio:16/9; object-fit:cover; border-radius:14px; border:1px solid rgba(51,65,85,.8); background:#020617; }
      .dashboard-preview.empty { display:grid; place-items:center; color:#64748b; }
      .dashboard-current-url { font-size:11px; line-height:1.35; color:#93c5fd; word-break:break-all; overflow-wrap:anywhere; background:#0f172a; border:1px solid #273244; border-radius:12px; padding:10px; min-height:34px; max-height:76px; overflow:auto; }
      .dashboard-upload-actions { display:flex; flex-direction:column; gap:8px; align-items:stretch; }
      .dashboard-upload-actions input[type=file] { display:none; }
      .dashboard-upload-actions button, .dashboard-upload-actions .file-btn { width:100%; box-sizing:border-box; max-width:100%; }
      .dashboard-upload-actions .file-btn { display:inline-flex; align-items:center; justify-content:center; text-decoration:none; padding:11px 14px; border-radius:12px; background:#1f2937; color:#dbeafe; border:1px solid #334155; cursor:pointer; font-weight:800; }
      .dashboard-upload-actions .file-btn:hover { border-color:#38bdf8; color:#fff; background:#243244; }
      .dashboard-toggle-row { display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:10px; }
      .youtube-settings-grid { display:grid; grid-template-columns:minmax(0,2fr) minmax(180px,1fr) minmax(160px,.8fr); gap:12px; align-items:end; }
      .youtube-settings-grid .field-wrap { min-width:0; }
      .sticky-save-row { display:flex; flex-wrap:wrap; gap:10px; margin-top:16px; position:sticky; bottom:0; padding-top:12px; background:linear-gradient(180deg, rgba(5,7,11,0), rgba(5,7,11,.92) 35%); }
      .sticky-save-row button { min-width:180px; }
      @media (max-width: 1280px) {
        .dashboard-upload-card { grid-template-columns:minmax(220px,260px) minmax(0,1fr); }
        .dashboard-upload-side { grid-column:1 / -1; }
        .dashboard-upload-actions { display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); }
      }
      @media (max-width: 900px) {
        .dashboard-upload-card { grid-template-columns:1fr; }
        .dashboard-upload-actions { grid-template-columns:1fr; }
        .dashboard-toggle-row, .youtube-settings-grid { grid-template-columns:1fr; }
      }
      .resource-summary-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin:14px 0; }
      .resource-summary-grid > div { border:1px solid rgba(56,189,248,.18); background:rgba(15,23,42,.62); border-radius:16px; padding:12px; display:flex; flex-direction:column; gap:5px; min-width:0; }
      .resource-summary-grid span { color:#94a3b8; font-size:12px; }
      .resource-summary-grid b { color:#f8fafc; font-size:20px; }
      .resource-summary-grid small { color:#7dd3fc; word-break:break-all; }
      .dashboard-resource-actions { margin:12px 0 16px; }
      .dashboard-info-grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
      .dashboard-info-panel { border:1px solid rgba(51,65,85,.72); background:rgba(15,23,42,.42); border-radius:18px; padding:14px; min-width:0; }
      .dashboard-info-panel h3 { margin:0 0 6px; font-size:15px; letter-spacing:.08em; text-transform:uppercase; }
      .dashboard-info-panel p { margin:0 0 12px; color:#94a3b8; }
      .resource-row { border:1px solid rgba(51,65,85,.72); border-radius:14px; padding:12px; background:rgba(2,6,23,.32); margin-bottom:10px; }
      .resource-row.missing { border-color:rgba(248,113,113,.38); background:rgba(69,10,10,.22); }
      .resource-title { display:flex; align-items:center; justify-content:space-between; gap:10px; }
      .resource-status { font-size:11px; font-weight:900; border-radius:999px; padding:4px 8px; border:1px solid rgba(71,85,105,.9); color:#cbd5e1; white-space:nowrap; }
      .resource-status.ok { color:#99f6e4; border-color:rgba(45,212,191,.35); background:rgba(20,184,166,.10); }
      .resource-status.missing { color:#fecaca; border-color:rgba(248,113,113,.42); background:rgba(127,29,29,.24); }
      .resource-meta { color:#94a3b8; font-size:12px; margin:5px 0; }
      .resource-url { color:#93c5fd; font-size:11px; line-height:1.35; word-break:break-all; margin-top:6px; }
      .resource-details { margin-top:8px; color:#94a3b8; font-size:11px; }
      .resource-details code { display:block; color:#cbd5e1; word-break:break-all; margin:4px 0; }

      .person-track-card { border:1px solid rgba(56,189,248,.16); border-radius:18px; background:rgba(15,23,42,.45); padding:14px; margin:14px 0; }

      .record-map-card { display:flex; flex-direction:column; gap:10px; margin-bottom:16px; }
      .record-map-title { color:#cbd5e1; font-size:12px; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }
      .record-map-canvas { min-height:220px; border:1px solid rgba(56,189,248,.18); border-radius:18px; overflow:hidden; background:rgba(2,6,23,.65); display:flex; align-items:center; justify-content:center; }
      .record-map-canvas img { display:block; width:100%; height:auto; }
      .record-map-placeholder { min-height:220px; width:100%; display:flex; align-items:center; justify-content:center; padding:18px; text-align:center; color:#94a3b8; }
      .record-map-address-label { color:#94a3b8; font-size:11px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; }
      .record-map-address { border:1px solid rgba(51,65,85,.72); background:rgba(15,23,42,.48); border-radius:14px; padding:12px 14px; color:#e2e8f0; font-size:13px; line-height:1.45; word-break:break-word; }
      .manual-detail-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; margin:0 0 14px; }
      .manual-detail-grid > div { border:1px solid rgba(51,65,85,.72); background:rgba(15,23,42,.46); border-radius:14px; padding:12px 14px; min-width:0; }
      .manual-detail-grid span { display:block; color:#94a3b8; font-size:11px; margin-bottom:4px; }
      .manual-detail-grid b { display:block; color:#f8fafc; font-size:15px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }

      .date-filter-wrap { position:relative; display:flex; flex-direction:column; gap:8px; }
      .date-filter-panel { position:absolute; right:0; top:calc(100% + 10px); z-index:40; width:min(520px, calc(100vw - 40px)); display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; padding:12px; border:1px solid rgba(56,189,248,.24); border-radius:18px; background:rgba(11,17,27,.98); box-shadow:0 22px 70px rgba(0,0,0,.45); }
      .date-filter-panel label { margin:0 0 6px; font-size:10px; color:#94a3b8; text-transform:uppercase; letter-spacing:.08em; }
      .date-filter-panel input, .date-filter-panel select { width:100%; min-height:38px; }
      .date-filter-panel button { align-self:end; min-height:38px; }
      @media (max-width: 850px) { .date-filter-panel { position:static; width:100%; grid-template-columns:1fr; } }

      .automation-card .toggle { margin:0; }
      .automation-field { display:flex; flex-direction:column; gap:6px; }
      .automation-field label { margin:0; color:#cbd5e1; font-size:12px; }
      @media (max-width: 980px) { .automation-grid { grid-template-columns:1fr; } }
      @media (max-width: 1500px) { .ai-four-grid { grid-template-columns:repeat(3, minmax(0, 1fr)) !important; } }
      @media (max-width: 1180px) { .ai-summary-layout { grid-template-columns:1fr; } .ai-four-grid { grid-template-columns:repeat(2, minmax(0, 1fr)) !important; } }
      @media (max-width: 720px) { .ai-summary-actions { grid-template-columns:1fr; } .ai-four-grid, .ai-role-grid.compact-grid { grid-template-columns:1fr !important; } }
      @media (max-width: 980px) { .ai-role-grid.compact-grid:not(.ai-four-grid) { grid-template-columns:1fr; } }

      .entity-current-line { color:#94a3b8; font-size:11px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; padding:2px 2px 0; }
      .custom-ai-block { display:flex; flex-direction:column; gap:8px; margin-top:8px; border-top:1px solid #223044; padding-top:14px; }
      .sticky-actions { position:sticky; bottom:0; background:linear-gradient(180deg, rgba(11,17,27,.50), rgba(11,17,27,.97)); padding-top:10px; z-index:3; }
      @media (max-width: 1150px) { .compact-ai-manager { grid-template-columns:1fr; } .ai-role-row.compact, .ai-role-input.compact { grid-template-columns:1fr; } }

      @media (max-width: 1150px) { .ai-role-row { grid-template-columns:1fr; } }
      @media (max-width: 1000px) { .wrap { padding:14px; } .grid, .settings-grid, .settings-grid.wide { grid-template-columns:1fr; } .summary, .three, .field-grid, .visual-grid, .dashboard-upload-grid, .dashboard-info-grid, .resource-summary-grid { grid-template-columns:1fr; } .settings-nav { grid-template-columns:repeat(2, minmax(0,1fr)); } .top { flex-direction:column; } .two { grid-template-columns:1fr; } table { font-size:13px; } th.hide-sm, td.hide-sm { display:none; } }
    `;
  }

  _renderTabs() {
    return `
      <div class="tabs">
        <button id="tabSettings" class="tab ${this._activeTab === "settings" ? "active" : ""}">${this._t("settingsTab")}</button>
        <button id="tabCharge" class="tab ${this._activeTab === "charge" ? "active" : ""}">${this._t("chargeTab")}</button>
        <button id="tabTrip" class="tab ${this._activeTab === "trip" ? "active" : ""}">${this._t("tripTab")}</button>
        <button id="tabManual" class="tab ${this._activeTab === "manual" ? "active" : ""}">${this._t("manualTrackingTab")}</button>
      </div>
    `;
  }

  _renderCurrencyOptions(selected) {
    const opts = this._settingsData?.currency_options || ["TL", "EUR", "USD", "GBP", "BGN"];
    return opts.map((c) => `<option value="${this._esc(c)}" ${c === selected ? "selected" : ""}>${this._esc(c)}</option>`).join("");
  }

  _renderChargeSummary() {
    const records = this._chargeRecords();
    const s = this._chargeSummaryFromRecords(records);
    const by = s.total_cost_by_currency || {};
    const costText = Object.keys(by).length
      ? Object.entries(by).map(([cur, val]) => `${this._fmtNumber(val, 2)} ${cur}`).join(" · ")
      : "-";
    return `
      <div class="summary">
        <div class="stat"><span class="muted">${this._t("count")} · ${this._filterLabel("charge")}</span><b>${s.count || 0}</b></div>
        <div class="stat"><span class="muted">${this._t("totalEnergy")}</span><b>${this._fmtNumber(s.total_kwh || 0, 2)} kWh</b></div>
        <div class="stat"><span class="muted">${this._t("totalCostByCurrency")}</span><b>${costText}</b></div>
      </div>
    `;
  }

  _renderTripSummary() {
    const records = this._tripRecords();
    const s = this._tripSummaryFromRecords(records);
    return `
      <div class="summary">
        <div class="stat"><span class="muted">${this._t("count")} · ${this._filterLabel("trip")}</span><b>${s.count || 0}</b></div>
        <div class="stat"><span class="muted">${this._t("totalDistance")}</span><b>${this._fmtNumber(s.total_distance_km || 0, 1)} km</b></div>
        <div class="stat"><span class="muted">${this._t("totalEnergy")}</span><b>${this._fmtNumber(s.total_energy_kwh || 0, 1)} kWh</b></div>
        <div class="stat"><span class="muted">${this._t("totalCost")}</span><b>${this._fmtNumber(s.total_cost || 0, 2)} ${this._esc(this._tripData?.currency || "")}</b></div>
        <div class="stat"><span class="muted">${this._t("totalDuration")}</span><b>${this._durationText(s.total_duration_minutes || 0)}</b></div>
        <div class="stat"><span class="muted">${this._t("avgConsumption")}</span><b>${this._fmtNumber(s.average_consumption_kwh_100km || 0, 2)} kWh/100</b></div>
      </div>
    `;
  }

  _renderDateFilterToolbar(kind) {
    const isTrip = kind === "trip";
    const isManual = kind === "manual";
    const prefix = isManual ? "Manual" : (isTrip ? "Trip" : "Charge");
    const filter = isManual ? this._manualTrackingFilter : (isTrip ? this._tripFilter : this._chargeFilter);
    const selectedMonth = isManual ? this._manualTrackingSelectedMonth : (isTrip ? this._tripSelectedMonth : this._chargeSelectedMonth);
    const rangeStart = isManual ? this._manualTrackingRangeStart : (isTrip ? this._tripRangeStart : this._chargeRangeStart);
    const rangeEnd = isManual ? this._manualTrackingRangeEnd : (isTrip ? this._tripRangeEnd : this._chargeRangeEnd);
    const panelOpen = isManual ? this._manualTrackingDatePanelOpen : (isTrip ? this._tripDatePanelOpen : this._chargeDatePanelOpen);
    const records = isManual ? (this._tripData?.records || []).filter((r) => this._isManualTrackingRecord(r)) : (isTrip ? (this._tripData?.records || []) : (this._chargeData?.records || []));
    const monthOptions = this._monthOptionsForRecords(records);
    return `
      <div class="date-filter-wrap">
        <div class="seg">
          <button id="filter${prefix}Today" class="${filter === "today" ? "active" : ""}">${this._t("todayRecords")}</button>
          <button id="filter${prefix}Month" class="${filter === "month" ? "active" : ""}">${this._filterLabel(kind)}</button>
          <button id="filter${prefix}All" class="${filter === "all" ? "active" : ""}">${this._t("allRecords")}</button>
        </div>
        ${panelOpen ? `
          <div class="date-filter-panel">
            <div>
              <label>${this._t("selectedMonth")}</label>
              <select id="filter${prefix}MonthSelect">
                ${monthOptions.map((m) => `<option value="${this._esc(m)}" ${m === selectedMonth ? "selected" : ""}>${this._esc(this._monthLabel(m))}</option>`).join("")}
              </select>
            </div>
            <div>
              <label>${this._t("startDate")}</label>
              <input id="filter${prefix}RangeStart" type="date" value="${this._esc(rangeStart || this._todayKey())}" />
            </div>
            <div>
              <label>${this._t("endDate")}</label>
              <input id="filter${prefix}RangeEnd" type="date" value="${this._esc(rangeEnd || this._todayKey())}" />
            </div>
            <button id="apply${prefix}RangeBtn" class="secondary">${this._t("applyRange")}</button>
          </div>
        ` : ""}
      </div>
    `;
  }

  _renderManualTrackingSummary() {
    const records = this._manualTrackingRecords();
    const s = this._tripSummaryFromRecords(records);
    return `
      <div class="summary">
        <div class="stat"><span class="muted">${this._t("count")} · ${this._filterLabel("manual")}</span><b>${s.count || 0}</b></div>
        <div class="stat"><span class="muted">${this._t("totalDistance")}</span><b>${this._fmtNumber(s.total_distance_km || 0, 1)} km</b></div>
        <div class="stat"><span class="muted">${this._t("totalEnergy")}</span><b>${this._fmtNumber(s.total_energy_kwh || 0, 1)} kWh</b></div>
        <div class="stat"><span class="muted">${this._t("totalDuration")}</span><b>${this._durationText(s.total_duration_minutes || 0)}</b></div>
        <div class="stat"><span class="muted">${this._t("avgConsumption")}</span><b>${this._fmtNumber(s.average_consumption_kwh_100km || 0, 2)} kWh/100</b></div>
      </div>
    `;
  }

  _renderManualTrackingRecords() {
    const records = this._manualTrackingRecords();
    if (!records.length) return `<div class="empty">${this._t("manualTrackingEmpty")}</div>`;
    return `
      <table>
        <thead><tr>
          <th>${this._t("date")}</th>
          <th>${this._t("startAddress")} / ${this._t("endAddress")}</th>
          <th>${this._t("distance")}</th>
          <th>${this._t("usedEnergy")}</th>
          <th class="hide-sm">${this._t("consumption")}</th>
        </tr></thead>
        <tbody>
          ${records.map((r) => `
            <tr class="record ${r.id === this._selectedManualTrackingId ? "selected" : ""}" data-id="${this._esc(r.id)}" data-kind="manual">
              <td>${this._esc(r.display_at || r.created_at || "-")}<div class="muted">${this._esc(r.source || "manual_tracking")}</div></td>
              <td class="addr"><b>${this._esc(r.start_address || "-")}</b><div class="muted">→ ${this._esc(r.end_address || "-")}</div></td>
              <td>${this._fmtNumber(r.trip_km, 2)} km</td>
              <td>${this._fmtNumber(r.used_kwh, 2)} kWh</td>
              <td class="hide-sm">${this._fmtNumber(r.consumption_kwh_100km, 2)}<div class="muted">${this._t("movingAverageSpeed")}: ${this._fmtNumber(r.average_moving_speed || r.average_speed || 0, 1)} km/sa</div></td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  _renderManualTrackingMapPreview() {
    if (!this._editingManualTracking) return "";
    const preview = this._manualTrackingMapPreview || {};
    const body = preview.loading
      ? `<div class="record-map-placeholder">${this._t("loadingMap")}</div>`
      : preview.image_url
        ? `<img src="${this._esc(preview.image_url)}" alt="${this._esc(this._t("fullTripMap"))}" />`
        : `<div class="record-map-placeholder">${this._esc(preview.error || this._t("mapUnavailable"))}</div>`;
    return `
      <div class="record-map-card">
        <div class="record-map-title">${this._t("fullTripMap")}</div>
        <div class="record-map-canvas">${body}</div>
      </div>
    `;
  }

  _renderManualTrackingDetails() {
    const r = this._editingManualTracking;
    if (!r) return `<div class="empty">${this._t("manualTrackingEmpty")}</div>`;
    return `
      ${this._renderManualTrackingMapPreview()}
      <div class="manual-detail-grid">
        <div><span>${this._t("date")}</span><b>${this._esc(r.display_at || r.created_at || "-")}</b></div>
        <div><span>${this._t("activitySource")}</span><b>${this._esc(r.source || "manual_tracking")}</b></div>
        <div><span>${this._t("distance")}</span><b>${this._fmtNumber(r.trip_km, 2)} km</b></div>
        <div><span>${this._t("totalDuration")}</span><b>${this._durationText(r.duration_minutes || 0)}</b></div>
        <div><span>${this._t("movingDuration")}</span><b>${r.moving_duration_text || this._secondsDurationText(r.moving_seconds || 0)}</b></div>
        <div><span>${this._t("traffic")}</span><b>${r.traffic_text || this._secondsDurationText(r.traffic_seconds || 0)}</b></div>
        <div><span>${this._t("stoppedInDrive")}</span><b>${r.stopped_in_drive_text || this._secondsDurationText(r.stopped_in_drive_seconds || 0)}</b></div>
        <div><span>${this._t("slowTraffic")}</span><b>${r.slow_traffic_text || this._secondsDurationText(r.slow_traffic_seconds || 0)}</b></div>
        <div><span>${this._t("parkedPause")}</span><b>${r.parked_pause_text || this._secondsDurationText(r.parked_pause_seconds || 0)}</b></div>
        <div><span>${this._t("finalParkWait")}</span><b>${r.final_park_wait_text || this._secondsDurationText(r.final_park_wait_seconds || 0)}</b></div>
        <div><span>${this._t("totalElapsed")}</span><b>${r.total_elapsed_text || this._secondsDurationText(r.total_elapsed_seconds || 0)}</b></div>
        <div><span>${this._t("normalDrive")}</span><b>${r.normal_drive_text || this._secondsDurationText(r.normal_drive_seconds || 0)}</b></div>
        <div><span>${this._t("movingAverageSpeed")}</span><b>${this._fmtNumber(r.average_moving_speed || r.average_speed || 0, 1)} km/sa</b></div>
        <div><span>${this._t("overallAverageSpeed")}</span><b>${this._fmtNumber(r.average_overall_speed || 0, 1)} km/sa</b></div>
        <div><span>${this._t("maxSpeed")}</span><b>${this._fmtNumber(r.max_speed || 0, 1)} km/sa</b></div>
        <div><span>${this._t("speedSamples")}</span><b>${this._esc(r.speed_sample_count || 0)}</b></div>
        <div><span>${this._t("speedSamplerInterval")}</span><b>${this._esc(r.speed_sampler_interval_seconds || 1)} sn</b></div>
        <div><span>${this._t("movingThreshold")}</span><b>${this._fmtNumber(r.moving_speed_threshold || 1, 1)} km/sa</b></div>
        <div><span>${this._t("usedEnergy")}</span><b>${this._fmtNumber(r.used_kwh, 2)} kWh</b></div>
        <div><span>${this._t("consumption")}</span><b>${this._fmtNumber(r.consumption_kwh_100km, 2)} kWh/100</b></div>
      </div>
      <label>${this._t("startAddress")}</label>
      <textarea readonly>${this._esc(r.start_address || "-")}</textarea>
      <label>${this._t("endAddress")}</label>
      <textarea readonly>${this._esc(r.end_address || "-")}</textarea>
    `;
  }

  _renderChargeRecords() {
    const records = this._chargeRecords();
    if (!records.length) return `<div class="empty">${this._t("empty")}</div>`;
    return `
      <table>
        <thead><tr>
          <th>${this._t("date")}</th>
          <th>${this._t("provider")}</th>
          <th>${this._t("energy")}</th>
          <th>${this._t("totalCost")}</th>
          <th class="hide-sm">${this._t("unitPrice")}</th>
        </tr></thead>
        <tbody>
          ${records.map((r) => `
            <tr class="record ${r.id === this._selectedChargeId ? "selected" : ""}" data-id="${this._esc(r.id)}" data-kind="charge">
              <td>${this._esc(r.display_at || r.created_at || "-")}</td>
              <td><b>${this._esc(r.provider || "-")}</b><div class="muted">${this._esc(r.source || "")}</div></td>
              <td>${this._fmtNumber(r.added_kwh, 2)}</td>
              <td>${this._fmtNumber(r.total_cost, 2)} ${this._esc(r.currency_label || this._chargeData?.currency || "")}</td>
              <td class="hide-sm">${this._fmtNumber(r.price_per_kwh, 4)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  _renderTripRecords() {
    const records = this._tripRecords();
    if (!records.length) return `<div class="empty">${this._t("empty")}</div>`;
    return `
      <table>
        <thead><tr>
          <th>${this._t("date")}</th>
          <th>${this._t("startAddress")} / ${this._t("endAddress")}</th>
          <th>${this._t("distance")}</th>
          <th>${this._t("usedEnergy")}</th>
          <th class="hide-sm">${this._t("consumption")}</th>
        </tr></thead>
        <tbody>
          ${records.map((r) => `
            <tr class="record ${r.id === this._selectedTripId ? "selected" : ""}" data-id="${this._esc(r.id)}" data-kind="trip">
              <td>${this._esc(r.display_at || r.created_at || "-")}<div class="muted">${this._esc(r.source || "")}</div></td>
              <td class="addr"><b>${this._esc(r.start_address || "-")}</b><div class="muted">→ ${this._esc(r.end_address || "-")}</div></td>
              <td>${this._fmtNumber(r.trip_km, 2)} km</td>
              <td>${this._fmtNumber(r.used_kwh, 2)} kWh</td>
              <td class="hide-sm">${this._fmtNumber(r.consumption_kwh_100km, 2)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  _renderChargeMapPreview() {
    if (!this._editingCharge) return "";
    const preview = this._chargeMapPreview || {};
    const body = preview.loading
      ? `<div class="record-map-placeholder">${this._t("loadingMap")}</div>`
      : preview.image_url
        ? `<img src="${this._esc(preview.image_url)}" alt="${this._esc(this._t("locationMap"))}" />`
        : `<div class="record-map-placeholder">${this._esc(preview.error || this._t("mapUnavailable"))}</div>`;
    const address = preview.full_address || this._editingCharge?.full_address || this._editingCharge?.location_label || this._t("noAddressAvailable");
    return `
      <div class="record-map-card">
        <div class="record-map-title">${this._t("locationMap")}</div>
        <div class="record-map-canvas">${body}</div>
        <div class="record-map-address-label">${this._t("fullAddress")}</div>
        <div class="record-map-address">${this._esc(address)}</div>
      </div>
    `;
  }

  _renderTripMapPreview() {
    if (!this._editingTrip) return "";
    const preview = this._tripMapPreview || {};
    const body = preview.loading
      ? `<div class="record-map-placeholder">${this._t("loadingMap")}</div>`
      : preview.image_url
        ? `<img src="${this._esc(preview.image_url)}" alt="${this._esc(this._t("routeMap"))}" />`
        : `<div class="record-map-placeholder">${this._esc(preview.error || this._t("mapUnavailable"))}</div>`;
    return `
      <div class="record-map-card">
        <div class="record-map-title">${this._t("routeMap")}</div>
        <div class="record-map-canvas">${body}</div>
      </div>
    `;
  }

  _renderChargeEditor() {
    const r = this._editingCharge;
    if (!r) {
      return `<div class="empty">${this._t("selectChargeHint")}</div><div class="actions"><button id="newChargeBtn">${this._t("addNew")}</button></div>`;
    }
    return `
      ${this._renderChargeMapPreview()}
      <label>${this._t("date")}</label>
      <input id="charge_display_at" value="${this._esc(r.display_at || "")}" />
      <label>${this._t("provider")}</label>
      <input id="charge_provider" value="${this._esc(r.provider || "")}" />
      <div class="two">
        <div><label>${this._t("energy")}</label><input id="charge_added_kwh" inputmode="decimal" value="${this._esc(r.added_kwh ?? "")}" /></div>
        <div><label>${this._t("totalCost")}</label><input id="charge_total_cost" inputmode="decimal" value="${this._esc(r.total_cost ?? "")}" /></div>
      </div>
      <div class="two">
        <div><label>${this._t("unitPrice")}</label><input id="charge_price_per_kwh" inputmode="decimal" value="${this._esc(r.price_per_kwh ?? "")}" /></div>
        <div><label>${this._t("currency")}</label><input id="charge_currency_label" value="${this._esc(r.currency_label || this._chargeData?.currency || this._currency || "TL")}" /></div>
      </div>
      <div class="actions">
        <button id="saveChargeBtn">${this._selectedChargeId ? this._t("saveUpdate") : this._t("saveNew")}</button>
        <button id="addChargeBtn" class="secondary">${this._t("saveNew")}</button>
        <button id="newChargeBtn" class="secondary">${this._t("addNew")}</button>
        <button id="deleteChargeBtn" class="danger" ${this._selectedChargeId ? "" : "disabled"}>${this._t("delete")}</button>
      </div>
    `;
  }

  _renderTripEditor() {
    const r = this._editingTrip;
    if (!r) {
      return `<div class="empty">${this._t("selectTripHint")}</div><div class="actions"><button id="newTripBtn">${this._t("addNew")}</button></div>`;
    }
    return `
      ${this._renderTripMapPreview()}
      <label>${this._t("date")}</label>
      <input id="trip_display_at" value="${this._esc(r.display_at || "")}" />
      <label>${this._t("startAddress")}</label>
      <textarea id="trip_start_address">${this._esc(r.start_address || "")}</textarea>
      <label>${this._t("endAddress")}</label>
      <textarea id="trip_end_address">${this._esc(r.end_address || "")}</textarea>
      <div class="two">
        <div><label>${this._t("distance")}</label><input id="trip_km" inputmode="decimal" value="${this._esc(r.trip_km ?? "")}" /></div>
        <div><label>${this._t("durationMinutes")}</label><input id="trip_duration_minutes" inputmode="decimal" value="${this._esc(r.duration_minutes ?? "")}" /></div>
      </div>
      <label>${this._t("durationText")}</label>
      <input id="trip_duration_text" value="${this._esc(r.duration_text || "")}" />
      <div class="two">
        <div><label>${this._t("usedEnergy")}</label><input id="trip_used_kwh" inputmode="decimal" value="${this._esc(r.used_kwh ?? "")}" /></div>
        <div><label>${this._t("consumption")}</label><input id="trip_consumption" inputmode="decimal" value="${this._esc(r.consumption_kwh_100km ?? "")}" /></div>
      </div>
      <div class="two">
        <div><label>${this._t("totalCost")}</label><input id="trip_total_cost" inputmode="decimal" value="${this._esc(r.total_cost ?? "")}" /></div>
        <div><label>${this._t("currency")}</label><input id="trip_currency_label" value="${this._esc(r.currency_label || this._tripData?.currency || this._currency || "TL")}" /></div>
      </div>
      <div class="note">${this._t("autoCalcHint")}</div>
      <div class="actions">
        <button id="saveTripBtn">${this._selectedTripId ? this._t("saveUpdate") : this._t("saveNew")}</button>
        <button id="addTripBtn" class="secondary">${this._t("saveNew")}</button>
        <button id="newTripBtn" class="secondary">${this._t("addNew")}</button>
        <button id="deleteTripBtn" class="danger" ${this._selectedTripId ? "" : "disabled"}>${this._t("delete")}</button>
      </div>
    `;
  }

  _renderStationList() {
    const stations = this._stations();
    if (!stations.length) return `<div class="empty">${this._t("noStations")}</div>`;
    const active = stations.slice(0, 3);
    const others = stations.slice(3);
    const stationRow = (s, index, mode = "pool") => {
      const slotButtons = `
        <div class="station-slot-control">
          <span>${this._t("setReportSlot")}</span>
          <div class="station-slot-buttons">
            <button class="mini-slot-btn ${index === 0 ? "current" : ""}" data-station-slot="0" data-station-index="${index}" title="${this._esc(this._t("moveToReportSlot"))} 1">1</button>
            <button class="mini-slot-btn ${index === 1 ? "current" : ""}" data-station-slot="1" data-station-index="${index}" title="${this._esc(this._t("moveToReportSlot"))} 2">2</button>
            <button class="mini-slot-btn ${index === 2 ? "current" : ""}" data-station-slot="2" data-station-index="${index}" title="${this._esc(this._t("moveToReportSlot"))} 3">3</button>
          </div>
        </div>
      `;
      return `
        <div class="station-row ${index === this._selectedStationIndex ? "selected" : ""} ${index < 3 ? "report-active" : ""}" data-station-index="${index}">
          <div class="station-order-badge ${index < 3 ? "report" : "pool"}">${index + 1}</div>
          <div class="station-main-info">
            <b>${this._esc(s.name)}</b>
            <div class="muted">${this._esc(s.currency)} / kWh</div>
            ${index < 3 ? `<div class="report-slot-inline">${this._t("reportSlot")} ${index + 1}</div>` : ""}
          </div>
          <div class="station-row-actions">
            ${slotButtons}
            <div class="price-badge">${this._fmtNumber(s.unit_price, 2)} ${this._esc(s.currency)}</div>
          </div>
        </div>
      `;
    };
    return `
      <div class="report-cost-slots">
        <div class="section-title small-title">${this._t("reportCostSlots")}</div>
        <div class="note">${this._t("reportCostSlotsSub")}</div>
        <div class="station-list report-slots">
          ${active.map((s, index) => stationRow(s, index, "active")).join("")}
        </div>
      </div>
      <div class="station-pool-block">
        <div class="section-title small-title">${this._t("savedStationPool")}</div>
        <div class="station-list">
          ${others.length ? others.map((s, offset) => stationRow(s, offset + 3, "pool")).join("") : `<div class="empty">${this._t("noStations")}</div>`}
        </div>
      </div>
    `;
  }

  _toggle(id, checked, label) {
    return `
      <div class="toggle-row">
        <span>${label}</span>
        <label class="switch">
          <input id="${id}" type="checkbox" ${checked ? "checked" : ""} />
          <i class="slider"></i>
        </label>
      </div>
    `;
  }

  _renderTrackerOptions(selected) {
    if (!this._hass?.states) return "";
    const allowed = Object.keys(this._hass.states)
      .filter((id) => id.startsWith("device_tracker.") || id.startsWith("person."))
      .sort();
    return `
      <datalist id="tracker_entity_options">
        ${allowed.map((id) => `<option value="${this._esc(id)}">${this._esc(this._hass.states[id]?.attributes?.friendly_name || id)}</option>`).join("")}
      </datalist>
    `;
  }

  _renderSettingsNav() {
    const items = [
      ["general", "settingsGeneralNav"],
      ["charging", "settingsChargingNav"],
      ["trip", "settingsTripNav"],
      ["ai_settings", "settingsAIConfigNav"],
      ["telegram", "settingsTelegramNav"],
      ["ai", "settingsAiNav"],
      ["automations", "settingsAutomationsNav"],
      ["dashboard", "settingsDashboardNav"],
    ];
    return `
      <div class="settings-nav">
        ${items.map(([id, label]) => `<button type="button" id="settingsNav_${this._esc(id)}" data-settings-tab="${this._esc(id)}" class="${this._activeSettingsTab === id ? "active" : ""}">${this._t(label)}</button>`).join("")}
      </div>
    `;
  }


  _renderGeneralSettings() {
    const general = this._settingsData?.general_settings || {};
    const summary = general.resource_summary || {};
    const system = general.system || {};
    const debugPayload = {
      language: general.app_language || this._lang || "-",
      default_open_tab: general.default_open_tab || "settings",
      status: this._status || "",
      error: this._error || "",
      frontend_build: this._frontendBuild || "",
      last_click_debug: this._lastClickDebug || {},
      resource_summary: summary || {},
      config_entry: Boolean(system.has_config_entry),
    };
    const debugOutput = this._manualDebugSnapshot || this._debugSnapshot();
    const panelMigrationOutput = this._panelMigrationOutput ?? (general.entity_store_audit || {});
    return `
      <div class="settings-grid wide">
        <section class="card accent">
          <div class="card-h"><div><h2>${this._t("generalSettings")}</h2><div class="hint">${this._t("generalSettingsSub")}</div></div></div>
          <div class="body">
            <div class="settings-hero"><b>${this._t("settingsGeneralNav")}</b><span class="muted">${this._t("generalSettingsSub")}</span></div>
            <div class="section-title">${this._t("appLanguage")}</div>
            <div class="field-grid">
              <div><label>${this._t("appLanguage")}</label><select id="general_app_language">
                <option value="tr" ${(general.app_language || this._lang) === "tr" ? "selected" : ""}>${this._t("languageTurkish")}</option>
                <option value="en" ${(general.app_language || this._lang) === "en" ? "selected" : ""}>${this._t("languageEnglish")}</option>
              </select></div>
              <div><label>${this._t("defaultOpenTab")}</label><select id="general_default_open_tab">
                <option value="settings" ${(general.default_open_tab || "settings") === "settings" ? "selected" : ""}>${this._t("defaultOpenSettings")}</option>
                <option value="charges" ${general.default_open_tab === "charges" ? "selected" : ""}>${this._t("defaultOpenCharges")}</option>
                <option value="trips" ${general.default_open_tab === "trips" ? "selected" : ""}>${this._t("defaultOpenTrips")}</option>
              </select></div>
            </div>
            <div class="section-title">${this._t("debugDiagnosticsMode")}</div>
            ${this._toggle("general_debug_enabled", general.debug_enabled, this._t("debugDiagnosticsMode"))}
            <div class="note">${this._t("debugDiagnosticsSub")}</div>
            ${general.debug_enabled ? `
              <div class="debug-toolbar">
                <div>
                  <b>${this._t("debugDiagnosticsDetails")}</b>
                  <div class="note">${this._t("debugDiagnosticsSub")}</div>
                </div>
                <div class="actions">
                  <button id="runDebugInfoBtn" class="secondary">${this._t("debugRun")}</button>
                  <button id="copyDebugInfoBtn" class="secondary">${this._t("debugCopy")}</button>
                  <button id="clearDebugInfoBtn" class="secondary">${this._t("debugClear")}</button>
                </div>
              </div>
              <div class="debug-panel debug-output-panel">
                <pre>${this._esc(JSON.stringify(debugOutput, null, 2))}</pre>
              </div>` : ""}
            <div class="actions"><button id="saveGeneralSettingsBtn">${this._t("saveGeneralSettings")}</button><button id="refreshBtn" class="secondary">${this._t("refresh")}</button></div>
          </div>
        </section>
        <section class="card">
          <div class="card-h"><div><h2>${this._t("systemSummary")}</h2><div class="hint">${this._t("generalSettingsSub")}</div></div></div>
          <div class="body">
            <div class="summary">
              <div><span>${this._t("appLanguage")}</span><b>${this._esc(general.app_language || this._lang || "-")}</b></div>
              <div><span>${this._t("resourceSummaryShort")}</span><b>${this._esc(String(summary.missing_total ?? summary.missing ?? 0))} / ${this._esc(String(summary.total ?? summary.resource_total ?? "-"))}</b></div>
              <div><span>Config entry</span><b>${system.has_config_entry ? "OK" : "Missing"}</b></div>
            </div>
            <div class="section-title">${this._t("panelMigrationOutput")}</div>
            <div class="note">${this._t("entityStoreAuditSub")}</div>
            <pre class="audit-pre">${this._esc(JSON.stringify(panelMigrationOutput, null, 2))}</pre>
            <div class="actions">
              <button id="migratePanelStoresBtn" class="secondary">${this._t("migratePanelStores")}</button>
              <button id="clearPanelMigrationOutputBtn" class="secondary">${this._t("clearPanelMigrationOutput")}</button>
            </div>
            <div class="section-title">${this._t("exportSettings")} / ${this._t("importSettings")}</div>
            <div class="actions">
              <button id="exportSettingsBtn" class="secondary">${this._t("exportSettings")}</button>
              <label class="file-btn" for="importSettingsFile">${this._t("importSettings")}</label>
              <input id="importSettingsFile" type="file" accept="application/json,.json" style="display:none" />
            </div>
            <div class="note" id="importSettingsNote">${this._t("importSettingsPlaceholder")}</div>
          </div>
        </section>
      </div>
    `;
  }

  _readGeneralSettingsForm() {
    const root = this.shadowRoot;
    return {
      app_language: root.getElementById("general_app_language")?.value || this._lang || "tr",
      debug_enabled: this._checked("general_debug_enabled"),
      default_open_tab: root.getElementById("general_default_open_tab")?.value || "settings",
    };
  }

  async _saveGeneralSettings() {
    if (!this._hass) return;
    const general_settings = this._readGeneralSettingsForm();
    this._loading = true;
    this._error = "";
    this._render();
    try {
      const startedAt = performance.now();
      const response = await this._hass.callApi("POST", "pom_tesla_report/settings", { general_settings });
      this._recordApiResult("POST settings/general", { status: "fulfilled", value: response }, startedAt);
      this._settingsData = this._applySettingsSaveResponse(response, { general_settings });
      this._lastSettingsSaveSummary = {
        area: "general",
        at: new Date().toISOString(),
        keys: Object.keys(general_settings || {}),
        language: general_settings.app_language,
        debug_enabled: Boolean(general_settings.debug_enabled),
      };
      this._status = this._t("generalSettingsSaved");
      this._pushDebugEvent("success", "General settings saved", { general_settings });
    } catch (err) {
      this._error = this._formatError(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _migratePanelEntityStores() {
    if (!this._hass) return;
    this._loading = true;
    this._error = "";
    this._render();
    try {
      const response = await this._hass.callApi("POST", "pom_tesla_report/settings", { action: "migrate_panel_entity_stores" });
      this._settingsData = this._normalizeSettingsPayload(response);
      this._panelMigrationOutput = response?.migration || response?.general_settings?.entity_store_audit || this._settingsData?.general_settings?.entity_store_audit || {};
      this._status = this._t("panelStoresMigrated");
      this._pushDebugEvent("success", "Panel entity stores migrated", this._panelMigrationOutput);
    } catch (err) {
      this._error = this._formatError(err);
      this._pushDebugEvent("error", "Panel entity store migration failed", { error: this._error });
    } finally {
      this._loading = false;
      this._render();
    }
  }

  _exportPanelSettings() {
    const data = this._settingsData || {};
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "pom_tesla_report_settings.json";
    a.click();
    URL.revokeObjectURL(url);
    this._status = this._t("exportSettingsDone");
    this._pushDebugEvent("success", "Settings exported");
    this._render();
  }

  _renderChargingSettings() {
    const charging = this._settingsData?.charging || {};
    const station = this._editingStation || { name: "", unit_price: "", currency: charging.report_currency || this._currency };
    return `
      <div class="settings-grid">
        <section class="card accent">
          <div class="card-h"><div><h2>${this._t("chargingSettings")}</h2><div class="hint">${this._t("chargingSettingsSub")}</div></div></div>
          <div class="body">
            <div class="settings-hero"><b>${this._t("settingsChargingNav")}</b><span class="muted">${this._t("settingsNote")}</span></div>
            <div class="two">
              <div><label>${this._t("reportCurrency")}</label><select id="settings_report_currency">${this._renderCurrencyOptions(charging.report_currency || this._currency)}</select></div>
              <div><label>${this._t("reportMode")}</label><select id="settings_report_mode">
                <option value="prompt" ${(charging.charging_report_mode || "prompt") === "prompt" ? "selected" : ""}>${this._t("promptMode")}</option>
                <option value="direct" ${charging.charging_report_mode === "direct" ? "selected" : ""}>${this._t("directMode")}</option>
              </select></div>
            </div>
            <div class="test-card">
              <h3>${this._t("chargeTelegramTests")}</h3>
              <p>${this._t("chargeTelegramTestsSub")}</p>
              <div class="charge-test-actions">
                <div id="sendTestChargeCostReportBtn" class="test-action-card primary" role="button" tabindex="0" data-panel-action="charge-test-monthly">${this._t("sendTestChargeCostReport")}</div>
                <div id="sendTestChargeCompletionReportBtn" class="test-action-card secondary" role="button" tabindex="0" data-panel-action="charge-test-completion">${this._t("sendTestChargeCompletionReport")}</div>
              </div>
              <div class="note">${this._t("testChargeNoLedger")}</div>
            </div>
            <div class="section-title">${this._t("builtInPrices")}</div>
            <div class="note">${this._t("builtInPricesSub")}</div>
            ${this._renderStationList()}
            <div class="actions"><button id="saveSettingsBtn">${this._t("saveChargingSettings")}</button><button id="refreshBtn" class="secondary">${this._t("refresh")}</button></div>
          </div>
        </section>
        <section class="card">
          <div class="card-h"><div><h2>${this._t("stationEditor")}</h2><div class="hint">${this._t("stationEditorSub")}</div></div></div>
          <div class="body">
            <label>${this._t("stationName")}</label>
            <input id="station_name" value="${this._esc(station.name || "")}" placeholder="ZES, Ionity, Lidl Bulgaria" />
            <div class="two">
              <div><label>${this._t("stationUnitPrice")}</label><input id="station_unit_price" inputmode="decimal" value="${this._esc(station.unit_price ?? "")}" /></div>
              <div><label>${this._t("stationCurrency")}</label><select id="station_currency">${this._renderCurrencyOptions(station.currency || charging.report_currency || this._currency)}</select></div>
            </div>
            <div class="actions">
              <button id="saveStationBtn">${this._t("saveStation")}</button>
              <button id="clearStationBtn" class="secondary" ${this._selectedStationIndex >= 0 ? "" : "disabled"}>${this._t("clearStationSelection")}</button>
              <button id="deleteStationBtn" class="danger" ${this._selectedStationIndex >= 0 ? "" : "disabled"}>${this._t("deleteStation")}</button>
            </div>
            <div class="note">${this._lang === "en" ? "Saved stations appear on the left. The top three rows are used in reports; move lower stations into slots 1/2/3 with the slot buttons." : "Kaydedilen istasyonlar solda görünür. Üstteki üç sıra raporlarda kullanılır; alttaki istasyonları 1/2/3 butonlarıyla üst slotlara taşıyabilirsin."}</div>
          </div>
        </section>
      </div>
    `;
  }


  _renderTelegramDiagnostics() {
    const diag = this._telegramDiagnostics || {};
    const state = diag.service_state || {};
    const logs = Array.isArray(diag.logs) ? diag.logs : [];
    const defaultMsg = this._lang === "en" ? "POM Telegram test message" : "POM Telegram test mesajı";
    const stateRows = [
      ["Mode", state.mode || "—"],
      ["Built-in", state.builtin_enabled ? "on" : "off"],
      ["Token", state.builtin_has_token ? "ok" : "missing"],
      ["Polling", state.builtin_poll_enabled ? "on" : "off"],
      ["HA service", state.ha_send_message_service ? "ok" : "missing"],
      ["Group", state.group_id || "—"],
    ];
    return `
      <div class="diag-box">
        <div class="section-title">${this._t("telegramServiceState")}</div>
        <div class="diag-grid">
          ${stateRows.map(([k, v]) => `<div><span>${this._esc(k)}</span><b>${this._esc(v)}</b></div>`).join("")}
        </div>
        <label>${this._t("telegramTestMessage")}</label>
        <input id="telegram_test_message" value="${this._esc(defaultMsg)}" />
        <div class="actions compact">
          <button id="sendTelegramTestBtn">${this._t("sendTelegramTest")}</button>
          <button id="pollTelegramTestBtn" class="secondary">${this._t("pollTelegramOnce")}</button>
          <button id="clearTelegramLogsBtn" class="secondary">${this._t("clearTelegramLogs")}</button>
        </div>
        <div class="section-title">${this._t("telegramLog")}</div>
        <div class="log-list">
          ${logs.length ? logs.map((item) => `
            <div class="log-row ${this._esc(item.level || "info")}">
              <div><b>${this._esc(item.level || "info")}</b><span>${this._esc(item.ts || "")}</span></div>
              <p>${this._esc(item.message || "")}</p>
              ${item.detail ? `<pre>${this._esc(item.detail)}</pre>` : ""}
            </div>
          `).join("") : `<div class="note">${this._t("noTelegramLogs")}</div>`}
        </div>
      </div>
    `;
  }

  _renderEntitiesSubNav() {
    const items = [
      ["ai", "entitiesAiTab"],
      ["report", "entitiesReportTab"],
      ["dashboard", "entitiesDashboardTab"],
    ];
    return `<div class="entities-subnav">${items.map(([id, label]) => `<button type="button" data-entities-subtab="${id}" class="${this._activeEntitiesTab === id ? "active" : ""}">${this._t(label)}</button>`).join("")}</div>`;
  }

  _entryForRole(kind, role, value) {
    const manager = this._settingsData?.[kind] || {};
    const entries = Array.isArray(manager.entries) ? manager.entries : [];
    return entries.find((item) => item && item.role === role && (!value || item.entity_id === value)) || null;
  }

  _confidenceText(label) {
    const value = String(label || "").toLowerCase();
    if (value === "very_high") return this._t("confidenceVeryHigh");
    if (value === "high") return this._t("confidenceHigh");
    if (value === "medium") return this._t("confidenceMedium");
    if (value === "low" || value === "very_low") return this._t("confidenceLow");
    return this._t("confidenceMedium");
  }

  _renderConfidenceBadge(entry) {
    if (!entry || !entry.entity_id) return "";
    const manual = String(entry.source || "").includes("manual") || entry.manual === true;
    const raw = Number(entry.confidence);
    if (manual && !Number.isFinite(raw)) {
      return `<div class="confidence-badge manual" title="${this._esc(this._t("confidenceManual"))}">${this._esc(this._t("confidenceManual"))}</div>`;
    }
    if (!Number.isFinite(raw) || raw <= 0) return "";
    const confidence = Math.max(0, Math.min(100, Math.round(raw)));
    let level = "low";
    if (confidence >= 95) level = "very-high";
    else if (confidence >= 85) level = "high";
    else if (confidence >= 70) level = "medium";
    const reason = entry.match_reason ? `${this._t("confidenceReason")}: ${entry.match_reason}` : "";
    const label = this._confidenceText(entry.confidence_label || level.replace("-", "_"));
    return `<div class="confidence-badge ${level}" title="${this._esc(reason)}">%${confidence} · ${this._esc(label)}</div>`;
  }

  _renderAIRoleTile(roleDef, value) {
    const role = roleDef.role || "other";
    const selected = this._entityOptionById(value || "");
    const entry = this._entryForRole("ai_entity_manager", role, value || "");
    const friendly = value ? (selected?.name || value) : this._t("chooseEntity");
    const meta = !value ? this._t("entityNotSelected") : (!selected ? this._t("unknownEntitySelected") : this._entityMeta(value));
    const emptyClass = !value ? " empty" : (!selected ? " invalid" : "");
    return `
      <div class="ai-role-tile ai-role-selectable${emptyClass}" data-entity-picker-target="ai_role_${this._esc(role)}" tabindex="0" role="button">
        <button type="button" class="ai-role-close clear-ai-role" data-role="${this._esc(role)}" title="${this._esc(this._t("clearAiRole"))}">×</button>
        <div class="ai-role-tile-head">
          <div class="ai-role-title">${this._esc(roleDef.label || role)}</div>
          <div class="ai-role-desc">${this._esc(roleDef.description || "")}</div>
          ${roleDef.expected_entity ? `<div class="ai-role-expected">${this._esc(this._t("entityExpectedEntity"))}: ${this._esc(roleDef.expected_entity)}</div>` : ""}
          ${this._renderConfidenceBadge(entry)}
        </div>
        <div class="ai-role-chip">
          <div class="ai-role-friendly">${this._esc(friendly)}</div>
          <div class="ai-role-meta-line">${this._esc(meta)}</div>
        </div>
      </div>
    `;
  }

  _renderAICustomTile(item, idx) {
    const entityId = item?.entity_id || "";
    const selected = this._entityOptionById(entityId);
    const friendly = entityId ? (selected?.name || entityId) : this._t("chooseEntity");
    const meta = !entityId ? this._t("customAiEntitiesSub") : (!selected ? this._t("unknownEntitySelected") : this._entityMeta(entityId));
    const emptyClass = !entityId ? " empty" : (!selected ? " invalid" : "");
    return `
      <div class="ai-role-tile ai-role-selectable custom${emptyClass}" data-entity-picker-target="ai_custom_${idx}" tabindex="0" role="button">
        <button type="button" class="ai-role-close remove-ai-custom-entry" data-index="${idx}" title="${this._esc(this._t("removeAiEntity"))}">×</button>
        <div class="ai-role-tile-head">
          <div class="ai-role-title">${this._esc(this._t("customAiEntities"))} #${idx + 1}</div>
          <div class="ai-role-desc">${this._esc(this._t("customAiEntitiesSub"))}</div>
        </div>
        <div class="ai-role-chip">
          <div class="ai-role-friendly">${this._esc(friendly)}</div>
          <div class="ai-role-meta-line">${this._esc(meta)}</div>
        </div>
      </div>
    `;
  }

  _renderReportRoleTile(roleDef, value) {
    const role = roleDef.role || "other";
    const selected = this._entityOptionById(value || "");
    const entry = this._entryForRole("report_entity_manager", role, value || "");
    const friendly = value ? (selected?.name || value) : this._t("chooseEntity");
    const meta = !value ? this._t("entityNotSelected") : (!selected ? this._t("unknownEntitySelected") : this._entityMeta(value));
    const emptyClass = !value ? " empty" : (!selected ? " invalid" : "");
    return `
      <div class="ai-role-tile ai-role-selectable report-role${emptyClass}" data-entity-picker-target="report_role_${this._esc(role)}" tabindex="0" role="button">
        <button type="button" class="ai-role-close clear-report-role" data-role="${this._esc(role)}" title="${this._esc(this._t("clearAiRole"))}">×</button>
        <div class="ai-role-tile-head">
          <div class="ai-role-title">${this._esc(roleDef.label || role)}</div>
          <div class="ai-role-desc">${this._esc(roleDef.description || "")}</div>
          ${roleDef.expected_entity ? `<div class="ai-role-expected">${this._esc(this._t("entityExpectedEntity"))}: ${this._esc(roleDef.expected_entity)}</div>` : ""}
          ${this._renderConfidenceBadge(entry)}
        </div>
        <div class="ai-role-chip">
          <div class="ai-role-friendly">${this._esc(friendly)}</div>
          <div class="ai-role-meta-line">${this._esc(meta)}</div>
        </div>
      </div>
    `;
  }


  _renderDashboardRoleTile(roleDef, value) {
    const role = roleDef.role || "other";
    const selected = this._entityOptionById(value || "");
    const entry = this._entryForRole("dashboard_entity_manager", role, value || "");
    const friendly = value ? (selected?.name || value) : this._t("chooseEntity");
    const meta = !value ? this._t("entityNotSelected") : (!selected ? this._t("unknownEntitySelected") : this._entityMeta(value));
    const emptyClass = !value ? " empty" : (!selected ? " invalid" : "");
    return `
      <div class="ai-role-tile ai-role-selectable dashboard-role${emptyClass}" data-entity-picker-target="dashboard_role_${this._esc(role)}" tabindex="0" role="button">
        <button type="button" class="ai-role-close clear-dashboard-role" data-role="${this._esc(role)}" title="${this._esc(this._t("clearAiRole"))}">×</button>
        <div class="ai-role-tile-head">
          <div class="ai-role-title">${this._esc(roleDef.label || role)}</div>
          <div class="ai-role-desc">${this._esc(roleDef.description || "")}</div>
          ${roleDef.expected_entity ? `<div class="ai-role-expected">${this._esc(this._t("entityExpectedEntity"))}: ${this._esc(roleDef.expected_entity)}</div>` : ""}
          ${this._renderConfidenceBadge(entry)}
        </div>
        <div class="ai-role-chip">
          <div class="ai-role-friendly">${this._esc(friendly)}</div>
          <div class="ai-role-meta-line">${this._esc(meta)}</div>
        </div>
        ${roleDef.category === "dashboard_custom_home" ? `
          <div class="dashboard-custom-icon-row" data-stop-picker="1">
            <label>${this._esc(this._t("dashboardCustomIcon"))}</label>
            <input class="dashboard-custom-icon-input" data-dashboard-icon-role="${this._esc(role)}" value="${this._esc(this._getDashboardEntityDraft().meta?.[role]?.icon || "")}" placeholder="mdi:home-lightning-bolt" />
            <div class="note tiny">${this._esc(this._t("dashboardCustomIconSub"))}</div>
          </div>
        ` : ""}
      </div>
    `;
  }

  _renderDashboardEntityManagerSettings() {
    const dashboard = this._settingsData?.dashboard_entity_manager || {};
    const roles = dashboard.roles || [];
    const groupedRoles = this._groupAIRolesByCategory(roles);
    const draft = this._getDashboardEntityDraft();
    const roleValues = draft.roles || {};
    const selectedCount = Object.values(roleValues).filter(Boolean).length;
    const missingCount = Math.max(0, roles.length - selectedCount);
    return `
      <div class="settings-grid wide ai-manager-grid ai-manager-stacked compact-ai-manager">
        <section class="card accent ai-summary-card">
          <div class="card-h"><div><h2>${this._t("dashboardEntityManager")}</h2><div class="hint">${this._t("dashboardEntityManagerSub")}</div></div></div>
          <div class="body">
            ${this._renderEntitiesSubNav()}
            <div class="ai-summary-layout">
              <div class="ai-summary-main">
                <div class="settings-hero compact"><b>${this._t("entitiesDashboardTab")}</b><span class="muted">${this._t("dashboardPrimarySourcesSub")}</span></div>
                <label>${this._t("dashboardMainTeslaEntity")}</label>
                ${this._renderEntityPickerField("dashboard_main_entity", draft.main_entity || dashboard.main_entity || "", "sensor.tesla_battery_level")}
                <div class="note">${this._t("dashboardMainTeslaEntitySub")}</div>
                <div class="note">${this._t("autoFindEntitiesSub")}</div>
              </div>
              <div class="ai-summary-side">
                <div class="summary-grid mini ai-summary-stats">
                  <div><span>${this._t("dashboardEntityCount")}</span><b>${this._esc(selectedCount)}</b></div>
                  <div><span>${this._t("dashboardRoleSlotCount")}</span><b>${this._esc(roles.length)}</b></div>
                  <div><span>${this._t("dashboardMissingCount")}</span><b>${this._esc(missingCount)}</b></div>
                </div>
                <div class="actions ai-summary-actions">
                  <button id="autoFindDashboardEntitiesBtn" class="primary-wide">${this._t("autoFindEntities")}</button>
                  <button type="button" class="secondary clear-all-dashboard-entities">${this._t("clearAllDashboardEntities")}</button>
                  <button id="saveDashboardEntityManagerBtn" class="secondary">${this._t("saveDashboardEntities")}</button>
                </div>
              </div>
            </div>
          </div>
        </section>
        <section class="card ai-roles-card compact-ai-card">
          <div class="card-h"><div><h2>${this._t("dashboardPrimarySources")}</h2><div class="hint">${this._t("dashboardPrimarySourcesSub")}</div></div></div>
          <div class="body ai-role-list compact">
            <div class="ai-category-list">
              ${!groupedRoles.length ? `<div class="note">${this._esc(this._t("dashboardPrimarySourcesSub"))}</div>` : ""}
              ${groupedRoles.map(([category, items]) => `
                <div class="ai-category-block ${this._esc(category)}">
                  <div class="ai-category-head">
                    <h3>${this._esc(items[0]?.category_label || this._t(this._categoryTranslationKey(category)))}</h3>
                    <span>${this._esc(this._t("entityCategoryCount").replace("{count}", String(items.length)))}</span>
                  </div>
                  <div class="ai-role-grid compact-grid ai-four-grid">
                    ${items.map((roleDef) => this._renderDashboardRoleTile(roleDef, roleValues[roleDef.role] || "")).join("")}
                  </div>
                </div>
              `).join("")}
            </div>
            <div class="actions sticky-actions"><button id="saveDashboardEntityManagerBtnBottom">${this._t("saveDashboardEntities")}</button><button id="autoFindDashboardEntitiesBtnBottom" class="secondary">${this._t("autoFindEntities")}</button><button type="button" class="secondary clear-all-dashboard-entities">${this._t("clearAllDashboardEntities")}</button></div>
          </div>
        </section>
      </div>
    `;
  }

  _renderReportEntityManagerSettings() {
    const report = this._settingsData?.report_entity_manager || {};
    const roles = report.roles || [];
    const groupedRoles = this._groupAIRolesByCategory(roles);
    const draft = this._getReportEntityDraft();
    const roleValues = draft.roles || {};
    const selectedCount = Object.values(roleValues).filter(Boolean).length;
    const mapCount = roles.filter((roleDef) => roleDef.role === "location_tracker" && roleValues[roleDef.role]).length;
    return `
      <div class="settings-grid wide ai-manager-grid ai-manager-stacked compact-ai-manager">
        <section class="card accent ai-summary-card">
          <div class="card-h"><div><h2>${this._t("reportEntityManager")}</h2><div class="hint">${this._t("reportEntityManagerSub")}</div></div></div>
          <div class="body">
            ${this._renderEntitiesSubNav()}
            <div class="ai-summary-layout">
              <div class="ai-summary-main">
                <div class="settings-hero compact"><b>${this._t("entitiesReportTab")}</b><span class="muted">${this._t("reportPrimarySourcesSub")}</span></div>
                <label>${this._t("reportMainTeslaEntity")}</label>
                ${this._renderEntityPickerField("report_main_entity", draft.main_entity || report.main_entity || "", "sensor.pom_battery_level")}
                <div class="note">${this._t("reportMainTeslaEntitySub")}</div>
                <div class="note">${this._t("autoFindEntitiesSub")}</div>
              </div>
              <div class="ai-summary-side">
                <div class="summary-grid mini ai-summary-stats">
                  <div><span>${this._t("reportEntityCount")}</span><b>${this._esc(selectedCount)}</b></div>
                  <div><span>${this._t("reportRoleSlotCount")}</span><b>${this._esc(roles.length)}</b></div>
                  <div><span>${this._t("reportMapCount")}</span><b>${this._esc(mapCount)}</b></div>
                </div>
                <div class="actions ai-summary-actions">
                  <button id="autoFindReportEntitiesBtn" class="primary-wide">${this._t("autoFindEntities")}</button>
                  <button id="saveReportEntityManagerBtn" class="secondary">${this._t("saveReportEntities")}</button>
                </div>
              </div>
            </div>
          </div>
        </section>
        <section class="card ai-roles-card compact-ai-card">
          <div class="card-h"><div><h2>${this._t("reportPrimarySources")}</h2><div class="hint">${this._t("reportPrimarySourcesSub")}</div></div></div>
          <div class="body ai-role-list compact">
            <div class="ai-category-list">
              ${groupedRoles.map(([category, items]) => `
                <div class="ai-category-block ${this._esc(category)}">
                  <div class="ai-category-head">
                    <h3>${this._esc(items[0]?.category_label || this._t(this._categoryTranslationKey(category)))}</h3>
                    <span>${this._esc(this._t("entityCategoryCount").replace("{count}", String(items.length)))}</span>
                  </div>
                  <div class="ai-role-grid compact-grid ai-four-grid">
                    ${items.map((roleDef) => this._renderReportRoleTile(roleDef, roleValues[roleDef.role] || "")).join("")}
                  </div>
                </div>
              `).join("")}
            </div>
            <div class="actions sticky-actions"><button id="saveReportEntityManagerBtnBottom">${this._t("saveReportEntities")}</button><button id="autoFindReportEntitiesBtnBottom" class="secondary">${this._t("autoFindEntities")}</button></div>
          </div>
        </section>
      </div>
    `;
  }

  _renderAIEntityManagerSettings() {
    if (this._activeEntitiesTab === "report") {
      return this._renderReportEntityManagerSettings();
    }
    if (this._activeEntitiesTab === "dashboard") {
      return this._renderDashboardEntityManagerSettings();
    }
    const ai = this._settingsData?.ai_entity_manager || {};
    const roles = ai.roles || [];
    const groupedRoles = this._groupAIRolesByCategory(roles);
    const draft = this._getAIEntityDraft();
    const roleValues = draft.roles || {};
    const customEntries = Array.isArray(draft.custom) ? draft.custom : [];
    const selectedCount = Object.values(roleValues).filter(Boolean).length + customEntries.filter((item) => item.entity_id).length;
    return `
      <div class="settings-grid wide ai-manager-grid ai-manager-stacked compact-ai-manager">
        <section class="card accent ai-summary-card">
          <div class="card-h"><div><h2>${this._t("aiEntityManager")}</h2><div class="hint">${this._t("aiEntityManagerSub")}</div></div></div>
          <div class="body">
            ${this._renderEntitiesSubNav()}
            <div class="ai-summary-layout">
              <div class="ai-summary-main">
                <div class="settings-hero compact"><b>${this._t("entitiesAiTab")}</b><span class="muted">${this._t("aiEntityManagerSub")}</span></div>
                <label>${this._t("aiMainTeslaEntity")}</label>
                ${this._renderEntityPickerField("ai_main_entity", draft.main_entity || ai.main_entity || "", "sensor.pom_battery_level")}
                <div class="note">${this._t("aiMainTeslaEntitySub")}</div>
                <div class="note">${this._t("autoFindEntitiesSub")}</div>
              </div>
              <div class="ai-summary-side">
                ${this._toggle("ai_auto_discover_device_entities", draft.auto_discover_device_entities, this._t("aiAutoDiscoverToggle"))}
                <div class="summary-grid mini ai-summary-stats">
                  <div><span>${this._t("aiEntityCount")}</span><b>${this._esc(selectedCount)}</b></div>
                  <div><span>${this._t("aiRoleSlotCount")}</span><b>${this._esc(roles.length)}</b></div>
                  <div><span>${this._t("aiCustomCount")}</span><b>${this._esc(customEntries.filter((item) => item.entity_id).length)}</b></div>
                </div>
                <div class="actions ai-summary-actions">
                  <button id="autoFindAIEntitiesBtn" class="primary-wide">${this._t("autoFindEntities")}</button>
                  <button type="button" class="secondary clear-all-ai-entities">${this._t("clearAllAiEntities")}</button>
                  <button id="saveAIEntityManagerBtn" class="secondary">${this._t("saveAiEntities")}</button>
                </div>
              </div>
            </div>
          </div>
        </section>
        <section class="card ai-roles-card compact-ai-card">
          <div class="card-h"><div><h2>${this._t("entityRole")}</h2><div class="hint">${this._t("selectedEntity")}</div></div></div>
          <div class="body ai-role-list compact">
            <div class="ai-category-list">
              ${groupedRoles.map(([category, items]) => `
                <div class="ai-category-block ${this._esc(category)}">
                  <div class="ai-category-head">
                    <h3>${this._esc(items[0]?.category_label || this._t(this._categoryTranslationKey(category)))}</h3>
                    <span>${this._esc(this._t("entityCategoryCount").replace("{count}", String(items.length)))}</span>
                  </div>
                  <div class="ai-role-grid compact-grid ai-four-grid">
                    ${items.map((roleDef) => this._renderAIRoleTile(roleDef, roleValues[roleDef.role] || "")).join("")}
                  </div>
                </div>
              `).join("")}
            </div>
            <div class="custom-ai-block compact">
              <div class="section-title">${this._t("customAiEntities")}</div>
              <div class="note">${this._t("customAiEntitiesSub")}</div>
              <div class="note">${this._t("aiExtraDeduped")}</div>
              <div class="ai-role-grid compact-grid custom-grid ai-four-grid">
                ${customEntries.map((item, idx) => this._renderAICustomTile(item, idx)).join("")}
              </div>
              <button type="button" class="secondary add-ai-entry">${this._t("addAiEntity")}</button>
            </div>
            <div class="actions sticky-actions"><button id="saveAIEntityManagerBtnBottom">${this._t("saveAiEntities")}</button><button id="autoFindAIEntitiesBtnBottom" class="secondary">${this._t("autoFindEntities")}</button><button type="button" class="secondary clear-all-ai-entities">${this._t("clearAllAiEntities")}</button></div>
          </div>
        </section>
      </div>
    `;
  }


  _selectOptions(value, options) {
    return options.map(([val, label]) => `<option value="${this._esc(val)}" ${String(value || "") === String(val) ? "selected" : ""}>${this._esc(label)}</option>`).join("");
  }

  _renderAIDiagnostics() {
    const diag = this._aiDiagnostics || {};
    const state = diag.service_state || {};
    const logs = Array.isArray(diag.logs) ? diag.logs : [];
    const defaultPrompt = this._lang === "en" ? "Reply briefly: did the POM Tesla AI connectivity test succeed?" : "Kısaca cevap ver: POM Tesla AI bağlantı testi başarılı mı?";
    const stateRows = [
      ["AI", state.ai_enabled ? "on" : "off"],
      ["API key", state.has_openai_key ? "ok" : "missing"],
      ["Model", state.model || "—"],
      ["Name", state.ai_name || "—"],
      ["Max tokens", state.max_output_tokens || "—"],
    ];
    return `
      <div class="diag-box">
        <div class="section-title">${this._t("aiServiceState")}</div>
        <div class="diag-grid">
          ${stateRows.map(([k, v]) => `<div><span>${this._esc(k)}</span><b>${this._esc(v)}</b></div>`).join("")}
        </div>
        <label>${this._t("aiTestPrompt")}</label>
        <input id="ai_test_prompt" value="${this._esc(defaultPrompt)}" />
        <div class="actions compact">
          <button id="runAITestBtn">${this._t("runAITest")}</button>
          <button id="runAITestTelegramBtn" class="secondary">${this._t("runAITestTelegram")}</button>
          <button id="clearAILogsBtn" class="secondary">${this._t("clearAILogs")}</button>
        </div>
        <div class="section-title">${this._t("aiLog")}</div>
        <div class="log-list">
          ${logs.length ? logs.map((item) => `
            <div class="log-row ${this._esc(item.level || "info")}">
              <div><b>${this._esc(item.level || "info")}</b><span>${this._esc(item.ts || "")}</span></div>
              <p>${this._esc(item.message || "")}</p>
              ${item.detail ? `<pre>${this._esc(item.detail)}</pre>` : ""}
            </div>
          `).join("") : `<div class="note">${this._t("noAILogs")}</div>`}
        </div>
      </div>
    `;
  }

  _renderAISettings() {
    const ai = this._settingsData?.ai_settings || {};
    return `
      <div class="settings-grid wide">
        <section class="card accent">
          <div class="card-h"><div><h2>${this._t("aiSettings")}</h2><div class="hint">${this._t("aiSettingsSub")}</div></div></div>
          <div class="body">
            <div class="settings-hero"><b>${this._t("settingsAIConfigNav")}</b><span class="muted">${this._t("aiSettingsSub")}</span></div>
            <div class="section-title">${this._t("aiBehavior")}</div>
            ${this._toggle("ai_settings_enabled", ai.ai_enabled, this._t("aiEnabled"))}
            <div class="field-grid">
              <div><label>${this._t("aiName")}</label><input id="ai_settings_name" value="${this._esc(ai.ai_name || "Tesla AI")}" /></div>
              <div><label>${this._t("aiPersonality")}</label><select id="ai_settings_personality">${this._selectOptions(ai.ai_personality || "friendly", [["professional", this._t("personalityProfessional")], ["friendly", this._t("personalityFriendly")], ["funny", this._t("personalityFunny")], ["short_direct", this._t("personalityShortDirect")], ["premium_tesla_assistant", this._t("personalityPremium")], ["turkish_buddy", this._t("personalityTurkishBuddy")]])}</select></div>
              <div><label>${this._t("aiAnswerLength")}</label><select id="ai_settings_answer_length">${this._selectOptions(ai.ai_answer_length || "short", [["short", this._t("answerShort")], ["normal", this._t("answerNormal")], ["detailed", this._t("answerDetailed")]])}</select></div>
              <div><label>${this._t("aiContextMode")}</label><select id="ai_settings_context_mode">${this._selectOptions(ai.ai_context_mode || "smart_manual", [["basic", this._t("contextBasic")], ["smart_auto", this._t("contextSmartAuto")], ["selected_device", this._t("contextSelectedDevice")], ["smart_manual", this._t("contextSmartManual")], ["manual_only", this._t("contextManualOnly")]])}</select></div>
            </div>

            <div class="section-title">${this._t("aiConnection")}</div>
            <div class="field-grid">
              <div><label>${this._t("openaiApiKey")}</label><input id="ai_settings_openai_api_key" type="password" autocomplete="off" value="${this._esc(ai.openai_api_key || "")}" /></div>
              <div><label>${this._t("openaiModel")}</label><input id="ai_settings_openai_model" value="${this._esc(ai.openai_model || "gpt-4.1-mini")}" /></div>
              <div><label>${this._t("aiMaxOutputTokens")}</label><input id="ai_settings_max_output_tokens" inputmode="numeric" value="${this._esc(ai.ai_max_output_tokens ?? 700)}" /></div>
            </div>

            <div class="section-title">${this._t("aiAddress")}</div>
            ${this._toggle("ai_settings_reverse_geocoding_enabled", ai.reverse_geocoding_enabled, this._t("reverseGeocodingEnabled"))}
            ${this._toggle("ai_settings_reverse_geocoding_use_in_ai", ai.reverse_geocoding_use_in_ai, this._t("reverseGeocodingUseInAi"))}
            <div class="field-grid">
              <div><label>${this._t("reverseGeocodingCacheMinutes")}</label><input id="ai_settings_reverse_geocoding_cache_minutes" inputmode="numeric" value="${this._esc(Math.max(5, Number(ai.reverse_geocoding_cache_minutes ?? 60)))}" /><div class="note">${this._t("minutesShort")} · min 5</div></div>
            </div>

            <div class="section-title">${this._t("aiTelegramContext")}</div>
            <div class="visual-grid">
              ${this._toggle("ai_settings_telegram_include_context", ai.ai_telegram_include_context, this._t("aiTelegramIncludeContext"))}
              ${this._toggle("ai_settings_confirm_optional_controls", ai.ai_confirm_optional_controls, this._t("aiConfirmOptionalControls"))}
            </div>
            <div class="actions"><button id="saveAISettingsBtn">${this._t("saveAISettings")}</button><button id="refreshBtn" class="secondary">${this._t("refresh")}</button></div>
          </div>
        </section>
        <section class="card">
          <div class="card-h"><div><h2>${this._t("aiDiagnostics")}</h2><div class="hint">${this._t("aiDiagnosticsSub")}</div></div></div>
          <div class="body">
            ${this._renderAIDiagnostics()}
          </div>
        </section>
      </div>
    `;
  }

  _automationCard(toggleId, checked, title, inputId, value, label, unit = "") {
    return `
      <div class="automation-card">
        ${this._toggle(toggleId, checked, title)}
        ${inputId ? `<div class="automation-field"><label>${this._esc(label || "")}</label><input id="${this._esc(inputId)}" inputmode="decimal" value="${this._esc(value ?? "")}" />${unit ? `<div class="note">${this._esc(unit)}</div>` : ""}</div>` : ""}
      </div>
    `;
  }

  _renderAutomationSettings() {
    const ai = this._settingsData?.ai_settings || {};
    return `
      <div class="settings-grid wide">
        <section class="card accent">
          <div class="card-h"><div><h2>${this._t("automationSettings")}</h2><div class="hint">${this._t("automationSettingsSub")}</div></div></div>
          <div class="body">
            <div class="settings-hero"><b>${this._t("settingsAutomationsNav")}</b><span class="muted">${this._t("automationSettingsSub")}</span></div>
            ${this._toggle("ai_settings_alerts_enabled", ai.ai_alerts_enabled, this._t("aiAlerts"))}
            <div class="field-grid">
              <div><label>${this._t("aiAlertStyle")}</label><select id="ai_settings_alert_style">${this._selectOptions(ai.ai_alert_style || "ai", [["rule", this._t("alertStyleRule")], ["ai", this._t("alertStyleAI")]])}</select></div>
              <div><label>${this._t("aiAlertCooldownMinutes")}</label><input id="ai_settings_alert_cooldown_minutes" inputmode="numeric" value="${this._esc(ai.ai_alert_cooldown_minutes ?? 30)}" /><div class="note">${this._t("minutesShort")}</div></div>
            </div>
          </div>
        </section>
        <section class="card">
          <div class="card-h"><div><h2>${this._t("aiAlerts")}</h2><div class="hint">${this._t("automationSettingsSub")}</div></div></div>
          <div class="body">
            <div class="automation-grid">
              ${this._automationCard("ai_settings_alert_low_battery_enabled", ai.ai_alert_low_battery_enabled, this._t("aiAlertLowBatteryEnabled"), "ai_settings_alert_low_battery_threshold", ai.ai_alert_low_battery_threshold ?? 20, this._t("aiAlertLowBatteryThreshold"), this._t("percentShort"))}
              ${this._automationCard("ai_settings_alert_charge_finished_enabled", ai.ai_alert_charge_finished_enabled, this._t("aiAlertChargeFinishedEnabled"))}
              ${this._automationCard("ai_settings_alert_charging_stopped_enabled", ai.ai_alert_charging_stopped_enabled, this._t("aiAlertChargingStoppedEnabled"))}
              ${this._automationCard("ai_settings_alert_tire_pressure_enabled", ai.ai_alert_tire_pressure_enabled, this._t("aiAlertTirePressureEnabled"), "ai_settings_alert_tire_pressure_threshold_bar", ai.ai_alert_tire_pressure_threshold_bar ?? 36, this._t("aiAlertTirePressureThresholdBar"), this._t("psiBarNote"))}
              ${this._automationCard("ai_settings_alert_high_battery_temp_enabled", ai.ai_alert_high_battery_temp_enabled, this._t("aiAlertHighBatteryTempEnabled"), "ai_settings_alert_high_battery_temp_threshold_c", ai.ai_alert_high_battery_temp_threshold_c ?? 55, this._t("aiAlertHighBatteryTempThresholdC"), "°C")}
              ${this._automationCard("ai_settings_alert_climate_left_on_enabled", ai.ai_alert_climate_left_on_enabled, this._t("aiAlertClimateLeftOnEnabled"), "ai_settings_alert_climate_left_on_delay_minutes", ai.ai_alert_climate_left_on_delay_minutes ?? 10, this._t("aiAlertClimateLeftOnDelayMinutes"), this._t("minutesShort"))}
              ${this._automationCard("ai_settings_alert_unlocked_enabled", ai.ai_alert_unlocked_enabled, this._t("aiAlertUnlockedEnabled"), "ai_settings_alert_unlocked_delay_minutes", ai.ai_alert_unlocked_delay_minutes ?? 2, this._t("aiAlertUnlockedDelayMinutes"), this._t("minutesShort"))}
              ${this._automationCard("ai_settings_alert_door_window_open_enabled", ai.ai_alert_door_window_open_enabled, this._t("aiAlertDoorWindowOpenEnabled"), "ai_settings_alert_door_window_open_delay_minutes", ai.ai_alert_door_window_open_delay_minutes ?? 5, this._t("aiAlertDoorWindowOpenDelayMinutes"), this._t("minutesShort"))}
              ${this._automationCard("ai_settings_alert_window_open_instant_enabled", ai.ai_alert_window_open_instant_enabled, this._t("aiAlertWindowOpenInstantEnabled"))}
            </div>
            <div class="actions"><button id="saveAutomationSettingsBtn">${this._t("saveAutomationSettings")}</button><button id="refreshBtn" class="secondary">${this._t("refresh")}</button></div>
          </div>
        </section>
      </div>
    `;
  }

  _readAISettingsForm() {
    const root = this.shadowRoot;
    const current = this._settingsData?.ai_settings || {};
    const value = (id, fallback = "") => {
      const el = root.getElementById(id);
      return el ? el.value : fallback;
    };
    const clean = (id, fallback = "") => String(value(id, fallback) || "").trim();
    const number = (id, fallback) => this._number(value(id, fallback));
    const checked = (id, fallback = false) => {
      const el = root.getElementById(id);
      return el ? Boolean(el.checked) : Boolean(fallback);
    };
    return {
      ai_enabled: checked("ai_settings_enabled", current.ai_enabled),
      ai_personality: value("ai_settings_personality", current.ai_personality || "friendly"),
      ai_answer_length: value("ai_settings_answer_length", current.ai_answer_length || "short"),
      ai_context_mode: value("ai_settings_context_mode", current.ai_context_mode || "smart_manual"),
      ai_name: clean("ai_settings_name", current.ai_name || "Tesla AI") || "Tesla AI",
      openai_api_key: clean("ai_settings_openai_api_key", current.openai_api_key || ""),
      openai_model: clean("ai_settings_openai_model", current.openai_model || "gpt-4.1-mini") || "gpt-4.1-mini",
      reverse_geocoding_enabled: checked("ai_settings_reverse_geocoding_enabled", current.reverse_geocoding_enabled),
      reverse_geocoding_cache_minutes: Math.max(5, number("ai_settings_reverse_geocoding_cache_minutes", current.reverse_geocoding_cache_minutes ?? 60)),
      reverse_geocoding_use_in_ai: checked("ai_settings_reverse_geocoding_use_in_ai", current.reverse_geocoding_use_in_ai),
      ai_max_output_tokens: number("ai_settings_max_output_tokens", current.ai_max_output_tokens ?? 700),
      ai_telegram_include_context: checked("ai_settings_telegram_include_context", current.ai_telegram_include_context),
      ai_confirm_optional_controls: checked("ai_settings_confirm_optional_controls", current.ai_confirm_optional_controls),
      ai_alerts_enabled: checked("ai_settings_alerts_enabled", current.ai_alerts_enabled),
      ai_alert_style: value("ai_settings_alert_style", current.ai_alert_style || "ai"),
      ai_alert_cooldown_minutes: number("ai_settings_alert_cooldown_minutes", current.ai_alert_cooldown_minutes ?? 30),
      ai_alert_low_battery_enabled: checked("ai_settings_alert_low_battery_enabled", current.ai_alert_low_battery_enabled),
      ai_alert_low_battery_threshold: number("ai_settings_alert_low_battery_threshold", current.ai_alert_low_battery_threshold ?? 20),
      // Moved to Live Trip settings. Preserve the stored value when saving AI settings.
      ai_alert_post_trip_summary_enabled: Boolean((this._settingsData?.trip_reports?.ai_trip_story_enabled ?? current.ai_alert_post_trip_summary_enabled ?? true)),
      ai_alert_charge_finished_enabled: checked("ai_settings_alert_charge_finished_enabled", current.ai_alert_charge_finished_enabled),
      ai_alert_charging_stopped_enabled: checked("ai_settings_alert_charging_stopped_enabled", current.ai_alert_charging_stopped_enabled),
      ai_alert_tire_pressure_enabled: checked("ai_settings_alert_tire_pressure_enabled", current.ai_alert_tire_pressure_enabled),
      ai_alert_tire_pressure_threshold_bar: number("ai_settings_alert_tire_pressure_threshold_bar", current.ai_alert_tire_pressure_threshold_bar ?? 36),
      ai_alert_high_battery_temp_enabled: checked("ai_settings_alert_high_battery_temp_enabled", current.ai_alert_high_battery_temp_enabled),
      ai_alert_high_battery_temp_threshold_c: number("ai_settings_alert_high_battery_temp_threshold_c", current.ai_alert_high_battery_temp_threshold_c ?? 55),
      ai_alert_climate_left_on_enabled: checked("ai_settings_alert_climate_left_on_enabled", current.ai_alert_climate_left_on_enabled),
      ai_alert_climate_left_on_delay_minutes: number("ai_settings_alert_climate_left_on_delay_minutes", current.ai_alert_climate_left_on_delay_minutes ?? 10),
      ai_alert_unlocked_enabled: checked("ai_settings_alert_unlocked_enabled", current.ai_alert_unlocked_enabled),
      ai_alert_unlocked_delay_minutes: number("ai_settings_alert_unlocked_delay_minutes", current.ai_alert_unlocked_delay_minutes ?? 2),
      ai_alert_door_window_open_enabled: checked("ai_settings_alert_door_window_open_enabled", current.ai_alert_door_window_open_enabled),
      ai_alert_door_window_open_delay_minutes: number("ai_settings_alert_door_window_open_delay_minutes", current.ai_alert_door_window_open_delay_minutes ?? 5),
      ai_alert_window_open_instant_enabled: checked("ai_settings_alert_window_open_instant_enabled", current.ai_alert_window_open_instant_enabled),
    };
  }

  async _saveAISettings(statusKey = "aiSettingsSaved") {
    if (!this._hass) return;
    const ai_settings = this._readAISettingsForm();
    this._loading = true;
    this._error = "";
    this._render();
    try {
      this._settingsData = this._applySettingsSaveResponse(await this._hass.callApi("POST", "pom_tesla_report/settings", { ai_settings }), { ai_settings });
      this._status = this._t(statusKey);
    } catch (err) {
      this._error = this._formatError(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _saveAutomationSettings() {
    return this._saveAISettings("automationSettingsSaved");
  }

  _readFileAsDataURL(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result || ""));
      reader.onerror = () => reject(reader.error || new Error("Could not read selected file."));
      reader.readAsDataURL(file);
    });
  }

  async _uploadDashboardBackground(slot) {
    if (!this._hass) return;
    const input = this.shadowRoot.getElementById(`dashboard_file_${slot}`);
    const file = input?.files?.[0];
    if (!file) {
      this._error = this._t("dashboardNoFileSelected");
      this._render();
      return;
    }
    this._loading = true;
    this._error = "";
    this._status = "";
    this._render();
    try {
      const dataUrl = await this._readFileAsDataURL(file);
      const payload = await this._hass.callApi("POST", "pom_tesla_report/dashboard_media", {
        action: "upload",
        slot,
        filename: file.name || `${slot}.png`,
        data_url: dataUrl,
      });
      if (payload?.success === false) throw new Error(payload?.error || "Upload failed.");
      this._settingsData = this._normalizeSettingsPayload(payload);
      this._status = this._t("dashboardUploadOk");
    } catch (err) {
      this._error = this._formatError(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _resetDashboardBackground(slot) {
    if (!this._hass) return;
    this._loading = true;
    this._error = "";
    this._render();
    try {
      const payload = await this._hass.callApi("POST", "pom_tesla_report/dashboard_media", { action: "reset", slot });
      this._settingsData = this._normalizeSettingsPayload(payload);
      this._status = this._t("dashboardUploadOk");
    } catch (err) {
      this._error = this._formatError(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }



  _renderTelegramReportCommandSettings(commands = {}) {
    const defaults = this._defaultTelegramReportCommands ? this._defaultTelegramReportCommands() : {
      charge_report: "charge",
      trip_summary: "trip",
      trip_all: "tripall",
      trip_single: "single",
      trip_last: "triplast",
    };
    const cmd = this._telegramReportCommands ? this._telegramReportCommands(commands) : {
      charge_report: String(commands?.charge_report || defaults.charge_report || "charge"),
      trip_summary: String(commands?.trip_summary || defaults.trip_summary || "trip"),
      trip_all: String(commands?.trip_all || defaults.trip_all || "tripall"),
      trip_single: String(commands?.trip_single || defaults.trip_single || "single"),
      trip_last: String(commands?.trip_last || defaults.trip_last || "triplast"),
    };
    const rows = [
      ["telegram_cmd_charge_report", "charge_report", this._lang === "en" ? "Charge report command" : "Şarj raporu komutu", this._lang === "en" ? "Sends this month’s charge summary and visual charge report." : "Bu ayın şarj özetini ve görsel şarj raporunu gönderir."],
      ["telegram_cmd_trip_summary", "trip_summary", this._lang === "en" ? "Monthly trip summary command" : "Aylık sürüş özeti komutu", this._lang === "en" ? "Sends the current month’s trip overview page." : "Bu ayın sürüş özet/overview raporunu gönderir."],
      ["telegram_cmd_trip_all", "trip_all", this._lang === "en" ? "All trip records command" : "Tüm sürüş kayıtları komutu", this._lang === "en" ? "Sends all monthly trip report pages." : "Bu ayki tüm sürüş kayıtlarını/sayfalarını gönderir."],
      ["telegram_cmd_trip_single", "trip_single", this._lang === "en" ? "Single-page trip report command" : "Tek sayfa sürüş raporu komutu", this._lang === "en" ? "Sends the monthly trip report in single-page mode." : "Aylık sürüş raporunu tek sayfa/single modda gönderir."],
      ["telegram_cmd_trip_last", "trip_last", this._lang === "en" ? "Last trip report command" : "Son sürüş raporu komutu", this._lang === "en" ? "Sends the latest completed trip visual report." : "En son tamamlanan sürüşün görsel raporunu gönderir."],
    ];
    return `
      <div class="section-title">${this._lang === "en" ? "Telegram report commands" : "Telegram rapor komutları"}</div>
      <div class="note">${this._lang === "en"
        ? "Write only the command word after /. Example: write sarj here, use /sarj in Telegram. Legacy /charge, /trip, /tripall, /single, /triplast and /lasttrip still work."
        : "Sadece / işaretinden sonraki komut kelimesini yaz. Örnek: buraya sarj yazarsan Telegram’da /sarj kullanılır. Eski /charge, /trip, /tripall, /single, /triplast ve /lasttrip yine çalışır."}</div>
      <div class="field-grid">
        ${rows.map(([id, key, label, desc]) => `
          <div>
            <label>${this._esc(label)}</label>
            <input id="${id}" value="${this._esc(cmd[key] || "")}" placeholder="${this._esc(defaults[key] || "")}" />
            <div class="note">/${this._esc(cmd[key] || defaults[key] || "")} — ${this._esc(desc)}</div>
          </div>
        `).join("")}
      </div>
    `;
  }


  _renderTelegramSettings() {
    const telegram = this._settingsData?.telegram || {};
    return `
      <div class="settings-grid wide">
        <section class="card accent">
          <div class="card-h"><div><h2>${this._t("telegramSettings")}</h2><div class="hint">${this._t("telegramSettingsSub")}</div></div></div>
          <div class="body">
            <div class="settings-hero"><b>${this._t("telegramHelpTitle")}</b><span class="muted">${this._t("telegramHelpText")}</span></div>
            ${this._toggle("telegram_builtin_enabled", telegram.builtin_telegram_enabled, this._t("useBuiltInTelegramBot"))}
            <label>${this._t("telegramBotToken")}</label>
            <input id="telegram_bot_token" type="password" autocomplete="off" value="${this._esc(telegram.builtin_telegram_bot_token || "")}" placeholder="123456:ABC..." />
            ${this._toggle("telegram_poll_enabled", telegram.builtin_telegram_poll_enabled, this._t("enableBuiltInTelegramPolling"))}
            <div class="field-grid">
              <div><label>${this._t("telegramPollingInterval")}</label><input id="telegram_poll_interval" inputmode="numeric" value="${this._esc(telegram.builtin_telegram_poll_interval_seconds ?? 3)}" /><div class="note">${this._t("secondsShort")}</div></div>
              <div><label>${this._t("telegramGroupId")}</label><input id="telegram_group_id" value="${this._esc(telegram.telegram_group_id || "")}" placeholder="-1003863356165" /></div>
            </div>
            ${this._toggle("telegram_replies_enabled", telegram.replies_enabled, this._t("enableReplies"))}
            ${this._toggle("telegram_ai_listener_enabled", telegram.ai_group_listener_enabled, this._t("enableTelegramAiGroupListener"))}
            ${this._renderTelegramReportCommandSettings(telegram.report_commands || {})}
            <div class="actions"><button id="saveTelegramSettingsBtn">${this._t("saveTelegramSettings")}</button><button id="refreshBtn" class="secondary">${this._t("refresh")}</button></div>
          </div>
        </section>
        <section class="card">
          <div class="card-h"><div><h2>${this._t("settingsTelegramNav")}</h2><div class="hint">${this._t("telegramSettingsSub")}</div></div></div>
          <div class="body">
            <div class="section-title">${this._t("telegramGroupId")}</div>
            <div class="metric-big">${this._esc(telegram.telegram_group_id || "—")}</div>
            <div class="note">${this._lang === "en" ? "This group ID is written to the report reply target, AI Telegram target, and AI listener chat ID. Keep test and production machines on separate bot tokens to avoid getUpdates conflicts." : "Bu grup ID rapor cevap hedefi, AI Telegram hedefi ve AI listener chat ID alanlarına yazılır. Test ve ana makinede getUpdates çakışması olmaması için ayrı bot token kullan."}</div>
            ${this._renderTelegramDiagnostics()}
          </div>
        </section>
      </div>
    `;
  }

  _renderTripSettings() {
    const trip = this._settingsData?.trip_reports || {};
    const tracker = trip.trip_map_tracker_entity || "";
    const section = this._tripSettingsSection || "tracking";
    const fieldToggles = [
      ["trip_show_distance", trip.show_distance, "showDistance"],
      ["trip_show_duration", trip.show_duration, "showDuration"],
      ["trip_show_traffic", trip.show_traffic, "showTraffic"],
      ["trip_show_average_speed", trip.show_average_speed, "showAverageSpeed"],
      ["trip_show_energy", trip.show_energy, "showEnergy"],
      ["trip_show_consumption", trip.show_consumption, "showConsumption"],
      ["trip_show_battery", trip.show_battery, "showBattery"],
      ["trip_show_cost", trip.show_cost, "showCost"],
      ["trip_show_climate", trip.show_climate, "showClimate"],
      ["trip_show_elevation", trip.show_elevation, "showElevation"],
      ["trip_show_trip_map", trip.show_trip_map, "showTripMap"],
    ];
    const moduleCard = (id, title, sub) => `<button type="button" class="module-card ${section === id ? "active" : ""}" data-trip-section="${this._esc(id)}"><b>${this._esc(title)}</b><span class="muted">${this._esc(sub)}</span></button>`;
    const trackingContent = `
      <div class="section-title">${this._t("trackingEmpty")}</div>
      <div class="note">${this._t("trackingEmptySub")}</div>
    `;
    const liveTripContent = `
      <div class="section-title">${this._t("liveTripSettings")}</div>
      <div class="note">${this._t("liveTripSettingsSub")}</div>
      ${this._toggle("trip_auto_trip_tracking", trip.auto_trip_tracking, this._t("enableAutoTripTracking"))}
      <div class="field-grid">
        <div><label>${this._t("startSpeedThreshold")}</label><input id="trip_auto_start_speed_threshold" inputmode="decimal" value="${this._esc(trip.auto_start_speed_threshold ?? 2)}" /><div class="note">${this._t("speedUnit")}</div></div>
        <div><label>${this._t("liveTripUpdateIntervalSeconds")}</label><input id="trip_live_trip_update_interval_seconds" inputmode="numeric" value="${this._esc(trip.live_trip_update_interval_seconds ?? 5)}" /><div class="note">${this._t("secondsShort")} · Hız örnekleme ayrı olarak 1 sn çalışır.</div></div>
        <div><label>${this._t("liveTripTrafficSpeedThreshold")}</label><input id="trip_live_trip_traffic_speed_threshold" inputmode="decimal" value="${this._esc(trip.live_trip_traffic_speed_threshold ?? 20)}" /><div class="note">${this._t("speedUnit")}</div></div>
        <div><label>${this._t("liveTripFinishDelaySeconds")}</label><input id="trip_live_trip_finish_delay_minutes" inputmode="decimal" value="${this._esc(this._secondsToMinutesValue(trip.live_trip_finish_delay_seconds ?? 1800))}" /><div class="note">${this._t("minutesShort")} · Park içinde tekrar hareket ederse Live Trip devam eder.</div></div>
        <div><label>${this._t("liveTripMinDistanceKm")}</label><input id="trip_live_trip_min_distance_km" inputmode="decimal" value="${this._esc(trip.live_trip_min_distance_km ?? 0)}" /><div class="note">km</div></div>
      </div>
      <div class="section-title">${this._lang === "en" ? "AI trip story" : "AI sürüş hikâyesi"}</div>
      <div class="note">${this._lang === "en"
        ? "This belongs to Live Trip. The AI story is sent only after the normal visual Live Trip report. It follows the same Park/report delay, so it cannot arrive before the main report."
        : "Bu ayar Live Trip içindedir. AI hikâyesi sadece normal görsel Live Trip raporu gönderildikten sonra gider. Park/rapor gecikmesini aynen takip eder; ana rapordan önce gelemez."}</div>
      ${this._toggle("trip_ai_story_enabled", trip.ai_trip_story_enabled, this._lang === "en" ? "Send AI story after Live Trip report" : "Live Trip raporundan sonra AI sürüş hikâyesi gönder")}
      <div class="note">${this._lang === "en"
        ? `Timing: uses the same Live Trip report delay (${this._secondsToMinutesValue(trip.live_trip_finish_delay_seconds ?? 1800)} min) and then sends after the visual report.`
        : `Zamanlama: aynı Live Trip rapor gecikmesini kullanır (${this._secondsToMinutesValue(trip.live_trip_finish_delay_seconds ?? 1800)} dk) ve görsel rapordan sonra gönderir.`}</div>
    `;
    const reportContent = `
      <div class="section-title">${this._t("mapCollection")}</div>
      ${this._toggle("trip_map_enabled", trip.trip_map_enabled, this._t("enableTripMapCollection"))}
      ${this._toggle("trip_map_send_separate_png", trip.trip_map_send_separate_png, this._t("enableSeparateMapPng"))}
      <label>${this._t("tripMapTrackerEntity")}</label>
      <input id="trip_map_tracker_entity" list="tracker_entity_options" value="${this._esc(tracker)}" placeholder="device_tracker.pom" />
      ${this._renderTrackerOptions(tracker)}
      <div class="field-grid">
        <div><label>${this._t("mapSampleInterval")}</label><input id="trip_map_sample_interval_seconds" inputmode="numeric" value="${this._esc(trip.trip_map_sample_interval_seconds ?? 5)}" /><div class="note">${this._t("secondsShort")}</div></div>
        <div><label>${this._t("minimumMovementMeters")}</label><input id="trip_map_min_movement_meters" inputmode="decimal" value="${this._esc(trip.trip_map_min_movement_meters ?? 15)}" /><div class="note">${this._t("metersShort")}</div></div>
      </div>
      <div class="section-title">${this._t("visualFields")}</div>
      <div class="note">${this._t("visualFieldsSub")}</div>
      <div class="visual-grid">
        ${fieldToggles.map(([id, checked, label]) => this._toggle(id, checked, this._t(label))).join("")}
      </div>
    `;
    const content = section === "live_trip" ? liveTripContent : (section === "report_fields" ? reportContent : trackingContent);
    const title = section === "live_trip" ? this._t("liveTripSettings") : (section === "report_fields" ? this._t("visualFields") : this._t("tracking"));
    return `
      <div class="settings-grid wide">
        <section class="card accent">
          <div class="card-h"><div><h2>${this._t("tripReportSettings")}</h2><div class="hint">${this._t("tripReportSettingsSub")}</div></div></div>
          <div class="body">
            <div class="module-list">
              ${moduleCard("tracking", this._t("tracking"), this._t("trackingEmptySub"))}
              ${moduleCard("live_trip", this._t("liveTripSettings"), this._t("liveTripSettingsSub"))}
              ${moduleCard("report_fields", this._t("visualFields"), this._t("visualFieldsSub"))}
            </div>
            <div class="test-card">
              <h3>${this._t("tripTelegramTest")}</h3>
              <p>${this._t("tripTelegramTestSub")}</p>
              <div class="actions wrap">
                <button id="sendTestTripReportBtn">${this._t("sendTestTripReport")}</button>
                <button id="startLiveTripTestBtn" class="secondary">${this._t("startLiveTripTest")}</button>
                <button id="finishLiveTripTestBtn" class="secondary">${this._t("finishLiveTripTest")}</button>
                <button id="resetLiveTripTestBtn" class="secondary">${this._t("resetLiveTripTest")}</button>
              </div>
              <div class="note">${this._t("liveTripTestSubNote")}</div>
              <div class="note">${this._t("testTripNoLedger")}</div>
              ${this._renderLiveTripDebugPanel()}
            </div>
          </div>
        </section>
        <section class="card">
          <div class="card-h"><div><h2>${this._esc(title)}</h2><div class="hint">${this._t("tripReportSettingsSub")}</div></div></div>
          <div class="body">
            ${content}
            <div class="actions"><button id="saveTripSettingsBtn">${this._t("saveTripSettings")}</button><button id="refreshBtn" class="secondary">${this._t("refresh")}</button></div>
          </div>
        </section>
      </div>
    `;
  }

  _renderComingSoonSettings() {
    return `<div class="coming">${this._t("comingSoon")}</div>`;
  }


  _dashboardPreview(url) {
    const value = String(url || "").trim();
    if (!value) return `<div class="dashboard-preview empty">—</div>`;
    return `<img class="dashboard-preview" src="${this._esc(value)}" alt="preview" />`;
  }

  _optionObjectToPairs(options) {
    if (Array.isArray(options)) {
      return options.map((item) => {
        if (Array.isArray(item)) return [item[0], item[1]];
        return [item?.value ?? "", item?.label ?? item?.value ?? ""];
      }).filter(([value]) => String(value || "").length);
    }
    return Object.entries(options || {}).map(([value, label]) => [value, label]);
  }

  _dashboardSelectFallbackOptions(id = "") {
    const key = String(id || "");
    const top = [
      ["elevation", "Elevation"],
      ["power", "Power"],
      ["speed", "Speed"],
      ["battery_level", "Battery level"],
      ["est_range", "Estimated range"],
      ["rated_range", "Rated range"],
      ["energy_remaining", "Energy remaining"],
      ["inside_temp", "Inside temperature"],
      ["outside_temp", "Outside temperature"],
      ["battery_temp", "Battery/module temperature"],
      ["odometer", "Odometer"],
      ["battery_heater", "Battery heater"],
      ["empty", "Empty / hidden"],
    ];
    const center = [
      ["speed", "Speed"],
      ["battery_level", "Battery level"],
      ["power", "Power"],
      ["energy_remaining", "Energy remaining"],
      ["empty", "Empty / hidden"],
    ];
    const sidebar = [
      ["empty", "Empty / hidden"],
      ["honk", "Honk horn"],
      ["flash_lights", "Flash lights"],
      ["sentry", "Sentry mode"],
      ["horn", "Horn"],
      ["fart", "Fart"],
      ["windows", "Windows"],
      ["rear_middle_seat_heater", "Rear middle seat heater"],
      ["rear_right_seat_heater", "Rear right seat heater"],
      ["rear_left_seat_heater", "Rear left seat heater"],
      ["right_seat_heater", "Right seat heater"],
      ["left_seat_heater", "Left seat heater"],
      ["charge_cable_lock", "Charge cable lock"],
      ["charge_port", "Charge port"],
      ["valet_mode", "Valet mode"],
      ["wake", "Wake vehicle"],
      ["home_entity_1", "Home entity 1"],
      ["home_entity_2", "Home entity 2"],
    ];
    const location = [
      ["auto_short", "Auto short address"],
      ["neighbourhood", "Neighborhood / quarter"],
      ["suburb", "Suburb"],
      ["district", "District"],
      ["city", "City / town"],
      ["road", "Road / street"],
    ];
    const bottom = [
      ["energy_remaining", "Energy remaining"],
      ["inside_temp", "Inside temperature"],
      ["battery_temp", "Battery/module temperature"],
      ["outside_temp", "Outside temperature"],
      ["odometer", "Odometer"],
      ["battery_heater", "Battery heater"],
      ["empty", "Empty / hidden"],
    ];
    if (key.includes("top_center")) return center;
    if (key.includes("top_")) return top;
    if (key.includes("sidebar_slot")) return sidebar;
    if (key.includes("location_display")) return location;
    if (key.includes("bottom_slot")) return bottom;
    return [["empty", "Empty / hidden"]];
  }

  _renderDashboardSelect(id, value, options) {
    const pairs = this._optionObjectToPairs(options);
    const finalPairs = pairs.length ? pairs : this._dashboardSelectFallbackOptions(id);
    const finalValue = String(value || (finalPairs[0]?.[0] ?? ""));
    return `<select id="${this._esc(id)}">${this._selectOptions(finalValue, finalPairs)}</select>`;
  }

  _personEntityOptions(selected = "") {
    const ids = Object.keys(this._hass?.states || {}).filter((id) => id.startsWith("person.")).sort((a, b) => this._entityDisplay(a).localeCompare(this._entityDisplay(b)));
    const pairs = ids.map((id) => [id, this._entityDisplay(id)]);
    if (selected && !pairs.some(([id]) => id === selected)) pairs.unshift([selected, selected]);
    return pairs;
  }

  _renderYoutubeDrivingBackgroundCard(cfg = {}) {
    return `
      <div class="dashboard-upload-card youtube-bg-card">
        <div class="dashboard-upload-main">
          <div>
            <div class="dashboard-upload-title">${this._t("dashboardYoutubeDrivingTitle")}</div>
            <div class="hint">${this._t("dashboardYoutubeDrivingSub")}</div>
          </div>
          <div class="dashboard-toggle-row">
            ${this._toggle("dashboard_youtube_driving_bg_enabled", Boolean(cfg.enabled), this._t("dashboardYoutubeDrivingEnabled"))}
            ${this._toggle("dashboard_youtube_driving_bg_mute", cfg.mute !== false, this._t("dashboardYoutubeMute"))}
            ${this._toggle("dashboard_youtube_driving_bg_loop", cfg.loop !== false, this._t("dashboardYoutubeLoop"))}
          </div>
          <div class="youtube-settings-grid">
            <div class="field-wrap"><label>${this._t("dashboardYoutubeVideo")}</label><input id="dashboard_youtube_driving_bg_video" value="${this._esc(cfg.video || "")}" placeholder="https://www.youtube.com/watch?v=..."></div>
            <div class="field-wrap"><label>Tesla Safe kalite</label><select id="dashboard_youtube_driving_bg_quality">
              <option value="360" ${String(cfg.quality || "480") === "360" ? "selected" : ""}>360p</option>
              <option value="480" ${String(cfg.quality || "480") === "480" ? "selected" : ""}>480p</option>
              <option value="720" ${String(cfg.quality || "480") === "720" ? "selected" : ""}>720p</option>
              <option value="1080_lite" ${String(cfg.quality || "480") === "1080_lite" ? "selected" : ""}>1080 Lite</option>
              <option value="1080" ${String(cfg.quality || "480") === "1080" ? "selected" : ""}>1080 Max</option>
            </select></div>
            <div class="field-wrap"><label>${this._t("dashboardYoutubeStartSeconds")}</label><input id="dashboard_youtube_driving_bg_start_seconds" type="number" min="0" step="1" value="${this._esc(String(cfg.start_seconds ?? 0))}"></div>
          </div>
          <div class="note">Tesla Safe YouTube: HA içinde yt-dlp + ffmpeg ile WebSocket MPEG-TS üretir, dashboard ise JSMpeg Canvas2D ile gösterir. Reconnect olursa oynatıcı kaldığı yere yakın yeniden bağlanır.</div>
        </div>
      </div>
    `;
  }

  _renderDashboardUploadCard(slot, title, currentUrl) {
    return `
      <div class="dashboard-upload-card">
        <div class="dashboard-upload-media">
          ${this._dashboardPreview(currentUrl)}
        </div>
        <div class="dashboard-upload-main">
          <div class="dashboard-upload-title">${this._esc(title)}</div>
          <div class="hint">${this._t("dashboardCurrentAsset")}</div>
          <div class="dashboard-current-url">${this._esc(currentUrl || "—")}</div>
        </div>
        <div class="dashboard-upload-side">
          <div class="dashboard-upload-actions">
            <label class="button secondary file-btn" for="dashboard_file_${this._esc(slot)}">${this._t("dashboardChooseFile")}</label>
            <input id="dashboard_file_${this._esc(slot)}" type="file" accept=".png,.jpg,.jpeg,.webp,.gif,image/png,image/jpeg,image/webp,image/gif" />
            <button class="secondary" id="dashboard_upload_btn_${this._esc(slot)}">${this._t("dashboardUpload")}</button>
            <button class="secondary" id="dashboard_reset_btn_${this._esc(slot)}">${this._t("dashboardResetDefault")}</button>
          </div>
          <div class="note" id="dashboard_file_note_${this._esc(slot)}">${this._t("dashboardNoFileSelected")}</div>
        </div>
      </div>
    `;
  }


  _statusPill(installed) {
    return `<span class="resource-status ${installed ? "ok" : "missing"}">${this._esc(installed ? this._t("dashboardInstalled") : this._t("dashboardMissing"))}</span>`;
  }

  _renderResourceRows(items = [], { showPaths = false } = {}) {
    if (!Array.isArray(items) || !items.length) return `<div class="note">—</div>`;
    return items.map((item) => `
      <div class="resource-row ${item.installed ? "ok" : "missing"}">
        <div class="resource-main">
          <div class="resource-title"><b>${this._esc(item.name || item.type || "")}</b>${this._statusPill(Boolean(item.installed))}</div>
          <div class="resource-meta"><span>${this._esc(this._t("dashboardType"))}: ${this._esc(item.type || "module")}</span></div>
          ${item.description ? `<div class="note">${this._esc(item.description)}</div>` : ""}
          ${item.url ? `<div class="resource-url">${this._esc(item.url)}</div>` : ""}
          ${item.github ? `<div class="resource-url"><b>${this._esc(this._t("dashboardGithub"))}:</b> ${this._esc(item.github)}</div>` : ""}
          ${showPaths && Array.isArray(item.found_paths) && item.found_paths.length ? `<div class="resource-url"><b>${this._esc(this._t("dashboardFoundPath"))}:</b> ${this._esc(item.found_paths.join(", "))}</div>` : ""}
          ${showPaths && Array.isArray(item.local_checks) && item.local_checks.length ? `<details class="resource-details"><summary>${this._esc(this._t("dashboardCheckPaths"))}</summary><div>${item.local_checks.map((path) => `<code>${this._esc(path)}</code>`).join("")}</div></details>` : ""}
        </div>
      </div>
    `).join("");
  }

  _renderDashboardGeneralSettings(dashboard) {
    const status = dashboard.resources_status || {};
    const summary = status.summary || {};
    return `
      <div class="settings-hero"><b>${this._t("dashboardGeneralSettings")}</b><span class="muted">${this._t("dashboardMenuGeneralSub")}</span></div>
      <div class="resource-summary-grid">
        <div><span>${this._t("dashboardResourcesTitle")}</span><b>${this._esc(summary.resources_missing ?? 0)} / ${this._esc(summary.resources_total ?? 0)}</b><small>${this._t("dashboardMissing")}</small></div>
        <div><span>${this._t("dashboardCustomCardInfo")}</span><b>${this._esc(summary.dependencies_missing ?? 0)} / ${this._esc(summary.dependencies_total ?? 0)}</b><small>${this._t("dashboardMissing")}</small></div>
        <div><span>${this._t("dashboardResourceStorage")}</span><b>${status.storage_exists ? "OK" : "—"}</b><small>${this._esc(status.storage_path || "")}</small></div>
      </div>
      <div class="actions dashboard-resource-actions">
        <button id="installDashboardResourcesBtn">${this._t("dashboardInstallResources")}</button>
        <button id="showMissingDashboardCardsBtn" class="secondary">${this._t("dashboardShowMissingCards")}</button>
      </div>
      <div class="dashboard-info-grid">
        <section class="dashboard-info-panel">
          <h3>${this._t("dashboardResourceInfo")}</h3>
          <p>${this._t("dashboardResourcesSub")}</p>
          ${this._renderResourceRows(status.resources || [])}
        </section>
        <section class="dashboard-info-panel">
          <h3>${this._t("dashboardCustomCardInfo")}</h3>
          <p>${this._t("dashboardMenuGeneralSub")}</p>
          ${this._renderResourceRows(status.dependencies || [], { showPaths: true })}
        </section>
      </div>
    `;
  }

  _renderDashboardRange(id, value, label, min = 0.7, max = 1.6, step = 0.05) {
    const v = Number(value ?? 1) || 1;
    return `
      <div class="range-field">
        <div class="range-head"><label>${this._esc(label)}</label><b id="${id}_value">${v.toFixed(2)}x</b></div>
        <input id="${id}" type="range" min="${this._esc(String(min))}" max="${this._esc(String(max))}" step="${this._esc(String(step))}" value="${this._esc(String(v))}">
      </div>
    `;
  }

  _renderDashboardSettingsContentSafe(dashboard, section) {
    try {
      return this._renderDashboardSettingsContent(dashboard, section);
    } catch (err) {
      const message = String(err?.message || err || "unknown render error");
      this._pushDebugEvent("error", "Dashboard section render failed", { section, error: message });
      return `<div class="error">Dashboard section render failed: ${this._esc(message)}</div>`;
    }
  }

  _renderDashboardSettingsContent(dashboard, section) {
    const fullscreen = dashboard.fullscreen || {};
    const images = dashboard.images || {};
    const top = dashboard.top_area || {};
    const topSlots = top.slots || {};
    const topScales = top.font_scales || {};
    const topScaleMin = Number(top.font_scale_min ?? 0.7);
    const topScaleMax = Number(top.font_scale_max ?? 1.6);
    const topScaleStep = Number(top.font_scale_step ?? 0.05);
    const topOptions = (Array.isArray(top.options_list) && top.options_list.length) ? top.options_list : (top.options || {});
    const centerOptions = (Array.isArray(top.center_options_list) && top.center_options_list.length) ? top.center_options_list : (top.center_options || topOptions);
    const sidebar = dashboard.sidebar || {};
    const sidebarSlots = sidebar.slots || {};
    const sidebarOptions = (Array.isArray(sidebar.options_list) && sidebar.options_list.length) ? sidebar.options_list : (sidebar.options || {});
    const bottom = dashboard.bottom_bar || {};
    const bottomSlots = bottom.slots || {};
    const bottomToggles = bottom.toggles || {};
    const bottomSlotOptions = (Array.isArray(bottom.slot_options_list) && bottom.slot_options_list.length) ? bottom.slot_options_list : (bottom.slot_options || {});
    const locationOptions = (Array.isArray(bottom.location_display_modes_list) && bottom.location_display_modes_list.length) ? bottom.location_display_modes_list : (bottom.location_display_modes || {});
    const map = dashboard.map || {};
    const person = dashboard.person_track || {};
    if (section === "general") return this._renderDashboardGeneralSettings(dashboard);
    if (section === "top_area") {
      return `
        <div class="settings-hero"><b>${this._t("dashboardTopAreaSettings")}</b><span class="muted">${this._t("dashboardTopHelp")}</span></div>
        <div class="field-grid">
          <div><label>top_left_slot_1</label>${this._renderDashboardSelect("dashboard_top_left_slot_1", topSlots.top_left_slot_1 || "elevation", topOptions)}</div>
          <div><label>top_left_slot_2</label>${this._renderDashboardSelect("dashboard_top_left_slot_2", topSlots.top_left_slot_2 || "power", topOptions)}</div>
          <div><label>top_center_slot</label>${this._renderDashboardSelect("dashboard_top_center_slot", topSlots.top_center_slot || "speed", centerOptions)}</div>
          <div><label>top_right_slot_1</label>${this._renderDashboardSelect("dashboard_top_right_slot_1", topSlots.top_right_slot_1 || "battery_level", topOptions)}</div>
          <div><label>top_right_slot_2</label>${this._renderDashboardSelect("dashboard_top_right_slot_2", topSlots.top_right_slot_2 || "est_range", topOptions)}</div>
        </div>
        <div class="section-title">${this._t("dashboardTopFontScales")}</div>
        <div class="range-grid">
          ${this._renderDashboardRange("dashboard_top_font_scale", topScales.top_font_scale ?? 1, this._t("dashboardTopFontGlobal"), topScaleMin, topScaleMax, topScaleStep)}
          ${this._renderDashboardRange("dashboard_top_left_font_scale", topScales.top_left_font_scale ?? 1, this._t("dashboardTopFontLeft"), topScaleMin, topScaleMax, topScaleStep)}
          ${this._renderDashboardRange("dashboard_top_center_font_scale", topScales.top_center_font_scale ?? 1, this._t("dashboardTopFontCenter"), topScaleMin, topScaleMax, topScaleStep)}
          ${this._renderDashboardRange("dashboard_top_right_font_scale", topScales.top_right_font_scale ?? 1, this._t("dashboardTopFontRight"), topScaleMin, topScaleMax, topScaleStep)}
        </div>
        <div class="visual-grid dashboard-toggle-grid">
          ${this._toggle("dashboard_rebuild_on_save", fullscreen.rebuild_on_save, this._t("rebuild_on_save"))}
        </div>
        <div class="actions"><button id="saveDashboardSettingsBtn">${this._t("saveDashboardSettings")}</button><button id="refreshBtn" class="secondary">${this._t("refresh")}</button></div>
      `;
    }
    if (section === "sidebar") {
      return `
        <div class="settings-hero"><b>${this._t("dashboardSidebarSettings")}</b><span class="muted">${this._t("dashboardSidebarHelp")}</span></div>
        <div class="field-grid">
          ${Array.from({length: 8}, (_, idx) => {
            const key = `sidebar_slot_${idx + 1}`;
            return `<div><label>${key}</label>${this._renderDashboardSelect(`dashboard_${key}`, sidebarSlots[key] || "empty", sidebarOptions)}</div>`;
          }).join("")}
        </div>
        <div class="actions"><button id="saveDashboardSettingsBtn">${this._t("saveDashboardSettings")}</button><button id="refreshBtn" class="secondary">${this._t("refresh")}</button></div>
      `;
    }
    if (section === "bottom_bar") {
      return `
        <div class="settings-hero"><b>${this._t("dashboardBottomBarSettings")}</b><span class="muted">${this._t("dashboardMenuBottomBarSub")}</span></div>
        <div class="field-grid">
          <div><label>${this._t("location_display_mode")}</label>${this._renderDashboardSelect("dashboard_location_display_mode", bottom.location_display_mode || "auto_short", locationOptions)}</div>
        </div>
        <div class="note">${this._t("bottomSlotsLiveNote")}</div>
        <div class="visual-grid dashboard-toggle-grid">
          ${this._toggle("dashboard_show_bottom_map_toggle", bottomToggles.show_bottom_map_toggle, "show_bottom_map_toggle")}
          ${this._toggle("dashboard_show_bottom_controls", bottomToggles.show_bottom_controls, "show_bottom_controls")}
          ${this._toggle("dashboard_show_bottom_person_toggle", bottomToggles.show_bottom_person_toggle, "show_bottom_person_toggle")}
          ${this._toggle("dashboard_show_bottom_charging", bottomToggles.show_bottom_charging, "show_bottom_charging")}
          ${this._toggle("dashboard_show_bottom_person_track_1", bottomToggles.show_bottom_person_track_1, "show_bottom_person_track_1")}
          ${this._toggle("dashboard_show_bottom_person_track_2", bottomToggles.show_bottom_person_track_2, "show_bottom_person_track_2")}
          ${this._toggle("dashboard_show_bottom_person_track_3", bottomToggles.show_bottom_person_track_3, "show_bottom_person_track_3")}
          ${this._toggle("dashboard_rebuild_on_save", fullscreen.rebuild_on_save, this._t("rebuild_on_save"))}
        </div>
        <div class="actions"><button id="saveDashboardSettingsBtn">${this._t("saveDashboardSettings")}</button><button id="refreshBtn" class="secondary">${this._t("refresh")}</button></div>
      `;
    }
    if (section === "map") {
      return `
        <div class="settings-hero"><b>${this._t("dashboardMapSettings")}</b><span class="muted">${this._t("dashboardMenuMapSub")}</span></div>
        <div class="field-grid">
          <div><label>${this._t("tesla_map_hours_to_show")}</label><input id="dashboard_tesla_map_hours_to_show" inputmode="numeric" value="${this._esc(map.tesla_map_hours_to_show ?? 1)}" /><div class="note">0-24</div></div>
          <div><label>${this._t("person_map_hours_to_show")}</label><input id="dashboard_person_map_hours_to_show" inputmode="numeric" value="${this._esc(map.person_map_hours_to_show ?? 0)}" /><div class="note">0-24</div></div>
        </div>
        <div class="visual-grid dashboard-toggle-grid">${this._toggle("dashboard_rebuild_on_save", fullscreen.rebuild_on_save, this._t("rebuild_on_save"))}</div>
        <div class="actions"><button id="saveDashboardSettingsBtn">${this._t("saveDashboardSettings")}</button><button id="refreshBtn" class="secondary">${this._t("refresh")}</button></div>
      `;
    }
    if (section === "person_track") {
      const personSelect = (idx) => this._renderDashboardSelect(`dashboard_person_track_${idx}_entity`, person[`person_track_${idx}_entity`] || "", [["", this._t("entityNotSelected")], ...this._personEntityOptions(person[`person_track_${idx}_entity`] || "")]);
      return `
        <div class="settings-hero"><b>${this._t("dashboardPersonTrackSettings")}</b><span class="muted">${this._t("dashboardMenuPersonTrackSub")}</span></div>
        <div class="visual-grid dashboard-toggle-grid">
          ${this._toggle("dashboard_person_track_enabled", person.person_track_enabled, this._t("person_track_enabled"))}
          ${this._toggle("dashboard_person_track_show_button", person.person_track_show_button, this._t("person_track_show_button"))}
        </div>
        <div class="field-grid"><div><label>${this._t("person_track_hours_to_show")}</label><input id="dashboard_person_track_hours_to_show" inputmode="numeric" value="${this._esc(person.person_track_hours_to_show ?? 15)}" /><div class="note">0-24</div></div></div>
        ${[1,2,3].map((idx) => `
          <div class="person-track-card">
            <div class="section-title">Person Track ${idx}</div>
            <div class="field-grid">
              <div><label>${this._t(`person_track_${idx}_entity`)}</label>${personSelect(idx)}</div>
              <div><label>${this._t(`person_track_${idx}_name`)}</label><input id="dashboard_person_track_${idx}_name" value="${this._esc(person[`person_track_${idx}_name`] || `Person ${idx}`)}" /></div>
            </div>
            ${this._toggle(`dashboard_person_track_${idx}_enabled`, person[`person_track_${idx}_enabled`], this._t(`person_track_${idx}_enabled`))}
          </div>
        `).join("")}
        <div class="visual-grid dashboard-toggle-grid">${this._toggle("dashboard_rebuild_on_save", fullscreen.rebuild_on_save, this._t("rebuild_on_save"))}</div>
        <div class="actions"><button id="saveDashboardSettingsBtn">${this._t("saveDashboardSettings")}</button><button id="refreshBtn" class="secondary">${this._t("refresh")}</button></div>
      `;
    }
    if (section === "backgrounds") {
      return `
        <div class="settings-hero"><b>${this._t("dashboardBackgrounds")}</b><span class="muted">${this._t("dashboardSettingsSub")}</span></div>
        <div class="note">${this._t("dashboardAllowedTypes")}</div>
        <div class="dashboard-upload-grid">
          ${this._renderDashboardUploadCard("parked", this._t("dashboardBackgroundParked"), images.parked || "")}
          ${this._renderDashboardUploadCard("charging", this._t("dashboardBackgroundCharging"), images.charging || "")}
          ${this._renderDashboardUploadCard("driving", this._t("dashboardBackgroundDriving"), images.driving || "")}
          ${this._renderYoutubeDrivingBackgroundCard(dashboard.youtube_driving_background || {})}
        </div>
        <div class="sticky-save-row">
          <button class="primary" id="saveDashboardSettingsBtnBackground">${this._t("saveDashboardSettings")}</button>
          <button id="reloadDashboardSettingsBtnBackground">${this._t("reload")}</button>
        </div>
      `;
    }
    return `
      <div class="settings-hero"><b>${this._t("dashboardFullscreenSettings")}</b><span class="muted">${this._t("dashboardMenuFullscreenSub")}</span></div>
      <div class="visual-grid dashboard-toggle-grid">
        ${this._toggle("dashboard_fullscreen_enabled", fullscreen.fullscreen_enabled, this._t("fullscreen_enabled"))}
        ${this._toggle("dashboard_fullscreen_hide_header", fullscreen.fullscreen_hide_header, this._t("fullscreen_hide_header"))}
        ${this._toggle("dashboard_fullscreen_hide_sidebar", fullscreen.fullscreen_hide_sidebar, this._t("fullscreen_hide_sidebar"))}
        ${this._toggle("dashboard_fullscreen_disable_scroll", fullscreen.fullscreen_disable_scroll, this._t("fullscreen_disable_scroll"))}
        ${this._toggle("dashboard_fullscreen_show_button", fullscreen.fullscreen_show_button, this._t("fullscreen_show_button"))}
        ${this._toggle("dashboard_rebuild_on_save", fullscreen.rebuild_on_save, this._t("rebuild_on_save"))}
      </div>
      <div class="actions"><button id="saveDashboardSettingsBtn">${this._t("saveDashboardSettings")}</button><button id="refreshBtn" class="secondary">${this._t("refresh")}</button></div>
    `;
  }

  _renderDashboardSettings() {
    const dashboard = this._settingsData?.dashboard_settings || {};
    const section = this._dashboardSettingsSection || "general";
    const moduleCard = (id, title, sub) => `<button type="button" id="dashboardSection_${this._esc(id)}" class="module-card ${section === id ? "active" : ""}" data-dashboard-section="${this._esc(id)}"><b>${this._esc(title)}</b><span class="muted">${this._esc(sub)}</span></button>`;
    const titleMap = {
      general: this._t("dashboardGeneralSettings"),
      fullscreen: this._t("dashboardFullscreenSettings"),
      top_area: this._t("dashboardTopAreaSettings"),
      sidebar: this._t("dashboardSidebarSettings"),
      bottom_bar: this._t("dashboardBottomBarSettings"),
      map: this._t("dashboardMapSettings"),
      person_track: this._t("dashboardPersonTrackSettings"),
      backgrounds: this._t("dashboardBackgrounds"),
    };
    return `
      <div class="settings-grid wide">
        <section class="card accent">
          <div class="card-h"><div><h2>${this._t("dashboardSettings")}</h2><div class="hint">${this._t("dashboardSettingsSub")}</div></div></div>
          <div class="body">
            <div class="module-list">
              ${moduleCard("general", this._t("dashboardMenuGeneral"), this._t("dashboardMenuGeneralSub"))}
              ${moduleCard("fullscreen", this._t("dashboardMenuFullscreen"), this._t("dashboardMenuFullscreenSub"))}
              ${moduleCard("top_area", this._t("dashboardMenuTopArea"), this._t("dashboardMenuTopAreaSub"))}
              ${moduleCard("sidebar", this._t("dashboardMenuSidebar"), this._t("dashboardMenuSidebarSub"))}
              ${moduleCard("bottom_bar", this._t("dashboardMenuBottomBar"), this._t("dashboardMenuBottomBarSub"))}
              ${moduleCard("map", this._t("dashboardMenuMap"), this._t("dashboardMenuMapSub"))}
              ${moduleCard("person_track", this._t("dashboardMenuPersonTrack"), this._t("dashboardMenuPersonTrackSub"))}
              ${moduleCard("backgrounds", this._t("dashboardMenuBackgrounds"), this._t("dashboardMenuBackgroundsSub"))}
            </div>
          </div>
        </section>
        <section class="card">
          <div class="card-h"><div><h2>${this._esc(titleMap[section] || this._t("dashboardSettings"))}</h2><div class="hint">${this._t("dashboardSettingsSub")}</div></div></div>
          <div class="body">${this._renderDashboardSettingsContentSafe(dashboard, section)}</div>
        </section>
      </div>
    `;
  }

  _readDashboardSettingsForm() {
    const current = this._settingsData?.dashboard_settings || {};
    const root = this.shadowRoot;
    const checked = (id, fallback) => root.getElementById(id)?.checked ?? Boolean(fallback);
    const value = (id, fallback) => root.getElementById(id)?.value || fallback || "";
    return {
      youtube_driving_background: {
        ...(current.youtube_driving_background || {}),
        enabled: checked("dashboard_youtube_driving_bg_enabled", current.youtube_driving_background?.enabled),
        video: value("dashboard_youtube_driving_bg_video", current.youtube_driving_background?.video || ""),
        start_seconds: this._number(root.getElementById("dashboard_youtube_driving_bg_start_seconds")?.value ?? current.youtube_driving_background?.start_seconds ?? 0),
        mute: checked("dashboard_youtube_driving_bg_mute", current.youtube_driving_background?.mute ?? true),
        loop: checked("dashboard_youtube_driving_bg_loop", current.youtube_driving_background?.loop ?? true),
        quality: value("dashboard_youtube_driving_bg_quality", current.youtube_driving_background?.quality || "480"),
      },
      fullscreen: {
        ...(current.fullscreen || {}),
        fullscreen_enabled: checked("dashboard_fullscreen_enabled", current.fullscreen?.fullscreen_enabled),
        fullscreen_hide_header: checked("dashboard_fullscreen_hide_header", current.fullscreen?.fullscreen_hide_header),
        fullscreen_hide_sidebar: checked("dashboard_fullscreen_hide_sidebar", current.fullscreen?.fullscreen_hide_sidebar),
        fullscreen_disable_scroll: checked("dashboard_fullscreen_disable_scroll", current.fullscreen?.fullscreen_disable_scroll),
        fullscreen_show_button: checked("dashboard_fullscreen_show_button", current.fullscreen?.fullscreen_show_button),
        rebuild_on_save: checked("dashboard_rebuild_on_save", current.fullscreen?.rebuild_on_save),
      },
      top_area: {
        slots: {
          ...(current.top_area?.slots || {}),
          top_left_slot_1: value("dashboard_top_left_slot_1", current.top_area?.slots?.top_left_slot_1),
          top_left_slot_2: value("dashboard_top_left_slot_2", current.top_area?.slots?.top_left_slot_2),
          top_center_slot: value("dashboard_top_center_slot", current.top_area?.slots?.top_center_slot),
          top_right_slot_1: value("dashboard_top_right_slot_1", current.top_area?.slots?.top_right_slot_1),
          top_right_slot_2: value("dashboard_top_right_slot_2", current.top_area?.slots?.top_right_slot_2),
        },
        font_scales: {
          ...(current.top_area?.font_scales || {}),
          top_font_scale: this._number(root.getElementById("dashboard_top_font_scale")?.value ?? current.top_area?.font_scales?.top_font_scale ?? 1),
          top_left_font_scale: this._number(root.getElementById("dashboard_top_left_font_scale")?.value ?? current.top_area?.font_scales?.top_left_font_scale ?? 1),
          top_center_font_scale: this._number(root.getElementById("dashboard_top_center_font_scale")?.value ?? current.top_area?.font_scales?.top_center_font_scale ?? 1),
          top_right_font_scale: this._number(root.getElementById("dashboard_top_right_font_scale")?.value ?? current.top_area?.font_scales?.top_right_font_scale ?? 1),
        },
      },
      sidebar: {
        slots: Object.fromEntries(Array.from({length: 8}, (_, idx) => {
          const key = `sidebar_slot_${idx + 1}`;
          return [key, value(`dashboard_${key}`, current.sidebar?.slots?.[key] || "empty")];
        })),
      },
      bottom_bar: {
        location_display_mode: value("dashboard_location_display_mode", current.bottom_bar?.location_display_mode || "auto_short"),
        slots: {
          bottom_slot_1: value("dashboard_bottom_slot_1", current.bottom_bar?.slots?.bottom_slot_1 || "energy_remaining"),
          bottom_slot_2: value("dashboard_bottom_slot_2", current.bottom_bar?.slots?.bottom_slot_2 || "inside_temp"),
          bottom_slot_3: value("dashboard_bottom_slot_3", current.bottom_bar?.slots?.bottom_slot_3 || "battery_temp"),
        },
        toggles: {
          show_bottom_map_toggle: checked("dashboard_show_bottom_map_toggle", current.bottom_bar?.toggles?.show_bottom_map_toggle),
          show_bottom_controls: checked("dashboard_show_bottom_controls", current.bottom_bar?.toggles?.show_bottom_controls),
          show_bottom_person_toggle: checked("dashboard_show_bottom_person_toggle", current.bottom_bar?.toggles?.show_bottom_person_toggle),
          show_bottom_charging: checked("dashboard_show_bottom_charging", current.bottom_bar?.toggles?.show_bottom_charging),
          show_bottom_person_track_1: checked("dashboard_show_bottom_person_track_1", current.bottom_bar?.toggles?.show_bottom_person_track_1),
          show_bottom_person_track_2: checked("dashboard_show_bottom_person_track_2", current.bottom_bar?.toggles?.show_bottom_person_track_2),
          show_bottom_person_track_3: checked("dashboard_show_bottom_person_track_3", current.bottom_bar?.toggles?.show_bottom_person_track_3),
        },
      },
      map: {
        tesla_map_hours_to_show: this._number(root.getElementById("dashboard_tesla_map_hours_to_show")?.value ?? current.map?.tesla_map_hours_to_show ?? 1),
        person_map_hours_to_show: this._number(root.getElementById("dashboard_person_map_hours_to_show")?.value ?? current.map?.person_map_hours_to_show ?? 0),
      },
      person_track: {
        person_track_enabled: checked("dashboard_person_track_enabled", current.person_track?.person_track_enabled),
        person_track_show_button: checked("dashboard_person_track_show_button", current.person_track?.person_track_show_button),
        person_track_hours_to_show: this._number(root.getElementById("dashboard_person_track_hours_to_show")?.value ?? current.person_track?.person_track_hours_to_show ?? 15),
        person_track_1_entity: value("dashboard_person_track_1_entity", current.person_track?.person_track_1_entity || ""),
        person_track_1_name: value("dashboard_person_track_1_name", current.person_track?.person_track_1_name || "Cavidan"),
        person_track_1_enabled: checked("dashboard_person_track_1_enabled", current.person_track?.person_track_1_enabled),
        person_track_2_entity: value("dashboard_person_track_2_entity", current.person_track?.person_track_2_entity || ""),
        person_track_2_name: value("dashboard_person_track_2_name", current.person_track?.person_track_2_name || "Ali"),
        person_track_2_enabled: checked("dashboard_person_track_2_enabled", current.person_track?.person_track_2_enabled),
        person_track_3_entity: value("dashboard_person_track_3_entity", current.person_track?.person_track_3_entity || ""),
        person_track_3_name: value("dashboard_person_track_3_name", current.person_track?.person_track_3_name || "Person 3"),
        person_track_3_enabled: checked("dashboard_person_track_3_enabled", current.person_track?.person_track_3_enabled),
      },
    };
  }


  async _refreshDashboardResources(action = "status") {
    if (!this._hass) return;
    this._loading = true;
    this._error = "";
    this._render();
    try {
      const payload = await this._hass.callApi("POST", "pom_tesla_report/dashboard_resources", { action });
      const status = payload?.resources_status || {};
      this._settingsData = this._normalizeSettingsPayload({
        ...(this._settingsData || {}),
        dashboard_settings: {
          ...((this._settingsData || {}).dashboard_settings || {}),
          resources_status: status,
        },
      });
      this._status = this._t(action === "install_resources" ? "dashboardResourcesInstallDone" : "dashboardResourcesUpdated");
    } catch (err) {
      this._error = this._formatError(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  async _saveDashboardSettings() {
    if (!this._hass) return;
    const dashboard_settings = this._readDashboardSettingsForm();
    this._loading = true;
    this._error = "";
    this._render();
    try {
      const payload = await this._hass.callApi("POST", "pom_tesla_report/settings", { dashboard_settings });
      this._settingsData = this._applySettingsSaveResponse(payload, { dashboard_settings });
      this._status = payload?.dashboard_rebuild_started ? this._t("dashboardSettingsSavedRebuild") : this._t("dashboardSettingsSaved");
    } catch (err) {
      this._error = this._formatError(err);
    } finally {
      this._loading = false;
      this._render();
    }
  }

  _renderSettings() {
    const content = this._activeSettingsTab === "general"
      ? this._renderGeneralSettings()
      : this._activeSettingsTab === "charging"
        ? this._renderChargingSettings()
      : this._activeSettingsTab === "trip"
        ? this._renderTripSettings()
        : this._activeSettingsTab === "ai_settings"
          ? this._renderAISettings()
          : this._activeSettingsTab === "telegram"
            ? this._renderTelegramSettings()
            : this._activeSettingsTab === "ai"
              ? this._renderAIEntityManagerSettings()
              : this._activeSettingsTab === "automations"
                ? this._renderAutomationSettings()
                : this._activeSettingsTab === "dashboard"
                  ? this._renderDashboardSettings()
                  : this._renderComingSoonSettings();
    return `
      <div class="settings-shell">
        <div class="settings-head">
          <div class="settings-title"><div class="settings-close">×</div><span>${this._t("settings")}</span></div>
          <div class="online">${this._t("settingsOnline")}</div>
        </div>
        ${this._renderSettingsNav()}
        <div class="settings-content">${content}</div>
      </div>
    `;
  }

  _renderActive() {
    if (this._activeTab === "settings") return this._renderSettings();
    if (this._activeTab === "manual") {
      return `
        <div class="grid">
          <section class="card">
            <div class="card-h">
              <div><h2>${this._t("manualTrackingRecords")}</h2><div class="hint">${this._t("manualTrackingRecordsSub")}</div></div>
              <div class="toolbar">
                ${this._renderDateFilterToolbar("manual")}
                <button id="refreshBtn" class="secondary">${this._t("refresh")}</button>
              </div>
            </div>
            <div class="body">
              ${this._renderManualTrackingSummary()}
              ${this._renderManualTrackingRecords()}
            </div>
          </section>
          <section class="card">
            <div class="card-h"><h2>${this._t("manualTrackingDetails")}</h2></div>
            <div class="body">
              ${this._renderManualTrackingDetails()}
            </div>
          </section>
        </div>
      `;
    }
    if (this._activeTab === "trip") {
      return `
        <div class="grid">
          <section class="card">
            <div class="card-h">
              <h2>${this._t("tripRecords")}</h2>
              <div class="toolbar">
                ${this._renderDateFilterToolbar("trip")}
                <button id="refreshBtn" class="secondary">${this._t("refresh")}</button>
              </div>
            </div>
            <div class="body">
              ${this._renderTripSummary()}
              ${this._renderTripRecords()}
            </div>
          </section>
          <section class="card">
            <div class="card-h"><h2>${this._selectedTripId ? this._t("saveUpdate") : this._t("addNew")}</h2></div>
            <div class="body">
              ${this._renderTripEditor()}
              <div class="note">${this._t("panelNote")}</div>
            </div>
          </section>
        </div>
      `;
    }
    return `
      <div class="grid">
        <section class="card">
          <div class="card-h">
            <h2>${this._t("chargeRecords")}</h2>
            <div class="toolbar">
              ${this._renderDateFilterToolbar("charge")}
              <button id="refreshBtn" class="secondary">${this._t("refresh")}</button>
            </div>
          </div>
          <div class="body">
            ${this._renderChargeSummary()}
            ${this._renderChargeRecords()}
          </div>
        </section>
        <section class="card">
          <div class="card-h"><h2>${this._selectedChargeId ? this._t("saveUpdate") : this._t("addNew")}</h2></div>
          <div class="body">
            ${this._renderChargeEditor()}
            <div class="note">${this._t("panelNote")}</div>
          </div>
        </section>
      </div>
    `;
  }

  _renderActiveSafe() {
    try {
      return this._renderActive();
    } catch (err) {
      this._pushDebugEvent("error", "Active render failed", { error: String(err?.message || err), active_tab: this._activeTab, active_settings_tab: this._activeSettingsTab });
      return `<div class="error">Active render failed: ${this._esc(String(err?.message || err))}</div>`;
    }
  }

  _render() {
    const loading = this._loading ? `<div class="status">${this._t("loading")}</div>` : "";
    const status = this._status ? `<div class="status">${this._esc(this._status)}</div>` : "";
    const error = this._error ? `<div class="error">${this._esc(this._error)}</div>` : "";
    this.shadowRoot.innerHTML = `
      <style>${this._styles()}</style>
      <div class="wrap">
        <div class="top">
          <div>
            <h1>${this._t("title")}</h1>
            <div class="sub">${this._t("subtitle")}</div>
          </div>
          <div class="pill">${this._currency}</div>
          <div class="pill build-pill">${this._esc(this._frontendBuild || "")}</div>
        </div>
        ${this._renderTabs()}
        ${loading}${error}${status}
        ${this._renderAutoFindNoticeBanner()}
        ${this._renderActiveSafe()}
      </div>
      ${this._renderEntityPickerOverlay()}
    `;
    this._syncHAEntityPickers();
    this.shadowRoot.getElementById("autoFindNoticeClose")?.addEventListener("click", (ev) => { ev.preventDefault(); this._closeAutoFindNotice(); });
    this.shadowRoot.getElementById("tabCharge")?.addEventListener("click", () => { this._activeTab = "charge"; this._status = ""; this._error = ""; this._render(); this._ensureActiveLoaded(); });
    this.shadowRoot.getElementById("tabTrip")?.addEventListener("click", () => { this._activeTab = "trip"; this._status = ""; this._error = ""; this._render(); this._ensureActiveLoaded(); });
    this.shadowRoot.getElementById("tabManual")?.addEventListener("click", () => { this._activeTab = "manual"; this._status = ""; this._error = ""; this._render(); this._ensureActiveLoaded(); });
    this.shadowRoot.getElementById("tabSettings")?.addEventListener("click", () => { this._activeTab = "settings"; this._status = ""; this._error = ""; this._render(); this._ensureActiveLoaded(); });
    this.shadowRoot.querySelectorAll("tr.record").forEach((row) => row.addEventListener("click", () => {
      if (row.dataset.kind === "manual") this._selectManualTrackingRecord(row.dataset.id);
      else if (row.dataset.kind === "trip") this._selectTripRecord(row.dataset.id);
      else this._selectChargeRecord(row.dataset.id);
    }));
    this.shadowRoot.querySelectorAll(".mini-slot-btn").forEach((btn) => btn.addEventListener("click", (ev) => { ev.preventDefault(); ev.stopPropagation(); this._moveStationToReportSlot(btn.dataset.stationIndex, btn.dataset.stationSlot); }));
    this.shadowRoot.querySelectorAll(".station-row").forEach((row) => row.addEventListener("click", () => this._selectStation(row.dataset.stationIndex)));
    this.shadowRoot.getElementById("refreshBtn")?.addEventListener("click", () => this._loadActive());
    this.shadowRoot.getElementById("filterChargeToday")?.addEventListener("click", () => this._setDateFilter("charge", "today"));
    this.shadowRoot.getElementById("filterChargeMonth")?.addEventListener("click", () => this._toggleMonthPanel("charge"));
    this.shadowRoot.getElementById("filterChargeAll")?.addEventListener("click", () => this._setDateFilter("charge", "all"));
    this.shadowRoot.getElementById("filterChargeMonthSelect")?.addEventListener("change", (ev) => this._setSelectedMonth("charge", ev.target.value));
    this.shadowRoot.getElementById("applyChargeRangeBtn")?.addEventListener("click", () => this._applyDateRange("charge"));
    this.shadowRoot.getElementById("filterTripToday")?.addEventListener("click", () => this._setDateFilter("trip", "today"));
    this.shadowRoot.getElementById("filterTripMonth")?.addEventListener("click", () => this._toggleMonthPanel("trip"));
    this.shadowRoot.getElementById("filterTripAll")?.addEventListener("click", () => this._setDateFilter("trip", "all"));
    this.shadowRoot.getElementById("filterTripMonthSelect")?.addEventListener("change", (ev) => this._setSelectedMonth("trip", ev.target.value));
    this.shadowRoot.getElementById("applyTripRangeBtn")?.addEventListener("click", () => this._applyDateRange("trip"));
    this.shadowRoot.getElementById("filterManualToday")?.addEventListener("click", () => this._setDateFilter("manual", "today"));
    this.shadowRoot.getElementById("filterManualMonth")?.addEventListener("click", () => this._toggleMonthPanel("manual"));
    this.shadowRoot.getElementById("filterManualAll")?.addEventListener("click", () => this._setDateFilter("manual", "all"));
    this.shadowRoot.getElementById("filterManualMonthSelect")?.addEventListener("change", (ev) => this._setSelectedMonth("manual", ev.target.value));
    this.shadowRoot.getElementById("applyManualRangeBtn")?.addEventListener("click", () => this._applyDateRange("manual"));
    this.shadowRoot.getElementById("newChargeBtn")?.addEventListener("click", () => this._newChargeRecord());
    this.shadowRoot.getElementById("saveChargeBtn")?.addEventListener("click", () => this._saveCharge(this._selectedChargeId ? "update" : "add"));
    this.shadowRoot.getElementById("addChargeBtn")?.addEventListener("click", () => this._saveCharge("add"));
    this.shadowRoot.getElementById("deleteChargeBtn")?.addEventListener("click", () => this._deleteCharge());
    this.shadowRoot.getElementById("newTripBtn")?.addEventListener("click", () => this._newTripRecord());
    this.shadowRoot.getElementById("saveTripBtn")?.addEventListener("click", () => this._saveTrip(this._selectedTripId ? "update" : "add"));
    this.shadowRoot.getElementById("addTripBtn")?.addEventListener("click", () => this._saveTrip("add"));
    this.shadowRoot.getElementById("deleteTripBtn")?.addEventListener("click", () => this._deleteTrip());
    ["general","charging","trip","ai_settings","telegram","ai","automations","dashboard"].forEach((tab) => {
      const el = this.shadowRoot.getElementById(`settingsNav_${tab}`);
      const jump = (ev, source) => {
        ev.preventDefault();
        ev.stopPropagation();
        this._lastClickDebug = { [source]: tab, active_settings_tab: this._activeSettingsTab };
        this._switchSettingsTabDirect(tab);
      };
      el?.addEventListener("pointerdown", (ev) => jump(ev, "direct_pointer_settings_tab"), { capture: true });
      el?.addEventListener("click", (ev) => jump(ev, "direct_click_settings_tab"));
    });
    this.shadowRoot.querySelectorAll("[data-dashboard-section]").forEach((el) => {
      const jump = (ev, source) => {
        ev.preventDefault();
        ev.stopPropagation();
        const section = el.dataset.dashboardSection || "general";
        this._lastClickDebug = { [source]: section, active_dashboard_section: this._dashboardSettingsSection };
        this._switchDashboardSectionDirect(section);
      };
      el.addEventListener("pointerdown", (ev) => jump(ev, "direct_pointer_dashboard_section"), { capture: true });
      el.addEventListener("click", (ev) => jump(ev, "direct_click_dashboard_section"));
    });
    this.shadowRoot.getElementById("saveSettingsBtn")?.addEventListener("click", () => this._saveSettings());
    this.shadowRoot.querySelectorAll("[data-panel-action]").forEach((el) => {
      el.addEventListener("click", (ev) => this._handlePanelAction(el.dataset.panelAction, ev));
      el.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter" || ev.key === " ") this._handlePanelAction(el.dataset.panelAction, ev);
      });
    });
    this.shadowRoot.getElementById("saveGeneralSettingsBtn")?.addEventListener("click", () => this._saveGeneralSettings());
    this.shadowRoot.getElementById("exportSettingsBtn")?.addEventListener("click", () => this._exportPanelSettings());
    const dashboardTopFontScaleIds = ["dashboard_top_font_scale","dashboard_top_left_font_scale","dashboard_top_center_font_scale","dashboard_top_right_font_scale"];
    dashboardTopFontScaleIds.forEach((id) => {
      const el = this.shadowRoot.getElementById(id);
      const out = this.shadowRoot.getElementById(`${id}_value`);
      el?.addEventListener("input", () => {
        if (out) out.textContent = `${(Number(el.value) || 1).toFixed(2)}x`;
      });
    });
    this.shadowRoot.getElementById("runDebugInfoBtn")?.addEventListener("click", () => this._runDebugDiagnostics());
    this.shadowRoot.getElementById("copyDebugInfoBtn")?.addEventListener("click", () => this._copyDebugInfo());
    this.shadowRoot.getElementById("clearDebugInfoBtn")?.addEventListener("click", () => this._clearDebugDiagnostics());
    this.shadowRoot.getElementById("migratePanelStoresBtn")?.addEventListener("click", () => this._migratePanelEntityStores());
    this.shadowRoot.getElementById("clearPanelMigrationOutputBtn")?.addEventListener("click", () => this._clearPanelMigrationOutput());
    this.shadowRoot.getElementById("importSettingsFile")?.addEventListener("change", (ev) => {
      const file = ev?.target?.files?.[0];
      const note = this.shadowRoot.getElementById("importSettingsNote");
      if (note) note.textContent = file ? `${this._t("selectedImportFile")}: ${file.name}` : this._t("importSettingsPlaceholder");
      if (file) this._pushDebugEvent("info", "Import file selected", { name: file.name, size: file.size, type: file.type });
    });
    this.shadowRoot.getElementById("saveTripSettingsBtn")?.addEventListener("click", () => this._saveTripSettings());
    this.shadowRoot.getElementById("sendTestTripReportBtn")?.addEventListener("click", () => this._sendTestTripReport());
    this.shadowRoot.getElementById("startLiveTripTestBtn")?.addEventListener("click", () => this._runLiveTripTestAction("start"));
    this.shadowRoot.getElementById("finishLiveTripTestBtn")?.addEventListener("click", () => this._runLiveTripTestAction("finish"));
    this.shadowRoot.getElementById("resetLiveTripTestBtn")?.addEventListener("click", () => this._runLiveTripTestAction("reset"));
    this.shadowRoot.getElementById("refreshLiveTripDebugBtn")?.addEventListener("click", () => this._loadLiveTripDebug(true));
    this.shadowRoot.getElementById("saveAISettingsBtn")?.addEventListener("click", () => this._saveAISettings());
    this.shadowRoot.getElementById("runAITestBtn")?.addEventListener("click", () => this._runAITest(false));
    this.shadowRoot.getElementById("runAITestTelegramBtn")?.addEventListener("click", () => this._runAITest(true));
    this.shadowRoot.getElementById("clearAILogsBtn")?.addEventListener("click", () => this._clearAILogs());
    this.shadowRoot.getElementById("saveAutomationSettingsBtn")?.addEventListener("click", () => this._saveAutomationSettings());
    this.shadowRoot.getElementById("installDashboardResourcesBtn")?.addEventListener("click", () => this._refreshDashboardResources("install_resources"));
    this.shadowRoot.getElementById("showMissingDashboardCardsBtn")?.addEventListener("click", () => this._refreshDashboardResources("show_missing"));
    this.shadowRoot.getElementById("saveDashboardSettingsBtnBackground")?.addEventListener("click", () => this._saveDashboardSettings());
    this.shadowRoot.getElementById("reloadDashboardSettingsBtnBackground")?.addEventListener("click", () => this._loadAll());
    this.shadowRoot.getElementById("saveDashboardSettingsBtn")?.addEventListener("click", () => this._saveDashboardSettings());
    ["parked", "charging", "driving"].forEach((slot) => {
      this.shadowRoot.getElementById(`dashboard_upload_btn_${slot}`)?.addEventListener("click", () => this._uploadDashboardBackground(slot));
      this.shadowRoot.getElementById(`dashboard_reset_btn_${slot}`)?.addEventListener("click", () => this._resetDashboardBackground(slot));
      this.shadowRoot.getElementById(`dashboard_file_${slot}`)?.addEventListener("change", (ev) => {
        const file = ev?.target?.files?.[0];
        const note = this.shadowRoot.getElementById(`dashboard_file_note_${slot}`);
        if (note) note.textContent = file ? `${this._t("dashboardFileReady")}: ${file.name}` : this._t("dashboardNoFileSelected");
      });
    });
    this.shadowRoot.getElementById("saveTelegramSettingsBtn")?.addEventListener("click", () => this._saveTelegramSettings());
    this.shadowRoot.getElementById("saveAIEntityManagerBtn")?.addEventListener("click", () => this._saveAIEntityManager());
    this.shadowRoot.getElementById("saveAIEntityManagerBtnBottom")?.addEventListener("click", () => this._saveAIEntityManager());
    this.shadowRoot.getElementById("autoFindAIEntitiesBtn")?.addEventListener("click", () => this._autoFindAIEntities());
    this.shadowRoot.getElementById("autoFindAIEntitiesBtnBottom")?.addEventListener("click", () => this._autoFindAIEntities());
    this.shadowRoot.getElementById("saveReportEntityManagerBtn")?.addEventListener("click", () => this._saveReportEntityManager());
    this.shadowRoot.getElementById("saveReportEntityManagerBtnBottom")?.addEventListener("click", () => this._saveReportEntityManager());
    this.shadowRoot.getElementById("autoFindReportEntitiesBtn")?.addEventListener("click", () => this._autoFindReportEntities());
    this.shadowRoot.getElementById("autoFindReportEntitiesBtnBottom")?.addEventListener("click", () => this._autoFindReportEntities());
    this.shadowRoot.getElementById("saveDashboardEntityManagerBtn")?.addEventListener("click", () => this._saveDashboardEntityManager());
    this.shadowRoot.getElementById("saveDashboardEntityManagerBtnBottom")?.addEventListener("click", () => this._saveDashboardEntityManager());
    this.shadowRoot.getElementById("autoFindDashboardEntitiesBtn")?.addEventListener("click", () => this._autoFindDashboardEntities());
    this.shadowRoot.getElementById("autoFindDashboardEntitiesBtnBottom")?.addEventListener("click", () => this._autoFindDashboardEntities());
    this.shadowRoot.querySelectorAll(".dashboard-custom-icon-input").forEach((el) => {
      const updateIcon = (ev) => {
        ev.stopPropagation();
        const role = el.dataset.dashboardIconRole || "";
        const draft = this._getDashboardEntityDraft();
        draft.meta = draft.meta || {};
        draft.meta[role] = draft.meta[role] || {};
        draft.meta[role].icon = el.value || "";
      };
      el.addEventListener("input", updateIcon);
      el.addEventListener("change", updateIcon);
      el.addEventListener("click", (ev) => ev.stopPropagation());
      el.addEventListener("keydown", (ev) => ev.stopPropagation());
      el.addEventListener("keyup", (ev) => ev.stopPropagation());
      el.addEventListener("keypress", (ev) => ev.stopPropagation());
    });
    this.shadowRoot.getElementById("sendTelegramTestBtn")?.addEventListener("click", () => this._runTelegramTest("send_test"));
    this.shadowRoot.getElementById("pollTelegramTestBtn")?.addEventListener("click", () => this._runTelegramTest("poll_once"));
    this.shadowRoot.getElementById("clearTelegramLogsBtn")?.addEventListener("click", () => this._clearTelegramLogs());
    this.shadowRoot.getElementById("saveStationBtn")?.addEventListener("click", () => this._addOrUpdateStation());
    this.shadowRoot.getElementById("clearStationBtn")?.addEventListener("click", () => this._newStation());
    this.shadowRoot.getElementById("deleteStationBtn")?.addEventListener("click", () => this._deleteStation());
    const entitySearch = this.shadowRoot.getElementById("entity_picker_search");
    if (entitySearch) {
      const keepInside = (ev) => {
        ev.stopPropagation();
      };
      entitySearch.addEventListener("input", (ev) => {
        // Do not re-render the whole panel while typing. Update only the list.
        // This keeps focus inside the search box and prevents HA keyboard shortcuts
        // from stealing focus.
        ev.stopPropagation();
        this._entityPickerSearch = entitySearch.value || "";
        this._refreshEntityPickerList();
        requestAnimationFrame(() => entitySearch.focus());
      });
      entitySearch.addEventListener("keydown", (ev) => {
        keepInside(ev);
        if (ev.key === "Escape") { ev.preventDefault(); this._closeEntityPicker(); }
        if (ev.key === "Enter") {
          const first = this._filteredEntityOptions()[0];
          if (first?.entity_id) { ev.preventDefault(); this._setEntityForPickerTarget(first.entity_id); }
        }
      });
      entitySearch.addEventListener("keyup", keepInside);
      entitySearch.addEventListener("keypress", keepInside);
    }
    this.shadowRoot.querySelectorAll(".entity-picker-field, .entity-picker-modal").forEach((el) => {
      el.addEventListener("keydown", (ev) => { ev.stopPropagation(); ev.stopImmediatePropagation?.(); });
      el.addEventListener("keyup", (ev) => { ev.stopPropagation(); ev.stopImmediatePropagation?.(); });
      el.addEventListener("keypress", (ev) => { ev.stopPropagation(); ev.stopImmediatePropagation?.(); });
    });
    ["station_name", "station_unit_price", "station_currency"].forEach((id) => {
      const el = this.shadowRoot.getElementById(id);
      if (!el) return;
      el.addEventListener("input", () => this._captureStationDraft());
      el.addEventListener("change", () => this._captureStationDraft());
    });
  }
}


// Defensive runtime guard for older cached alpha203 bundles.
if (typeof PomTeslaReportPanel !== "undefined" && !PomTeslaReportPanel.prototype._renderTelegramReportCommandSettings) {
  PomTeslaReportPanel.prototype._renderTelegramReportCommandSettings = function(commands = {}) {
    const defaults = this._defaultTelegramReportCommands ? this._defaultTelegramReportCommands() : {
      charge_report: "charge", trip_summary: "trip", trip_all: "tripall", trip_single: "single", trip_last: "triplast",
    };
    const cmd = this._telegramReportCommands ? this._telegramReportCommands(commands) : Object.fromEntries(Object.entries(defaults).map(([k, v]) => [k, commands?.[k] || v]));
    return `
      <div class="section-title">${this._lang === "en" ? "Telegram report commands" : "Telegram rapor komutları"}</div>
      <div class="field-grid">
        ${[
          ["telegram_cmd_charge_report", "charge_report", this._lang === "en" ? "Charge report command" : "Şarj raporu komutu", this._lang === "en" ? "Monthly charge report." : "Bu ayın şarj raporunu gönderir."],
          ["telegram_cmd_trip_summary", "trip_summary", this._lang === "en" ? "Monthly trip summary command" : "Aylık sürüş özeti komutu", this._lang === "en" ? "Monthly trip overview." : "Bu ayın sürüş özetini gönderir."],
          ["telegram_cmd_trip_all", "trip_all", this._lang === "en" ? "All trip records command" : "Tüm sürüş kayıtları komutu", this._lang === "en" ? "All monthly trip pages." : "Bu ayki tüm sürüş sayfalarını gönderir."],
          ["telegram_cmd_trip_single", "trip_single", this._lang === "en" ? "Single-page trip command" : "Tek sayfa sürüş komutu", this._lang === "en" ? "Single-page trip report." : "Tek sayfa sürüş raporunu gönderir."],
          ["telegram_cmd_trip_last", "trip_last", this._lang === "en" ? "Last trip command" : "Son sürüş komutu", this._lang === "en" ? "Latest trip report." : "Son sürüş raporunu gönderir."],
        ].map(([id, key, label, desc]) => `
          <div>
            <label>${this._esc(label)}</label>
            <input id="${id}" value="${this._esc(cmd[key] || "")}" placeholder="${this._esc(defaults[key] || "")}" />
            <div class="note">/${this._esc(cmd[key] || defaults[key] || "")} — ${this._esc(desc)}</div>
          </div>`).join("")}
      </div>
    `;
  };
}

if (!customElements.get("pom-tesla-report-panel")) {
  customElements.define("pom-tesla-report-panel-alpha221", PomTeslaReportPanel);
}

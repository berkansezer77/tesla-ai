class PomTeslaDriveDashboardCard extends HTMLElement {
  static getConfigElement() { return document.createElement('div'); }
  static getStubConfig() { return {}; }

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = null;
    this._chromeGuardTimer = null;
  }

  connectedCallback() {
    this._startEarlyChromeGuard();
  }

  disconnectedCallback() {
    if (this._chromeGuardTimer) {
      clearInterval(this._chromeGuardTimer);
      this._chromeGuardTimer = null;
    }
  }

  _fullscreenActive() {
    try {
      const st = this._hass?.states?.['switch.pom_tesla_dashboard_fullscreen']?.state;
      if (st === 'on') {
        window.localStorage.setItem('pomTeslaDashboardFullscreen', 'on');
        return true;
      }
      if (st === 'off') {
        window.localStorage.setItem('pomTeslaDashboardFullscreen', 'off');
        return false;
      }
    } catch (err) {}
    try {
      return window.localStorage.getItem('pomTeslaDashboardFullscreen') === 'on';
    } catch (err) {
      return false;
    }
  }

  _isDriveDashboardPath() {
    try {
      const path = window.location.pathname || '';
      return path.endsWith('/pom-drive-dashboard/drive') || path === '/pom-drive-dashboard/drive';
    } catch (err) {
      return false;
    }
  }

  _isAppSwitcherElement(el) {
    try {
      return Boolean(el && (el.id === 'pom-tesla-app-switcher' || el.closest?.('#pom-tesla-app-switcher')));
    } catch (err) {
      return false;
    }
  }

  _startEarlyChromeGuard() {
    const run = () => this._applyEarlyChromeGuard();
    run();
    requestAnimationFrame(run);
    [40, 120, 260, 520, 900, 1500, 2400].forEach((ms) => setTimeout(run, ms));
    if (!this._chromeGuardTimer) {
      this._chromeGuardTimer = setInterval(run, 1200);
    }
  }

  _applyEarlyChromeGuard() {
    const store = window.__pomTeslaDriveEarlyChromeStyles = window.__pomTeslaDriveEarlyChromeStyles || new Map();
    const remember = (el, prop) => {
      if (!el) return;
      let rec = store.get(el);
      if (!rec) { rec = {}; store.set(el, rec); }
      if (!(prop in rec)) {
        try { rec[prop] = { value: el.style.getPropertyValue(prop), priority: el.style.getPropertyPriority(prop) }; }
        catch (err) { rec[prop] = { value: '', priority: '' }; }
      }
    };
    const setImportant = (el, prop, value) => {
      if (!el) return;
      try { remember(el, prop); el.style.setProperty(prop, value, 'important'); } catch (err) {}
    };
    const restore = () => {
      try {
        store.forEach((props, el) => {
          Object.entries(props).forEach(([prop, old]) => {
            try {
              if (old.value) el.style.setProperty(prop, old.value, old.priority || '');
              else el.style.removeProperty(prop);
            } catch (err) {}
          });
        });
        store.clear();
      } catch (err) {}
    };

    const active = this._fullscreenActive();
    if (!active) {
      restore();
      return;
    }

    const roots = [];
    const seen = new Set();
    const collect = (root, depth = 0) => {
      if (!root || depth > 8 || seen.has(root)) return;
      seen.add(root);
      roots.push(root);
      let nodes = [];
      try { nodes = root.querySelectorAll ? root.querySelectorAll('*') : []; } catch (err) { nodes = []; }
      nodes.forEach((node) => { if (node.shadowRoot) collect(node.shadowRoot, depth + 1); });
    };
    collect(document, 0);

    [
      document.documentElement,
      document.body
    ].forEach((el) => {
      setImportant(el, '--header-height', '0px');
      setImportant(el, '--app-toolbar-height', '0px');
      setImportant(el, '--ha-top-app-bar-width', '100vw');
      setImportant(el, '--mdc-top-app-bar-width', '100vw');
      setImportant(el, '--ha-sidebar-width', '0px');
      setImportant(el, '--ha-drawer-width', '0px');
      setImportant(el, '--mdc-drawer-width', '0px');
      setImportant(el, '--app-drawer-width', '0px');
      setImportant(el, '--sidebar-width', '0px');
      setImportant(el, '--drawer-width', '0px');
      setImportant(el, '--mdc-drawer-modal-width', '0px');
    });
    setImportant(document.documentElement, 'overflow', 'hidden');
    setImportant(document.documentElement, 'height', '100vh');
    setImportant(document.body, 'overflow', 'hidden');
    setImportant(document.body, 'height', '100vh');
    setImportant(document.body, 'margin', '0');

    const hideEl = (el) => {
      if (!el || this._isAppSwitcherElement(el)) return;
      setImportant(el, 'display', 'none');
      setImportant(el, 'visibility', 'hidden');
      setImportant(el, 'pointer-events', 'none');
    };
    const vw = Math.max(document.documentElement?.clientWidth || 0, window.innerWidth || 0);
    const isTopChrome = (el) => {
      try {
        if (!el || this._isAppSwitcherElement(el)) return false;
        const r = el.getBoundingClientRect();
        return r && r.width > 0 && r.height > 0 && r.top <= 92 && r.bottom <= 140;
      } catch (err) {
        return false;
      }
    };
    const isTopRightChrome = (el) => {
      try {
        if (!el || this._isAppSwitcherElement(el)) return false;
        const r = el.getBoundingClientRect();
        if (!r || r.width <= 0 || r.height <= 0) return false;
        return r.top <= 112 && r.bottom <= 156 && r.right >= (vw - 360) && r.width <= 360 && r.height <= 96;
      } catch (err) {
        return false;
      }
    };
    const textLooksLikeUpdateChrome = (el) => {
      try {
        const text = String(el.textContent || '').trim().toLowerCase();
        if (!text) return false;
        return text.includes('updated just now') || text.includes('update now') || text === 'update' || text === 'refresh' || text.includes('just now');
      } catch (err) {
        return false;
      }
    };
    const tagLooksLikeChromeButton = (el) => {
      try {
        const tag = String(el.localName || el.tagName || '').toLowerCase();
        return tag.includes('icon-button') || tag.includes('ha-menu') || tag.includes('ha-button') || tag.includes('mwc-button') || tag.includes('paper-icon') || tag === 'ha-assist-chip';
      } catch (err) {
        return false;
      }
    };

    roots.forEach((root) => {
      ['app-header','app-toolbar','ha-top-app-bar-fixed','ha-top-app-bar','ha-header-bar','.toolbar[slot="toolbar"]','[slot="toolbar"]','.top-app-bar'].forEach((sel) => {
        try { root.querySelectorAll(sel).forEach(hideEl); } catch (err) {}
      });
      ['ha-menu-button','ha-button-menu','ha-control-button-menu','ha-icon-button','mwc-icon-button','paper-icon-button','ha-assist-chip'].forEach((sel) => {
        try { root.querySelectorAll(sel).forEach((el) => { if (isTopChrome(el)) hideEl(el); }); } catch (err) {}
      });
      ['ha-sidebar','.sidebar','[data-panel="sidebar"]','[slot="sidebar"]','[slot="drawer"]','ha-navigation-list','nav.sidebar','aside.sidebar'].forEach((sel) => {
        try { root.querySelectorAll(sel).forEach(hideEl); } catch (err) {}
      });
      // alpha294: Drive dashboard has a Home Assistant top-right refresh/update
      // chip in some shell layouts. It is not part of the dashboard footer Last
      // Update. Hide only small top-right chrome elements while fullscreen is on.
      try {
        root.querySelectorAll('*').forEach((el) => {
          if (!isTopRightChrome(el)) return;
          if (textLooksLikeUpdateChrome(el) || tagLooksLikeChromeButton(el)) {
            hideEl(el);
          }
        });
      } catch (err) {}
      ['home-assistant','home-assistant-main','app-drawer-layout','ha-drawer','mwc-drawer','sl-drawer','ha-panel-lovelace','hui-root','hui-view','hui-panel-view','#view'].forEach((sel) => {
        try { root.querySelectorAll(sel).forEach((el) => {
          setImportant(el, '--ha-sidebar-width', '0px');
          setImportant(el, '--ha-drawer-width', '0px');
          setImportant(el, '--mdc-drawer-width', '0px');
          setImportant(el, '--app-drawer-width', '0px');
          setImportant(el, '--sidebar-width', '0px');
          setImportant(el, '--drawer-width', '0px');
          setImportant(el, '--mdc-drawer-modal-width', '0px');
          setImportant(el, '--ha-top-app-bar-width', '100vw');
          setImportant(el, '--mdc-top-app-bar-width', '100vw');
          setImportant(el, 'margin-left', '0px');
          setImportant(el, 'padding-left', '0px');
          setImportant(el, 'left', '0px');
          setImportant(el, 'width', '100vw');
          setImportant(el, 'max-width', '100vw');
        }); } catch (err) {}
      });
    });
  }

  setConfig(config) {
    this._config = config || {};
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._applyEarlyChromeGuard();
    this._render();
  }

  getCardSize() { return 12; }

  _entity(key, fallback) {
    return (this._config.entities && this._config.entities[key]) || fallback;
  }

  _state(entityId) {
    if (!this._hass || !entityId) return null;
    return this._hass.states[entityId] || null;
  }

  _raw(key, fallback) {
    const entityId = this._entity(key, fallback);
    const st = this._state(entityId);
    if (!st) return null;
    const value = st.state;
    if (value === undefined || value === null || value === '' || value === 'unknown' || value === 'unavailable') return null;
    return value;
  }

  _num(key, fallback) {
    const raw = this._raw(key, fallback);
    if (raw === null) return null;
    const n = Number(String(raw).replace(',', '.'));
    return Number.isFinite(n) ? n : null;
  }

  _attr(key, fallback, attr) {
    const st = this._state(this._entity(key, fallback));
    if (!st || !st.attributes) return null;
    const value = st.attributes[attr];
    return value === undefined || value === null || value === '' ? null : value;
  }

  _fmt(value, unit = '', digits = 0, empty = '—') {
    if (value === null || value === undefined || value === '' || value === 'unknown' || value === 'unavailable') return empty;
    const n = Number(String(value).replace(',', '.'));
    if (Number.isFinite(n)) return `${n.toFixed(digits)}${unit ? ` ${unit}` : ''}`;
    return `${value}${unit ? ` ${unit}` : ''}`;
  }

  _fmtText(value, empty = '—') {
    if (value === null || value === undefined || value === '' || value === 'unknown' || value === 'unavailable') return empty;
    return String(value);
  }

  _lang() {
    const raw = String(this._config?.language || this._config?.app_language || this._hass?.language || 'tr').trim().toLowerCase();
    return raw.startsWith('en') ? 'en' : 'tr';
  }

  _t(key) {
    const dict = {
      en: {
        title: 'Drive Dashboard', home: 'home', disconnected: 'Disconnected', connected: 'Connected', charging: 'Charging', notCharging: 'Not charging',
        running: 'Running', off: 'Off', unlocked: 'Unlocked', allClosed: 'All Closed', heating: 'Heating', normal: 'Normal', away: 'Away', noDestination: 'No active destination',
        battery: 'Battery', ratedRange: 'Rated Range', estimatedRange: 'Estimated Range', drive: 'Drive', shiftState: 'Shift State', route: 'Route',
        distanceToArrival: 'Distance to Arrival', socAtArrival: 'SoC at Arrival', timeToArrival: 'Time to Arrival', trafficDelay: 'Traffic Delay',
        energyCharging: 'Energy & Charging', energyRemaining: 'Energy Remaining', energy: 'Energy', climate: 'Climate', inside: 'Inside', outside: 'Outside',
        driverPassengerSet: 'Driver & Passenger Set', elevation: 'Elevation', currentElevation: 'Current Elevation', vehicleHealth: 'Vehicle Health', location: 'Location',
        dashcam: 'Dashcam', doorsWindows: 'Doors & Windows', batteryHeater: 'Battery Heater', tirePressure: 'Tire Pressure', tirePressureOk: 'Tire Pressure: OK',
        frontLeft: 'Front Left', frontRight: 'Front Right', rearLeft: 'Rear Left', rearRight: 'Rear Right', diagnostics: 'Diagnostics', odometer: 'Odometer',
        phantomDrain: 'Phantom Drain', lifetimeEnergy: 'Lifetime Energy', batteryModules: 'Battery Modules', speed: 'Speed', setTemp: 'Set Temp', lastUpdate: 'Last Update',
        minuteShort: 'min', park: 'PARK', reverse: 'REVERSE', neutral: 'NEUTRAL', driveState: 'DRIVE'
      },
      tr: {
        title: 'Sürüş Ekranı', home: 'ev', disconnected: 'Bağlı değil', connected: 'Bağlı', charging: 'Şarj oluyor', notCharging: 'Şarj olmuyor',
        running: 'Çalışıyor', off: 'Kapalı', unlocked: 'Kilit açık', allClosed: 'Kapalı', heating: 'Isıtıyor', normal: 'Normal', away: 'Yolda', noDestination: 'Aktif hedef yok',
        battery: 'Batarya', ratedRange: 'Nominal Menzil', estimatedRange: 'Tahmini Menzil', drive: 'Sürüş', shiftState: 'Vites Durumu', route: 'Rota',
        distanceToArrival: 'Varışa Mesafe', socAtArrival: 'Varış Bataryası', timeToArrival: 'Varış Süresi', trafficDelay: 'Trafik Gecikmesi',
        energyCharging: 'Enerji & Şarj', energyRemaining: 'Kalan Enerji', energy: 'Güç', climate: 'Klima', inside: 'İçerisi', outside: 'Dışarısı',
        driverPassengerSet: 'Sürücü & Yolcu Ayarı', elevation: 'Rakım', currentElevation: 'Mevcut Rakım', vehicleHealth: 'Araç Sağlığı', location: 'Konum',
        dashcam: 'Dashcam', doorsWindows: 'Kapılar & Camlar', batteryHeater: 'Batarya Isıtıcı', tirePressure: 'Lastik Basıncı', tirePressureOk: 'Lastik Basıncı: OK',
        frontLeft: 'Ön Sol', frontRight: 'Ön Sağ', rearLeft: 'Arka Sol', rearRight: 'Arka Sağ', diagnostics: 'Diagnostik', odometer: 'Kilometre',
        phantomDrain: 'Bekleme Tüketimi', lifetimeEnergy: 'Toplam Enerji', batteryModules: 'Batarya Modülleri', speed: 'Hız', setTemp: 'Set Sıcaklığı', lastUpdate: 'Son Güncelleme',
        minuteShort: 'dk', park: 'PARK', reverse: 'GERİ', neutral: 'BOŞ', driveState: 'SÜRÜŞ'
      }
    };
    return (dict[this._lang()] && dict[this._lang()][key]) || dict.en[key] || key;
  }

  _stateLabel(value) {
    if (value === null || value === undefined || value === '' || value === 'unknown' || value === 'unavailable') return '—';
    const raw = String(value);
    const key = raw.trim().toLowerCase();
    const map = {
      home: this._t('home'), away: this._t('away'), connected: this._t('connected'), disconnected: this._t('disconnected'),
      charging: this._t('charging'), 'not charging': this._t('notCharging'), running: this._t('running'), off: this._t('off'),
      unlocked: this._t('unlocked'), locked: this._t('allClosed'), closed: this._t('allClosed'), open: this._t('unlocked'),
      normal: this._t('normal'), heating: this._t('heating'), true: this._t('connected'), false: this._t('disconnected'),
      on: this._t('connected'), paused: this._t('off')
    };
    return map[key] || raw;
  }

  _safeUrl(value) {
    const raw = String(value || '').trim();
    if (!raw) return '';
    if (raw.startsWith('/local/') || raw.startsWith('/pom_tesla_report/') || raw.startsWith('https://') || raw.startsWith('http://')) return raw.replace(/"/g, '%22');
    return '';
  }

  _shiftLabel(value) {
    const raw = String(value || '').toLowerCase();
    if (raw === 'd') return this._t('driveState');
    if (raw === 'r') return this._t('reverse');
    if (raw === 'n') return this._t('neutral');
    if (raw === 'p') return this._t('park');
    return raw ? raw.toUpperCase() : '—';
  }

  _comfortState(insideTemp, outsideTemp, driverTemp, passengerTemp) {
    const inside = Number(insideTemp);
    const outside = Number(outsideTemp);
    const driver = Number(driverTemp);
    const passenger = Number(passengerTemp);
    if (!Number.isFinite(inside)) {
      return { label: 'Unknown', colorClass: 'dim', icon: 'mdi:help-circle-outline' };
    }

    const setTemps = [driver, passenger].filter((v) => Number.isFinite(v));
    const target = setTemps.length ? (setTemps.reduce((a, b) => a + b, 0) / setTemps.length) : null;

    if (inside >= 42 || inside <= 5) {
      return { label: 'Bad', colorClass: 'bad', icon: 'mdi:alert-circle-outline' };
    }

    let score = 0;
    if (inside >= 20 && inside <= 26.5) score += 3;
    else if (inside >= 18 && inside <= 28.5) score += 2;
    else if (inside >= 16 && inside <= 31) score += 0;
    else score -= 3;

    if (target !== null) {
      const deltaTarget = Math.abs(inside - target);
      if (deltaTarget <= 3) score += 1;
      else if (deltaTarget <= 6) score += 0;
      else if (deltaTarget <= 10) score -= 1;
      else score -= 2;
    }

    if (Number.isFinite(outside)) {
      const deltaOutside = Math.abs(inside - outside);
      if (deltaOutside <= 6) score += 1;
      else if (deltaOutside <= 12) score += 0;
      else score -= 1;

      const outsideExtreme = outside >= 35 || outside <= 0;
      if (outsideExtreme) {
        if (inside >= 19 && inside <= 27) score += 1;
        else score -= 1;
      }
    }

    if (score >= 3) return { label: 'Good', colorClass: 'good', icon: 'mdi:check-circle-outline' };
    if (score >= 1) return { label: 'Okay', colorClass: 'warn', icon: 'mdi:checkbox-marked-circle-outline' };
    return { label: 'Bad', colorClass: 'bad', icon: 'mdi:alert-circle-outline' };
  }

  _climateSetDisplay(driverTemp, passengerTemp) {
    const driver = Number(driverTemp);
    const passenger = Number(passengerTemp);
    if (Number.isFinite(driver) && Number.isFinite(passenger)) {
      if (Math.abs(driver - passenger) < 0.05) return this._fmt(driver, '°C', 1);
      return `${this._fmt(driver, '°C', 1)} / ${this._fmt(passenger, '°C', 1)}`;
    }
    if (Number.isFinite(driver)) return this._fmt(driver, '°C', 1);
    if (Number.isFinite(passenger)) return this._fmt(passenger, '°C', 1);
    return '—';
  }

  _boolLabel(key, fallback, onText, offText, unknownText = '—') {
    const raw = this._raw(key, fallback);
    if (raw === null) return unknownText;
    const v = String(raw).toLowerCase();
    if (['on', 'true', 'open', 'unlocked', 'running'].includes(v)) return onText;
    if (['off', 'false', 'closed', 'locked', 'paused'].includes(v)) return offText;
    return this._stateLabel(raw);
  }

  _updatedTime() {
    try {
      return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (err) {
      return '';
    }
  }

  _batteryRing(percent) {
    const p = Math.max(0, Math.min(100, Number(percent || 0)));
    return `conic-gradient(#2f8cff ${p * 3.6}deg, rgba(255,255,255,.08) 0deg)`;
  }

  _render() {
    if (!this.shadowRoot || !this._hass) return;

    const battery = this._num('battery_level', 'sensor.pom_battery_level');
    const ratedRange = this._num('battery_range', 'sensor.pom_battery_range');
    const estimatedRange = this._num('battery_range_estimate', 'sensor.pom_battery_range_estimate');
    const energyRemaining = this._num('energy_remaining', 'sensor.pom_energy_remaining');
    // The Drive Dashboard speed uses the same Entities > Dashboard role as the
    // main Tesla Dashboard (`dashboard_top_speed`). If the generated YAML does
    // not contain that binding yet, fall back to sensor.tesla_speed first.
    const speed = this._num('speed', 'sensor.tesla_speed') ?? this._num('speed_pom_fallback', 'sensor.pom_speed');
    const power = this._num('power', 'sensor.pom_power') ?? this._num('power_fallback', 'sensor.tesla_power');
    const shift = this._raw('shift_state', 'sensor.pom_shift_state');
    const shiftLabel = this._shiftLabel(shift);
    const location = this._raw('location_label', 'sensor.pom_tesla_dashboard_location_label') || this._raw('location_tracker', 'device_tracker.pom_location');
    const destination = this._raw('destination', 'sensor.pom_destination');
    const distanceToArrival = this._num('distance_to_arrival', 'sensor.pom_distance_to_arrival');
    const timeToArrivalRaw = this._raw('time_to_arrival', 'sensor.pom_time_to_arrival');
    const trafficDelay = this._num('traffic_delay', 'sensor.pom_traffic_delay');
    const energyAtArrival = this._num('energy_at_arrival', 'sensor.pom_state_of_charge_at_arrival') ?? this._num('energy_at_arrival_fallback', 'sensor.pom_energy_at_arrival');
    const insideTemp = this._num('inside_temperature', 'sensor.pom_inside_temperature');
    const outsideTemp = this._num('outside_temperature', 'sensor.pom_outside_temperature');
    const driverTemp = this._num('driver_temperature_setting', 'sensor.pom_driver_temperature_setting');
    const passengerTemp = this._num('passenger_temperature_setting', 'sensor.pom_passenger_temperature_setting');
    const comfort = this._comfortState(insideTemp, outsideTemp, driverTemp, passengerTemp);
    const climateSetText = this._climateSetDisplay(driverTemp, passengerTemp);
    const elevation = this._num('elevation', 'sensor.tesla_elevation') ?? this._num('elevation_pom', 'sensor.pom_elevation');
    const odometer = this._num('odometer', 'sensor.pom_odometer');
    const phantom = this._num('phantom_drain', 'sensor.pom_phantom_drain');
    const moduleTemp = this._num('battery_module_temperature_max', 'sensor.pom_battery_module_temperature_max');
    const packTemp = this._num('battery_pack_temperature', 'sensor.pom_battery_pack_temperature');
    const chargeStatus = this._boolLabel('charging_state', 'binary_sensor.pom_charging', this._t('charging'), this._t('notCharging'));
    const cableStatus = this._boolLabel('charge_cable', 'binary_sensor.pom_charge_cable', this._t('connected'), this._t('disconnected'));
    const dashcam = this._boolLabel('dashcam', 'binary_sensor.pom_dashcam', this._t('running'), this._t('off'));
    const doors = this._boolLabel('lock', 'lock.pom_lock', this._t('unlocked'), this._t('allClosed'));
    const heater = this._boolLabel('battery_heater', 'binary_sensor.pom_battery_heater', this._t('heating'), this._t('normal'));
    const fl = this._num('tire_pressure_front_left', 'sensor.pom_tire_pressure_front_left');
    const fr = this._num('tire_pressure_front_right', 'sensor.pom_tire_pressure_front_right');
    const rl = this._num('tire_pressure_rear_left', 'sensor.pom_tire_pressure_rear_left');
    const rr = this._num('tire_pressure_rear_right', 'sensor.pom_tire_pressure_rear_right');
    const bluetooth = this._stateLabel(this._raw('bluetooth_status', 'binary_sensor.pom_bluetooth') || this._t('disconnected'));
    const lifetimeEnergyUsed = this._num('lifetime_energy_used', 'sensor.pom_lifetime_energy_used');
    const routeStatus = destination ? this._t('away') : '—';
    const title = (this._config.title && this._config.title !== 'Drive Dashboard') ? this._config.title : this._t('title');
    const vehicleImage = this._safeUrl(this._config.vehicle_image || '');
    const tireImage = this._safeUrl(this._config.tire_pressure_image || '');

    const timeToArrival = (() => {
      if (!timeToArrivalRaw) return '—';
      const n = Number(String(timeToArrivalRaw).replace(',', '.'));
      if (Number.isFinite(n)) return `${Math.round(n)} ${this._t('minuteShort')}`;
      const d = new Date(timeToArrivalRaw);
      if (!Number.isNaN(d.getTime())) {
        const mins = Math.max(0, Math.round((d.getTime() - Date.now()) / 60000));
        return `${mins} ${this._t('minuteShort')}`;
      }
      return String(timeToArrivalRaw);
    })();

    const mapGraphic = `
      <div class="mini-map">
        <svg viewBox="0 0 600 190" preserveAspectRatio="none" aria-hidden="true">
          <path class="road" d="M0 150 C80 120 110 125 180 95 C260 58 305 70 380 78 C470 88 505 55 600 42"/>
          <path class="route" d="M58 149 C108 130 147 127 197 101 C267 65 312 77 383 85 C462 94 508 63 547 53"/>
          <circle class="pos" cx="95" cy="136" r="14"/>
          <circle class="pin" cx="548" cy="53" r="17"/>
        </svg>
      </div>`;

    const driveBgStyle = vehicleImage ? ` style="--drive-bg:url('${vehicleImage}')"` : '';
    const tireLayoutStyle = tireImage ? ` style="--tire-image:url('${tireImage}')"` : '';
    const tireCardStyle = tireImage ? ` style="--tire-card-bg:url('${tireImage}')"` : '';
    const carGraphic = vehicleImage
      ? ''
      : `<div class="vehicle-svg">
          <svg viewBox="0 0 520 300" aria-hidden="true">
            <defs>
              <radialGradient id="glow" cx="50%" cy="70%" r="55%"><stop offset="0" stop-color="#1677ff" stop-opacity=".36"/><stop offset="1" stop-color="#1677ff" stop-opacity="0"/></radialGradient>
              <linearGradient id="body" x1="0" x2="1"><stop offset="0" stop-color="#151a22"/><stop offset=".45" stop-color="#585f6a"/><stop offset="1" stop-color="#11161f"/></linearGradient>
            </defs>
            <ellipse cx="260" cy="196" rx="225" ry="90" fill="url(#glow)"/>
            <path d="M127 184 C145 93 190 55 260 55 C330 55 375 93 393 184 L371 238 C322 264 198 264 149 238 Z" fill="url(#body)" stroke="#8d98aa" stroke-opacity=".25"/>
            <path d="M181 117 C202 82 230 72 260 72 C290 72 318 82 339 117 C302 105 218 105 181 117 Z" fill="#070a10" opacity=".85"/>
            <path d="M151 171 C182 162 205 164 223 179 C184 188 164 186 151 171 Z" fill="#e9f4ff" opacity=".92"/>
            <path d="M369 171 C338 162 315 164 297 179 C336 188 356 186 369 171 Z" fill="#e9f4ff" opacity=".92"/>
            <path d="M170 226 C220 247 300 247 350 226" fill="none" stroke="#29313d" stroke-width="10" stroke-linecap="round"/>
            <text x="260" y="214" text-anchor="middle" fill="#dce6f5" font-size="28" font-family="Arial" font-weight="700">T</text>
          </svg>
        </div>`;

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display:block;
          position:relative;
          width:100%;
          max-width:100%;
          height:calc(100dvh - var(--pom-drive-dashboard-offset, 0px));
          min-height:0;
          max-height:calc(100dvh - var(--pom-drive-dashboard-offset, 0px));
          margin:0;
          padding:0;
          overflow:hidden;
          background:#03060b;
          box-sizing:border-box;
        }
        .wrap {
          --blue:#2488ff; --blue2:#54a6ff; --text:#f3f7ff; --muted:#aab6c8; --line:rgba(255,255,255,.12);
          width:100%; max-width:100%; height:100%; min-height:0; box-sizing:border-box; padding:clamp(4px, .45vw, 8px); color:var(--text);
          font-family: var(--ha-font-family-body, Inter, Roboto, Arial, sans-serif);
          background:
            radial-gradient(circle at 50% 20%, rgba(33,120,255,.18), transparent 34%),
            radial-gradient(circle at 78% 18%, rgba(25,142,255,.10), transparent 30%),
            linear-gradient(180deg, #03060b 0%, #090d13 100%);
          border:1px solid rgba(100,160,255,.18); border-radius:0; overflow:hidden;
        }
        .topbar { display:flex; align-items:center; justify-content:space-between; margin-bottom:clamp(3px, .35vh, 5px); gap:12px; min-height:clamp(28px, 3.8vh, 42px); }
        .brand { display:flex; align-items:center; gap:18px; min-width:0; }
        .tesla-mark { font-size:clamp(24px, 2.1vw, 34px); line-height:1; color:var(--blue); font-weight:900; font-family:Georgia,serif; transform:scaleX(1.2); }
        .title { font-size:clamp(17px, 1.45vw, 24px); font-weight:700; letter-spacing:.2px; }
        .sub { display:flex; gap:10px; align-items:center; color:var(--muted); margin-top:2px; font-size:clamp(10px, .9vw, 12px); }
        .sub .blue { color:var(--blue2); }
        .grid { display:grid; grid-template-columns: 1.02fr 1.02fr 1.04fr; grid-template-rows: repeat(3, minmax(0, 1fr)) clamp(48px, 6%, 58px); gap:clamp(4px, .45vw, 7px); height:calc(100% - clamp(34px, 4.4vh, 46px)); min-height:0; min-width:0; overflow:hidden; }
        .card { position:relative; min-width:0; border-radius:14px; background:linear-gradient(160deg, rgba(20,27,38,.78), rgba(8,11,17,.86)); border:1px solid rgba(120,160,210,.18); box-shadow: inset 0 1px 0 rgba(255,255,255,.04), 0 18px 42px rgba(0,0,0,.35); overflow:hidden; }
        .card.blue-border { border-color:rgba(36,136,255,.75); box-shadow:0 0 0 1px rgba(36,136,255,.15), inset 0 1px 0 rgba(255,255,255,.05), 0 0 42px rgba(36,136,255,.14); }
        .card-head { display:flex; align-items:center; gap:8px; padding:clamp(8px, .95vh, 12px) clamp(10px, 1.0vw, 16px) 0; color:#dce8fa; font-size:11px; font-weight:700; letter-spacing:.8px; text-transform:uppercase; }
        ha-icon { color:var(--blue); --mdc-icon-size:20px; }
        .battery-main { display:grid; grid-template-columns:1.1fr .9fr; height:calc(100% - 32px); align-items:center; padding:2px clamp(12px, 1.3vw, 22px) 10px clamp(28px, 2.6vw, 44px); gap:clamp(14px, 1.5vw, 24px); }
        .big-num { font-size:clamp(42px, 4.0vw, 64px); font-weight:300; letter-spacing:-4px; line-height:.9; }
        .big-num span { font-size:28px; margin-left:4px; }
        .range-stack { border-left:1px solid var(--line); padding-left:22px; display:grid; gap:8px; }
        .range-num { font-size:22px; }
        .label { color:var(--muted); font-size:12px; margin-top:2px; }
        .bar { height:11px; border-radius:5px; background:rgba(255,255,255,.10); overflow:hidden; margin:12px 0 0; max-width:245px; }
        .bar > i { display:block; height:100%; background:linear-gradient(90deg,#2b86ff,#66aeff); width:var(--pct); }
        .energy-line { display:none; }
        .energy-value { font-size:28px; }
        .drive { grid-column:2; grid-row:1; display:flex; flex-direction:column; align-items:center; justify-content:center; isolation:isolate; background:linear-gradient(160deg, rgba(20,27,38,.78), rgba(8,11,17,.86)); }
        .drive.has-bg { background:linear-gradient(160deg, rgba(20,27,38,.78), rgba(8,11,17,.86)); }
        .drive.has-bg::before { content:""; position:absolute; inset:0; z-index:0; pointer-events:none; background:
            linear-gradient(180deg, rgba(5,10,18,.42), rgba(5,10,18,.74)),
            linear-gradient(90deg, rgba(5,10,18,.18), rgba(5,10,18,.06) 50%, rgba(5,10,18,.18)),
            var(--drive-bg) center center / cover no-repeat; }
        .drive.has-bg::after { display:none; content:none; }
        .drive > * { position:relative; z-index:2; }
        .speed { position:absolute; top:clamp(30px, 4.7vh, 42px); text-align:center; }
        .speed .n { font-size:clamp(44px, 4.2vw, 68px); font-weight:300; line-height:.85; }
        .speed .u { color:var(--muted); font-size:16px; margin-top:8px; }
        .vehicle-svg { width:min(68%, 360px); max-height:50%; margin-top:clamp(48px, 6.6vh, 62px); filter:drop-shadow(0 30px 44px rgba(0,0,0,.5)); }
        .shift { position:absolute; right:clamp(14px, 1.5vw, 24px); top:clamp(112px, 15vh, 138px); text-align:center; color:var(--blue2); font-size:clamp(22px, 2vw, 28px); letter-spacing:.5px; }
        .shift small { display:block; color:var(--muted); font-size:13px; letter-spacing:0; margin-top:4px; }
        .shift-circle { margin:10px auto 0; width:32px; height:32px; border-radius:50%; border:3px solid var(--blue); display:grid; place-items:center; color:var(--blue2); font-size:22px; }
        .route { grid-column:3; grid-row:1; }
        .route-title { padding:clamp(12px, 1.4vh, 22px) 20px 8px; font-size:clamp(18px, 1.45vw, 24px); line-height:1.08; min-height:36px; }
         .route-details { border-top:1px solid var(--line); border-bottom:1px solid var(--line); margin:0 20px; padding:12px 0; display:grid; grid-template-columns:1fr 1fr; gap:20px 32px; }
        .detail { display:flex; align-items:center; gap:10px; }
        .detail .v { font-size:17px; } .detail .l { color:var(--muted); font-size:10px; margin-top:2px; }
        .route-status { display:flex; align-items:center; gap:10px; padding:10px 20px; font-size:15px; }
        .smallgrid { grid-column:1 / 4; grid-row:2 / 4; display:grid; grid-template-columns: 1.02fr 1.02fr 1.04fr; grid-template-rows: repeat(2, minmax(0, 1fr)); gap:clamp(5px, .55vw, 8px); min-height:0; overflow:hidden; }
        .smallgrid > .card { min-width:0; width:100%; box-sizing:border-box; }
        .mini { min-height:0; min-width:0; }
        .mini .content { padding:clamp(8px, .85vw, 13px); box-sizing:border-box; }
        .energy-card { grid-column:1; grid-row:1; }
        .climate-card { grid-column:2; grid-row:1; }
        .elevation-card { grid-column:3; grid-row:1; }
        .health-card { grid-column:1; grid-row:2; }
        .tire-panel-card { grid-column:2; grid-row:2; }
        .diagnostics-card { grid-column:3; grid-row:2; }
         .kv { display:flex; align-items:center; justify-content:space-between; gap:8px; margin:clamp(3px, .48vh, 7px) 0; color:#eaf2ff; }
        .kv .left { display:flex; align-items:center; gap:10px; color:#dce6f4; }
        .kv .right { color:#f5f8ff; }
        .green { color:#44e25f !important; } .dim { color:var(--muted) !important; }
        .large-kwh { font-size:clamp(22px, 2.05vw, 29px); margin:clamp(5px, .75vh, 9px) 0 4px; }
        .energy-card-content { display:flex; flex-direction:column; align-items:stretch; justify-content:flex-start; gap:0; min-height:0; width:100%; box-sizing:border-box; }
        .energy-top { display:grid; grid-template-columns:minmax(0, 1fr) minmax(132px, 30%); gap:14px; align-items:start; width:100%; }
        .energy-main { min-width:0; padding-right:16px; border-right:1px solid var(--line); box-sizing:border-box; }
        .energy-separator { height:1px; width:100%; margin:10px 0 0; background:var(--line); opacity:.95; }
        .energy-body { padding-top:10px; }
        .energy-side { min-width:0; text-align:left; padding-top:clamp(10px, 1.0vh, 14px); }
        .energy-side .energy-title { color:var(--blue2); font-size:clamp(20px, 1.9vw, 28px); line-height:1; letter-spacing:.5px; text-transform:uppercase; }
        .energy-side .energy-value { color:#f5f8ff; font-size:clamp(24px, 2.2vw, 34px); line-height:1.12; margin-top:10px; font-weight:500; white-space:nowrap; }
        .split { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:clamp(7px, 1.0vh, 11px); }
        .split > div { border-right:1px solid var(--line); padding-right:16px; } .split > div:last-child { border-right:0; padding-right:0; }
        .temp-big { font-size:23px; }
        .climate-card { overflow:hidden; display:flex; flex-direction:column; min-width:0; width:auto; box-sizing:border-box; }
        .climate-card .card-head { flex:0 0 auto; }
        .climate-card .content { flex:1 1 auto; min-height:0; padding:0; display:flex; flex-direction:column; gap:0; box-sizing:border-box; }
        .climate-top { display:grid; grid-template-columns:1fr 1fr; gap:10px; padding:clamp(8px, .85vw, 13px) clamp(8px, .85vw, 13px) 0; box-sizing:border-box; }
        .climate-top > div { border-right:1px solid var(--line); padding-right:16px; min-width:0; }
        .climate-top > div:last-child { border-right:0; padding-right:0; }
        .climate-mid { border-top:1px solid var(--line); margin:10px clamp(8px, .85vw, 13px) 0; padding-top:12px; display:flex; align-items:center; gap:12px; color:#dce6f4; box-sizing:border-box; }
        .climate-mid ha-icon { color:var(--blue2); --mdc-icon-size:28px; }
        .climate-mid-value { font-size:clamp(16px, 1.35vw, 22px); line-height:1.08; font-weight:500; }
        .spark { width:100%; height:clamp(34px, 5.2vh, 50px); margin:clamp(5px, .7vh, 8px) 0; }
        .spark path { fill:none; stroke:#2d8cff; stroke-width:4; stroke-linecap:round; stroke-linejoin:round; filter:drop-shadow(0 0 8px rgba(45,140,255,.55)); }
         .tire-card { position:relative; overflow:hidden; }
        .tire-card > * { position:relative; z-index:1; }
        .tire-card.has-bg::before { content:""; position:absolute; inset:0; z-index:0; background:
          linear-gradient(180deg, rgba(5,10,18,.58), rgba(5,10,18,.78)),
          linear-gradient(90deg, rgba(5,10,18,.26), rgba(5,10,18,.10) 50%, rgba(5,10,18,.26)),
          var(--tire-card-bg) center center / cover no-repeat; }
        .tire-layout { display:grid; grid-template-columns:1fr 46px 1fr; align-items:center; gap:6px; padding:clamp(7px, .8vh, 10px) 12px 4px; text-align:center; }
        .tire-car { width:40px; height:clamp(76px, 11vh, 104px); margin:auto; border-radius:30px 30px 18px 18px; background:linear-gradient(180deg,#222a35,#0c0f14); border:1px solid rgba(255,255,255,.16); position:relative; box-shadow:inset 0 0 25px rgba(255,255,255,.04); }
        .tire-car:before,.tire-car:after{content:"";position:absolute;left:11px;right:11px;height:24px;border-radius:50%;background:rgba(255,255,255,.09);} .tire-car:before{top:20px}.tire-car:after{bottom:20px}
        .tire-card.has-bg .tire-layout { grid-template-columns:1fr clamp(82px, 9.5vw, 124px) 1fr; gap:8px; min-height:clamp(160px, 18vh, 220px); align-items:center; }
        .tire-card.has-bg .tire-car { width:1px; height:1px; opacity:0; border:0; box-shadow:none; background:none; }
        .tire-card.has-bg .tire-car:before,.tire-card.has-bg .tire-car:after{display:none;}
        .psi { font-size:clamp(17px, 1.7vw, 21px); } .psi small { display:block; font-size:10px; color:var(--muted); }
        .footer { grid-column:1 / 4; grid-row:4; display:grid; grid-template-columns: repeat(6, 1fr); align-items:center; padding:0 clamp(6px, .9vw, 12px); min-height:48px; }
        .foot-item { display:flex; align-items:center; justify-content:center; gap:8px; border-right:1px solid var(--line); min-height:46px; overflow:hidden; }
        .foot-item:last-child { border-right:0; }
        .foot-label { color:var(--muted); font-size:9px; text-transform:uppercase; letter-spacing:.45px; white-space:nowrap; }
        .foot-value { font-size:13px; margin-top:1px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .mini-map { height:150px; margin:18px 28px 0; border-radius:14px; background:linear-gradient(160deg,#111820,#070a10); border:1px solid rgba(255,255,255,.07); overflow:hidden; opacity:.9; }
        .mini-map svg { width:100%; height:100%; } .road { fill:none; stroke:rgba(255,255,255,.10); stroke-width:46; } .route { fill:none; stroke:#258bff; stroke-width:12; stroke-linecap:round; filter:drop-shadow(0 0 10px rgba(38,139,255,.75)); } .pos { fill:#50a0ff; stroke:white; stroke-width:5; } .pin { fill:#258bff; stroke:#0a1320; stroke-width:6; }
        .battery-ring { width:160px; height:160px; border-radius:50%; background:var(--ring); display:grid; place-items:center; margin:auto; position:relative; }
        .battery-ring:after { content:""; position:absolute; inset:14px; background:#0a0e15; border-radius:50%; box-shadow:inset 0 0 22px rgba(0,0,0,.6); }
        .battery-ring .ring-label { position:relative; z-index:1; font-size:56px; font-weight:300; } .ring-label span { font-size:22px; }
        @media (max-width: 1350px) {
          .smallgrid { grid-template-columns:1.02fr 1.02fr 1.04fr; grid-template-rows:repeat(2, minmax(0,1fr)); }
          :host { --pom-drive-dashboard-offset: 10px; }
          .grid { grid-template-rows:repeat(3, minmax(0, 1fr)) 52px; }
          .mini .content { padding:8px 10px; }
          .card-head { padding:8px 10px 0; font-size:10px; }
          .battery-main { padding:0 12px 8px 24px; gap:8px; }
          .range-stack { padding-left:14px; gap:6px; }
          .route-title { padding:10px 14px 6px; font-size:clamp(16px, 1.45vw, 20px); min-height:30px; }
          .route-details { margin:0 14px; padding:8px 0; gap:8px 12px; }
          .route-status { padding:6px 14px; font-size:13px; }
          .shift { right:12px; top:clamp(76px, 10.5vh, 96px); font-size:19px; }
          .vehicle-svg { width:min(56%, 285px); max-height:42%; }
          .large-kwh { margin-top:5px; }
          .energy-side .energy-title { font-size:18px; }
          .energy-side .energy-value { font-size:24px; margin-top:8px; }
        }
        @media (min-width: 1500px) {
          .grid { grid-template-rows:repeat(3, minmax(0, 1fr)) 56px; }
          .smallgrid { grid-template-columns: 1.02fr 1.02fr 1.04fr; grid-template-rows: repeat(2, minmax(0,1fr)); }
          .mini .content { padding:14px 18px; }
          .large-kwh { font-size:clamp(28px, 2.0vw, 36px); }
          .temp-big { font-size:clamp(24px, 1.9vw, 32px); }
          .psi { font-size:clamp(19px, 1.35vw, 24px); }
          .climate-mid ha-icon { --mdc-icon-size:30px; }
          .climate-mid-value { font-size:clamp(16px, 1.3vw, 21px); }
        }
        @media (max-height: 760px) and (orientation: landscape) {
          .wrap { padding:3px 5px; }
          .topbar { min-height:30px; margin-bottom:3px; }
          .title { font-size:16px; }
          .tesla-mark { font-size:24px; }
          .sub { font-size:10px; margin-top:1px; }
          .grid { height:calc(100% - 34px); grid-template-rows:repeat(3, minmax(0, 1fr)) 46px; gap:4px; }
          .card { border-radius:11px; }
          .card-head { padding:6px 9px 0; font-size:9px; gap:6px; }
          .battery-main { padding:0 10px 7px 20px; }
          .big-num { font-size:clamp(34px, 4.0vw, 48px); }
          .range-num { font-size:18px; }
          .label { font-size:10px; }
          .route-title { padding:8px 12px 4px; font-size:15px; min-height:24px; }
          .route-details { margin:0 12px; padding:6px 0; gap:6px 10px; }
          .detail .v { font-size:14px; }
          .detail .l { font-size:9px; }
          .route-status { padding:4px 12px; font-size:12px; }
          .speed { top:26px; }
          .speed .n { font-size:42px; }
          .speed .u { font-size:12px; margin-top:4px; }
          .shift { top:78px; right:10px; font-size:18px; }
          .shift small { font-size:10px; }
          .shift-circle { width:26px; height:26px; border-width:2px; font-size:18px; margin-top:6px; }
          .mini .content { padding:6px 9px; }
          .large-kwh { font-size:22px; margin:5px 0 3px; }
          .energy-card-content { gap:10px; }
          .energy-top { grid-template-columns:minmax(0,1fr) minmax(104px, 30%); gap:10px; }
          .energy-main { padding-right:12px; }
          .energy-body { padding-top:8px; }
          .energy-side { min-width:96px; padding-top:8px; }
          .energy-side .energy-title { font-size:17px; }
          .energy-side .energy-value { font-size:21px; margin-top:7px; }
          .temp-big { font-size:20px; }
          .climate-card .content { gap:0; }
          .climate-mid { margin:8px 10px 0; padding-top:9px; gap:10px; }
          .climate-mid ha-icon { --mdc-icon-size:26px; }
          .climate-mid-value { font-size:16px; }
          .spark { height:32px; }
          .tire-layout { grid-template-columns:1fr 36px 1fr; padding:5px 9px 2px; }
          .tire-car { width:34px; height:70px; }
          .tire-card.has-bg .tire-layout { grid-template-columns:1fr 72px 1fr; min-height:132px; }
          .tire-card.has-bg .tire-car { width:1px; height:1px; }
          .psi { font-size:16px; }
          .psi small { font-size:8px; }
          .footer { min-height:46px; }
          .foot-item { min-height:44px; gap:6px; }
          .foot-label { font-size:8px; }
          .foot-value { font-size:12px; }
        }
        @media (max-width: 920px) {
          :host { position:relative; width:100%; height:auto; min-height:100dvh; overflow:visible; }
          .wrap { position:relative; width:100%; height:auto; min-height:100dvh; overflow:auto; }
          .grid { grid-template-columns:1fr; grid-template-rows:auto; height:auto; min-height:0; }
          .drive,.route,.smallgrid,.footer { grid-column:1; grid-row:auto; }
          .smallgrid { grid-template-columns:1fr; }
          .footer { grid-template-columns:1fr 1fr; gap:0; }
          .energy-card-content { flex-direction:column; }
          .energy-top { grid-template-columns:1fr; gap:8px; }
          .energy-main { padding-right:0; border-right:0; }
          .energy-body { padding-top:8px; }
          .energy-side { min-width:0; width:100%; text-align:left; padding-top:4px; }
        }
      </style>
      <div class="wrap">
        <div class="topbar">
          <div class="brand"><div class="tesla-mark">T</div><div><div class="title">${title}</div><div class="sub"><span class="blue">⌂ ${this._stateLabel(location || this._t('home'))}</span><span>•</span><span>${this._stateLabel(bluetooth || this._t('disconnected'))}</span></div></div></div>
        </div>
        <div class="grid">
          <section class="card blue-border">
            <div class="card-head"><ha-icon icon="mdi:battery"></ha-icon><span>${this._t('battery')}</span></div>
            <div class="battery-main">
              <div><div class="big-num">${this._fmt(battery, '', 0)}<span>%</span></div><div class="bar" style="--pct:${Math.max(0,Math.min(100,battery || 0))}%"><i></i></div></div>
              <div class="range-stack"><div><div class="range-num">${this._fmt(ratedRange,'km',1)}</div><div class="label">${this._t('ratedRange')}</div></div><div><div class="range-num">${this._fmt(estimatedRange,'km',1)}</div><div class="label">${this._t('estimatedRange')}</div></div></div>
            </div>
          </section>
          <section class="card drive ${vehicleImage ? 'has-bg' : ''}"${driveBgStyle}>
            <div class="card-head" style="position:absolute;left:0;top:0"><ha-icon icon="mdi:speedometer"></ha-icon><span>${this._t('drive')}</span></div>
            <div class="speed"><div class="n">${this._fmt(speed,'',0)}</div><div class="u">km/h</div></div>${carGraphic}
            <div class="shift">${shiftLabel}<small>${this._t('shiftState')}</small><div class="shift-circle">${String(shift || 'P').toUpperCase().slice(0,1)}</div></div>
          </section>
          <section class="card route">
            <div class="card-head"><ha-icon icon="mdi:navigation-variant"></ha-icon><span>${this._t('route')}</span></div>
            <div class="route-title">${this._fmtText(destination, this._t('noDestination'))}</div>
            <div class="route-details">
              <div class="detail"><ha-icon icon="mdi:map-marker-distance"></ha-icon><div><div class="v">${this._fmt(distanceToArrival,'km',2)}</div><div class="l">${this._t('distanceToArrival')}</div></div></div>
              <div class="detail"><ha-icon icon="mdi:battery"></ha-icon><div><div class="v">${this._fmt(energyAtArrival,'%',0)}</div><div class="l">${this._t('socAtArrival')}</div></div></div>
              <div class="detail"><ha-icon icon="mdi:clock-outline"></ha-icon><div><div class="v">${timeToArrival}</div><div class="l">${this._t('timeToArrival')}</div></div></div>
              <div class="detail"><ha-icon icon="mdi:car-clock"></ha-icon><div><div class="v">${this._fmt(trafficDelay,'m',0)}</div><div class="l">${this._t('trafficDelay')}</div></div></div>
            </div>
            <div class="route-status"><ha-icon icon="mdi:arrow-top-right"></ha-icon><div><div>${routeStatus}</div><div class="label">${this._t('route')}</div></div></div>
          </section>
          <div class="smallgrid">
            <section class="card mini energy-card"><div class="card-head"><ha-icon icon="mdi:lightning-bolt"></ha-icon><span>${this._t('energyCharging')}</span></div><div class="content energy-card-content"><div class="energy-top"><div class="energy-main"><div class="large-kwh">${this._fmt(energyRemaining,'kWh',2)}</div><div class="label">${this._t('energyRemaining')}</div></div><div class="energy-side"><div class="energy-title">${this._t('energy')}</div><div class="energy-value">${this._fmt(power,'kW',1)}</div></div></div><div class="energy-separator"></div><div class="energy-body"><div class="kv"><div class="left"><ha-icon icon="mdi:ev-station"></ha-icon>${chargeStatus}</div></div><div class="kv"><div class="left"><ha-icon icon="mdi:connection"></ha-icon>${cableStatus}</div></div></div></div></section>
            <section class="card mini climate-card"><div class="card-head"><ha-icon icon="mdi:fan"></ha-icon><span>${this._t('climate')}</span></div><div class="content"><div class="climate-top"><div><div class="temp-big">${this._fmt(insideTemp,'°C',1)}</div><div class="label">${this._t('inside')}</div></div><div><div class="temp-big">${this._fmt(outsideTemp,'°C',1)}</div><div class="label">${this._t('outside')}</div></div></div><div class="climate-mid"><ha-icon icon="mdi:thermometer"></ha-icon><div><div class="climate-mid-value">${climateSetText}</div><div class="label">${this._t('driverPassengerSet')}</div></div></div></div></section>
            <section class="card mini elevation-card"><div class="card-head"><ha-icon icon="mdi:image-filter-hdr"></ha-icon><span>${this._t('elevation')}</span></div><div class="content"><div class="large-kwh">${this._fmt(elevation,'m',0)}</div><div class="label">${this._t('currentElevation')}</div><svg class="spark" viewBox="0 0 240 70"><path d="M8 55 L38 45 L62 44 L88 25 L112 34 L138 29 L160 13 L188 24 L218 9"/></svg></div></section>
            <section class="card mini health-card"><div class="card-head"><ha-icon icon="mdi:shield-check"></ha-icon><span>${this._t('vehicleHealth')}</span></div><div class="content"><div class="kv"><div class="left"><ha-icon icon="mdi:map-marker"></ha-icon>${this._t('location')}</div><div class="right">${this._stateLabel(location || this._t('home'))}</div></div><div class="kv"><div class="left"><ha-icon icon="mdi:camera"></ha-icon>${this._t('dashcam')}</div><div class="right green">${dashcam}</div></div><div class="kv"><div class="left"><ha-icon icon="mdi:lock"></ha-icon>${this._t('doorsWindows')}</div><div class="right green">${doors}</div></div><div class="kv"><div class="left"><ha-icon icon="mdi:thermometer"></ha-icon>${this._t('batteryHeater')}</div><div class="right green">${heater}</div></div></div></section>
            <section class="card mini tire-panel-card tire-card ${tireImage ? 'has-bg' : ''}"${tireCardStyle}><div class="card-head"><ha-icon icon="mdi:car-tire-alert"></ha-icon><span>${this._t('tirePressure')}</span></div><div class="tire-layout ${tireImage ? 'has-bg' : ''}"${tireLayoutStyle}><div><div class="psi">${this._fmt(fl,'',1)}<small>psi · ${this._t('frontLeft')}</small></div><br><div class="psi">${this._fmt(rl,'',1)}<small>psi · ${this._t('rearLeft')}</small></div></div><div class="tire-car"></div><div><div class="psi">${this._fmt(fr,'',1)}<small>psi · ${this._t('frontRight')}</small></div><br><div class="psi">${this._fmt(rr,'',1)}<small>psi · ${this._t('rearRight')}</small></div></div></div><div class="label green" style="text-align:center">${this._t('tirePressureOk')}</div></section>
            <section class="card mini diagnostics-card"><div class="card-head"><ha-icon icon="mdi:pulse"></ha-icon><span>${this._t('diagnostics')}</span></div><div class="content"><div class="kv"><div class="left"><ha-icon icon="mdi:counter"></ha-icon>${this._t('odometer')}</div><div>${this._fmt(odometer,'km',0)}</div></div><div class="kv"><div class="left"><ha-icon icon="mdi:gauge-empty"></ha-icon>${this._t('phantomDrain')}</div><div>${this._fmt(phantom,'%',2)}</div></div><div class="kv"><div class="left"><ha-icon icon="mdi:flash"></ha-icon>${this._t('lifetimeEnergy')}</div><div>${this._fmt(lifetimeEnergyUsed,'kWh',0)}</div></div><div class="kv"><div class="left"><ha-icon icon="mdi:thermometer-lines"></ha-icon>${this._t('batteryModules')}</div><div>${this._fmt(moduleTemp,'°C',1)}${packTemp !== null ? ' / ' + this._fmt(packTemp,'°C',1) : ''}</div></div></div></section>
          </div>
          <section class="card footer">
            <div class="foot-item"><ha-icon icon="mdi:map-marker"></ha-icon><div><div class="foot-label">${this._t('location')}</div><div class="foot-value">${this._stateLabel(location || this._t('home'))}</div></div></div>
            <div class="foot-item"><ha-icon icon="mdi:speedometer"></ha-icon><div><div class="foot-label">${this._t('speed')}</div><div class="foot-value">${this._fmt(speed,'km/h',2)}</div></div></div>
            <div class="foot-item"><ha-icon icon="mdi:counter"></ha-icon><div><div class="foot-label">${this._t('odometer')}</div><div class="foot-value">${this._fmt(odometer,'km',0)}</div></div></div>
            <div class="foot-item"><ha-icon icon="mdi:battery"></ha-icon><div><div class="foot-label">${this._t('energyRemaining')}</div><div class="foot-value">${this._fmt(energyRemaining,'kWh',2)}</div></div></div>
            <div class="foot-item"><ha-icon icon="mdi:thermometer"></ha-icon><div><div class="foot-label">${this._t('setTemp')}</div><div class="foot-value">${this._fmt(driverTemp,'°C',1)}</div></div></div>
            <div class="foot-item"><ha-icon icon="mdi:clock-outline"></ha-icon><div><div class="foot-label">${this._t('lastUpdate')}</div><div class="foot-value">${this._updatedTime()}</div></div></div>
          </section>
        </div>
      </div>`;
  }
}

if (!customElements.get('pom-tesla-drive-dashboard-card')) {
  customElements.define('pom-tesla-drive-dashboard-card', PomTeslaDriveDashboardCard);
}

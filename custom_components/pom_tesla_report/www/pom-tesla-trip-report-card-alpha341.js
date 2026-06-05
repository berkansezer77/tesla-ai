class PomTeslaTripReportCard extends HTMLElement {
  static get version() { return '1.9.7-alpha341'; }
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = null;
    this._session = null;
    this._timer = null;
    this._commentPanelOpen = false;
    this._lastToggleAt = 0;
  }

  _toggleAiPanel(ev) {
    if (ev) {
      ev.preventDefault?.();
      ev.stopPropagation?.();
    }
    this._lastToggleAt = Date.now();
    this._commentPanelOpen = !this._commentPanelOpen;
    this.render();
  }

  setConfig(config) {
    this._config = {
      title: 'Sürüş Raporu',
      storage_key: 'default',
      car_icon: '🚘',
      supercharger_price: 9.80,
      start_speed_threshold: 3,
      traffic_speed_threshold: 10,
      finish_delay_seconds: 90,
      show_status_badge: false,
      live_mode: true,
      live_backend_mode: true,
      live_trip_entity: '',

      // Core live entities. If the report-specific entities below are not given,
      // the card computes values from these while the dashboard is open.
      speed_entity: '',
      odometer_entity: '',
      energy_remaining_entity: '',
      battery_level_entity: '',
      elevation_entity: '',
      climate_entity: '',
      shift_state_entity: '',
      active_entity: '',

      // Optional report/live entities. When provided, they override computed values.
      trip_distance_entity: '',
      trip_duration_entity: '',
      trip_traffic_entity: '',
      trip_average_speed_entity: '',
      trip_energy_entity: '',
      trip_consumption_entity: '',
      trip_battery_start_entity: '',
      trip_battery_end_entity: '',
      trip_cost_entity: '',
      trip_climate_entity: '',
      trip_elevation_min_entity: '',
      trip_elevation_max_entity: '',
      report_date_entity: '',
      ...config,
    };
    this._loadSession();
  }

  connectedCallback() {
    if (!this._timer) {
      this._timer = window.setInterval(() => {
        if (this._hass) {
          this._updateSession();
          this.render();
        }
      }, 1000);
    }
  }

  disconnectedCallback() {
    if (this._timer) {
      window.clearInterval(this._timer);
      this._timer = null;
    }
  }

  set hass(hass) {
    this._hass = hass;
    this._updateSession();
    this.render();
  }

  getCardSize() { return 5; }

  _liveStateObj() {
    if (!this._hass || !this._config.live_backend_mode) return null;

    const configured = this._config.live_trip_entity || 'sensor.pom_live_trip';
    let stateObj = configured ? this._hass.states[configured] : null;
    if (stateObj && stateObj.state !== 'unknown' && stateObj.state !== 'unavailable') return stateObj;

    // Entity registry can rename the sensor to sensor.pom_live_trip_2, etc.
    // Fall back to the first POM live trip sensor by attributes/friendly name.
    const candidates = Object.entries(this._hass.states || {})
      .filter(([entityId, obj]) => {
        if (!entityId.startsWith('sensor.')) return false;
        if (!obj || obj.state === 'unknown' || obj.state === 'unavailable') return false;
        const attrs = obj.attributes || {};
        const name = String(attrs.friendly_name || '').toLowerCase();
        return attrs.report_type === 'live_trip' || name === 'pom live trip' || name.includes('pom live trip');
      })
      .map(([, obj]) => obj);
    return candidates.length ? candidates[0] : null;
  }

  _liveAttrs() {
    const stateObj = this._liveStateObj();
    return stateObj ? (stateObj.attributes || null) : null;
  }

  _attr(attrs, key, fallback = null) {
    if (!attrs || attrs[key] === undefined || attrs[key] === null || attrs[key] === '') return fallback;
    return attrs[key];
  }

  _storageKey() {
    return `pom-tesla-trip-report-card:${this._config.storage_key || 'default'}`;
  }

  _newEmptySession() {
    return {
      active: false,
      finishing: false,
      started_at: null,
      finished_at: null,
      start_ts: null,
      finish_ts: null,
      inactive_since: null,
      last_ts: null,
      start_odometer: null,
      last_odometer: null,
      start_energy: null,
      last_energy: null,
      start_battery: null,
      last_battery: null,
      min_elevation: null,
      max_elevation: null,
      traffic_seconds: 0,
      moving_seconds: 0,
      climate_seconds: 0,
    };
  }

  _loadSession() {
    try {
      const raw = window.localStorage.getItem(this._storageKey());
      this._session = raw ? { ...this._newEmptySession(), ...JSON.parse(raw) } : this._newEmptySession();
    } catch (_err) {
      this._session = this._newEmptySession();
    }
  }

  _saveSession() {
    try { window.localStorage.setItem(this._storageKey(), JSON.stringify(this._session)); } catch (_err) {}
  }

  _state(entityId, fallback = '—') {
    if (!this._hass || !entityId) return fallback;
    const stateObj = this._hass.states[entityId];
    if (!stateObj || stateObj.state === 'unknown' || stateObj.state === 'unavailable') return fallback;
    return stateObj.state;
  }

  _numState(entityId, fallback = null) {
    const raw = this._state(entityId, null);
    if (raw === null || raw === '—') return fallback;
    const value = Number(String(raw).replace(',', '.'));
    return Number.isFinite(value) ? value : fallback;
  }

  _formatNumber(value, decimals = 1, fallback = '—') {
    const num = Number(value);
    if (!Number.isFinite(num)) return fallback;
    return num.toFixed(decimals);
  }

  _normalizeBatteryText(value) {
    if (value === null || value === undefined) return '—';
    let text = String(value).trim();
    if (!text || text === '—') return '—';
    text = text
      .replace(/\u00e2\u2020\u2019/g, '->')
      .replace(/\u2192/g, '->')
      .replace(/%([0-9]+(?:\.[0-9]+)?)/g, '$1%')
      .replace(/\s*->\s*/g, ' -> ');
    return text;
  }

  _formatDate(ts) {
    if (!ts) return this._dateText(Date.now());
    return this._dateText(ts);
  }

  _dateText(ts = Date.now()) {
    const d = new Date(ts);
    const dd = String(d.getDate()).padStart(2, '0');
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const yyyy = d.getFullYear();
    const hh = String(d.getHours()).padStart(2, '0');
    const min = String(d.getMinutes()).padStart(2, '0');
    const sec = String(d.getSeconds()).padStart(2, '0');
    return `${dd}.${mm}.${yyyy} ${hh}:${min}:${sec}`;
  }

  _durationText(seconds) {
    const sec = Math.max(0, Number(seconds) || 0);
    const minutes = Math.round(sec / 60);
    if (minutes <= 0) return '—';
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    if (h && m) return `${h}sa ${m}dk`;
    if (h) return `${h}sa`;
    return `${m}dk`;
  }

  _compactDurationText(value) {
    if (value === null || value === undefined) return '—';
    let text = String(value).trim();
    if (!text || text === '—') return '—';

    const lower = text.toLowerCase();
    if (lower.includes('kullanılmadı')) return '—';

    text = text
      .replace(/^Klima\s+/i, '')
      .replace(/\s*açıktı\.?$/i, '')
      .replace(/\s*açık\.?$/i, '')
      .replace(/\s*kullanıldı\.?$/i, '')
      .replace(/dakika/gi, 'dk')
      .replace(/saat/gi, 'sa')
      .replace(/dk\./gi, 'dk')
      .replace(/sa\./gi, 'sa')
      .replace(/\s*\.\s*$/g, '')
      .replace(/(\d+)\s*sa\s+(\d+)\s*dk/gi, '$1sa $2dk')
      .replace(/(\d+)\s*dk/gi, '$1dk')
      .replace(/(\d+)\s*sa/gi, '$1sa')
      .replace(/\s+/g, ' ')
      .trim();
    return text || '—';
  }

  _escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  _liveAiAttr(live, primary, fallbackName, fallback = null) {
    const p = this._attr(live, primary, undefined);
    if (p !== undefined && p !== null && p !== '') return p;
    return this._attr(live, fallbackName, fallback);
  }

  _liveAiSegments(live) {
    const raw = this._liveAiAttr(live, 'ai_live_segments', 'live_ai_segments', []);
    return Array.isArray(raw) ? raw.filter(Boolean) : [];
  }

  _liveAiLatestSegment(live) {
    const latest = this._liveAiAttr(live, 'ai_live_latest_segment', 'live_ai_latest_segment', null);
    if (latest && typeof latest === 'object' && !Array.isArray(latest) && Object.keys(latest).length) return latest;
    const segments = this._liveAiSegments(live);
    return segments.length ? segments[segments.length - 1] : null;
  }

  _liveAiPanelData(live, distanceText) {
    const tripKm = Number(this._attr(live, 'trip_km', 0)) || 0;
    const status = String(this._liveAiAttr(live, 'ai_live_comment_status', 'live_ai_comment_status', 'waiting') || 'waiting').trim().toLowerCase();
    const source = String(this._liveAiAttr(live, 'ai_live_comment_source', 'live_ai_comment_source', '') || '').trim();
    const latest = this._liveAiLatestSegment(live);
    const segments = this._liveAiSegments(live);
    const segmentSize = Number(this._liveAiAttr(live, 'ai_live_segment_size_km', 'live_ai_segment_size_km', 10)) || 10;
    const nextTarget = Number(this._liveAiAttr(live, 'ai_live_next_target_km', 'live_ai_segment_next_target_km', segmentSize)) || segmentSize;
    const rawWaitingText = String(this._liveAiAttr(live, 'ai_live_waiting_text', 'live_ai_waiting_text', '') || '').trim();
    const segmentLabel = Number.isInteger(segmentSize) ? String(segmentSize) : String(Math.round(segmentSize * 10) / 10);
    const computedWaitingText = tripKm <= 0.05
      ? `İlk yorum ${segmentLabel} km civarında hazır olacak.`
      : `Bir sonraki Live Trip yorumu için yaklaşık ${Math.max(0, nextTarget - tripKm).toFixed(1)} km kaldı.`;
    const waitingText = rawWaitingText && !(segmentSize !== 10 && rawWaitingText.includes('10 km')) ? rawWaitingText : computedWaitingText;
    const lastCompletedIndex = Number(latest?.segment_index || this._liveAiAttr(live, 'ai_live_last_completed_index', 'live_ai_segment_last_completed_index', 0) || 0) || 0;
    const segmentStart = Math.max(0, lastCompletedIndex * segmentSize);
    const distanceIntoCurrent = Math.max(0, tripKm - segmentStart);
    const progress = Math.max(0, Math.min(100, (distanceIntoCurrent / segmentSize) * 100));
    const remainingKm = Math.max(0, nextTarget - tripKm);
    const latestComment = String(latest?.comment || this._attr(live, 'live_comment', '') || '').trim();
    let title = '';
    let body = latestComment;
    let footer = latest ? `${latest.segment_label || 'Son bölüm'} · ${latest.source === 'openai' ? 'AI yorum' : 'Akıllı özet'}` : waitingText;
    if (status === 'generating') {
      title = latest?.segment_label ? `${latest.segment_label} hazırlanıyor` : 'Yorum hazırlanıyor';
      body = latestComment || `Son ${segmentLabel} km bölümü için yorum hazırlanıyor. Birkaç saniye içinde burada görünecek.`;
      footer = 'Yeni bölüm analizi üretiliyor';
    } else if (status === 'error') {
      title = '';
      body = 'Yorum şu anda hazırlanamadı. Sürüş ilerledikçe sonraki bölümde tekrar denenecek.';
      footer = 'Geçici hata';
    } else if (!body) {
      title = '';
      body = waitingText;
      footer = `Şu an: ${distanceText} km`;
    }
    return { tripKm, status, source, waitingText, latest, segments, nextTarget, segmentSize, progress, remainingKm, title, body, footer };
  }

  _renderAiHistoryChips(segments, activeIndex) {
    if (!Array.isArray(segments) || !segments.length) return '';
    return segments.slice(-6).map((segment) => {
      const active = Number(segment?.segment_index || 0) === Number(activeIndex || 0);
      const label = this._escapeHtml(segment?.segment_label || 'Bölüm');
      return `<span class="ai-chip ${active ? 'active' : ''}">${label}</span>`;
    }).join('');
  }

  _isTruthyState(value) {
    const s = String(value || '').toLowerCase();
    return ['on', 'true', '1', 'yes', 'active', 'driving', 'charging'].includes(s);
  }

  _isDrivingByShift(value) {
    const s = String(value || '').trim().toLowerCase();
    if (!s || s === '—') return null;
    if (['p', 'park', 'parking', 'parked', 'off', 'asleep', 'sleeping'].includes(s)) return false;
    if (['d', 'drive', 'driving', 'r', 'reverse', 'n', 'neutral'].includes(s)) return true;
    return null;
  }

  _climateActive() {
    const state = String(this._state(this._config.climate_entity, '')).toLowerCase();
    if (!state) return false;
    return !['off', 'idle', 'unavailable', 'unknown', '—'].includes(state);
  }

  _currentDrivingActive() {
    const c = this._config;
    if (c.active_entity) {
      return this._isTruthyState(this._state(c.active_entity, 'off'));
    }
    if (c.shift_state_entity) {
      const byShift = this._isDrivingByShift(this._state(c.shift_state_entity, ''));
      if (byShift !== null) return byShift;
    }
    const speed = this._numState(c.speed_entity, 0) || 0;
    return speed >= Number(c.start_speed_threshold || 3);
  }

  _startNewSession(now) {
    const c = this._config;
    const odometer = this._numState(c.odometer_entity, null);
    const energy = this._numState(c.energy_remaining_entity, null);
    const battery = this._numState(c.battery_level_entity, null);
    const elevation = this._numState(c.elevation_entity, null);
    this._session = {
      ...this._newEmptySession(),
      active: true,
      finishing: false,
      started_at: this._dateText(now),
      start_ts: now,
      last_ts: now,
      start_odometer: odometer,
      last_odometer: odometer,
      start_energy: energy,
      last_energy: energy,
      start_battery: battery,
      last_battery: battery,
      min_elevation: elevation,
      max_elevation: elevation,
      traffic_seconds: 0,
      climate_seconds: 0,
    };
  }

  _updateSession() {
    if (!this._hass || this._config.live_mode === false) return;
    if (!this._session) this._loadSession();

    const now = Date.now();
    const c = this._config;
    const activeNow = this._currentDrivingActive();
    const speed = this._numState(c.speed_entity, 0) || 0;
    const odometer = this._numState(c.odometer_entity, this._session?.last_odometer ?? null);
    const energy = this._numState(c.energy_remaining_entity, this._session?.last_energy ?? null);
    const battery = this._numState(c.battery_level_entity, this._session?.last_battery ?? null);
    const elevation = this._numState(c.elevation_entity, null);

    if (activeNow && !this._session.active) {
      this._startNewSession(now);
    }

    if (this._session.active) {
      const lastTs = this._session.last_ts || now;
      const delta = Math.max(0, Math.min(30_000, now - lastTs)) / 1000;

      if (speed >= Number(c.start_speed_threshold || 3)) {
        this._session.moving_seconds = (Number(this._session.moving_seconds) || 0) + delta;
      }
      if (speed < Number(c.traffic_speed_threshold || 10)) {
        this._session.traffic_seconds = (Number(this._session.traffic_seconds) || 0) + delta;
      }
      if (this._climateActive()) {
        this._session.climate_seconds = (Number(this._session.climate_seconds) || 0) + delta;
      }
      if (Number.isFinite(elevation)) {
        this._session.min_elevation = this._session.min_elevation === null ? elevation : Math.min(Number(this._session.min_elevation), elevation);
        this._session.max_elevation = this._session.max_elevation === null ? elevation : Math.max(Number(this._session.max_elevation), elevation);
      }

      this._session.last_ts = now;
      this._session.last_odometer = odometer;
      this._session.last_energy = energy;
      this._session.last_battery = battery;

      if (!activeNow) {
        if (!this._session.inactive_since) this._session.inactive_since = now;
        this._session.finishing = true;
        const delayMs = Number(c.finish_delay_seconds || 90) * 1000;
        if (now - this._session.inactive_since >= delayMs) {
          this._session.active = false;
          this._session.finishing = false;
          this._session.finished_at = this._dateText(now);
          this._session.finish_ts = now;
        }
      } else {
        this._session.inactive_since = null;
        this._session.finishing = false;
      }
      this._saveSession();
    }
  }

  _overrideText(entityId, fallback = null) {
    if (!entityId) return fallback;
    const state = this._state(entityId, null);
    return state === null ? fallback : state;
  }

  _computedDistance() {
    const s = this._session || this._newEmptySession();
    if (s.start_odometer !== null && s.last_odometer !== null) {
      return Math.max(0, Number(s.last_odometer) - Number(s.start_odometer));
    }
    return 0;
  }

  _computedEnergy() {
    const s = this._session || this._newEmptySession();
    if (s.start_energy !== null && s.last_energy !== null) {
      return Math.max(0, Number(s.start_energy) - Number(s.last_energy));
    }
    return 0;
  }

  _computedDurationSeconds() {
    const s = this._session || this._newEmptySession();
    if (!s.start_ts) return 0;
    const end = s.active ? Date.now() : (s.finish_ts || s.last_ts || Date.now());
    return Math.max(0, (end - Number(s.start_ts)) / 1000);
  }

  _reportDate() {
    const fromEntity = this._overrideText(this._config.report_date_entity, null);
    if (fromEntity) return fromEntity;
    const s = this._session || this._newEmptySession();
    return s.started_at || this._dateText(Date.now());
  }

  _statusText() {
    const s = this._session || this._newEmptySession();
    if (s.active && s.finishing) return 'Bitiyor';
    if (s.active) return 'Canlı';
    if (s.finished_at) return 'Final';
    return 'Hazır';
  }

  render() {
    if (!this.shadowRoot) return;
    if (!this._session) this._loadSession();
    const c = this._config;
    const s = this._session || this._newEmptySession();

    const live = this._liveAttrs();
    const distance = this._overrideText(c.trip_distance_entity, null) ?? (live ? this._formatNumber(this._attr(live, 'trip_km', 0), 2, '0.00') : this._formatNumber(this._computedDistance(), 2, '0.00'));
    const duration = this._compactDurationText(this._overrideText(c.trip_duration_entity, null) ?? (live ? String(this._attr(live, 'duration_text', '—')) : this._durationText(this._computedDurationSeconds())));
    const traffic = this._compactDurationText(this._overrideText(c.trip_traffic_entity, null) ?? (live ? String(this._attr(live, 'traffic_text', '—')) : this._durationText(s.traffic_seconds || 0)));
    const usedEnergyNum = live ? Number(this._attr(live, 'used_kwh', 0)) : this._computedEnergy();
    const tripEnergy = this._overrideText(c.trip_energy_entity, null) ?? this._formatNumber(usedEnergyNum, 2, '0.00');

    // alpha226: Tessie-style average = distance / moving time.
    // Overall average remains distance / total report duration.
    const computedDistance = this._computedDistance();
    const computedDurationSeconds = this._computedDurationSeconds();
    const computedMovingSeconds = Number(s.moving_seconds || 0);
    const avgOverallComputed = computedDurationSeconds > 0 ? computedDistance / (computedDurationSeconds / 3600) : 0;
    const avgMovingComputed = computedMovingSeconds > 0 ? computedDistance / (computedMovingSeconds / 3600) : avgOverallComputed;
    const avgSpeed = this._overrideText(c.trip_average_speed_entity, null) ?? (live ? this._formatNumber(this._attr(live, 'average_speed', this._attr(live, 'average_moving_speed', 0)), 0, '0') : this._formatNumber(avgMovingComputed, 0, '0'));
    const overallSpeed = live ? this._formatNumber(this._attr(live, 'average_overall_speed', avgOverallComputed), 0, '0') : this._formatNumber(avgOverallComputed, 0, '0');
    const trafficDelayText = live ? String(this._attr(live, 'traffic_delay_text', '')) : '';
    const trafficPercent = live ? Number(this._attr(live, 'traffic_congestion_percent', 0)) : 0;
    const trafficImpact = live ? String(this._attr(live, 'traffic_impact_label', '')) : '';
    const trafficRefSpeed = live ? Number(this._attr(live, 'traffic_reference_speed_kmh', 0)) : 0;
    const trafficType = live ? String(this._attr(live, 'traffic_reference_trip_type_label', '')) : '';
    const consumptionComputed = computedDistance > 0 ? usedEnergyNum / computedDistance * 100 : 0;
    const consumption = this._overrideText(c.trip_consumption_entity, null) ?? (live ? this._formatNumber(this._attr(live, 'consumption_kwh_100km', 0), 2, '0.00') : this._formatNumber(consumptionComputed, 2, '0.00'));
    const costComputed = usedEnergyNum * Number(c.supercharger_price || 0);
    const tripCost = this._overrideText(c.trip_cost_entity, null) ?? (live ? this._formatNumber(this._attr(live, 'supercharger_trip_cost', 0), 2, '0.00') : this._formatNumber(costComputed, 2, '0.00'));
    const climateDuration = this._compactDurationText(this._overrideText(c.trip_climate_entity, null) ?? (live ? String(this._attr(live, 'climate_text', '—')) : this._durationText(s.climate_seconds || 0)));

    const startBattery = this._overrideText(c.trip_battery_start_entity, null) ?? (live ? this._formatNumber(this._attr(live, 'start_battery', null), 1, null) : (s.start_battery !== null ? this._formatNumber(s.start_battery, 1, '—') : null));
    const endBattery = this._overrideText(c.trip_battery_end_entity, null) ?? (live ? this._formatNumber(this._attr(live, 'end_battery', null), 1, null) : (s.last_battery !== null ? this._formatNumber(s.last_battery, 1, '—') : null));
    const batteryText = live ? this._normalizeBatteryText(this._attr(live, 'battery_text', '—')) : (startBattery !== null && endBattery !== null ? `${startBattery}% -> ${endBattery}%` : '—');
    const batteryBar = endBattery !== null ? Math.max(0, Math.min(100, Number(endBattery) || 0)) : 0;

    const minElevation = this._overrideText(c.trip_elevation_min_entity, null) ?? (live ? this._formatNumber(this._attr(live, 'min_elevation', null), 0, null) : (s.min_elevation !== null ? this._formatNumber(s.min_elevation, 0, '—') : null));
    const maxElevation = this._overrideText(c.trip_elevation_max_entity, null) ?? (live ? this._formatNumber(this._attr(live, 'max_elevation', null), 0, null) : (s.max_elevation !== null ? this._formatNumber(s.max_elevation, 0, '—') : null));
    const elevationText = minElevation !== null && maxElevation !== null ? `${minElevation}–${maxElevation} m` : '— m';
    const status = live ? String(this._attr(live, 'status', 'Hazır')) : this._statusText();
    const aiPanel = this._liveAiPanelData(live, distance);
    const aiStatusLabel = aiPanel.status === 'generating' ? 'Hazırlanıyor' : (aiPanel.status === 'ready' ? 'Hazır' : (aiPanel.status === 'error' ? 'Hata' : 'Bekliyor'));
    const aiHistory = this._renderAiHistoryChips(aiPanel.segments, aiPanel.latest?.segment_index);

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          width: 100%;
          container-type: inline-size;
          --pom-white: rgba(255,255,255,.96);
          --pom-muted: rgba(255,255,255,.56);
          --pom-soft: rgba(255,255,255,.42);
          --pom-line: rgba(255,255,255,.11);
          --pom-green: #18d2aa;
          --pom-red: #ff5360;
          --pom-card: rgba(11,12,16,.86);
          font-family: Inter, Roboto, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        ha-card {
          position: relative;
          width: 100%;
          overflow: hidden;
          border-radius: 30px;
          border: 1px solid rgba(24,210,170,.18);
          background: linear-gradient(126deg, rgba(10,12,17,.94), rgba(28,20,18,.88));
          box-shadow: 0 24px 80px rgba(0,0,0,.46);
          backdrop-filter: blur(18px) saturate(150%);
          -webkit-backdrop-filter: blur(18px) saturate(150%);
          color: var(--pom-white);
        }
        .wrap { padding: clamp(14px, 1.8cqw, 28px); }
        .top { display: flex; align-items: flex-start; justify-content: space-between; gap: clamp(12px, 2cqw, 22px); }
        .title { font-size: clamp(24px, 3.2cqw, 40px); line-height: 1; font-weight: 950; letter-spacing: -0.03em; }
        .date { margin-top: 8px; color: var(--pom-muted); font-size: clamp(12px, 1.35cqw, 18px); font-weight: 850; }
        .badge { margin-top: 10px; display: inline-flex; align-items:center; gap: 7px; padding: 5px 10px; border-radius: 999px; background: rgba(24,210,170,.13); border: 1px solid rgba(24,210,170,.24); color: #95ffe4; font-weight: 900; font-size: 12px; letter-spacing:.02em; }
        .car {
          width: clamp(48px, 7cqw, 66px);
          height: clamp(48px, 7cqw, 66px);
          border-radius: 50%;
          background: radial-gradient(circle at 30% 30%, #ff8f9a 0 8%, #ff5664 26%, #ff4456 64%, #cb2139 100%);
          box-shadow: 0 0 28px rgba(255,79,91,.38), 0 0 0 1px rgba(255,255,255,.08) inset;
          display:flex;
          align-items:center;
          justify-content:center;
          font-size: clamp(20px, 3cqw, 29px);
          flex: 0 0 auto;
          cursor: pointer;
          border: 0;
          color: #fff;
          position: relative;
          z-index: 80;
          pointer-events: auto;
          transition: transform .22s ease, box-shadow .22s ease, filter .22s ease;
          position: relative;
        }
        .car::after {
          content: 'AI';
          position: absolute;
          right: -5px;
          bottom: -5px;
          min-width: 23px;
          height: 18px;
          padding: 0 6px;
          border-radius: 999px;
          background: linear-gradient(135deg, #60a5fa, #a855f7);
          color: #fff;
          font-size: 10px;
          font-weight: 950;
          letter-spacing: .05em;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 0 16px rgba(96,165,250,.42), 0 0 0 1px rgba(255,255,255,.18) inset;
        }
        .car:hover { transform: translateY(-1px) scale(1.04); box-shadow: 0 0 34px rgba(255,79,91,.52), 0 14px 28px rgba(255,79,91,.26), 0 0 0 1px rgba(255,255,255,.08) inset; }
        .car.open { filter: saturate(1.08); box-shadow: 0 0 0 1px rgba(255,255,255,.12) inset, 0 0 42px rgba(255,92,171,.36), 0 18px 34px rgba(48,22,116,.34); }
        .car .ai-mini-badge {
          position:absolute;
          right: -5px;
          bottom: -4px;
          min-width: 22px;
          height: 18px;
          padding: 0 5px;
          border-radius: 999px;
          background: linear-gradient(135deg, #60a5fa, #a855f7);
          border: 1px solid rgba(255,255,255,.35);
          color: #fff;
          display:flex;
          align-items:center;
          justify-content:center;
          font-size: 10px;
          line-height: 1;
          font-weight: 950;
          letter-spacing: .04em;
          box-shadow: 0 0 16px rgba(96,165,250,.46), 0 6px 14px rgba(0,0,0,.35);
          pointer-events: none;
        }
        .ai-panel {
          margin-top: clamp(14px, 1.7cqw, 20px);
          border-radius: 26px;
          border: 1px solid rgba(131, 115, 255, .26);
          background:
            radial-gradient(circle at top left, rgba(122, 91, 255, .16), transparent 36%),
            radial-gradient(circle at top right, rgba(255, 74, 137, .16), transparent 32%),
            linear-gradient(145deg, rgba(18,19,33,.92), rgba(15,16,27,.88));
          box-shadow: 0 20px 48px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.04);
          overflow: hidden;
          max-height: 0;
          opacity: 0;
          transform: translateY(-8px);
          transition: max-height .28s ease, opacity .24s ease, transform .24s ease, margin-top .24s ease;
          pointer-events: none;
        }
        .ai-panel.open { max-height: 380px; opacity: 1; transform: translateY(0); pointer-events: auto; }
        .ai-panel-inner { padding: clamp(16px, 2cqw, 24px); }
        .ai-comment-shell {
          margin-top: 15px;
          padding: clamp(15px, 1.8cqw, 22px);
          border-radius: 22px;
          border: 1px solid rgba(96,165,250,.18);
          background:
            radial-gradient(circle at left center, rgba(96,165,250,.12), transparent 36%),
            radial-gradient(circle at right center, rgba(236,72,153,.10), transparent 38%),
            rgba(255,255,255,.045);
          box-shadow: inset 0 1px 0 rgba(255,255,255,.05), 0 14px 34px rgba(0,0,0,.22);
        }
        .ai-panel-head { display:flex; align-items:flex-start; justify-content:space-between; gap: 14px; }
        .ai-kicker { font-size: clamp(11px, 1cqw, 14px); font-weight: 900; letter-spacing: .16em; color: rgba(180,195,255,.78); text-transform: uppercase; }
        .ai-title { display: none; }
        .ai-status-badge { display:inline-flex; align-items:center; gap: 8px; padding: 8px 12px; border-radius: 999px; background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.08); color: rgba(255,255,255,.84); font-size: 12px; font-weight: 900; white-space: nowrap; }
        .ai-status-dot { width: 10px; height: 10px; border-radius: 50%; background: #8b5cf6; box-shadow: 0 0 14px rgba(139,92,246,.46); }
        .ai-status-badge.ready .ai-status-dot { background: #18d2aa; box-shadow: 0 0 14px rgba(24,210,170,.46); }
        .ai-status-badge.generating .ai-status-dot { background: #ff5a95; box-shadow: 0 0 14px rgba(255,90,149,.52); animation: aiPulse 1.2s infinite; }
        .ai-status-badge.waiting .ai-status-dot { background: #60a5fa; box-shadow: 0 0 14px rgba(96,165,250,.42); }
        .ai-status-badge.error .ai-status-dot { background: #ff5360; box-shadow: 0 0 14px rgba(255,83,96,.42); }
        .ai-body {
          margin: 0;
          font-size: clamp(15px, 1.45cqw, 20px);
          line-height: 1.48;
          color: rgba(255,255,255,.94);
          font-weight: 760;
          letter-spacing: -0.01em;
          display: -webkit-box;
          -webkit-line-clamp: 5;
          -webkit-box-orient: vertical;
          overflow: hidden;
          max-height: calc(1.48em * 5);
        }
        .ai-progress-wrap { margin-top: 14px; }
        .ai-progress-head { display:flex; align-items:center; justify-content:space-between; gap: 12px; font-size: clamp(12px, 1.02cqw, 14px); font-weight: 850; color: rgba(255,255,255,.66); }
        .ai-progress {
          margin-top: 10px;
          height: 10px;
          border-radius: 999px;
          overflow: hidden;
          background: rgba(255,255,255,.08);
          box-shadow: inset 0 1px 3px rgba(0,0,0,.18);
        }
        .ai-progress-bar {
          height: 100%;
          width: ${Math.max(4, aiPanel.progress)}%;
          background: linear-gradient(90deg, #5eead4 0%, #60a5fa 48%, #a855f7 100%);
          border-radius: 999px;
          box-shadow: 0 0 18px rgba(96,165,250,.22);
        }
        .ai-history { margin-top: 14px; display:flex; flex-wrap:wrap; gap: 8px; }
        .ai-chip {
          display:inline-flex;
          align-items:center;
          padding: 7px 12px;
          border-radius: 999px;
          background: rgba(255,255,255,.05);
          border: 1px solid rgba(255,255,255,.08);
          color: rgba(255,255,255,.76);
          font-size: 12px;
          font-weight: 900;
        }
        .ai-chip.active {
          background: linear-gradient(135deg, rgba(96,165,250,.22), rgba(168,85,247,.22));
          border-color: rgba(121,128,255,.34);
          color: #fff;
          box-shadow: 0 10px 24px rgba(36,36,80,.24);
        }
        @keyframes aiPulse {
          0%,100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.22); opacity: .74; }
        }
        .divider { height: 1px; background: var(--pom-line); margin: clamp(14px, 1.8cqw, 22px) 0 0; }
        .metrics { display:grid; grid-template-columns: repeat(7, minmax(0, 1fr)); border-bottom: 1px solid var(--pom-line); }
        .metric { min-height: clamp(58px, 7.4cqw, 92px); display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center; border-right: 1px solid var(--pom-line); min-width:0; }
        .metric:last-child { border-right: 0; }
        .label { color: var(--pom-muted); font-weight: 950; font-size: clamp(10px, 1.18cqw, 16px); margin-bottom: clamp(5px, .9cqw, 9px); white-space: nowrap; text-align:center; width:100%; }
        .metric-value { display:flex; align-items:baseline; justify-content:center; width:100%; min-width:0; white-space:nowrap; text-align:center; }
        .value { font-size: clamp(18px, 2.25cqw, 34px); line-height: .95; font-weight: 950; letter-spacing: -0.04em; white-space: nowrap; }
        .value.red { color: var(--pom-red); text-shadow: 0 0 26px rgba(255,83,96,.25); }
        .unit { font-size: clamp(8px, .92cqw, 14px); color: var(--pom-muted); font-weight: 900; margin-left: 4px; letter-spacing: -0.03em; }
        .bottom {
          display:grid;
          grid-template-columns: 1.45fr 1fr 1fr 1fr;
          gap: 0;
          padding-top: clamp(14px, 2.2cqw, 18px);
          align-items: stretch;
        }
        .box {
          padding: 0 clamp(10px, 1.6cqw, 22px);
          border-right: 1px solid var(--pom-line);
          min-height: clamp(76px, 8.8cqw, 104px);
          min-width: 0;
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          text-align: center;
        }
        .box:first-child { padding-left: 0; }
        .box:last-child { border-right: 0; padding-right: 0; }
        .box-label {
          display:flex;
          align-items:center;
          justify-content:center;
          gap: 9px;
          width: 100%;
          color: rgba(255,255,255,.76);
          font-size: clamp(13px, 1.45cqw, 22px);
          font-weight: 950;
          margin-bottom: clamp(8px, 1.1cqw, 14px);
          white-space: nowrap;
          line-height: 1.1;
        }
        .box-value {
          color: var(--pom-white);
          font-size: clamp(20px, 2.4cqw, 38px);
          line-height: 1;
          font-weight: 950;
          white-space: nowrap;
          text-align: center;
          width: 100%;
        }
        .box-value.green { color: var(--pom-green); }
        .bar {
          margin: clamp(10px, 1.1cqw, 14px) auto 0;
          height: clamp(8px, .8cqw, 11px);
          border-radius: 999px;
          background: rgba(255,255,255,.12);
          overflow:hidden;
          width: min(100%, 320px);
        }
        .bar-inner { width: ${batteryBar}%; height:100%; border-radius:999px; background: linear-gradient(90deg, #10b981, #30e6b8); }
        @container (max-width: 700px) {
          .metrics { grid-template-columns: repeat(3, minmax(0, 1fr)); }
          .metric { border-bottom: 1px solid var(--pom-line); }
          .metric:nth-child(3), .metric:nth-child(6) { border-right: 0; }
          .metric:nth-child(n+4) { border-bottom: 0; }
          .bottom { grid-template-columns: repeat(2, minmax(0, 1fr)); row-gap: 18px; }
          .box:nth-child(2) { border-right: 0; }
          .box:nth-child(3) { padding-left: 0; }
          .box { min-height: 82px; }
        }
        @container (max-width: 480px) {
          .wrap { padding: 14px; }
          .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
          .metric { border-bottom: 1px solid var(--pom-line); }
          .metric:nth-child(2), .metric:nth-child(4), .metric:nth-child(6) { border-right: 0; }
          .metric:nth-child(3) { border-right: 1px solid var(--pom-line); }
          .metric:nth-child(n+5) { border-bottom: 0; }
          .bottom { grid-template-columns: 1fr; }
          .box { border-right: 0; padding: 0 0 18px 0; min-height: 0; }
          .box:last-child { padding-bottom: 0; }
          .box-label { font-size: 15px; }
          .box-value { font-size: 24px; }
          .ai-panel-head { flex-direction: column; }
          .ai-status-badge { align-self: flex-start; }
          .ai-title { font-size: 20px; }
        }
      </style>
      <ha-card>
        <div class="wrap">
          <div class="top">
            <div>
              <div class="title">${c.title}</div>
              <div class="date">${this._reportDate()}</div>
            </div>
            <button class="car ${this._commentPanelOpen ? 'open' : ''}" type="button" title="Live Trip AI yorum paneli" aria-label="Live Trip AI yorum panelini aç veya kapat">${c.car_icon}<span class="ai-mini-badge">AI</span></button>
          </div>
          <section class="ai-panel ${this._commentPanelOpen ? 'open' : ''}">
            <div class="ai-panel-inner">
              <div class="ai-panel-head">
                <div>
                  <div class="ai-kicker">Live Trip Comment</div>
                </div>
                <div class="ai-status-badge ${aiPanel.status}"><span class="ai-status-dot"></span>${aiStatusLabel}</div>
              </div>
              <div class="ai-comment-shell"><div class="ai-body">${this._escapeHtml(aiPanel.body)}</div></div>
              <div class="ai-progress-wrap">
                <div class="ai-progress-head">
                  <span>${this._escapeHtml(aiPanel.footer)}</span>
                  <span>${this._escapeHtml(aiPanel.remainingKm > 0.01 ? `Sonraki yorum ~${aiPanel.nextTarget.toFixed(0)} km` : 'Yorum eşik noktası aşıldı')}</span>
                </div>
                <div class="ai-progress"><div class="ai-progress-bar"></div></div>
              </div>
              ${aiHistory ? `<div class="ai-history">${aiHistory}</div>` : ``}
            </div>
          </section>
          <div class="divider"></div>
          <div class="metrics">
            <div class="metric"><div class="label">Mesafe</div><div class="metric-value"><span class="value">${distance}</span><span class="unit">km</span></div></div>
            <div class="metric"><div class="label">Süre</div><div class="metric-value"><span class="value">${duration}</span></div></div>
            <div class="metric"><div class="label">Trafik</div><div class="metric-value"><span class="value">${traffic}</span></div></div>
            <div class="metric"><div class="label">Ort. hız</div><div class="metric-value"><span class="value">${avgSpeed}</span><span class="unit">km/sa</span></div></div>
            <div class="metric"><div class="label">Genel ort.</div><div class="metric-value"><span class="value">${overallSpeed}</span><span class="unit">km/sa</span></div></div>
            <div class="metric"><div class="label">Enerji</div><div class="metric-value"><span class="value red">${tripEnergy}</span><span class="unit">kWh</span></div></div>
            <div class="metric"><div class="label">Tüketim</div><div class="metric-value"><span class="value">${consumption}</span><span class="unit">kWh/100</span></div></div>
          </div>
          <div class="bottom">
            <div class="box">
              <div class="box-label">▰ Batarya</div>
              <div class="box-value green">${batteryText}</div>
              <div class="bar"><div class="bar-inner"></div></div>
            </div>
            <div class="box"><div class="box-label">💰 Supercharger</div><div class="box-value">${tripCost} TL</div></div>
            <div class="box"><div class="box-label">❄️ Klima</div><div class="box-value">${climateDuration}</div></div>
            <div class="box"><div class="box-label">⛰️ Rakım</div><div class="box-value">${elevationText}</div></div>
          </div>
        </div>
      </ha-card>
    `;

    const toggle = this.shadowRoot.querySelector('.car');
    if (toggle) {
      toggle.onclick = (ev) => this._toggleAiPanel(ev);
      toggle.onpointerup = (ev) => {
        if (Date.now() - this._lastToggleAt > 250) this._toggleAiPanel(ev);
      };
      toggle.ontouchend = (ev) => {
        if (Date.now() - this._lastToggleAt > 250) this._toggleAiPanel(ev);
      };
    }
  }

  static getStubConfig() {
    return {
      type: 'custom:pom-tesla-trip-report-card-alpha341',
      live_trip_entity: '',
      speed_entity: '',
      odometer_entity: '',
      energy_remaining_entity: '',
      battery_level_entity: '',
      elevation_entity: '',
      climate_entity: '',
      shift_state_entity: '',
    };
  }
}

class PomTeslaTripReportCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { ...config };
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
  }

  _value(key) { return this._config?.[key] ?? ''; }

  _changed(ev) {
    const key = ev.target.dataset.key;
    let value = ev.target.value;
    if (ev.target.type === 'number') value = Number(value);
    const config = { ...this._config, [key]: value };
    this._config = config;
    this.dispatchEvent(new CustomEvent('config-changed', { detail: { config }, bubbles: true, composed: true }));
  }

  render() {
    if (!this.shadowRoot) this.attachShadow({ mode: 'open' });
    const fields = [
      ['title', 'Başlık'],
      ['live_trip_entity', 'Backend live trip sensor'],
      ['speed_entity', 'Speed entity'],
      ['shift_state_entity', 'Shift state entity'],
      ['active_entity', 'Trip active entity'],
      ['odometer_entity', 'Odometer entity'],
      ['energy_remaining_entity', 'Energy remaining kWh entity'],
      ['battery_level_entity', 'Battery level entity'],
      ['elevation_entity', 'Elevation entity'],
      ['climate_entity', 'Climate entity'],
      ['trip_distance_entity', 'Mesafe entity'],
      ['trip_duration_entity', 'Süre entity'],
      ['trip_traffic_entity', 'Trafik entity'],
      ['trip_average_speed_entity', 'Ortalama hız entity'],
      ['trip_energy_entity', 'Enerji entity'],
      ['trip_consumption_entity', 'Tüketim entity'],
      ['trip_cost_entity', 'Maliyet entity'],
      ['trip_climate_entity', 'Klima süre entity'],
      ['trip_elevation_min_entity', 'Min rakım entity'],
      ['trip_elevation_max_entity', 'Max rakım entity'],
    ];
    this.shadowRoot.innerHTML = `
      <style>
        .editor { display:grid; gap: 10px; padding: 8px 0; }
        label { display:grid; gap: 4px; color: var(--primary-text-color); font-size: 13px; }
        input { box-sizing:border-box; width:100%; padding: 8px 10px; border-radius: 6px; border: 1px solid var(--divider-color); background: var(--card-background-color); color: var(--primary-text-color); }
      </style>
      <div class="editor">
        ${fields.map(([key, label]) => `<label>${label}<input data-key="${key}" value="${this._value(key)}"></label>`).join('')}
        <label>Supercharger TL/kWh<input type="number" step="0.01" data-key="supercharger_price" value="${this._value('supercharger_price') || 9.8}"></label>
        <label>Start speed threshold<input type="number" step="0.1" data-key="start_speed_threshold" value="${this._value('start_speed_threshold') || 3}"></label>
        <label>Finish delay seconds<input type="number" step="1" data-key="finish_delay_seconds" value="${this._value('finish_delay_seconds') || 90}"></label>
      </div>`;
    this.shadowRoot.querySelectorAll('input').forEach((input) => input.addEventListener('change', (ev) => this._changed(ev)));
  }
}

if (!customElements.get('pom-tesla-trip-report-card-alpha341')) {
  customElements.define('pom-tesla-trip-report-card-alpha341', PomTeslaTripReportCard);
}
if (!customElements.get('pom-tesla-trip-report-card-editor')) {
  customElements.define('pom-tesla-trip-report-card-editor', PomTeslaTripReportCardEditor);
}
PomTeslaTripReportCard.getConfigElement = function() {
  return document.createElement('pom-tesla-trip-report-card-editor');
};

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'pom-tesla-trip-report-card-alpha341',
  name: 'POM Tesla Trip Report Card alpha341',
  description: 'Live Tesla trip report card for POM Tesla Report.',
});

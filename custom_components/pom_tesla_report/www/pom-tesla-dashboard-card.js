class PomTeslaDashboardCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = null;
  }

  setConfig(config) {
    this._config = {
      background_image: '',
      background_position: 'center',
      background_size: 'cover',
      battery_level_entity: '',
      battery_range_entity: '',
      battery_range_estimate_entity: '',
      speed_entity: '',
      power_entity: '',
      elevation_entity: '',
      energy_remaining_entity: '',
      outside_temp_entity: '',
      tire_pressure_entity: '',
      location_entity: '',
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
      title: 'Sürüş Raporu',
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  getCardSize() {
    return 8;
  }

  _state(entityId, fallback = '—') {
    if (!this._hass || !entityId) return fallback;
    const stateObj = this._hass.states[entityId];
    if (!stateObj || stateObj.state === 'unknown' || stateObj.state === 'unavailable') return fallback;
    return stateObj.state;
  }

  _attr(entityId, attr, fallback = undefined) {
    if (!this._hass || !entityId) return fallback;
    const stateObj = this._hass.states[entityId];
    return stateObj?.attributes?.[attr] ?? fallback;
  }

  _unit(entityId, fallback = '') {
    return this._attr(entityId, 'unit_of_measurement', fallback) || fallback;
  }

  _num(entityId, decimals = 0, fallback = '—') {
    const raw = this._state(entityId, null);
    const value = Number(raw);
    if (!Number.isFinite(value)) return fallback;
    return value.toFixed(decimals);
  }

  _dateText() {
    const d = new Date();
    const dd = String(d.getDate()).padStart(2, '0');
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const yyyy = d.getFullYear();
    const hh = String(d.getHours()).padStart(2, '0');
    const min = String(d.getMinutes()).padStart(2, '0');
    return `${dd}.${mm}.${yyyy} ${hh}:${min}`;
  }

  _tripBatteryText() {
    const start = this._state(this._config.trip_battery_start_entity, null);
    const end = this._state(this._config.trip_battery_end_entity, null);
    if (start !== null && end !== null) return `${start}% -> ${end}%`;
    const level = this._state(this._config.battery_level_entity, '—');
    return `%${level}`;
  }

  _elevationRangeText() {
    const min = this._state(this._config.trip_elevation_min_entity, null);
    const max = this._state(this._config.trip_elevation_max_entity, null);
    if (min !== null && max !== null) return `${min}–${max} m`;
    const current = this._state(this._config.elevation_entity, '—');
    return `${current} m`;
  }

  _bottomLocation() {
    const entity = this._config.location_entity;
    const postal = this._attr(entity, 'postal_town', null);
    const locality = this._attr(entity, 'locality', null);
    const state = this._state(entity, null);
    return postal || locality || state || this._config.location_label || 'Konum';
  }

  render() {
    if (!this.shadowRoot) return;

    const c = this._config;
    const speed = this._num(c.speed_entity, 0, '0');
    const battery = this._num(c.battery_level_entity, 0, '—');
    const range = this._num(c.battery_range_entity, 1, '—');
    const estimateRange = this._num(c.battery_range_estimate_entity, 1, range);
    const power = this._num(c.power_entity, 1, '0.0');
    const elevation = this._num(c.elevation_entity, 1, '—');
    const remainingEnergy = this._num(c.energy_remaining_entity, 1, '—');
    const outsideTemp = this._num(c.outside_temp_entity, 1, '—');
    const tirePressure = this._num(c.tire_pressure_entity, 1, '—');
    const location = this._bottomLocation();

    const tripDistance = this._num(c.trip_distance_entity, 2, '—');
    const tripDuration = this._state(c.trip_duration_entity, '—');
    const tripTraffic = this._state(c.trip_traffic_entity, tripDuration);
    const avgSpeed = this._num(c.trip_average_speed_entity, 0, '—');
    const tripEnergy = this._num(c.trip_energy_entity, 2, '—');
    const consumption = this._num(c.trip_consumption_entity, 2, '—');
    const tripCost = this._num(c.trip_cost_entity, 2, '—');
    const climateDuration = this._state(c.trip_climate_entity, '—');
    const elevationRange = this._elevationRangeText();

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          width: 100%;
          height: 100%;
          --pom-white: rgba(255,255,255,.96);
          --pom-muted: rgba(255,255,255,.55);
          --pom-soft: rgba(255,255,255,.35);
          --pom-green: #18d2aa;
          --pom-blue: #2f8df2;
          --pom-red: #ff5360;
          --pom-panel: rgba(10,12,18,.78);
          --pom-panel-2: rgba(24,24,30,.72);
          font-family: Inter, Roboto, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        ha-card {
          height: 100vh;
          min-height: 720px;
          width: 100%;
          position: relative;
          overflow: hidden;
          border: 0;
          border-radius: 0;
          background:
            linear-gradient(90deg, rgba(0,0,0,.78), rgba(0,0,0,.25), rgba(0,0,0,.65)),
            linear-gradient(180deg, rgba(0,0,0,.45), rgba(0,0,0,.72)),
            url('${c.background_image}');
          background-size: ${c.background_size};
          background-position: ${c.background_position};
          color: var(--pom-white);
        }

        .vignette {
          position: absolute;
          inset: 0;
          background: radial-gradient(circle at center 48%, rgba(255,255,255,.04), transparent 32%), radial-gradient(circle at bottom, rgba(0,0,0,.08), rgba(0,0,0,.56));
          pointer-events: none;
        }

        .top-left {
          position: absolute;
          top: 22px;
          left: 35%;
          transform: translateX(-50%);
          text-align: center;
          color: var(--pom-white);
          text-shadow: 0 5px 24px rgba(0,0,0,.65);
        }
        .top-left .label, .battery-box .label {
          font-size: clamp(18px, 2vw, 32px);
          letter-spacing: .13em;
          color: var(--pom-soft);
          font-weight: 800;
        }
        .top-left .value {
          font-size: clamp(30px, 4vw, 56px);
          font-weight: 900;
          line-height: .95;
        }
        .top-left .power-label { margin-top: 18px; }

        .speed-ring {
          position: absolute;
          top: 18px;
          left: 56%;
          transform: translateX(-50%);
          width: clamp(150px, 18vw, 240px);
          height: clamp(150px, 18vw, 240px);
          border-radius: 50%;
          background: radial-gradient(circle at center, rgba(0,0,0,.96) 0 52%, rgba(120,160,180,.18) 53% 100%);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          box-shadow: 0 0 80px rgba(0,0,0,.45), inset 0 0 24px rgba(255,255,255,.05);
        }
        .speed-ring .speed {
          font-size: clamp(58px, 8vw, 114px);
          line-height: .85;
          font-weight: 900;
        }
        .speed-ring .speed-label {
          margin-top: 14px;
          font-size: clamp(14px, 1.5vw, 24px);
          letter-spacing: .17em;
          color: rgba(255,255,255,.64);
        }

        .battery-box {
          position: absolute;
          top: 22px;
          right: 20%;
          text-align: left;
          text-shadow: 0 5px 24px rgba(0,0,0,.65);
        }
        .battery-box .battery {
          font-size: clamp(58px, 7vw, 105px);
          line-height: .9;
          font-weight: 900;
        }
        .battery-box .range {
          margin-top: 4px;
          color: var(--pom-green);
          font-size: clamp(24px, 3vw, 42px);
          font-weight: 700;
        }

        .report-card {
          position: absolute;
          left: 50%;
          top: 48%;
          transform: translate(-50%, -50%);
          width: min(72vw, 1280px);
          border-radius: 28px;
          background: linear-gradient(125deg, rgba(8,10,14,.93), rgba(24,18,16,.86));
          border: 1px solid rgba(255,255,255,.08);
          box-shadow: 0 26px 90px rgba(0,0,0,.58);
          backdrop-filter: blur(18px) saturate(150%);
          -webkit-backdrop-filter: blur(18px) saturate(150%);
          overflow: hidden;
        }
        .report-top {
          padding: 34px 34px 22px 34px;
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 20px;
        }
        .report-title {
          font-size: clamp(26px, 2.2vw, 40px);
          font-weight: 900;
          line-height: 1;
        }
        .report-date {
          margin-top: 10px;
          color: var(--pom-muted);
          font-size: clamp(14px, 1.2vw, 20px);
          font-weight: 700;
        }
        .car-button {
          width: 64px;
          height: 64px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #ff4f5b;
          box-shadow: 0 12px 30px rgba(255,79,91,.26);
          font-size: 24px;
          flex: 0 0 auto;
        }
        .metrics {
          display: grid;
          grid-template-columns: repeat(6, 1fr);
          border-top: 1px solid rgba(255,255,255,.09);
          border-bottom: 1px solid rgba(255,255,255,.09);
          padding: 24px 28px;
        }
        .metric {
          text-align: center;
          border-right: 1px solid rgba(255,255,255,.10);
          min-width: 0;
        }
        .metric:last-child { border-right: 0; }
        .metric .m-label {
          font-size: clamp(12px, 1.05vw, 17px);
          font-weight: 900;
          color: rgba(255,255,255,.48);
          margin-bottom: 12px;
        }
        .metric .m-value {
          font-size: clamp(26px, 2.6vw, 38px);
          font-weight: 900;
          line-height: 1;
          color: var(--pom-white);
        }
        .metric .m-unit {
          margin-left: 4px;
          font-size: clamp(11px, .95vw, 15px);
          color: rgba(255,255,255,.55);
          font-weight: 800;
        }
        .metric .red { color: var(--pom-red); }

        .bottom-report {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          padding: 24px 28px 30px 28px;
          gap: 0;
        }
        .bottom-box {
          padding: 0 28px;
          border-right: 1px solid rgba(255,255,255,.10);
          min-height: 88px;
        }
        .bottom-box:first-child { padding-left: 0; }
        .bottom-box:last-child { border-right: 0; padding-right: 0; }
        .bottom-box .b-label {
          display: flex;
          align-items: center;
          gap: 10px;
          color: rgba(255,255,255,.68);
          font-size: clamp(16px, 1.35vw, 22px);
          font-weight: 900;
          margin-bottom: 14px;
        }
        .bottom-box .b-value {
          font-size: clamp(25px, 2.3vw, 36px);
          font-weight: 900;
          color: var(--pom-white);
        }
        .bottom-box .b-value.green { color: var(--pom-green); }

        .battery-bar {
          margin-top: 16px;
          height: 10px;
          border-radius: 999px;
          overflow: hidden;
          background: rgba(255,255,255,.11);
        }
        .battery-bar-inner {
          height: 100%;
          width: ${Math.max(0, Math.min(100, Number(battery) || 0))}%;
          background: linear-gradient(90deg, #0ebc8c, #26e2b9);
          border-radius: 999px;
        }

        .bottom-nav {
          position: absolute;
          bottom: 34px;
          left: 50%;
          transform: translateX(-50%);
          width: min(64vw, 980px);
          min-height: 64px;
          background: rgba(6,8,16,.92);
          border: 1px solid rgba(255,255,255,.08);
          box-shadow: 0 18px 50px rgba(0,0,0,.58);
          border-radius: 36px;
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 8px 12px;
          color: white;
          overflow: hidden;
        }
        .nav-pill {
          height: 48px;
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 0 20px;
          border-radius: 28px;
          color: rgba(255,255,255,.82);
          font-size: clamp(13px, 1.1vw, 18px);
          font-weight: 900;
          white-space: nowrap;
        }
        .nav-pill.active {
          background: #007c62;
          color: white;
        }
        .nav-pill.location {
          background: #216fc5;
          color: white;
        }
        .nav-icon {
          flex: 0 0 auto;
          height: 48px;
          width: 48px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: rgba(255,255,255,.82);
          font-size: 22px;
        }

        @media (max-width: 1100px) {
          ha-card { min-height: 820px; }
          .top-left { left: 25%; }
          .speed-ring { left: 50%; }
          .battery-box { right: 8%; }
          .report-card { width: 82vw; top: 50%; }
          .metrics { grid-template-columns: repeat(3, 1fr); row-gap: 22px; }
          .metric:nth-child(3) { border-right: 0; }
          .bottom-report { grid-template-columns: repeat(2, 1fr); row-gap: 22px; }
          .bottom-nav { width: 82vw; }
        }
      </style>
      <ha-card>
        <div class="vignette"></div>
        <div class="top-left">
          <div class="label">EĞİM</div>
          <div class="value">${elevation} M</div>
          <div class="label power-label">POWER</div>
          <div class="value">${power}kW</div>
        </div>

        <div class="speed-ring">
          <div class="speed">${speed}</div>
          <div class="speed-label">SPEED</div>
        </div>

        <div class="battery-box">
          <div class="label">BATARYA</div>
          <div class="battery">${battery}%</div>
          <div class="range">${range} km</div>
        </div>

        <section class="report-card">
          <div class="report-top">
            <div>
              <div class="report-title">${c.title}</div>
              <div class="report-date">${this._dateText()}</div>
            </div>
            <div class="car-button">🚘</div>
          </div>
          <div class="metrics">
            <div class="metric"><div class="m-label">Mesafe</div><div><span class="m-value">${tripDistance}</span><span class="m-unit">km</span></div></div>
            <div class="metric"><div class="m-label">Süre</div><div><span class="m-value">${tripDuration}</span></div></div>
            <div class="metric"><div class="m-label">Trafik</div><div><span class="m-value">${tripTraffic}</span></div></div>
            <div class="metric"><div class="m-label">Ort. hız</div><div><span class="m-value">${avgSpeed}</span><span class="m-unit">km/sa</span></div></div>
            <div class="metric"><div class="m-label">Enerji</div><div><span class="m-value red">${tripEnergy}</span><span class="m-unit">kWh</span></div></div>
            <div class="metric"><div class="m-label">Tüketim</div><div><span class="m-value">${consumption}</span><span class="m-unit">kWh/100</span></div></div>
          </div>
          <div class="bottom-report">
            <div class="bottom-box">
              <div class="b-label">▰ Batarya</div>
              <div class="b-value green">${this._tripBatteryText()}</div>
              <div class="battery-bar"><div class="battery-bar-inner"></div></div>
            </div>
            <div class="bottom-box">
              <div class="b-label">💰 Supercharger</div>
              <div class="b-value">${tripCost} TL</div>
            </div>
            <div class="bottom-box">
              <div class="b-label">❄️ Klima</div>
              <div class="b-value">${climateDuration}</div>
            </div>
            <div class="bottom-box">
              <div class="b-label">⛰️ Rakım</div>
              <div class="b-value">${elevationRange}</div>
            </div>
          </div>
        </section>

        <nav class="bottom-nav">
          <div class="nav-pill active">⌘ ${estimateRange} km</div>
          <div class="nav-pill">⚡ ${remainingEnergy} kWh</div>
          <div class="nav-pill">◷ ${outsideTemp}°</div>
          <div class="nav-pill">🛞 ${tirePressure}</div>
          <div class="nav-pill location">📍 ${location}</div>
          <div class="nav-icon">🗺️</div>
          <div class="nav-icon">☷</div>
          <div class="nav-icon">🛰️</div>
          <div class="nav-icon">🔋</div>
        </nav>
      </ha-card>
    `;
  }

  static getStubConfig() {
    return {
      type: 'custom:pom-tesla-dashboard-card',
      background_image: '/local/png/tesla.png',
    };
  }
}

if (!customElements.get('pom-tesla-dashboard-card')) {
  customElements.define('pom-tesla-dashboard-card', PomTeslaDashboardCard);
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'pom-tesla-dashboard-card',
  name: 'POM Tesla Dashboard Card',
  description: 'Fullscreen Tesla-style dashboard card for POM Tesla Report.',
});

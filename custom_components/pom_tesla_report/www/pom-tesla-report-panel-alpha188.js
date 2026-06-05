class PomTeslaReportPanelAlpha188 extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  set hass(value) {
    this._hass = value;
    if (!this._rendered) {
      this._render();
    }
  }

  set narrow(value) {
    this._narrow = value;
  }

  set panel(value) {
    this._panel = value;
  }

  connectedCallback() {
    this._render();
  }

  _render() {
    if (!this.shadowRoot) return;
    this._rendered = true;
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          min-height: 100vh;
          box-sizing: border-box;
          background: radial-gradient(circle at top left, rgba(64, 145, 255, .20), transparent 32%),
                      linear-gradient(145deg, #070b16, #101827 48%, #05070d);
          color: #eef4ff;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
        }
        .wrap {
          max-width: 980px;
          margin: 0 auto;
          padding: 42px 22px;
        }
        .card {
          border: 1px solid rgba(255,255,255,.12);
          background: rgba(255,255,255,.07);
          box-shadow: 0 18px 70px rgba(0,0,0,.35);
          border-radius: 28px;
          padding: 28px;
          backdrop-filter: blur(18px);
        }
        h1 {
          margin: 0 0 10px;
          font-size: 30px;
          letter-spacing: -.03em;
        }
        p {
          color: rgba(238,244,255,.78);
          font-size: 15px;
          line-height: 1.55;
          margin: 8px 0;
        }
        code {
          padding: 3px 7px;
          border-radius: 8px;
          background: rgba(255,255,255,.10);
          color: #dce9ff;
        }
        .ok {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          margin-top: 18px;
          padding: 10px 14px;
          border-radius: 999px;
          background: rgba(50, 220, 140, .13);
          border: 1px solid rgba(50, 220, 140, .24);
          color: #b8ffd8;
          font-weight: 700;
        }
        .warn {
          margin-top: 20px;
          padding: 14px 16px;
          border-radius: 18px;
          background: rgba(255, 180, 64, .10);
          border: 1px solid rgba(255, 180, 64, .22);
        }
      </style>
      <div class="wrap">
        <div class="card">
          <h1>POM Tesla Report</h1>
          <p><b>alpha188 sidebar minimal shell</b></p>
          <p>Bu teşhis build’i sidebar açılışında hiçbir API çağrısı, kayıt okuma, ayar yükleme, timer veya Telegram işlemi başlatmaz.</p>
          <p>Amaç: Home Assistant restart’ının panel frontend ilk yüklemesinden mi, yoksa backend/API/runtime tarafindan mi geldiğini izole etmek.</p>
          <div class="ok">✓ Minimal panel yüklendi</div>
          <div class="warn">
            <p>Bu ekranda kalıp Home Assistant restart atmıyorsa sorun eski panelin ilk açılışta yaptığı API/data yüklemelerindedir.</p>
            <p>Eğer bu ekranda bile restart atıyorsa sorun panel registration/static serving veya entegrasyon setup tarafındadır.</p>
          </div>
          <p>Beklenen log marker: <code>POM Tesla Report alpha188 sidebar minimal shell loaded</code></p>
        </div>
      </div>
    `;
  }
}

customElements.define("pom-tesla-report-panel-alpha188", PomTeslaReportPanelAlpha188);

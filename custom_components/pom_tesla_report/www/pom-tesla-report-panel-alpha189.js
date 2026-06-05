class PomTeslaReportPanelAlpha189 extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._state = {
      status: "waiting",
      message: "Settings API testi birazdan başlayacak.",
      detail: "",
      elapsed: "",
    };
  }

  set hass(value) {
    this._hass = value;
    if (!this._rendered) this._render();
  }

  set narrow(value) {
    this._narrow = value;
  }

  set panel(value) {
    this._panel = value;
  }

  connectedCallback() {
    this._render();
    if (!this._started) {
      this._started = true;
      window.setTimeout(() => this._probeSettingsApi(), 800);
    }
  }

  async _probeSettingsApi() {
    const started = performance.now();
    this._state = {
      status: "running",
      message: "Sadece Settings API çağrılıyor...",
      detail: "GET /api/pom_tesla_report/settings",
      elapsed: "",
    };
    this._render();

    try {
      const response = await fetch("/api/pom_tesla_report/settings", {
        credentials: "same-origin",
        cache: "no-store",
      });
      const text = await response.text();
      const elapsed = `${Math.round(performance.now() - started)} ms`;
      let payload = null;
      try {
        payload = JSON.parse(text);
      } catch (_err) {}

      if (!response.ok) {
        this._state = {
          status: "error",
          message: `Settings API hata döndü: HTTP ${response.status}`,
          detail: text.slice(0, 2000),
          elapsed,
        };
      } else {
        const keys = payload && typeof payload === "object" ? Object.keys(payload).slice(0, 24).join(", ") : "JSON parse edilemedi";
        this._state = {
          status: "ok",
          message: "Settings API başarıyla döndü.",
          detail: `Süre: ${elapsed}\nAnahtarlar: ${keys}`,
          elapsed,
        };
      }
    } catch (err) {
      this._state = {
        status: "error",
        message: "Settings API çağrısı tarayıcı tarafında hata verdi.",
        detail: String(err && err.stack ? err.stack : err),
        elapsed: `${Math.round(performance.now() - started)} ms`,
      };
    }
    this._render();
  }

  _badgeText() {
    if (this._state.status === "ok") return "✓ Settings API başarılı";
    if (this._state.status === "error") return "✕ Settings API hata";
    if (this._state.status === "running") return "… Settings API çağrılıyor";
    return "Hazır";
  }

  _render() {
    if (!this.shadowRoot) return;
    this._rendered = true;
    const status = this._state.status;
    const badgeClass = status === "ok" ? "ok" : status === "error" ? "err" : "run";
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
        .wrap { max-width: 980px; margin: 0 auto; padding: 42px 22px; }
        .card {
          border: 1px solid rgba(255,255,255,.12);
          background: rgba(255,255,255,.07);
          box-shadow: 0 18px 70px rgba(0,0,0,.35);
          border-radius: 28px;
          padding: 28px;
          backdrop-filter: blur(18px);
        }
        h1 { margin: 0 0 10px; font-size: 30px; letter-spacing: -.03em; }
        p { color: rgba(238,244,255,.78); font-size: 15px; line-height: 1.55; margin: 8px 0; }
        code, pre {
          padding: 3px 7px;
          border-radius: 8px;
          background: rgba(255,255,255,.10);
          color: #dce9ff;
        }
        pre {
          white-space: pre-wrap;
          overflow-wrap: anywhere;
          margin-top: 16px;
          padding: 16px;
          max-height: 340px;
          overflow: auto;
        }
        .badge {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          margin-top: 18px;
          padding: 10px 14px;
          border-radius: 999px;
          font-weight: 800;
        }
        .ok { background: rgba(50, 220, 140, .13); border: 1px solid rgba(50, 220, 140, .24); color: #b8ffd8; }
        .err { background: rgba(255, 70, 90, .13); border: 1px solid rgba(255, 70, 90, .30); color: #ffd0d6; }
        .run { background: rgba(80, 150, 255, .13); border: 1px solid rgba(80, 150, 255, .28); color: #d5e8ff; }
        .warn {
          margin-top: 20px;
          padding: 14px 16px;
          border-radius: 18px;
          background: rgba(255, 180, 64, .10);
          border: 1px solid rgba(255, 180, 64, .22);
        }
        button {
          margin-top: 16px;
          border: 0;
          border-radius: 14px;
          padding: 12px 16px;
          background: #23a7e8;
          color: white;
          font-weight: 800;
          cursor: pointer;
        }
      </style>
      <div class="wrap">
        <div class="card">
          <h1>POM Tesla Report</h1>
          <p><b>alpha189 settings API probe</b></p>
          <p>Bu teşhis build’i sidebar açılışında sadece tek bir API çağrısı yapar:</p>
          <p><code>GET /api/pom_tesla_report/settings</code></p>
          <div class="badge ${badgeClass}">${this._badgeText()}</div>
          <p>${this._state.message}</p>
          <pre>${this._escape(this._state.detail || "")}</pre>
          <button type="button" id="retry">Tekrar test et</button>
          <div class="warn">
            <p>Bu ekranda restart olursa sorun Settings API payload/endpoint tarafındadır.</p>
            <p>Restart olmazsa bir sonraki testte Charge Records veya Trip Records API çağrısını izole edeceğiz.</p>
          </div>
          <p>Beklenen log marker: <code>POM Tesla Report alpha189 settings API probe loaded</code></p>
        </div>
      </div>
    `;
    const retry = this.shadowRoot.getElementById("retry");
    if (retry) retry.onclick = () => this._probeSettingsApi();
  }

  _escape(value) {
    return String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }
}

customElements.define("pom-tesla-report-panel-alpha189", PomTeslaReportPanelAlpha189);

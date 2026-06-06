Current active package: `2.2.0-alpha.373`. Active panel: `pom-tesla-report-panel-alpha373.js` / `pom-tesla-report-panel-alpha373`. Alpha360 fixes Proactive Automations / AI Alerts sending through the built-in POM Telegram path and dynamic listener registration; it preserves dashboard calculations, Live Trip, Charge popup layout, Telegram/AI trip report logic, candidate filter behavior, entity mapping, and Trip Records.

# Alpha356 note
Current active package: `2.2.0-alpha.373`. Active panel: `pom-tesla-report-panel-alpha373.js` / `pom-tesla-report-panel-alpha373`. Alpha359 only fixes top-area dashboard label language during dashboard rebuild; it preserves Charge popup tap-to-close behavior, Live Trip calculations, Telegram/AI report logic, candidate filter behavior, entity mapping, and Trip Records.

## alpha355 – Charge popup centering and close button alignment

- Based on alpha354.
- Charge popup Tesla small-screen visual tuning only: the popup card now centers against the actual viewport instead of being anchored left by the Lovelace stack/container.
- The close `X` button positioning was changed from right-offset media rules to viewport-center/card-edge geometry, so it should sit next to the popup instead of far away.
- Preserved Charge calculations, Live Trip calculations, candidate-trip filter behavior, Telegram, AI, Trip Records, Charge Records, entity mapping, and the stable Live Trip card type.
- Manifest/panel/frontend version: `2.2.0-dashboard-alpha355-charge-popup-center-close-align`; active panel: `pom-tesla-report-panel-alpha355.js` / `pom-tesla-report-panel-alpha355`.

## alpha353 – Charge Card Tesla small-screen responsive fix

- Based on alpha351. This is a layout-only dashboard update for the Charge Status popup/card on Tesla-sized small browser viewports such as roughly 1180×919.
- Charge popup wrapper no longer uses viewport-based inner width that could overflow the scaled card; the inner `charge-wrap` now follows the parent width.
- Added tablet/Tesla viewport breakpoints around <=1220 px and <=1185×940 to reduce scale, padding, gaps, ring size, card heights, chart height, and cost-card size so the full charge card fits better without cutting off.
- Live Trip calculations, candidate trip filter, Telegram, AI scheduling, Trip Records, and language logic were not changed.
- Manifest/panel/frontend version: `2.2.0-dashboard-alpha353-charge-card-size-close-tune`; active panel: `pom-tesla-report-panel-alpha353.js` / `pom-tesla-report-panel-alpha353`.

## alpha351 – Live Trip Card language-only fix

- Language-only update on top of alpha350. Live Trip calculations, candidate/short-maneuver logic, Telegram send flow, AI scheduling, Trip Records and dashboard layout were not changed.
- The stable Live Trip card now reads `report_language` / `language` from `sensor.pom_live_trip` and falls back to HA/config language. When English is selected, the card title, metric labels, status badge, waiting text, next-comment label and km/h units render in English.
- Backend Live Trip public attributes now expose `report_language`, and waiting text is generated in the configured report/app language.
- Panel-only Live Trip AI test state also writes `report_language`, so test comments and waiting/status text follow the current app language.
- Manifest/panel/frontend version: `2.2.0-dashboard-alpha351-live-trip-language-fix`; active panel: `pom-tesla-report-panel-alpha351.js` / `pom-tesla-report-panel-alpha351`.
- Stable card type remains `custom:pom-tesla-trip-report-card`; no versioned card type was introduced.

## alpha350 – Candidate filter safety / richer Live Trip AI details

- Short manoeuvre / candidate-trip filter was made safer for automatic post-drive reports: once distance or duration thresholds are reached, the trip is explicitly confirmed and the normal Trip Report PNG + built-in Telegram + AI story pipeline is allowed to run.
- Candidate/filter diagnostics are now stored in Live Trip attributes and Trip Records: `candidate_confirmed`, `candidate_confirm_reason`, `candidate_distance_km`, `candidate_duration_seconds`, `candidate_finish_decision`, `trip_finish_pipeline_started`, and related source/timestamp fields.
- Fixed a malformed short-manoeuvre settings block inherited from the alpha348 line so the filter cannot fail silently while checking duration thresholds.
- Live Trip AI segment comments now receive cached street/neighbourhood context and elevation delta/range data. AI/fallback comments can mention the current street/neighbourhood and whether elevation likely affected consumption.
- Live Trip card type remains the stable `custom:pom-tesla-trip-report-card`; no versioned-card rollback is changed.
- Manifest/panel/frontend version: `2.2.0-dashboard-alpha350-live-ai-rich-comment-test`; active panel: `pom-tesla-report-panel-alpha350.js` / `pom-tesla-report-panel-alpha350`.

## alpha348 – Built-in Telegram trip/AI safe-send

- HA Telegram entegrasyonu zorunlu değildir. Telegram gönderimleri POM'un kendi built-in bot token yolu ile yapılır; `telegram_bot` servisi sadece opsiyonel geriye uyumluluk/fallback olarak kalır.
- Otomatik sürüş bitişinde Trip Report PNG gönderilemezse artık tamamen sessiz kalmaz; mümkünse built-in Telegram üzerinden kısa metin fallback mesajı gönderir.
- Post-trip AI sürüş yorumu artık normal PNG raporunun Telegram'a başarıyla gitmesine bağlı değildir. Trip Records kaydı oluştuysa ve Telegram hedefi varsa AI yorumu built-in Telegram helper ile ayrıca gönderilmeye çalışılır.
- Trip Records/pipeline teşhis alanlarına `telegram_report_fallback_text_status`, `ai_story_schedule_status`, `ai_story_schedule_target_status` ve hata durumunda ilgili error bilgileri yazılır.
- Live Trip AI alpha346 stabil kart davranışı korunur; kart tipi hâlâ `custom:pom-tesla-trip-report-card` olarak kalır.
- Manifest/panel/frontend version: `2.2.0-dashboard-alpha348-built-in-telegram-trip-ai-safe-send`; active panel: `pom-tesla-report-panel-alpha348.js` / `pom-tesla-report-panel-alpha348`.

## alpha347 – Telegram trip report send helper fix

- Otomatik/servis sürüş bitişinde normal Trip Report PNG gönderimi artık doğrudan `hass.services.async_call("telegram_bot", "send_photo")` kullanmıyor; entegrasyonun ortak `async_telegram_send_photo()` helper'ı kullanılıyor.
- Böylece built-in Telegram bot modu aktifken de sürüş PNG raporu gönderilebilir; HA `telegram_bot.send_photo` servisi yoksa rapor sessizce atlanmaz.
- Ayrı harita PNG gönderimi de aynı helper'a taşındı.
- Trip Records içine `telegram_report_status` ve `telegram_map_status` yazılıyor; hata olursa `telegram_report_error` ve pipeline error kaydı kalıyor.
- Live Trip AI alpha346 stabil kart davranışı korunur; kart tipi hâlâ `custom:pom-tesla-trip-report-card` ve versioned card type'a dönülmedi.
- Manifest/panel/frontend version: `2.2.0-dashboard-alpha347-telegram-trip-send-helper-fix`; active panel: `pom-tesla-report-panel-alpha347.js` / `pom-tesla-report-panel-alpha347`.

## alpha346 – Live Trip card stable restore / AI interval display fix

- Dashboard Live Trip kart tipi alpha345'teki versioned `custom:pom-tesla-trip-report-card-alpha345` kullanımından tekrar stabil `custom:pom-tesla-trip-report-card` tipine döndürüldü; alpha345'te bazı HA/Lovelace oturumlarında kart komple yüklenmeyebiliyordu.
- Cache kırma yine korunur: `DASHBOARD_FRONTEND_VERSION` alpha346'ya güncellendi ve yeni stable JS URL'si yüklenecek.
- Live Trip AI bekleme/ilerleme hesaplaması kart içinde güçlendirildi: 1 km seçili ve sürüş 3.54 km ise kart artık stale `~10 km` yerine mesafe bazlı sonraki hedefi yaklaşık 4 km olarak türetir.
- Panel test yorumu gerçek segmenti tüketmeden dashboard attribute'larından okunmaya devam eder; stale waiting text otomatik hesaplanan metinle değiştirilir.
- Manifest/panel/frontend version: `2.2.0-dashboard-alpha346-live-trip-card-stable-restore`; active panel: `pom-tesla-report-panel-alpha346.js` / `pom-tesla-report-panel-alpha346`.

## alpha345 – Live Trip AI card cache/binding fix

- Support report proved backend/runtime state is correct: selected interval is `1 km`, `ai_live_next_target_km` is `1`, and the panel test comment is present in Live Trip attributes. The remaining problem was therefore frontend binding/cache, not the AI engine.
- Fixed stale frontend loading by bumping `DASHBOARD_FRONTEND_VERSION` from the old alpha342 value to alpha345, so Lovelace resource URLs receive a new cache-busting query.
- Dashboard YAML now uses the versioned card type `custom:pom-tesla-trip-report-card-alpha345` instead of the already-registered stable custom element. This bypasses browser/Home Assistant `customElements` cache where the old stable card could keep rendering `~10 km` even when backend attributes were `1 km`.
- The stable card and alpha345 bridge both define the alpha345 custom element, and the card now scores live-trip candidates so a stale duplicate entity should not beat the one with fresh AI attributes.
- No change to Trip Records, Charge Records, Auto Find, Telegram, HGS-removed clean structure, or Drive Dashboard layout.
- Manifest/panel/frontend version: `2.2.0-dashboard-alpha345-live-trip-ai-card-cache-bust`; active panel: `pom-tesla-report-panel-alpha345.js` / `pom-tesla-report-panel-alpha345`.

## alpha344 – Live Trip AI runtime/state sync fix

- Fixed the remaining case where the settings panel could save 1/5 km, but the Live Trip card still displayed stale 10 km because the running Live Trip engine/sensor was still using setup-time data.
- The live engine, scheduler, sensor attributes and panel endpoints now re-read the freshest config-entry/in-memory options before exposing `ai_live_segment_size_km`, `ai_live_next_target_km`, and waiting text.
- The sensor now self-heals the runtime interval right before Home Assistant exposes attributes to the dashboard card.
- Panel-only AI test comments still do not consume real driving segments; they update the Live Trip AI panel for visual testing only.
- Manifest/panel/frontend version: `2.2.0-dashboard-alpha344-live-trip-ai-runtime-state-fix`; active panel: `pom-tesla-report-panel-alpha344.js` / `pom-tesla-report-panel-alpha344`.

## alpha343 – Live Trip AI test/target fix

- Live Trip AI test button no longer consumes a real 1/5/10 km segment. A panel-only test comment is now shown without pushing the next real comment target from 5 km to 10 km.
- Live Trip report card now ignores panel-test segment indexes for progress/next-target calculations and defensively recomputes stale next-target/waiting text from the selected interval.
- Backend public Live Trip attributes now reconcile `ai_live_next_target_km` from completed real segments, preventing stale `Sonraki yorum ~10 km` display after 1 km or 5 km is selected.
- Manifest/panel/frontend version: `2.2.0-dashboard-alpha343-live-trip-ai-test-target-fix`; active panel: `pom-tesla-report-panel-alpha343.js` / `pom-tesla-report-panel-alpha343`.
- Stable dashboard card type remains `custom:pom-tesla-trip-report-card`; the stable JS also defines the alpha343 alias and `pom-tesla-trip-report-card-alpha343.js` is included for cache busting.

## alpha342 – Live Trip AI save/card rollback

- Alpha341 üzerine yeniden uygulanan düzeltme: hızlı Settings payload içine `live_trip_ai_segment_distance_km`, aralık seçenekleri ve ilgili Live Trip AI alanları eklendi. Bu nedenle 1/5/10 km seçimi sayfa refresh sonrası tekrar 10 km'ye düşmemeli.
- Dashboard Live Trip kart tipi tekrar stabil `custom:pom-tesla-trip-report-card` tipine döndürüldü. Bu, alpha341 versioned kart resource/type kaynaklı Live Trip kartının tamamen kaybolma riskini azaltır.
- Stabil `pom-tesla-trip-report-card.js` dosyası alpha342 alias'ını da tanımlar; ayrıca cache busting için `pom-tesla-trip-report-card-alpha342.js` köprü dosyası pakete eklendi.
- `AI yorumunu test et` akışı korunur: gerçek sürüş yokken panel-only test state üretir, Trip Records'a yazmaz ve Telegram'a göndermez; sadece Live Trip AI kartında test yorumunu göstermek için sensör state'ini günceller.
- Manifest/panel/frontend sürümü `2.2.0-dashboard-alpha342-live-trip-ai-save-card-rollback`; aktif panel `pom-tesla-report-panel-alpha342.js` / `pom-tesla-report-panel-alpha342`.

## alpha341 – Live Trip AI interval reliable save/test

- Live Trip AI yorum aralığı için ayrı, güvenilir bir panel endpoint eklendi: `/api/pom_tesla_report/live_trip_ai_interval`. 1/5/10 km seçimi artık dropdown değişince hemen kaydedilir ve aktif Live Trip state’ine senkronize edilir.
- `AI yorumunu test et` artık genel settings kaydına bağımlı değil; önce interval endpoint’iyle seçili aralığı kaydeder, sonra panel-only test yorumunu üretir.
- Test yorumu artık OpenAI ağına bağımlı kalmadan deterministik panel test yorumu yazar; amaç UI/sensor/popup akışını dışarı çıkmadan doğrulamaktır. Gerçek sürüş yorumları OpenAI/fallback pipeline’ını kullanmaya devam eder.
- Live Trip kartı alpha341 resource/type ile güncellendi: `custom:pom-tesla-trip-report-card-alpha341`.
- Panel ve manifest sürümü `2.2.0-dashboard-alpha341-live-trip-ai-interval-reliable-test`.

## alpha340 – Live Trip AI interval save/test fix

- Live Trip AI yorum aralığı (1/5/10 km) seçiminin panelde ve config-entry options içinde kalıcı kaydedilmesi güçlendirildi.
- “AI yorumunu test et” butonunda yanlış modal çağrısı düzeltildi; mevcut kırmızı bekleme popup’ı kullanılıyor.
- Test butonu seçili km aralığını önce kalıcı options’a yazar, sonra panel-only test yorumunu üretir.
- Panel JS cache/version alpha340’a çekildi: `pom-tesla-report-panel-alpha340.js` / `pom-tesla-report-panel-alpha340`.

## alpha339 – Live Trip AI interval/test fix

- Live Trip AI yorum aralığı 1/5/10 km olarak değiştirildiğinde aktif sürüş state’i artık hemen senkronize edilir; panelde eski 10 km metni kalmamalıdır.
- Aralık değişikliği sürüş ortasında yapılırsa Live Trip ana sayaçları sıfırlanmaz; yalnızca AI yorum baseline/sonraki hedef temiz şekilde yeniden hizalanır.
- “AI yorumunu test et” endpoint’i seçili 1/5/10 km aralığını doğrudan kullanır ve panelde test yorumu görünmesi için sensör state’ini günceller.
- Live Trip AI kartı alpha339’a taşındı: `custom:pom-tesla-trip-report-card-alpha339` / `pom-tesla-trip-report-card-alpha339.js`; stabil `pom-tesla-trip-report-card.js` içinde de alpha339 alias’ı korunur.
- Frontend bekleme metni artık stale `10 km` text’ine körü körüne güvenmez; sensör attribute’ları eskiyse bile seçili aralığa göre güvenli metin üretir.

## alpha338 – Live Trip AI test and 1/5/10 km intervals

- Live Trip AI comment interval is now configurable from Trip settings with 1 km, 5 km, and 10 km presets. Default remains 10 km.
- The scheduler now uses the selected interval for real drive comments instead of a fixed 10 km threshold.
- Added a panel-only “AI yorumunu test et / Test AI comment” button so the Live Trip AI popup can be tested without driving. It does not write Trip Records or send Telegram reports.
- Settings API, sensor attributes, and Live Trip AI segment JSON now preserve the selected interval.
- Active panel version updated to `pom-tesla-report-panel-alpha338.js` / `pom-tesla-report-panel-alpha338`.

## alpha337 – Live Trip AI 10 km scheduler fix

- Live Trip AI 10 km yorum tetikleyicisi güçlendirildi. Sonraki yorum eşiği artık eski/stale `live_ai_segment_next_target_km` değerine güvenmek yerine tamamlanan segment sayısından deterministik hesaplanıyor.
- 10 km eşiğinde 50 metre tolerans eklendi; odometre/polling yuvarlaması yüzünden yorumun kaçması engellendi.
- AI yorum üretim task watchdog eklendi: takılı kalan/gereğinden uzun süren görevler temizlenip tekrar denenebiliyor.
- Task cleanup düzeltildi; biten Live Trip AI task'leri store içinde stale kalmıyor.
- `sensor.pom_live_trip` attribute'larına `ai_live_scheduler_debug` ve `ai_live_last_prompt_ts` eklendi. Böylece 10 km yorumunun neden beklediği/çalıştığı destek raporundan görülebilir.
- Dashboard/Drive görsel yapısı, Trip Records, Telegram dönem komutları ve alpha336 haftalık görsel layout fix korunmuştur.

## alpha336 – Weekly trip report renderer layout fix

- `/tripweek`, `/triptoday`, `/tripall` monthly-style trip summary PNG renderer layout was tightened. Long Turkish start/end addresses are now clipped to safe single-line rows, preventing them from overlapping the lower metric row.
- Trip record metric values now use safer fixed columns and smaller fonts so consumption, speed and cost fields no longer collide in Telegram-compressed images.
- Weekly/daily period subtitle now says selected period instead of active month.
- Active panel version is now `pom-tesla-report-panel-alpha336.js` / `pom-tesla-report-panel-alpha336`; manifest version is `2.2.0-dashboard-alpha336-weekly-trip-render-layout-fix`.

## alpha335 – Telegram trip period commands and duplicate send guard

- Telegram trip commands now have a stronger duplicate-event guard. This prevents the same `/tripall` or `/single` command from being handled twice when both `telegram_text` and `telegram_command` events, or both built-in polling and Home Assistant Telegram events, deliver the same message.
- Added two deterministic trip period commands:
  - `/triptoday`: sends today's trip summary visual pages.
  - `/tripweek`: sends the current week's trip summary visual pages, using Monday as the start of the week and Sunday as the end.
- Command help now lists `/triptoday` and `/tripweek` in both Turkish and English.
- Trip period visuals reuse the existing monthly trip renderer with period-specific labels, captions and empty-data messages.
- Active panel version is now `pom-tesla-report-panel-alpha335.js` / `pom-tesla-report-panel-alpha335`; manifest version is `2.2.0-dashboard-alpha335-telegram-trip-periods-dedupe`.

## alpha334 – Candidate Trip / Short Maneuver filter

- Live Trip start logic now supports a candidate-trip stage to prevent tiny garage/parking repositioning movements from becoming a new Live Trip.
- New Live Trip settings were added under Sürüş > Canlı Sürüş: short parking maneuvers toggle, real-trip confirmation distance, and real-trip confirmation time.
- Default behavior: short maneuver filtering is enabled, with a 0.30 km or 2 minute confirmation threshold. If the car returns to Park before either threshold is reached, the movement is ignored and no new Live Trip report is started.
- The normal automatic trip report path also checks the same short-maneuver thresholds before sending/writing a delayed report, so tiny garage moves should not create Telegram/Trip Records noise.
- `sensor.pom_live_trip` now exposes candidate/short-maneuver diagnostics such as candidate_trip, candidate_confirmed, ignored_short_maneuver and short_maneuver_reason.
- Active panel version is now `pom-tesla-report-panel-alpha334.js` / `pom-tesla-report-panel-alpha334`; manifest version is `2.2.0-dashboard-alpha334-candidate-trip-short-maneuver`.

## alpha333 – Dashboard görsel yükleme anında uygulanır

- Dashboard arka plan görseli yükleme akışı düzeltildi: kullanıcı `Yükle / Upload` düğmesine bastığında görsel artık yalnızca dosyaya yazılıp beklemez; seçenekler config entry + runtime data içine anında işlenir ve Tesla/Drive dashboard YAML dosyaları aynı istek içinde yeniden üretilir.
- Park, şarj, sürüş, Drive araç görseli ve Drive lastik görseli slotlarının tamamı için `Dashboard ayarlarını kaydet` düğmesine ayrıca basma zorunluluğu kaldırıldı.
- Reset/varsayılana dön işlemleri de aynı şekilde dashboard rebuild tetikler ve yeni görsel ayarı hemen uygulanır.
- Kırmızı bekleme popup'ı yükleme + YAML rebuild bitene kadar ekranda kalır; kullanıcı işlem tamamlanmadan sayfayı kapatmaması gerektiğini net görür.
- Aktif panel sürümü alpha333 olarak güncellendi: `pom-tesla-report-panel-alpha333.js` / `pom-tesla-report-panel-alpha333`.

## alpha332 – Global bekleme popup, timer ve dil desteği

- Backup bekleme popup’ı TR/EN uygulama diline duyarlı hale getirildi ve canlı geçen süre timer’ı eklendi.
- Aynı kırmızı temalı işlem popup’ı artık AI, Report ve Dashboard sekmelerindeki Fast Auto Find / Deep Auto Find işlemlerinde de görünür; işlem tamamlanınca otomatik kapanır.
- Dashboard Background görsel yükleme işlemlerine de aynı popup bağlandı; yükleme yüzdesi ve geçen süre gösterilir.
- Eski Auto Find banner’ı işlem popup’ı açıkken gizlenir, böylece kullanıcı aynı anda iki ayrı uyarı görmez.
- Aktif panel sürümü alpha332 olarak güncellendi: `pom-tesla-report-panel-alpha332.js` / `pom-tesla-report-panel-alpha332`.

## alpha331 – Backup UI sadeleştirme ve bekleme popup

- General Settings içindeki Ayar yedekleme alanı sadeleştirildi. Kullanıcı için ana seçenek artık büyük “Tam yedek” kartı; sadece ayarlar ve sadece kayıtlar daha küçük ikincil seçenekler olarak kaldı.
- “Tam yedek JSON” butonu gelişmiş/küçük seçenek olarak alt satıra taşındı; ana akışta kullanıcıyı karıştırmayacak şekilde geri planda tutuldu.
- Tam yedek veya kayıt export işlemi sırasında kırmızı temalı, blur arka planlı bekleme popup’ı eklendi. Popup kullanıcıya işlemin sürdüğünü ve sayfayı kapatmamasını net gösterir.
- Aktif panel sürümü alpha331 olarak güncellendi: `pom-tesla-report-panel-alpha331.js` / `pom-tesla-report-panel-alpha331`.

## alpha330 – Full backup export

- Based on alpha329. Added a safe export-only backup layer; no restore/import overwrite behavior was added in this version.
- General Settings > Settings backup now includes three separate export actions:
  - Export settings: existing settings-only JSON remains unchanged.
  - Export records: trip and charge records are downloaded as a records-only JSON.
  - Export full backup: downloads a ZIP containing settings, trip records, charge records, manual tracking records, Live Trip debug state, Live Trip AI segment JSON files, dashboard resource status, generated dashboard YAML files, and uploaded dashboard background image files.
- Added `/api/pom_tesla_report/backup_export` backend endpoint with `format=zip` and `format=json` support.
- Versioned frontend/cache/card identifiers moved to alpha330 (`pom-tesla-report-panel-alpha330.js`, `pom-tesla-trip-report-card-alpha330.js`, `custom:pom-tesla-trip-report-card-alpha330`).
- Restore/import is intentionally deferred to a later alpha so merge vs replace behavior can be implemented safely.

## alpha329 – Live Trip AI comment focus panel

- Live Trip AI popup panel was simplified around the actual comment: `Bölüm` and `Şu anki mesafe` info boxes were removed because those values are already visible elsewhere on the dashboard.
- The comment now sits inside a larger premium glass/glow text shell, giving the AI message more visual weight and more readable space.
- AI comment guard was relaxed from ultra-short 2 sentences to a compact in-car paragraph of up to 4 short sentences / about 450 characters; frontend clamps the visible comment to 5 lines so it still stays inside the panel.
- Versioned card/resource moved to `pom-tesla-trip-report-card-alpha329.js` and `custom:pom-tesla-trip-report-card-alpha329`; stable bridge JS also defines the alpha329 alias.
- Manifest/panel/frontend cache version updated to `2.2.0-dashboard-alpha329-live-trip-ai-comment-focus`.

## alpha328 – Live Trip AI panel tidy / short-comment guard

- Live Trip AI popup panel cleaned up: redundant large `Live Trip AI` heading was removed, leaving only the compact `Live Trip Comment` header and the actual comment text.
- Technical `Kaynak` box was removed from the in-car panel; only segment and current distance remain visible.
- Live Trip AI comments are now guarded on both backend and frontend: prompt asks for max 2 sentences / ~280 characters, backend trims long replies to about 300 characters, and the dashboard clamps comment display to 3 lines.
- Versioned card/resource moved to `pom-tesla-trip-report-card-alpha328.js` and `custom:pom-tesla-trip-report-card-alpha328`; stable bridge JS also defines the alpha328 alias.
- Manifest/panel/frontend cache version updated to `2.2.0-dashboard-alpha328-live-trip-ai-panel-tidy`.

## alpha327 – Live Trip AI resource bridge fix

- Alpha326'daki Live Trip kartı `Configuration error` hatasını düzeltmek için versioned card resource yükleme yolu güçlendirildi.
- `custom:pom-tesla-trip-report-card-alpha327` artık hem kendi `pom-tesla-trip-report-card-alpha327.js` dosyasından hem de stabil `pom-tesla-trip-report-card.js` resource'u içinden alias olarak tanımlanıyor. Böylece Lovelace resource yükleme sırası/cache yarışı kartı düşürmemeli.
- Dashboard template alpha327 kart tipine geçirildi.
- Backend'deki ayrı JSON + 10 km AI segment yorum sistemi korunuyor.
- Live Trip ortasındaki trafik modeli satırı kaldırılmış yapı korunuyor; AI panel kırmızı araç düğmesindeki AI rozetinden açılır.

## alpha326 – Live Trip AI versioned card resource

- Live Trip AI panelin görünmemesinin asıl nedeni düzeltildi: Dashboard `custom:pom-tesla-trip-report-card` yerine yeni versioned kartı kullanır: `custom:pom-tesla-trip-report-card-alpha326`.
- Yeni Lovelace resource eklendi: `/pom_tesla_report/pom-tesla-trip-report-card-alpha326.js?v=2.2.0-dashboard-alpha326-live-trip-ai-versioned-card`. Böylece eski tarayıcı/customElements cache’i yeni AI panelini engelleyemez.
- Kırmızı araç düğmesine görünür `AI` rozeti eklendi; click/pointer/touch toggle daha sağlam hale getirildi.
- Live Trip kartındaki debug amaçlı `Trafik modeli` satırı kaldırıldı; yorum paneli artık tek hedef içerik.
- Backend ayrı JSON segment sistemi ve 10 km segment AI yorum mantığı korunur.

## alpha325 – Live Trip AI cache bust / görünür AI düğmesi

- Dashboard frontend resource cache sürümü güncellendi: `DASHBOARD_FRONTEND_VERSION` artık alpha325 değerini kullanıyor. Önceki alpha324 paketinde resource URL hâlâ eski alpha284 cache anahtarını kullandığı için tarayıcı eski Trip Report Card JS'ini tutabiliyordu; bu yüzden kırmızı düğme AI panelini açmıyordu.
- Sürüş Raporu kırmızı butonunda küçük `AI` rozeti gösterildi; kullanıcı panelin nereden açılacağını daha net görecek.
- Live Trip AI segment backend ve ayrı JSON yapısı korunuyor. Kart tipi tekrar stabil `custom:pom-tesla-trip-report-card` olarak kalıyor.
- Aktif panel sürümü: `pom-tesla-report-panel-alpha325.js` / `pom-tesla-report-panel-alpha325`.

## alpha324 – Live Trip AI original card fix

- alpha323'te Live Trip kartını yeni custom-card tag adına taşımak bazı Home Assistant oturumlarında `Configuration error` ürettiği için bu değişiklik geri alındı.
- Dashboard tekrar stabil `custom:pom-tesla-trip-report-card` tipini kullanıyor.
- AI yorum paneli kodu aynı mevcut `pom-tesla-trip-report-card.js` içine işlendi; ekstra `pom-tesla-trip-report-card-alpha323.js` kaynağı kaldırıldı.
- Amaç: eski/çift custom element çakışmasını kaldırırken kırmızı araç düğmesiyle açılıp kapanan Live Trip AI panelini korumak.
- Backend tarafındaki ayrı JSON segment kaydı ve 10 km segment mantığı korunuyor.
- Aktif panel: `pom-tesla-report-panel-alpha324.js` / `pom-tesla-report-panel-alpha324`.

## alpha323 – Live Trip AI card click/cache fix

- Live Trip / Sürüş Raporu kartındaki AI panel görünmeme sorunu için kart custom element adı versionlandı: `pom-tesla-trip-report-card-alpha323`.
- Dashboard template artık doğrudan `custom:pom-tesla-trip-report-card-alpha323` kullanıyor; böylece tarayıcıda eski `pom-tesla-trip-report-card` customElements kaydı kalmış olsa bile yeni AI panel kodu yüklenir.
- Yeni frontend resource eklendi: `/pom_tesla_report/pom-tesla-trip-report-card-alpha323.js` ve `/local/pom_tesla_report/pom-tesla-trip-report-card-alpha323.js`.
- alpha322 Live Trip AI segment JSON, 10 km segment yorumları, kırmızı buton toggle paneli ve fallback akıllı özet mantığı korunur.
- Aktif panel sürümü alpha323 olarak güncellendi.

# POM Tesla Dashboard Map - alpha294

## Active identifiers
- Panel JS: `pom-tesla-report-panel-alpha294.js`
- Custom element: `pom-tesla-report-panel-alpha294`
- Manifest version: `2.2.0-dashboard-alpha294-switcher-update-speed-source`

## Dashboard files
- Main Tesla dashboard: `pom_tesla_dashboard.yaml`
- Drive dashboard: `pom_tesla_drive_dashboard.yaml`

## Navigation
- The dashboard switcher is app-owned and injected as a fixed body-level floating control.
- Main Tesla dashboard switch opens `/pom-drive-dashboard/drive`.
- Drive dashboard switch opens `/tesla-dashboard/tesla`.
- The switcher is intentionally not inside the Drive Dashboard title/header area, so it can remain visible when the title/header area is clipped by the fullscreen layout.

## Fullscreen approach
- No `kiosk_mode:` YAML block is used.
- No external Kiosk Mode dependency is required.
- The existing integration fullscreen helper/controller remains the source of fullscreen behavior.
- The shared fullscreen controller mirrors `switch.pom_tesla_dashboard_fullscreen` into localStorage key `pomTeslaDashboardFullscreen` so page navigation/refresh can use the last known fullscreen intent before HA state hydration completes.
- Drive Dashboard has an early chrome guard in `pom-tesla-drive-dashboard-card.js` and a light app-switcher-side cleanup to reduce the first-load flash of HA header/update icons when fullscreen mode is already active.

## Drive Dashboard speed source
- Drive Dashboard speed reads generated config key `entities.speed`.
- That key is created from Entities > Dashboard role `dashboard_top_speed`, which is the same role used by the main Tesla dashboard top speed binding.
- If the generated YAML has no `entities.speed` binding, fallback order is `sensor.tesla_speed`, then `sensor.pom_speed`.

## Preserved
- Existing Auto Find and entity selection pipeline
- Trip/Charge/AI/Telegram/report systems
- HGS-removed clean structure
- Footer `Last Update` in the Drive Dashboard


## alpha302 – Drive default bundled visuals
- Based on stable alpha294 line (`pom_tesla_report(6).zip`).
- Added bundled default Drive center vehicle visual and bundled default Tire Pressure vehicle visual.
- New static assets are served from `/pom_tesla_report/drive-default-vehicle.png` and `/pom_tesla_report/drive-default-tire-top.png`.
- `pom-tesla-drive-dashboard-card.js` now uses the bundled Drive vehicle image automatically when no custom `vehicle_image` is configured.
- Tire Pressure card now shows a bundled top-view tire visual by default; no user setup is required on first install.
- Existing user override flow for custom Drive vehicle image remains available.
- No chrome-less app/iframe wrapper changes were included; stable alpha294 line is preserved.


## alpha303 – Drive center image scale tuning
- Based on alpha302.
- Tuned the default Drive center vehicle visual so it no longer fills the whole Drive card background.
- The bundled vehicle image is now rendered smaller, centered lower in the card, visually closer to the requested reference layout.
- Tire Pressure bundled visual remains unchanged from alpha302.
- Stable alpha294 project line remains preserved; no chromeless app/iframe work included.


## alpha304 – Remove bundled Drive visuals, add Tire Pressure image upload and safer uploads
- Based on stable alpha294 line via alpha303 working tree.
- Removed the generated bundled Drive center and Tire Pressure default image embedding; those generated PNG assets are no longer packaged.
- Drive center visual now appears only when the user sets a custom Drive vehicle image, otherwise the original lightweight inline fallback remains.
- Added a separate Tire Pressure image/background upload slot in Dashboard > Backgrounds.
- Drive Dashboard YAML now supports `tire_pressure_image` and passes it into `pom-tesla-drive-dashboard-card`.
- Dashboard media upload now uses multipart upload instead of base64 data URLs to reduce browser/HA frontend lock-ups.
- Upload progress is shown inside the upload card when the browser provides progress events.
- No chromeless app/iframe/kiosk work included; stable alpha294 dashboard line remains preserved.


## alpha305 – Tire background cover behavior
- Based on alpha304 stable line.
- Tire Pressure uploaded image now fills the whole Tire Pressure card as a background using cover mode.
- Added dark overlay layers for readability so PSI values remain visible over the image.
- Removed the small centered tire preview behavior when a Tire Pressure background image is configured.
- Drive/Tire upload flow, multipart upload, and progress UI from alpha304 are preserved.


## alpha306 – Drive background cover behavior
- Based on alpha305 stable line.
- Drive uploaded image now uses the whole Drive card as a cover background, matching the Tire Pressure background behavior style.
- Added layered dark overlays and a mild blue glow for readability of speed/shift labels over the image.
- Existing upload flow and progress UI remain unchanged.


## alpha307 – Remove Drive background center glow
- Based on alpha306.
- Removed the extra circular blue radial glow layer from the Drive card background when a custom Drive image is configured.
- Drive image still uses cover mode with only the readability dark overlays preserved.
- Tire Pressure cover background behavior from alpha305 is unchanged.


## alpha308 – Drive power moved to Energy card
- Based on alpha307 stable line.
- Removed the `0.0 kW` power readout from under the central speed value in the Drive card.
- Added a right-side Energy block inside the `Energy & Charging` card, visually echoing the Drive shift-state style.
- The new Energy block shows a blue `Energy` label with the current white power value beneath it.
- Drive glow removal from alpha307 and Drive/Tire background cover behavior remain preserved.


## alpha309 – Climate comfort status card
- Based on alpha308 stable line.
- Redesigned the Drive Dashboard Climate card to more closely match the requested compact layout.
- Climate card now shows Inside and Outside temperatures on the top row, Driver & Passenger Set on a separate row, and a bottom `Comfort: ...` status row.
- Comfort status is calculated dynamically using inside temperature, outside temperature, and the climate set temperatures.
- Very uncomfortable cases (for example very high inside temperature such as 50°C, even if outside is 30°C) are shown as red `Bad`.
- Added status colors: green `Good`, amber `Okay`, red `Bad`, and grey `Unknown`.


## alpha310 – Climate card matched closer to reference
- Based on alpha309 stable line.
- Reworked Climate card spacing, typography, and footer strip to visually align more closely with the provided reference image.
- Comfort evaluation was relaxed so normal cabin cases such as ~25.5°C inside and ~24.5°C outside are not incorrectly marked as `Bad`.
- If driver/passenger set temperatures are identical, the card now shows a single set-point value instead of duplicating it.
- Enlarged the thermometer icon, reduced the set temperature font size, and moved the Comfort row into a bottom shaded strip similar to the reference.


## alpha311 – Climate footer visibility fix
- Based on alpha310 stable line.
- Fixed the Climate card layout so the bottom Comfort footer strip stays visible inside the card instead of being pushed below the visible area.
- Climate card now uses a flex-column card layout with the content area sized correctly under the header.
- Slightly tightened the Climate spacing so the footer remains visible more reliably on shorter card heights.


## alpha312 – Climate width alignment and Drive header cleanup
- Based on alpha311 stable line.
- Fixed the Climate card internal layout so the footer strip no longer causes the card to visually stretch wider than the Drive card above it.
- Reworked Climate padding/margins so the footer stays inside the card without changing the grid alignment.
- Removed the extra top `Drive` view title by making the Drive dashboard Lovelace view title blank while keeping the dashboard itself available in the sidebar.


## alpha314 – Climate strip removal and energy separator
- Based on alpha313 stable line.
- Removed the Climate card bottom `Comfort: ...` strip because it was stretching / destabilizing the mini-card row alignment.
- Added a horizontal separator under `Energy Remaining` inside the Energy & Charging card.
- Kept the split Energy layout from alpha313.


## alpha315 – Energy layout repair and mini-card grid fix
- Based on alpha314.
- Repaired the Energy & Charging card layout by restoring explicit `energy-top`, `energy-main`, `energy-side`, and `energy-body` structure/CSS.
- Added the intended separator under `Energy Remaining`.
- Removed the forced `width:100%` behavior from the Climate card and tightened mini-card sizing so the mini-card grid stays visually aligned.


## alpha316 – Drive mini-grid lock and energy card rebuild
- Based on alpha315.
- Explicitly assigned grid positions for all six mini cards in Drive Dashboard to prevent width drift.
- Rebuilt the Energy & Charging card into a stable split layout with a right-side Energy column and a separator under Energy Remaining.
- Removed the Climate card forced full-width behavior and locked mini-card box sizing more strictly.
- Updated the visible version badge to match the active alpha.


## alpha317 – Grid alignment, full-width separator, and version badge fix
- Based on alpha316.
- Fixed Drive Dashboard mini-card column alignment by making the lower mini-grid use the same 1.02 / 1.02 / 1.04 column ratios as the top grid.
- Moved the Energy & Charging separator outside the left sub-column so it spans the whole card, including the Energy power column.
- Updated manifest, panel constants, active panel JS file, custom element name, and visible frontend build badge to `alpha317-grid-version-separator-fix`.
- Removed unused Climate comfort-strip CSS after the strip was removed, reducing the chance of hidden layout side effects.


## alpha318 – Battery card left padding tune
- Based on alpha317.
- Moved the Battery percentage/bar block slightly right so the `78%` value is not too close to the left card edge.
- Updated manifest, panel constants, active panel JS file, custom element name, and visible frontend build badge to `alpha318-battery-left-padding`.


## alpha319 – Drive Dashboard language localization
- Based on alpha318 stable line.
- Drive Dashboard now receives the global `app_language` option from the generated YAML.
- `pom-tesla-drive-dashboard-card.js` now localizes Drive page labels according to application language: Turkish when `tr`, English when `en`.
- Localized Battery, Drive, Route, Energy & Charging, Climate, Elevation, Vehicle Health, Tire Pressure, Diagnostics, and footer labels.
- Localized status text such as charging/disconnected/running/all closed/normal and time-to-arrival minute suffix.
- Updated manifest, panel constants, active panel JS file, custom element name, and visible frontend build badge to `alpha319-drive-i18n`.


## alpha320 – Cautious traffic / slowdown analysis
- Based on alpha319 Drive i18n line.
- Reworked traffic interpretation so raw low-speed / stop-go percentage is no longer treated as traffic percentage.
- Added conservative slowdown classification fields: `slowdown_reason`, `slowdown_reason_label`, `raw_low_speed_percent`, `effective_traffic_delay_seconds`, `effective_traffic_delay_text`, `effective_traffic_impact`, and `traffic_confidence`.
- Short urban trips, traffic lights/junction stops, and destination/parking-search patterns are now down-ranked and should not be described as heavy traffic by AI.
- Trip PNG traffic section labels were softened to slowdown/low-speed analysis and now prioritize effective delay and reason over raw low-speed percentage.
- AI prompt rules now explicitly forbid calling raw low-speed percent “heavy traffic” without meaningful effective delay and confidence.
- Updated manifest, panel constants, active panel JS file, custom element name, and visible frontend build badge to `alpha320-cautious-traffic-analysis`.


## alpha322 – Live Trip AI popup panel fix

- Rebuilt from alpha321 clean base to avoid the previous setup-time NameError.
- Live Trip / Sürüş Raporu kartındaki sağ üst kırmızı araç düğmesi artık etkileşimli; tıklayınca açılan, tekrar tıklayınca kapanan yeni Live Trip AI yorum paneli eklendi.
- Panel neon/purple-pink glow, durum rozeti, ilerleme çubuğu ve geçmiş 10 km segment etiketleri gösterir.
- Backend tarafında ana Trip/Live Trip ledger akışını bozmadan ayrı JSON dosyası eklendi: `pom_tesla_live_trip_ai_segments_<entry_id>.json`.
- AI yorum mantığı segment bazlıdır: 0–10 km, 10–20 km, 20–30 km. Her yorum sadece ilgili son segmenti yorumlar.
- OpenAI anahtarı yoksa veya AI özet kapalıysa güvenli şablon tabanlı fallback yorum gösterilir.
- Aktif panel sürümü alpha322 olarak güncellendi: `pom-tesla-report-panel-alpha322.js` / `pom-tesla-report-panel-alpha322`.

## alpha321 – AI user address setting
- Based on alpha320 cautious traffic analysis.
- Added an AI setting named `Size hitap şekli` / `How AI should address you`, stored as `ai_user_address`.
- AI prompts now use the configured user address and explicitly avoid calling the user Berkan unless that setting is actually Berkan.
- Post-trip AI story prompts no longer hardcode Berkan in the task text.
- Panel AI Settings UI, settings payload, Options Flow mapping, and visible frontend build badge were updated to alpha321.

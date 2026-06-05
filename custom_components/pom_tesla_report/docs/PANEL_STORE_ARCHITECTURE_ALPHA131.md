## alpha355 – Charge popup centering and close button alignment

- Based on alpha354.
- Charge popup Tesla small-screen visual tuning only: the popup card now centers against the actual viewport instead of being anchored left by the Lovelace stack/container.
- The close `X` button positioning was changed from right-offset media rules to viewport-center/card-edge geometry, so it should sit next to the popup instead of far away.
- Preserved Charge calculations, Live Trip calculations, candidate-trip filter behavior, Telegram, AI, Trip Records, Charge Records, entity mapping, and the stable Live Trip card type.
- Manifest/panel/frontend version: `2.2.0-dashboard-alpha355-charge-popup-center-close-align`; active panel: `pom-tesla-report-panel-alpha355.js` / `pom-tesla-report-panel-alpha355`.

## alpha240 note

No store migration. Frontend render crash fixed.

## alpha239 note

No store migration. New health endpoint is stateless and reads live runtime metrics.

## alpha238 note

No store migration. Grade fields are computed dynamically from trip report data and stored with new trip report payloads.

## alpha237 note

No store migration. System Health reads current panel stores and reports invalid self-reference rows as diagnostics.

## alpha236 note

No store migration. Invalid stored rows are ignored at runtime and by the panel normalization layer. Saving after opening the panel should persist the cleaned Dashboard Entity Manager map.

## alpha235 note

No store migration. New trip record score fields are additive; older records remain readable.

## alpha234 note

No store migration. Vehicle location reply behavior changed from image+text to a single photo-with-caption response.

## alpha233 note

No store migration. Regenerate/update dashboard to apply map YAML changes.

## alpha232 note

No store migration. Generated dashboard YAML changed; users may need to regenerate dashboard to see the new map style.

## alpha231 note

No store migration. Weather context is runtime-only for AI story generation.

## alpha230 note

No store migration. Fast Auto Find writes into the same panel entity stores as Deep Auto Find.

## alpha229 note

No store migration. New AI context keys are computed dynamically from report data.

## alpha228 note

No store migration. New trip record fields are additive. Existing records remain readable.

## alpha227 note

No store migration. Adds fallback computation for overall speed in test/renderer paths.

## alpha226 note

No store migration. Existing trip records with `average_overall_speed` will display it. Older records without it show 0.0 until regenerated/updated.

## alpha225 note

`panel_report_entity_map` is now the authoritative runtime source for Reports/Live Trip/Manual Tracking once it has saved rows. Legacy keys remain compatibility fallback only when the panel report map is empty.

## alpha224 note

No migration required. Dashboard Entity Manager can now store `dashboard_top_speed`, and dashboard helper maps it to `entity_speed`.

## alpha223 note

No store migration required. New optional fields are added to entity map rows:
- source_key
- source_label
- source_platform
- source_device_id

## alpha222 note

No store migration required.
`vehicle_entity_map` is now actively refreshed by Reports and Dashboard Auto Find as well as AI Auto Find.
Manual panel stores remain authoritative for explicitly selected values.

## alpha221 note

- No store migration.
- Auto Find warning state is frontend-only.
- Warning is now inline banner, not fullscreen overlay.

## alpha219 note

- No migration required.
- Auto Find entries now carry metadata fields:
  - confidence
  - confidence_label
  - match_source
  - match_reason
  - auto_find_score
  - review
- AI Auto Find also refreshes `vehicle_entity_map` as a master entity map.

## alpha217 note

- No store migration.
- Fast dashboard settings response now includes full dashboard settings sections except expensive resource audit.

## alpha216 note

- No store migration.
- Panel settings save can now schedule a background dashboard YAML rebuild.

## alpha215 note

- No store migration.
- Frontend fallback options protect dashboard slot selectors from missing backend option lists.

## alpha214 note

- No persistent store migration.
- Runtime job store `panel_autofind_jobs` now includes `report`.
- Report Auto Find results still save into the existing panel report entity map.

## alpha213 note

- No panel store migration.
- Options Flow is reduced to Test Tools only.
- Device page cleanup is handled by switch/select platform setup registry cleanup.

## alpha212 note

- No persistent store migration.
- New in-memory job store: `panel_autofind_jobs`.
- Job state is runtime-only and not persisted across HA restart.

## alpha211 note

- No store migration.
- Clear All works on the frontend draft and persists only after Save.

## alpha210 note

- No store migration.
- Dashboard Auto Find candidate generation optimized.

## alpha209 note

- No store migration.
- Frontend category rendering fixed.

## alpha208 note

- No panel store migration required.
- New Dashboard Entity Manager roles are stored in the existing `panel_dashboard_entity_map`.
- New generated binary sensors read this map live from config entry options / `hass.data`.

## alpha207 note

- No panel store migration.
- Telegram event routing now supports HA `telegram_command`.

## alpha206 note

- No store migration.
- Live Telegram command matching now prioritizes `hass.data[DOMAIN][entry_id]`.

## alpha205 note

- No store migration.
- Telegram command listener now refreshes config-entry options per incoming event.

## alpha204 note

- No store migration.
- Frontend render method was repaired.

## alpha203 note

- New options payload field: `telegram_report_commands`.
- Stored in config entry options through Settings → Telegram save.
- No panel entity-store migration required.

## alpha202 note

- No panel store migration.
- Telegram command routing was separated from AI listener routing.

## alpha201 note

- No panel store migration.
- Elevation runtime state gains idle bootstrap fields/statuses.

## alpha200 note

- No panel store migration.
- Elevation runtime state is initialized on sensor setup.

## alpha199 note

- Runtime elevation cache was added to HA `hass.data`.
- No panel-store schema migration required.

## alpha198 note

- Panel store architecture unchanged.
- New user-facing trip_reports field: `ai_trip_story_enabled`, backed internally by the compatible post-trip AI summary option.

## alpha197 note

- Panel store architecture is unchanged.
- Trip ledger records may now receive `ai_summary` and `ai_summary_at` after the background AI story task completes.

## alpha196 note

- Panel store architecture unchanged.
- Partial settings-save response now includes authoritative entity-manager sections when those sections are saved.

## alpha195 note

- Panel store architecture unchanged.
- Settings GET now has fast default / explicit full mode split.

## alpha194 note

- Panel store architecture unchanged.
- Settings POST now returns lightweight partial update responses instead of full settings payloads.

## alpha193 note

- Panel store architecture unchanged.
- Frontend startup behavior changed from eager all-data load to per-tab lazy-load.

## alpha187 note\n\n- Panel store architecture is unchanged.\n- Emergency stability hardening focused on offloading file I/O and disabling duplicate Telegram polling.\n\n## alpha186 note

- Panel store architecture is unchanged.
- Sidebar/API stability hardening only.

## alpha185 note\n\n- Panel store architecture is unchanged.\n- Settings saves update Home Assistant config-entry options and refresh `hass.data` without forcing an automatic reload.\n- Dashboard resource status cache was introduced for non-blocking Settings payloads.\n\n## alpha184 note\n\n- Panel store architecture is unchanged.\n- Final Park wait duration fields are report/ledger/debug fields, not new panel stores.\n\n## alpha183 note\n\n- Panel store architecture is unchanged.\n- Traffic breakdown fields are runtime/report/ledger fields, not new panel stores.\n\n## alpha182 note

- Panel store architecture is unchanged.
- One-second speed sampling uses runtime state and trip ledger fields; no new panel store was introduced.

## alpha181 note\n\n- Panel store architecture is unchanged.\n- Speed sampling fields are runtime/report/ledger fields, not new persistent panel stores.\n\n## alpha179 note\n\n- Panel store architecture is unchanged.\n- Live Trip Park grace uses the existing Options/config-entry option key `live_trip_finish_delay_seconds`; only the panel unit changed from seconds display to minutes display.\n\n## alpha178 note

- Panel store architecture is unchanged.
- Manual Tracking tab is a filtered view over the existing trip monthly ledger and does not introduce a new persistent store.
- The backend now persists route point metadata into future trip ledger rows for full route-map previews.

## alpha177 note

- Panel store architecture is unchanged.
- Station preset ordering still uses the existing `charging.provider_presets` list; the first three entries are the report cost slots.

## alpha176 note

- Panel store architecture is unchanged.
- Station preset ordering is still stored in the existing `charge_provider_presets` option list.
- First three entries are treated as report cost slots; no separate store was introduced.

## alpha175 note\n\n- Panel store architecture is unchanged.\n- Date filtering is client-side over the existing charge/trip record payloads and does not introduce new persistent stores.\n\n## alpha174 note

- Panel stores unchanged. alpha174 only fixes the record-map preview API error handling and option lookup.

## alpha173 note

- Panel store architecture is unchanged in alpha173.
- New charge/trip map preview behavior is read-only with respect to record stores: it reads the selected record by id and generates preview PNGs under `/config/www/pom_tesla_report/panel_maps/`.
- No new panel entity stores or configuration stores were added.

## alpha172 note

- No entity role mapping changed in alpha172. The update only changes Settings > General debug/migration output controls and documentation.

## alpha169 - 1080 performance profiles

- Added a lighter 1080 profile for VM/Tesla browser performance.
- Dashboard quality options now include:
  - 360p
  - 480p
  - 720p
  - 1080 Lite
  - 1080 Max
- New backend quality profile:
  - `1080_lite`: scale `1600:-2`, bitrate `3000k`, maxrate `4200k`, bufsize `1800k`
- Full `1080` remains available as 1080 Max:
  - scale `1920:-2`, bitrate `4500k`, maxrate `6000k`, bufsize `2500k`
- Added ffmpeg `-threads 0` for automatic thread usage.
- 1080/1080 Lite output fps is now 24 instead of 25 to reduce encode/render pressure.
- Keeps alpha168 fast input seek and alpha165+ global producer architecture.
- Changed panel element to `pom-tesla-report-panel-alpha169` and JS file to `pom-tesla-report-panel-alpha169.js`.
- Build marker: `alpha169-1080-performance-profiles`.

## alpha168 - Fast input seek for YouTube start seconds

- Fixed white screen when Dashboard YouTube start seconds is set, e.g. 59 seconds.
- Cause: ffmpeg used output-side seek together with `-re`, so it waited in real time until the requested timestamp before producing frames.
- Changed ffmpeg order to fast input-side seek:
  - before: `ffmpeg -re -i URL -ss 59 ...`
  - now: `ffmpeg -ss 59 -re -i URL ...`
- This should start near the configured second immediately instead of showing a white screen for that many seconds.
- 1080p support from alpha167 remains.
- Producer debug now reports `seek_mode: input_fast` when start offset is used.
- Changed panel element to `pom-tesla-report-panel-alpha168` and JS file to `pom-tesla-report-panel-alpha168.js`.
- Build marker: `alpha168-fast-input-seek`.

## alpha167 - 1080p quality and producer start seconds

- Added 1080p to Tesla Safe YouTube quality options.
- Added backend 1080p quality mapping:
  - scale `1920:-2`
  - bitrate `4500k`
  - maxrate `6000k`
  - bufsize `2500k`
- Dashboard quality select now includes 1080p.
- Fixed Dashboard YouTube start seconds not being applied in global producer mode.
- Dashboard player URL now sends `start=<seconds>`.
- Producer key now includes start offset: `quality|start|url`.
- Producer ffmpeg now receives `start_offset` at first start, so a configured 59 second start should start near 59 seconds instead of 0.
- Health/debug producer status includes `start_offset`.
- Changed panel element to `pom-tesla-report-panel-alpha167` and JS file to `pom-tesla-report-panel-alpha167.js`.
- Build marker: `alpha167-1080p-start-seconds`.

## alpha166 - ffmpeg real-time input pacing

- Fixed YouTube Canvas playback running too fast, e.g. roughly 3x speed.
- Added `-re` before ffmpeg input:
  - `ffmpeg ... -re -i <youtube-googlevideo-url> ...`
- This tells ffmpeg to read the YouTube/VOD input at real-time speed instead of downloading/decoding as fast as possible.
- Keeps the alpha165 global producer architecture:
  - producer mode is default
  - one ffmpeg process per YouTube URL + quality
  - WebSocket clients subscribe to existing producer
- Health/debug `producer_ffmpeg_starting` now includes `realtime_input: true`.
- Changed panel element to `pom-tesla-report-panel-alpha166` and JS file to `pom-tesla-report-panel-alpha166.js`.
- Build marker: `alpha166-ffmpeg-realtime-input`.

## alpha165 - Producer mode as WebSocket default

- Fixed cases where health showed `producer_count: 0` and `stage: ws_ffmpeg_log`, meaning the old per-client WebSocket path was still used.
- WebSocket endpoint now defaults to global producer mode even if the URL does not contain `producer=1`.
- Old per-client mode can be forced only with `legacy=1`.
- Health endpoint now reports:
  - `producer_default: true`
  - `legacy_query_param: legacy=1`
- Dashboard helper still sends `producer=1`, but the endpoint no longer depends on that parameter.
- Changed panel element to `pom-tesla-report-panel-alpha165` and JS file to `pom-tesla-report-panel-alpha165.js`.
- Build marker: `alpha165-producer-default`.

## alpha164 - Global YouTube JSMpeg producer relay

- Reworked dashboard YouTube Canvas playback to use a global producer/relay model.
- Dashboard player URL now sends `producer=1`.
- In producer mode:
  - yt-dlp resolves the stream once per YouTube URL + quality.
  - one ffmpeg process runs independently from browser/WebSocket client lifetime.
  - WebSocket clients subscribe to the existing MPEG-TS producer output.
  - if Tesla/Lovelace reconnects the iframe, ffmpeg is not restarted, so the video should not jump back to 0.
  - producer stops automatically after 120 seconds with no subscribers.
- Existing per-client WebSocket streaming path remains available as fallback/diagnostics.
- Health endpoint now includes `producer_count`.
- New status stages:
  - `producer_resolving`
  - `producer_ffmpeg_starting`
  - `producer_started`
  - `producer_streaming`
  - `producer_client_subscribed`
  - `producer_client_unsubscribed`
  - `producer_stopped`
- Changed panel element to `pom-tesla-report-panel-alpha164` and JS file to `pom-tesla-report-panel-alpha164.js`.
- Build marker: `alpha164-global-youtube-producer`.

## alpha163 - Stable WebSocket mode without cache/resume for dashboard

- Restored dashboard YouTube Canvas background to stable live WebSocket mode.
- Dashboard player URL now sends:
  - `nocache=1`
  - `resume=0`
- This bypasses the resolve cache and session resume logic for dashboard playback to recover reliable video startup.
- Cache/resume code remains in backend for future experimentation, but dashboard does not use it in this build.
- Purpose: regain the last known working state before optimizing restart behavior.
- Changed panel element to `pom-tesla-report-panel-alpha163` and JS file to `pom-tesla-report-panel-alpha163.js`.
- Build marker: `alpha163-stable-ws-no-cache-resume`.

## alpha162 - Safer ffmpeg seek for cached YouTube streams

- Fixed a likely stall where WebSocket status stayed at `ws_resolved_cache` and never reached `ws_streaming`.
- Moved ffmpeg seek from input-side seek to output-side seek:
  - before: `ffmpeg -ss <offset> -i googlevideo...`
  - now: `ffmpeg -i googlevideo... -ss <offset> ...`
- This is slower to seek, but safer for cached googlevideo network URLs.
- Added `ws_ffmpeg_starting` debug stage before ffmpeg process creation.
- Cache/resume/duration logic from alpha160/161 remains unchanged.
- Changed panel element to `pom-tesla-report-panel-alpha162` and JS file to `pom-tesla-report-panel-alpha162.js`.
- Build marker: `alpha162-seek-after-input`.

## alpha161 - Import time fix for YouTube resolve cache

- Fixed `ws_yt_dlp_error: name 'time' is not defined`.
- alpha160 introduced `time.monotonic()` for yt-dlp resolve cache/session timing but missed `import time` in `panel.py`.
- YouTube resolve cache and safe resume behavior from alpha160 are unchanged.
- Changed panel element to `pom-tesla-report-panel-alpha161` and JS file to `pom-tesla-report-panel-alpha161.js`.
- Build marker: `alpha161-import-time-fix`.

## alpha160 - YouTube resolve cache and start-offset handling

- Fixed repeated `ws_resolving` on reconnects by caching yt-dlp resolved direct media URL, HTTP headers and duration for URL + quality.
- Reconnects now reuse cached direct URL for up to 30 minutes instead of re-running yt-dlp every time.
- Dashboard player URL now passes:
  - `start=<configured start seconds>`
  - `session=dashboard_youtube_canvas`
  - `resume=1`
  - `loop=1/0`
- YouTube URL parameters like `t=102` or `start=102` are parsed and used as base start offset.
- Safe resume offset now adds configured start offset + elapsed session offset and clamps/modulos based on video duration.
- Health/debug can show:
  - `ws_resolved_cache`
  - `cache_hit`
  - `start_base`
  - `resume_offset`
  - `start_offset`
- Changed panel element to `pom-tesla-report-panel-alpha160` and JS file to `pom-tesla-report-panel-alpha160.js`.
- Build marker: `alpha160-youtube-resolve-cache`.

## alpha159 - Safe YouTube Canvas resume with duration

- Reintroduced resume, but with duration awareness to avoid alpha157's blank screen on short videos.
- yt-dlp duration is now captured and reported in WebSocket debug status.
- Dashboard sends:
  - `session=dashboard_youtube_canvas`
  - `resume=1`
  - `loop=1/0`
- Reconnect behavior:
  - long videos resume near elapsed playback time
  - short videos never seek past duration
  - when loop is enabled, elapsed time is modulo video duration
- ffmpeg gets `-ss <safe offset>` only when offset is safe.
- Health/debug can show:
  - `duration`
  - `ws_resume_offset`
  - `session`
  - `resume`
  - `loop`
- Changed panel element to `pom-tesla-report-panel-alpha159` and JS file to `pom-tesla-report-panel-alpha159.js`.
- Build marker: `alpha159-safe-resume-duration`.

## alpha158 - Disable resume seek, keep stable iframe

- Reverted the alpha157 session resume seek behavior because short videos can seek past the video duration and result in a blank/white screen.
- Kept the alpha156 persistent iframe approach:
  - no Lovelace conditional iframe destruction
  - visibility controlled by CSS
- Dashboard player URL now includes a stable `player_id` derived from URL + quality for diagnostics.
- No `session=...` / `resume=1` is sent by dashboard.
- Health/debug can show `player_id` when WebSocket streaming starts.
- Changed panel element to `pom-tesla-report-panel-alpha158` and JS file to `pom-tesla-report-panel-alpha158.js`.
- Build marker: `alpha158-no-resume-debug`.

## alpha156 - Stable YouTube Canvas iframe visibility

- Fixed dashboard YouTube Canvas background restarting from the beginning after a short time.
- Root cause: Lovelace `conditional` cards can destroy/recreate the iframe when HA state updates.
- Changed dashboard YouTube background generation:
  - no repeated conditional iframe cards
  - one persistent fullscreen iframe
  - visibility is toggled with card-mod CSS based on shift state
- This keeps the JSMpeg/WebSocket player alive, so video should not restart on normal dashboard updates.
- The iframe is visible only when shift state is D/drive/driving; otherwise it is hidden via CSS.
- Changed panel element to `pom-tesla-report-panel-alpha156` and JS file to `pom-tesla-report-panel-alpha156.js`.
- Build marker: `alpha156-stable-youtube-iframe`.

## alpha155 - Dashboard Tesla Safe YouTube Canvas background

- Integrated the working YouTube -> yt-dlp -> ffmpeg -> WebSocket MPEG-TS -> JSMpeg Canvas2D pipeline into `Dashboard > Background`.
- Existing YouTube Driving Background is now treated as Tesla Safe YouTube Canvas background.
- Generated dashboard uses an iframe to `/pom_tesla_report/youtube_jsmpeg_player?...&hide=1`, not a YouTube iframe.
- Video is shown only when the shift/driving state is D/drive/driving.
- Added Dashboard Background quality setting:
  - 360p
  - 480p
  - 720p
- Saved option:
  - `youtube_driving_bg_quality`
- The previous HTTP/YouTube iframe wrapper files remain harmless, but the generated dashboard now uses the HA WebSocket/JSMpeg player path.
- Changed panel element to `pom-tesla-report-panel-alpha155` and JS file to `pom-tesla-report-panel-alpha155.js`.
- Build marker: `alpha155-dashboard-safe-youtube-canvas`.

## alpha154 - YouTube JSMpeg WebSocket live stream

- HTTP chunked stream reached the browser but JSMpeg did not decode frames.
- Added a WebSocket MPEG-TS endpoint, which is the more typical JSMpeg live-stream transport.
- New endpoint: `/pom_tesla_report/youtube_jsmpeg_ws`.
- Player now builds a `ws://` or `wss://` URL and passes it to JSMpeg.
- Existing HTTP stream endpoint is kept for diagnostics/fallback.
- Health endpoint now reports `websocket_url`.
- Changed panel element to `pom-tesla-report-panel-alpha154` and JS file to `pom-tesla-report-panel-alpha154.js`.
- Build marker: `alpha154-youtube-jsmpeg-websocket`.

## alpha153 - YouTube JSMpeg progressive decode fix

- Health showed `stage: streaming`, meaning HA/yt-dlp/ffmpeg successfully sent data to the browser.
- Fixed frontend JSMpeg player config for HTTP live stream by changing `progressive: false` to `progressive: true`.
- Increased video buffer from 8 MB to 12 MB.
- Added JSMpeg decode diagnostics:
  - `onSourceEstablished`
  - `onVideoDecode`
  - 7 second no-frame warning
- Added ffmpeg MPEG-TS low-latency mux options:
  - `-muxdelay 0`
  - `-muxpreload 0`
- Changed panel element to `pom-tesla-report-panel-alpha153` and JS file to `pom-tesla-report-panel-alpha153.js`.
- Build marker: `alpha153-youtube-jsmpeg-progressive-fix`.

## alpha152 - YouTube JSMpeg headers/debug fix

- Improved YouTube live JSMpeg stream resolving by using the yt-dlp Python API instead of only `yt-dlp -g`.
- Direct YouTube stream HTTP headers returned by yt-dlp are now forwarded to ffmpeg.
- Format selection now prefers H264/MP4-compatible video streams.
- Health endpoint now returns `last_youtube_jsmpeg` diagnostic status.
- ffmpeg stderr is logged at warning level and mirrored into the health status.
- Stream status records resolving/resolved/streaming/no_output/finished stages.
- Changed panel element to `pom-tesla-report-panel-alpha152` and JS file to `pom-tesla-report-panel-alpha152.js`.
- Build marker: `alpha152-youtube-headers-debug`.

## alpha151 - Public YouTube JSMpeg test views

- Fixed `401: Unauthorized` when opening the YouTube JSMpeg test endpoints directly in a browser.
- Moved the test endpoints out of `/api/...`:
  - `/pom_tesla_report/youtube_jsmpeg_health`
  - `/pom_tesla_report/youtube_jsmpeg_player`
  - `/pom_tesla_report/youtube_jsmpeg_stream`
- Set only these experimental YouTube/JSMpeg views to `requires_auth = False` so Tesla Browser can open them directly.
- Existing app APIs remain authenticated.
- Changed panel element to `pom-tesla-report-panel-alpha151` and JS file to `pom-tesla-report-panel-alpha151.js`.
- Build marker: `alpha151-public-youtube-jsmpeg-views`.

## alpha150 - Home Assistant internal YouTube JSMpeg live test

- Added internal HA endpoints for live YouTube -> JSMpeg Canvas testing, without using an external Python server.
- Added manifest requirement: `yt-dlp`.
- New authenticated endpoints:
  - `/api/pom_tesla_report/youtube_jsmpeg_player`
  - `/api/pom_tesla_report/youtube_jsmpeg_stream`
  - `/api/pom_tesla_report/youtube_jsmpeg_health`
- The player page resolves YouTube through yt-dlp, transcodes with ffmpeg to MPEG1/MPEG-TS, and renders on Tesla via JSMpeg Canvas2D.
- This is experimental and depends on ffmpeg being available in the HA environment.
- Changed panel element to `pom-tesla-report-panel-alpha150` and JS file to `pom-tesla-report-panel-alpha150.js`.
- Build marker: `alpha150-ha-youtube-jsmpeg-live`.

## alpha149 - YouTube fullscreen fixed layer

- Fixed YouTube Driving Background rendering as a normal stack card instead of a true fullscreen background.
- Wrapped the iframe card in `custom:mod-card` and applied fixed viewport CSS to the outer host.
- The YouTube wrapper remains:
  `/pom_tesla_report/dashboard/png/youtube_background.html?...`
- Changed panel element to `pom-tesla-report-panel-alpha149` and JS file to `pom-tesla-report-panel-alpha149.js`.
- Build marker: `alpha149-youtube-fullscreen-layer`.

## alpha148 - YouTube wrapper background

- Reworked experimental YouTube Driving Background to use a local wrapper HTML instead of embedding YouTube directly in the dashboard iframe card.
- Added `dashboard/png/youtube_background.html`, served through the existing static dashboard asset path.
- Generated dashboard now points to:
  `/pom_tesla_report/dashboard/png/youtube_background.html?video=<id>&start=<seconds>&mute=<0|1>&loop=<0|1>`
- The wrapper internally creates a `youtube-nocookie.com/embed/...` iframe with:
  - autoplay
  - playsinline
  - mute
  - loop/playlist
  - origin
  - allow autoplay / encrypted-media / fullscreen
  - referrerpolicy
- This improves compatibility with YouTube embed restrictions, but videos with owner/region/age/embed restrictions can still show YouTube error 153.
- Changed panel element to `pom-tesla-report-panel-alpha148` and JS file to `pom-tesla-report-panel-alpha148.js`.
- Build marker: `alpha148-youtube-wrapper-background`.

## alpha147 - Background local save button

- Added a local save/reload row directly inside `Dashboard > Background`.
- This fixes the UX issue where YouTube Driving Background values changed in the UI but were lost after refresh because the page-level save button was not visible/reachable from the Background section.
- Added `saveDashboardSettingsBtnBackground` and `reloadDashboardSettingsBtnBackground` listeners.
- Changed panel element to `pom-tesla-report-panel-alpha147` and JS file to `pom-tesla-report-panel-alpha147.js`.
- Build marker: `alpha147-background-save-button`.

## alpha146 - YouTube Driving Background save fix

- Fixed YouTube Driving Background settings not being saved/restored from `Dashboard > Background`.
- Ensured frontend normalization includes `dashboard_settings.youtube_driving_background`.
- Ensured `_readDashboardSettingsForm()` sends the YouTube fields in dashboard settings payload.
- Ensured backend dashboard settings payload returns the saved YouTube values.
- Ensured backend dashboard settings save writes:
  - `youtube_driving_bg_enabled`
  - `youtube_driving_bg_video`
  - `youtube_driving_bg_start_seconds`
  - `youtube_driving_bg_mute`
  - `youtube_driving_bg_loop`
- Changed panel element to `pom-tesla-report-panel-alpha146` and JS file to `pom-tesla-report-panel-alpha146.js`.
- Build marker: `alpha146-youtube-save-fix`.

## alpha145 - YouTube background card render method fix

- Fixed `Dashboard > Background` render error: `_renderYoutubeDrivingBackgroundCard is not a function`.
- Added the missing `_renderYoutubeDrivingBackgroundCard(cfg = {})` method to the frontend class.
- Changed panel element to `pom-tesla-report-panel-alpha145` and JS file to `pom-tesla-report-panel-alpha145.js`.
- Build marker: `alpha145-youtube-card-method-fix`.

## alpha144 - Real dashboard safe method fix

- Fixed the alpha143 regression where `_renderDashboardSettingsContentSafe()` was still not added because the patch checked for any occurrence of the name, including the existing call site.
- The method is now added by checking the actual method signature.
- Changed panel element to `pom-tesla-report-panel-alpha144` and JS file to `pom-tesla-report-panel-alpha144.js`.
- Build marker: `alpha144-real-safe-method-fix`.

## alpha143 - Dashboard safe render method fix

- Fixed the alpha142 frontend crash: `this._renderDashboardSettingsContentSafe is not a function`.
- Root cause: the dashboard settings template called `_renderDashboardSettingsContentSafe()` but the method was missing from the frontend class.
- Added `_renderDashboardSettingsContentSafe()` properly.
- Kept the background section render guard and ensured `images` is defined for `Dashboard > Background`.
- Changed panel element to `pom-tesla-report-panel-alpha143` and JS file to `pom-tesla-report-panel-alpha143.js`.
- Build marker: `alpha143-dashboard-safe-method-fix`.

## alpha142 - Settings tab pointerdown fix

- Changed panel element to `pom-tesla-report-panel-alpha142` and JS file to `pom-tesla-report-panel-alpha142.js`.
- Settings top nav buttons now have stable `data-settings-tab` attributes and capture-phase `pointerdown` listeners.
- Pointerdown handler now checks settings tabs before dashboard section cards.
- Added `_renderActiveSafe()` to surface top-level render errors instead of silently leaving the old UI.
- Build marker: `alpha142-settings-tab-pointerdown-fix`.

## alpha141 - Dashboard Background render fix

- Fixed Dashboard > Background section not visually opening even though `active_dashboard_section` became `backgrounds`.
- Root cause: `_renderDashboardSettingsContent()` used `images.parked / images.charging / images.driving` in the `backgrounds` section without defining `images`.
- Added `const images = dashboard.images || {};`.
- Added a safe render wrapper for dashboard sections so future section render errors are shown in the UI and debug events instead of silently leaving the previous section visible.
- Changed panel element to `pom-tesla-report-panel-alpha141` and JS file to `pom-tesla-report-panel-alpha141.js`.
- Build marker: `alpha141-background-render-fix`.

## alpha140 - Dashboard menu pointerdown fix

- Changed panel element to `pom-tesla-report-panel-alpha140` and JS file to `pom-tesla-report-panel-alpha140.js`.
- Added capture-phase `pointerdown` handling for Dashboard module cards.
- Dashboard left module cards now have stable IDs such as `dashboardSection_backgrounds`.
- This fixes cases where cards receive focus but the click handler does not switch the dashboard section.
- Build marker: `alpha140-pointerdown-dashboard-menu`.

## alpha139 - Unique panel custom element name

- Changed the custom panel element name from `pom-tesla-report-panel` to `pom-tesla-report-panel-alpha139`.
- Changed frontend module filename to `pom-tesla-report-panel-alpha139.js`.
- This avoids the browser/Home Assistant `customElements.define()` collision where an older already-defined `pom-tesla-report-panel` class can keep running even after the JS file is updated.
- Visible frontend build marker is now `alpha139-unique-element`.

## alpha138 - Unique frontend JS filename

- Changed panel frontend module filename from `pom-tesla-report-panel.js` to `pom-tesla-report-panel-alpha138.js`.
- Updated panel registration to use the unique filename.
- Added visible frontend build marker `alpha138-unique-js`.
- Added `panel_js_file` and `panel_js_url` to settings system payload for diagnostics.
- This bypasses Home Assistant/browser/module cache that kept loading old panel JS even after version query changes.

## alpha137 - Panel re-register cache-bust fix

- Fixed the real cause of stale frontend code: Home Assistant kept the existing `/pom-tesla-report` custom panel registration and did not receive the new `js_url`.
- Panel setup now removes the existing frontend panel registration before registering it again with the current `?v=<manifest version>` URL.
- This should make the browser load the new `pom-tesla-report-panel.js` instead of silently using old cached frontend code.
- Alpha136 visible build/debug tracing remains in the frontend so successful loading can be verified.

## alpha136 - Click trace and navigation hardening

- Added visible frontend build badge: `alpha136-click-trace`.
- Added `last_click_debug` to debug output so click target/path can be inspected.
- Restored direct render-time listeners for Settings tab navigation while keeping delegated handlers.
- Added direct render-time listeners for Dashboard module cards while keeping delegated handlers.
- This is intended to determine whether the user is seeing old cached JS or a click/overlay issue.

## alpha135 - Dashboard settings navigation click fix

- Fixed unreliable clicks in Settings > Dashboard after alpha134.
- Settings top nav now uses delegated `[data-settings-tab]` click handling instead of per-render individual listeners.
- Dashboard left module cards continue using `[data-dashboard-section]`, now with stronger event stop/clear behavior.
- Added pointer-event/z-index safeguards for settings navigation and module cards.
- YouTube Driving Background feature from alpha134 is preserved.

## alpha134 - Experimental YouTube Driving Background

- Added an experimental YouTube Driving Background card under `Dashboard > Background`.
- New settings:
  - `youtube_driving_bg_enabled`
  - `youtube_driving_bg_video`
  - `youtube_driving_bg_start_seconds`
  - `youtube_driving_bg_mute`
  - `youtube_driving_bg_loop`
- When enabled and the vehicle shift-state entity is `d`, `D`, `drive`, or `driving`, the generated dashboard injects a full-screen YouTube iframe background.
- The normal driving background remains the fallback; disabling the YouTube option restores the old behavior.
- This is intentionally experimental and should be tested on the current dashboard before becoming a final wallpaper mode.

## alpha133 - Settings API fix for top area font scale

- Fixed a backend 500 error in `/api/pom_tesla_report/settings`.
- Alpha132 used `_bounded_float_panel()` in dashboard settings payload/save handling but the helper was missing from `panel.py`.
- Added the missing helper so `top_font_scale`, `top_left_font_scale`, `top_center_font_scale`, and `top_right_font_scale` load correctly.

# Alpha131 Documentation Update - Panel Store Architecture Finalization

## Purpose

This document records the current post-alpha130 architecture and the tested migration path from Options Flow entity management to app-panel entity management.

The project now treats the app panel as the authoritative entity-management surface for Reports, AI, and Dashboard. Options Flow remains only as legacy/fallback infrastructure until a separate experimental build disables or removes the old entity manager pages.

## Current authoritative entity stores

The app panel now owns three independent stores:

```text
panel_report_entity_map
panel_ai_entity_map
panel_dashboard_entity_map
```

Runtime priority is:

```text
1. panel_report_entity_map / panel_ai_entity_map / panel_dashboard_entity_map
2. legacy vehicle_entity_map / dashboard_entity_map fallback
3. old legacy Options Flow keys
```

Fallback is used only when the corresponding panel store is empty.

## Verified tests

### Test 1 - Panel store audit

Observed state:

```json
{
  "reports": {
    "source": "panel_report_entity_map",
    "panel_count": 10,
    "ready": true
  },
  "ai": {
    "source": "panel_ai_entity_map",
    "panel_count": 84,
    "ready": true
  },
  "dashboard": {
    "source": "panel_dashboard_entity_map",
    "panel_count": 25,
    "ready": true
  },
  "migration_needed": false
}
```

Result: PASS.

### Test 2 - Flow corruption / fallback isolation

Options Flow entity selections were intentionally changed to unrelated entities. Fallback counts changed, proving Flow changed legacy data, but the panel sources remained:

```text
reports.source = panel_report_entity_map
ai.source = panel_ai_entity_map
dashboard.source = panel_dashboard_entity_map
migration_needed = false
```

Result: PASS.

### Test 3 - Reports / Live Trip binding

Report and Live Trip debug showed the correct panel-bound entities after Flow corruption:

```text
battery_level     -> sensor.pom_pil_seviyesi
energy_remaining  -> sensor.pom_kalan_enerji
speed             -> sensor.pom_hiz
shift_state       -> sensor.pom_kaydirma_durumu
odometer          -> sensor.pom_kilometre_sayaci
charging_state    -> binary_sensor.pom_sarj_oluyor
charge_energy     -> sensor.pom_sarj_enerjisi_eklendi
location_tracker  -> device_tracker.pom_konum
```

Developer Tools simulation with `shift_state = d/drive` and `speed = 20/30` triggered Live Trip report delivery to Telegram.

Result: PASS.

### Test 4 - AI / Telegram action commands

Telegram AI commands such as flash lights worked even when Flow-side entity selection was disabled/empty. The action resolved from panel-selected AI entities.

Result: PASS.

### Test 5 - Dashboard entity binding

Dashboard Entity Manager was cleaned up and dashboard bottom-bar battery heater binding was fixed.

`Battery heater` panel selection now overlays:

```text
entity_battery_heater
entity_battery_temp   # compatibility mirror
```

The bottom-bar `battery_heater` slot resolves in this order:

```text
entity_battery_heater
entity_battery_temp
default binary_sensor.tesla_battery_heater
```

Result: PASS after alpha130.

## Dashboard Entity Manager map after alpha129/alpha130

### Top area / bottom card shared entity group

```text
Güç
Eğim
Batarya yüzde
Kalan tahmini menzil
Dış ısı
Konum
Arabanın gösterdiği menzil
Energy Remaining
İç ısı
Battery heater
Odometer
Person 1
Person 2
Person 3
```

### Sidebar group

```text
Homelink
Buz çözme
Direksiyon ısıtıcı
Flash Lights
Korna
Sentry Mode
Fart
Wake
Vale Mode
```

The old user-facing display/action duplicates were removed. For example, `Korna butonu görünümü` and `Korna komutu` are no longer shown as two separate user-facing roles. A single `Korna` role is shown.

### Charge popup group

The charge popup entity list was intentionally left as-is because the current popup roles matched the requested mapping.

### Custom Home Assistant entities

The custom Home Assistant entity section now supports three custom entities:

```text
Custom Home Assistant Entity 1
Custom Home Assistant Entity 2
Custom Home Assistant Entity 3
```

## Known design decision

Flow still exists, but entity management should no longer be trusted as the primary source. The next experimental build should target a separate test machine and remove/disable entity manager pages in Options Flow while keeping the current alpha130 test machine as a working reference.

Proposed next experimental package:

```text
alpha131_no_entity_flow_experimental
```

Recommended behavior:

```text
- Keep setup/config entry creation possible.
- Disable or replace Reports Entity Manager Flow page with a legacy notice.
- Disable or replace AI Entity Manager Flow page with a legacy notice.
- Disable or replace Dashboard Entity Manager Flow page with a legacy notice.
- Do not let Flow write vehicle_entity_map, dashboard_entity_map, or legacy report entity keys.
- Keep panel stores as the single source for entity management.
```

## Remaining validation before fully deleting Options Flow

Before removing Options Flow completely, validate the following non-entity settings from the panel:

```text
AI settings
Telegram settings
Charge report settings
Trip report settings
Automations settings
Dashboard fullscreen/top/sidebar/bottom/map/person/background settings
Export/import including panel_*_entity_map stores
New installation / first-run setup behavior
```

## Current safe baseline

The safe working baseline is:

```text
2.2.0-dashboard-alpha130
```

Do not delete the current working test machine. Use it as the reference environment while testing the Flow-disabled experimental build on a separate machine.

## Alpha132 note - Top area font scale controls

Dashboard top area now supports panel-controlled font scaling via `top_font_scale`, `top_left_font_scale`, `top_center_font_scale`, and `top_right_font_scale`. These are dashboard visual options and are saved through the panel dashboard settings path.

## alpha248 note

Added `trip_reports.ai_trip_story_detail_level` to the panel settings payload. Backend persists it as `ai_trip_story_detail_level` in config entry options. Accepted values: `basic`, `balanced`, `detailed`; default is `detailed`. Trip Records can display `ai_summary`, `ai_summary_detail_level`, `ai_summary_telegram_status`, and `ai_summary_at` from the trip ledger.

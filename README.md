[index (1).html](https://github.com/user-attachments/files/27308871/index.1.html)
# meshnet<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#050508">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="MeshNet">
<meta name="description" content="Rede distribuída — compartilhe CPU e RAM entre qualquer dispositivo em tempo real">
<meta property="og:title" content="MeshNet — Computação Distribuída">
<meta property="og:description" content="Crie uma sala e receba CPU e RAM de qualquer dispositivo conectado">
<meta property="og:type" content="website">
<title>MeshNet</title>

<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.js"></script>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,300;0,400;0,500;1,400&family=Clash+Display:wght@400;500;600;700&display=swap" rel="stylesheet">

<style>
/* ─── Reset ─────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }

/* ─── Tokens ─────────────────────────────────────── */
:root {
  --ink:    #050508;
  --paper:  #f2f0ea;
  --paper2: #e8e4db;
  --paper3: #ddd8cc;
  --line:   rgba(5,5,8,.1);
  --line2:  rgba(5,5,8,.18);
  --muted:  #8a8780;
  --acc:    #1a1aff;
  --acc2:   #00b37e;
  --acc3:   #e63c2f;
  --gold:   #c8a84b;
  --ok:     #00b37e;
  --warn:   #e09c1a;
  --err:    #e63c2f;
  --r:      6px;
  --r2:     12px;
  --r3:     20px;
  --mono:   'DM Mono', monospace;
  --display:'Clash Display', system-ui, sans-serif;
  --sat: env(safe-area-inset-top,0px);
  --sab: env(safe-area-inset-bottom,0px);
}

/* ─── Base ───────────────────────────────────────── */
html { height: 100%; background: var(--paper); }
body {
  font-family: var(--display);
  color: var(--ink);
  height: 100dvh;
  overflow: hidden;
  padding-top: var(--sat);
  background: var(--paper);
}

/* Grain overlay */
body::before {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 9998;
  opacity: .025;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  background-size: 256px;
}

::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--paper3); border-radius: 2px; }

/* ─── Shell ──────────────────────────────────────── */
#shell { display: grid; grid-template-rows: auto 1fr; height: 100dvh; }

#topbar {
  background: var(--ink);
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.logo {
  font-family: var(--mono);
  font-size: 13px;
  font-weight: 500;
  color: var(--paper);
  letter-spacing: .14em;
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
}
.logo-hex {
  width: 22px; height: 22px;
  display: flex; align-items: center; justify-content: center;
}

#cpill {
  font-size: 10px;
  font-family: var(--mono);
  padding: 3px 10px;
  border-radius: 20px;
  border: 1px solid rgba(255,255,255,.12);
  color: rgba(255,255,255,.4);
  white-space: nowrap;
  transition: all .3s;
}
#cpill.on  { color: var(--ok);   border-color: rgba(0,179,126,.4); background: rgba(0,179,126,.12); }
#cpill.warn{ color: var(--warn); border-color: rgba(224,156,26,.4); background: rgba(224,156,26,.1); }
#cpill.err { color: var(--err);  border-color: rgba(230,60,47,.4);  background: rgba(230,60,47,.1); }

#btnback { display: none; }

/* ─── Views ──────────────────────────────────────── */
#body { position: relative; overflow: hidden; height: 100%; }
.view { position: absolute; inset: 0; overflow-y: auto; display: none; padding-bottom: calc(20px + var(--sab)); }
.view.on { display: block; }

/* ─── LOBBY ──────────────────────────────────────── */
.hero {
  padding: 48px 24px 32px;
  display: grid;
  grid-template-columns: 1fr;
  gap: 0;
  max-width: 700px;
  margin: 0 auto;
}

.hero-eyebrow {
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: .2em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.hero-eyebrow::before {
  content: '';
  width: 24px;
  height: 1px;
  background: var(--muted);
}

.hero h1 {
  font-family: var(--display);
  font-size: clamp(36px, 8vw, 72px);
  font-weight: 700;
  line-height: .95;
  letter-spacing: -.02em;
  margin-bottom: 20px;
}
.hero h1 em {
  font-style: normal;
  color: var(--acc);
  position: relative;
}
.hero h1 em::after {
  content: '';
  position: absolute;
  bottom: 4px;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--acc);
  opacity: .3;
}

.hero-desc {
  font-family: var(--mono);
  font-size: 13px;
  color: var(--muted);
  line-height: 1.8;
  max-width: 360px;
  margin-bottom: 28px;
}

.hero-actions { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 40px; }

/* Share strip */
.share-strip {
  display: flex;
  align-items: stretch;
  border: 1px solid var(--line2);
  border-radius: var(--r2);
  overflow: hidden;
  max-width: 100%;
  margin-bottom: 40px;
  background: var(--paper2);
}
.share-strip-label {
  font-family: var(--mono);
  font-size: 9px;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: var(--muted);
  padding: 0 12px;
  display: flex;
  align-items: center;
  border-right: 1px solid var(--line);
  background: var(--paper3);
  flex-shrink: 0;
}
.share-strip-url {
  flex: 1;
  font-family: var(--mono);
  font-size: 11px;
  color: var(--acc);
  padding: 10px 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
  min-width: 0;
}
.share-strip-btn {
  background: var(--ink);
  color: var(--paper);
  border: none;
  padding: 10px 16px;
  font-family: var(--mono);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: .08em;
  cursor: pointer;
  white-space: nowrap;
  transition: background .2s;
  flex-shrink: 0;
}
.share-strip-btn:hover { background: #333; }

/* Section */
.section { padding: 0 24px 32px; max-width: 700px; margin: 0 auto; }
.sec-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--line);
}
.sec-label {
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: var(--muted);
  display: flex;
  align-items: center;
  gap: 8px;
}
.sec-label-count {
  background: var(--ink);
  color: var(--paper);
  font-size: 9px;
  padding: 1px 6px;
  border-radius: 20px;
}

/* Room cards */
.rgrid { display: grid; gap: 8px; }
@media(min-width:560px){ .rgrid { grid-template-columns: repeat(2,1fr); } }
@media(min-width:860px){ .rgrid { grid-template-columns: repeat(3,1fr); } }

.rc {
  background: var(--paper2);
  border: 1px solid var(--line);
  border-radius: var(--r2);
  padding: 16px;
  cursor: pointer;
  transition: border-color .18s, transform .15s, background .18s;
  position: relative;
  overflow: hidden;
}
.rc::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: var(--acc);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform .2s;
}
.rc:hover { border-color: var(--line2); background: var(--paper3); transform: translateY(-1px); }
.rc:hover::after { transform: scaleX(1); }
.rc:active { transform: scale(.99); }

.rc-name {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 7px;
  letter-spacing: -.01em;
}
.rc-id {
  font-family: var(--mono);
  font-size: 10px;
  color: var(--acc);
  margin-bottom: 10px;
}
.rc-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-family: var(--mono);
  font-size: 10px;
  color: var(--muted);
}
.livdot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--ok);
  display: inline-block;
  margin-right: 4px;
  box-shadow: 0 0 5px rgba(0,179,126,.5);
}

.badge {
  font-size: 9px;
  font-weight: 600;
  font-family: var(--mono);
  padding: 2px 7px;
  border-radius: 4px;
  letter-spacing: .04em;
}
.b-lock { background: rgba(200,168,75,.15); color: var(--gold); border: 1px solid rgba(200,168,75,.3); }
.b-mine { background: rgba(26,26,255,.08); color: var(--acc); border: 1px solid rgba(26,26,255,.2); }

.empty {
  text-align: center;
  padding: 48px 16px;
  color: var(--paper3);
  font-family: var(--mono);
  font-size: 12px;
  line-height: 2;
  background: var(--paper2);
  border: 1px dashed var(--line2);
  border-radius: var(--r2);
}

/* ─── ROOM ───────────────────────────────────────── */
#v-room { display: flex; flex-direction: column; overflow: hidden; }
#v-room.on { display: flex; }

#rbar {
  background: var(--paper2);
  border-bottom: 1px solid var(--line);
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}
#rbar .ri { flex: 1; min-width: 0; }
#rbar .rname {
  font-size: 15px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: -.01em;
}
#rbar .rmeta { font-family: var(--mono); font-size: 10px; color: var(--muted); margin-top: 1px; }
#rid-badge {
  font-family: var(--mono);
  font-size: 10px;
  color: var(--acc);
  background: var(--paper3);
  padding: 4px 10px;
  border-radius: var(--r);
  border: 1px solid rgba(26,26,255,.2);
  cursor: pointer;
  flex-shrink: 0;
  letter-spacing: .04em;
}

#rcontent {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: 800px;
  width: 100%;
  margin: 0 auto;
}

/* Meters */
.meters { display: grid; grid-template-columns: repeat(3,1fr); gap: 8px; }
.meter {
  background: var(--ink);
  border-radius: var(--r2);
  padding: 14px;
  color: var(--paper);
}
.ml {
  font-family: var(--mono);
  font-size: 9px;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: rgba(242,240,234,.4);
  margin-bottom: 6px;
}
.mv {
  font-family: var(--mono);
  font-size: 22px;
  font-weight: 500;
  line-height: 1;
  margin-bottom: 6px;
}
.mb { height: 2px; background: rgba(255,255,255,.1); border-radius: 1px; }
.mbf { height: 100%; border-radius: 1px; transition: width .5s ease; }

/* Members */
.mgrid { display: grid; gap: 8px; }
@media(min-width:480px){ .mgrid { grid-template-columns: repeat(2,1fr); } }
@media(min-width:760px){ .mgrid { grid-template-columns: repeat(3,1fr); } }

.mc {
  background: var(--paper2);
  border: 1px solid var(--line);
  border-radius: var(--r2);
  padding: 12px;
  transition: border-color .2s;
}
.mc.hst { border-color: rgba(26,26,255,.3); background: rgba(26,26,255,.03); }
.mct { display: flex; align-items: center; gap: 9px; margin-bottom: 10px; }
.av {
  width: 34px; height: 34px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--mono);
  font-size: 12px;
  font-weight: 500;
  flex-shrink: 0;
}
.mnm {
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 5px;
  flex-wrap: wrap;
  letter-spacing: -.01em;
}
.mos { font-family: var(--mono); font-size: 10px; color: var(--muted); }
.mst { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; }
.msi {
  background: var(--paper3);
  border-radius: var(--r);
  padding: 6px 8px;
}
.msil { font-family: var(--mono); font-size: 9px; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; }
.msiv { font-family: var(--mono); font-size: 13px; font-weight: 500; margin-top: 2px; }
.sdot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.son { background: var(--ok); box-shadow: 0 0 5px rgba(0,179,126,.4); }
.sof { background: var(--paper3); }

/* Host actions */
.hact {
  background: var(--ink);
  border-radius: var(--r2);
  padding: 14px;
  color: var(--paper);
}
.hact-l {
  font-family: var(--mono);
  font-size: 9px;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: rgba(242,240,234,.4);
  margin-bottom: 10px;
}
.tgrid { display: grid; grid-template-columns: repeat(auto-fit,minmax(120px,1fr)); gap: 6px; }
.tbtn {
  background: rgba(242,240,234,.07);
  border: 1px solid rgba(242,240,234,.12);
  border-radius: var(--r);
  padding: 9px 12px;
  font-family: var(--display);
  font-size: 12px;
  font-weight: 500;
  color: var(--paper);
  cursor: pointer;
  text-align: left;
  transition: all .17s;
  width: 100%;
}
.tbtn:hover { background: rgba(242,240,234,.13); border-color: rgba(242,240,234,.2); }
.tbtn:active { transform: scale(.97); }
.tbtn:disabled { opacity: .3; cursor: not-allowed; }

/* Tasks */
.ti {
  background: var(--paper2);
  border: 1px solid var(--line);
  border-radius: var(--r2);
  padding: 10px 12px;
  margin-bottom: 6px;
}
.tih { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }
.tiid { font-family: var(--mono); font-size: 11px; font-weight: 500; color: var(--acc); }
.tis { font-family: var(--mono); font-size: 10px; padding: 2px 8px; border-radius: 4px; }
.tis.d { background: rgba(0,179,126,.1); color: var(--ok); }
.tis.r { background: rgba(224,156,26,.1); color: var(--warn); }
.tim { font-family: var(--mono); font-size: 10px; color: var(--muted); }
.tib { height: 2px; background: var(--paper3); border-radius: 1px; margin-top: 7px; }
.tibf { height: 100%; border-radius: 1px; background: var(--acc); transition: width .4s; }

/* Log */
.logbox {
  background: var(--ink);
  border-radius: var(--r2);
  padding: 10px 12px;
  font-family: var(--mono);
  font-size: 11px;
  max-height: 130px;
  overflow-y: auto;
  color: rgba(242,240,234,.5);
}
.logbox::-webkit-scrollbar-thumb { background: rgba(255,255,255,.1); }
.ll { line-height: 1.7; margin-bottom: 1px; }
.ll.OK { color: var(--ok); }
.ll.W  { color: var(--warn); }
.ll.E  { color: var(--err); }
.ll.I  { color: rgba(242,240,234,.4); }

/* ─── Buttons ────────────────────────────────────── */
.btn {
  font-family: var(--display);
  font-size: 13px;
  font-weight: 600;
  padding: 10px 22px;
  border-radius: var(--r);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all .17s;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  letter-spacing: -.01em;
  white-space: nowrap;
}
.bp {
  background: var(--ink);
  color: var(--paper);
  border-color: var(--ink);
}
.bp:hover { background: #222; }
.bp:active { transform: scale(.97); }
.bs {
  background: var(--paper2);
  color: var(--ink);
  border-color: var(--line2);
}
.bs:hover { background: var(--paper3); }
.bg {
  background: transparent;
  color: var(--muted);
  border-color: var(--line);
}
.bg:hover { color: var(--ink); border-color: var(--line2); }
.bsm { padding: 7px 14px; font-size: 12px; }
.bxs { padding: 4px 10px; font-size: 11px; }

/* ─── Modal ──────────────────────────────────────── */
#ov {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(5,5,8,.6);
  backdrop-filter: blur(8px);
  z-index: 100;
  align-items: flex-end;
  justify-content: center;
}
#ov.on { display: flex; }
@media(min-width:500px){ #ov { align-items: center; } }

#mod {
  background: var(--paper);
  border: 1px solid var(--line2);
  border-radius: var(--r3) var(--r3) 0 0;
  padding: 28px 24px;
  padding-bottom: calc(28px + var(--sab));
  width: 100%;
  max-width: 440px;
  animation: su .2s ease;
}
@media(min-width:500px){ #mod { border-radius: var(--r3); padding-bottom: 28px; } }
@keyframes su { from { transform: translateY(32px); opacity: 0; } to { transform: none; opacity: 1; } }
#mod h3 { font-size: 20px; font-weight: 700; margin-bottom: 4px; letter-spacing: -.02em; }
.mdesc { font-family: var(--mono); font-size: 12px; color: var(--muted); margin-bottom: 20px; line-height: 1.7; }
.fld { margin-bottom: 12px; }
.fld label {
  display: block;
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 5px;
}
.fld input {
  width: 100%;
  background: var(--paper2);
  border: 1px solid var(--line2);
  border-radius: var(--r);
  padding: 11px 13px;
  font-family: var(--mono);
  font-size: 14px;
  color: var(--ink);
  outline: none;
  transition: border-color .2s;
  -webkit-appearance: none;
}
.fld input:focus { border-color: var(--acc); }
.mbtns { display: flex; gap: 8px; justify-content: flex-end; margin-top: 20px; }

/* ─── Install banner ─────────────────────────────── */
#instbanner {
  display: none;
  position: fixed;
  bottom: calc(16px + var(--sab));
  left: 50%;
  transform: translateX(-50%);
  background: var(--ink);
  color: var(--paper);
  border-radius: var(--r2);
  padding: 12px 16px;
  align-items: center;
  gap: 12px;
  box-shadow: 0 12px 40px rgba(5,5,8,.3);
  z-index: 50;
  max-width: 340px;
  width: calc(100% - 28px);
}
#instbanner.on { display: flex; }
#instbanner p { font-size: 13px; flex: 1; }
#instbanner p small { display: block; font-family: var(--mono); font-size: 10px; color: rgba(242,240,234,.4); }

/* ─── Animations ─────────────────────────────────── */
@keyframes fi { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
.rc, .mc, .ti { animation: fi .2s ease; }
@keyframes spin { to { transform: rotate(360deg); } }
.spin { display: inline-block; animation: spin .8s linear infinite; }
</style>
</head>
<body>
<div id="shell">
  <div id="topbar">
    <div class="logo">
      <div class="logo-hex">
        <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
          <polygon points="11,2 19.5,6.5 19.5,15.5 11,20 2.5,15.5 2.5,6.5"
            stroke="#f2f0ea" stroke-width="1.2" fill="none" opacity=".6"/>
          <circle cx="11" cy="11" r="3" fill="#1a1aff"/>
        </svg>
      </div>
      MESHNET
    </div>
    <span id="cpill">● conectando</span>
    <button class="btn bg bsm" id="btnback" onclick="leaveRoom()" style="display:none;color:rgba(242,240,234,.5);border-color:rgba(242,240,234,.15)">← sair</button>
  </div>

  <div id="body">

    <!-- LOBBY -->
    <div class="view on" id="v-lobby">
      <div class="hero">
        <div class="hero-eyebrow">Computação distribuída via Supabase Realtime</div>
        <h1>Compartilhe<br><em>poder</em><br>de processamento</h1>
        <p class="hero-desc">
          Crie uma sala e vire o HOST receptor.<br>
          Qualquer dispositivo com navegador<br>
          entra e contribui CPU + RAM para você.
        </p>

        <div class="share-strip">
          <div class="share-strip-label">link</div>
          <div class="share-strip-url" id="share-url" onclick="copyShareUrl()">carregando...</div>
          <button class="share-strip-btn" onclick="copyShareUrl()">COPIAR</button>
        </div>

        <div class="hero-actions">
          <button class="btn bp" onclick="openModal('create')">✦ Criar sala</button>
          <button class="btn bs" onclick="openModal('join')">→ Entrar em sala</button>
        </div>
      </div>

      <div class="section">
        <div class="sec-head">
          <span class="sec-label">
            Salas ativas
            <span class="sec-label-count" id="room-count" style="display:none">0</span>
          </span>
          <span style="font-family:var(--mono);font-size:10px;color:var(--muted)">
            atualiza em tempo real
          </span>
        </div>
        <div class="rgrid" id="rgrid">
          <div class="empty">
            <span class="spin" style="font-size:18px;color:var(--muted)">⬡</span><br><br>
            Conectando ao Supabase...
          </div>
        </div>
      </div>
    </div>

    <!-- ROOM -->
    <div class="view" id="v-room">
      <div id="rbar">
        <div class="ri">
          <div class="rname" id="rname">—</div>
          <div class="rmeta" id="rmeta">—</div>
        </div>
        <span id="rid-badge" onclick="copyRid()" title="Copiar link da sala"></span>
      </div>
      <div id="rcontent">

        <div class="meters">
          <div class="meter">
            <div class="ml">Dispositivos</div>
            <div class="mv" id="mdev" style="color:var(--acc2)">0</div>
            <div style="font-family:var(--mono);font-size:10px;color:rgba(242,240,234,.35)">clientes online</div>
          </div>
          <div class="meter">
            <div class="ml">CPU pool</div>
            <div class="mv" id="mcpu" style="color:var(--acc)">0%</div>
            <div class="mb"><div class="mbf" id="bcpu" style="background:var(--acc);width:0%"></div></div>
          </div>
          <div class="meter">
            <div class="ml">RAM pool</div>
            <div class="mv" id="mram" style="color:var(--acc3)">0GB</div>
            <div class="mb"><div class="mbf" id="bram" style="background:var(--acc3);width:0%"></div></div>
          </div>
        </div>

        <div class="hact" id="hact" style="display:none">
          <div class="hact-l">Distribuir tarefa</div>
          <div class="tgrid">
            <button class="tbtn" onclick="sendTask('compute')">⚡ Cálculo</button>
            <button class="tbtn" onclick="sendTask('sort')">🔢 Ordenação</button>
            <button class="tbtn" onclick="sendTask('hash')">🔐 Hashing</button>
          </div>
        </div>

        <div>
          <div class="sec-head" style="margin-bottom:10px">
            <span class="sec-label">Membros da sala</span>
            <span style="font-family:var(--mono);font-size:10px;color:var(--acc);cursor:pointer" onclick="copyRid()">
              compartilhar ↗
            </span>
          </div>
          <div class="mgrid" id="mgrid">
            <div class="empty" style="background:var(--paper2)">Aguardando membros...</div>
          </div>
        </div>

        <div id="tsec" style="display:none">
          <div class="sec-head" style="margin-bottom:10px">
            <span class="sec-label">Tarefas</span>
          </div>
          <div id="tlist"></div>
        </div>

        <div>
          <div class="sec-head" style="margin-bottom:8px">
            <span class="sec-label">Log</span>
          </div>
          <div class="logbox" id="logbox"></div>
        </div>

      </div>
    </div>

  </div>
</div>

<!-- MODAL -->
<div id="ov" onclick="if(event.target===this)closeModal()">
  <div id="mod">
    <h3 id="mtitle"></h3>
    <p class="mdesc" id="mdesc"></p>
    <div id="mbody"></div>
    <div class="mbtns">
      <button class="btn bg" onclick="closeModal()">Cancelar</button>
      <button class="btn bp" id="mok">Confirmar</button>
    </div>
  </div>
</div>

<!-- INSTALL BANNER -->
<div id="instbanner">
  <span style="font-size:20px">📲</span>
  <p>Instalar MeshNet<small>adicionar à tela inicial</small></p>
  <button class="btn bp bsm" onclick="installApp()">Instalar</button>
  <button class="btn bg bxs" style="color:rgba(242,240,234,.4);border-color:rgba(242,240,234,.1)"
    onclick="document.getElementById('instbanner').classList.remove('on')">✕</button>
</div>

<script>
'use strict';
// ════════════════════════════════════════════════════
//  SUPABASE CONFIG
// ════════════════════════════════════════════════════
const SB_URL = 'https://wvzaeoezostmydkpqelt.supabase.co';
const SB_KEY = 'sb_publishable_sYPZqHBknaVtEr1dS0eILQ_0ViliBl6';

// ════════════════════════════════════════════════════
//  ESTADO
// ════════════════════════════════════════════════════
let sb           = null;
let lobbyChannel = null;
let roomChannel  = null;

const myId = crypto.randomUUID();
let myName   = '';
let myRoomId = null;
let isHost   = false;

const members  = {};
const tasks    = {};
const taskRes  = {};

const COLS  = ['#1a1aff','#00b37e','#e63c2f','#c8a84b','#7c3aed','#0891b2','#d97706','#9333ea'];
const OSICO = { Windows:'🪟', Linux:'🐧', macOS:'🍎', Android:'📱', iOS:'📱' };

// ════════════════════════════════════════════════════
//  PWA
// ════════════════════════════════════════════════════
let dip;
window.addEventListener('beforeinstallprompt', e => {
  e.preventDefault(); dip = e;
  document.getElementById('instbanner').classList.add('on');
});
function installApp(){ if(dip){ dip.prompt(); dip.userChoice.then(()=>{ document.getElementById('instbanner').classList.remove('on'); dip=null; }); } }

// ════════════════════════════════════════════════════
//  INIT SUPABASE
// ════════════════════════════════════════════════════
function init(){
  try {
    sb = supabase.createClient(SB_URL, SB_KEY, {
      realtime: { params: { eventsPerSecond: 20 } }
    });
    document.getElementById('share-url').textContent = location.href;
    subscribeLobby();
    // Deep link
    const urlRoom = new URLSearchParams(location.search).get('room');
    if(urlRoom) setTimeout(()=>openModal('join', urlRoom), 800);
  } catch(e) {
    setPill('err','● erro');
    ulog('Erro ao conectar: '+e.message,'E');
  }
}

// ════════════════════════════════════════════════════
//  CANAL LOBBY — presença global de salas
// ════════════════════════════════════════════════════
function subscribeLobby(){
  if(lobbyChannel) sb.removeChannel(lobbyChannel);

  lobbyChannel = sb.channel('meshnet:lobby', {
    config: { presence: { key: myId }, broadcast: { self: false } }
  });

  lobbyChannel
    .on('presence', { event: 'sync'  }, () => { renderLobby(); setPill('on','● online'); })
    .on('presence', { event: 'join'  }, () => renderLobby())
    .on('presence', { event: 'leave' }, () => renderLobby())
    .subscribe(status => {
      if(status === 'SUBSCRIBED'){
        setPill('on','● online');
        ulog('Conectado — Supabase Realtime ativo','OK');
        renderLobby();
      }
    });
}

function getLobbyRooms(){
  if(!lobbyChannel) return [];
  return Object.values(lobbyChannel.presenceState())
    .flat()
    .filter(p => p.type === 'ROOM')
    .map(p => ({
      id:           p.room_id,
      name:         p.room_name,
      host_name:    p.host_name,
      has_password: p.has_password,
      created_at:   p.created_at,
      member_count: p.member_count || 0,
    }));
}

async function announceRoom(rid, name, hasPwd){
  if(!lobbyChannel) return;
  await lobbyChannel.track({
    type: 'ROOM', room_id: rid, room_name: name,
    host_name: myName, has_password: hasPwd,
    created_at: nowTs(), member_count: 0,
  });
}

async function updateLobbyCount(){
  if(!lobbyChannel || !isHost) return;
  const cur = Object.values(lobbyChannel.presenceState())
    .flat().find(p => p.type==='ROOM' && p.room_id===myRoomId);
  if(cur) await lobbyChannel.track({...cur, member_count: Object.keys(members).length});
}

// ════════════════════════════════════════════════════
//  CANAL SALA — HOST ↔ clientes
// ════════════════════════════════════════════════════
function subscribeRoom(rid){
  if(roomChannel) sb.removeChannel(roomChannel);

  roomChannel = sb.channel(`meshnet:room:${rid}`, {
    config: {
      presence:  { key: myId },
      broadcast: { self: false, ack: false },
    }
  });

  roomChannel
    .on('presence', { event: 'join' }, ({ newPresences }) => {
      if(!isHost) return;
      newPresences.forEach(p => {
        if(p.type === 'CLIENT' && p.member_id && !members[p.member_id]){
          members[p.member_id] = {
            id: p.member_id, name: p.name, os: p.os,
            cpu_avail: p.cpu_avail||0, ram_avail: p.ram_avail||0,
            cpu_count: p.cpu_count||1, ram_total: p.ram_total||8,
            tasks_done: 0, joined_at: nowTs(),
          };
          ulog(`🔗 ${p.name} (${p.os}) entrou na sala`,'OK');
          broadcastState();
          renderRoom();
          updateLobbyCount();
        }
      });
    })
    .on('presence', { event: 'leave' }, ({ leftPresences }) => {
      if(!isHost) return;
      leftPresences.forEach(p => {
        if(p.type==='CLIENT' && p.member_id && members[p.member_id]){
          ulog(`❌ ${members[p.member_id].name} saiu`,'W');
          delete members[p.member_id];
          broadcastState();
          renderRoom();
          updateLobbyCount();
        }
      });
    })
    .on('broadcast', { event: 'msg' }, ({ payload }) => handleMsg(payload))
    .subscribe(async status => {
      if(status !== 'SUBSCRIBED') return;
      if(isHost){
        await roomChannel.track({ type:'HOST', member_id:myId, name:myName, os:getOS() });
        ulog('Sala criada — aguardando membros','OK');
      } else {
        await roomChannel.track({
          type:'CLIENT', member_id:myId, name:myName, os:getOS(),
          cpu_avail: Math.round(15+Math.random()*65),
          ram_avail: Math.round((0.5+Math.random()*6)*10)/10,
          cpu_count: navigator.hardwareConcurrency||4,
          ram_total: 8,
        });
        // Pede estado ao HOST
        setTimeout(() => roomSend({ type:'GET_STATE', from:myId }), 600);
        ulog('Entrou na sala — aguardando estado do HOST','I');

        // Heartbeat a cada 7s
        setInterval(async () => {
          if(!myRoomId || isHost) return;
          await roomSend({
            type: 'HB', from: myId,
            cpu_avail: Math.round(15+Math.random()*65),
            ram_avail: Math.round((0.5+Math.random()*6)*10)/10,
          });
        }, 7000);
      }
    });
}

async function roomSend(payload){
  if(!roomChannel) return;
  await roomChannel.send({ type:'broadcast', event:'msg', payload });
}

// ════════════════════════════════════════════════════
//  HANDLER DE MENSAGENS DA SALA
// ════════════════════════════════════════════════════
function handleMsg(msg){
  const t = msg.type;

  if(t === 'GET_STATE' && isHost){
    broadcastState();
  }
  else if(t === 'ROOM_STATE' && !isHost){
    const st = msg.state;
    if(st){
      document.getElementById('rname').textContent    = st.room_name || 'Sala';
      document.getElementById('rid-badge').textContent = st.room_id || myRoomId;
      document.getElementById('rmeta').textContent    =
        `HOST: ${st.host_name} · Supabase Realtime`;
      renderRoomFromState(st);
    }
  }
  else if(t === 'HB' && isHost){
    if(members[msg.from]){
      members[msg.from].cpu_avail = msg.cpu_avail;
      members[msg.from].ram_avail = msg.ram_avail;
      renderRoom();
    }
  }
  else if(t === 'TASK' && !isHost){
    if(msg.target === myId) runTask(msg);
  }
  else if(t === 'TASK_RESULT' && isHost){
    handleTaskResult(msg);
  }
}

// ════════════════════════════════════════════════════
//  CRIAR SALA
// ════════════════════════════════════════════════════
async function createRoom(name, nick, password){
  myName = nick; isHost = true;
  myRoomId = 'MN-' + Math.random().toString(36).slice(2,8).toUpperCase();

  showView('room');
  document.getElementById('btnback').style.display = '';
  document.getElementById('rname').textContent     = name;
  document.getElementById('rid-badge').textContent = myRoomId;
  document.getElementById('rmeta').textContent     = `HOST 👑 · ${myRoomId}`;
  document.getElementById('hact').style.display    = '';

  subscribeRoom(myRoomId);
  await announceRoom(myRoomId, name, !!password);
  renderRoom();
  updateShareUrl();
}

// ════════════════════════════════════════════════════
//  ENTRAR NA SALA
// ════════════════════════════════════════════════════
function joinRoom(rid, nick, password){
  myName = nick; isHost = false; myRoomId = rid;

  showView('room');
  document.getElementById('btnback').style.display    = '';
  document.getElementById('rname').textContent        = '...';
  document.getElementById('rid-badge').textContent    = rid;
  document.getElementById('rmeta').textContent        = 'conectando...';
  document.getElementById('hact').style.display       = 'none';

  subscribeRoom(rid);
  updateShareUrl();
}

// ════════════════════════════════════════════════════
//  SAIR DA SALA
// ════════════════════════════════════════════════════
async function leaveRoom(){
  if(isHost && lobbyChannel) await lobbyChannel.untrack();
  if(roomChannel){ await roomChannel.untrack(); sb.removeChannel(roomChannel); roomChannel=null; }
  Object.keys(members).forEach(k=>delete members[k]);
  Object.keys(tasks).forEach(k=>delete tasks[k]);
  myRoomId=null; isHost=false;
  showView('lobby');
  document.getElementById('btnback').style.display='none';
  updateShareUrl();
}

// ════════════════════════════════════════════════════
//  DISTRIBUIR TAREFAS
// ════════════════════════════════════════════════════
async function sendTask(type){
  const clients = Object.values(members);
  if(!clients.length){ alert('Nenhum cliente na sala'); return; }
  const tid     = 'T-'+Math.random().toString(36).slice(2,8).toUpperCase();
  const payload = Array.from({length:2000},()=>Math.floor(Math.random()*1e6));
  const chunks  = splitList(payload, clients.length);
  tasks[tid] = {
    id:tid, type, total:clients.length, done:0,
    devices: clients.map(c=>c.name),
    created_at: nowTs(), finished_at:null, status:'running',
  };
  taskRes[tid] = {};
  for(let i=0;i<clients.length;i++){
    await roomSend({
      type:'TASK', task_id:tid, task_type:type,
      target:clients[i].id,
      chunk:chunks[i], chunk_index:i, total:clients.length,
    });
    ulog(`→ ${tid} p${i+1}/${clients.length} → ${clients[i].name}`,'I');
  }
  renderRoom();
}

// ════════════════════════════════════════════════════
//  EXECUTAR TAREFA (cliente no browser)
// ════════════════════════════════════════════════════
async function runTask(msg){
  ulog(`⚡ ${msg.task_id} [${msg.task_type}] — ${msg.chunk?.length} itens`,'I');
  await new Promise(r=>setTimeout(r,10));
  const chunk=msg.chunk||[]; const t0=performance.now(); let res={};
  if(msg.task_type==='compute'){
    let s=0; chunk.forEach(x=>s+=Math.sqrt(Math.abs(x))*Math.sin(x));
    res={sum:Math.round(s*1000)/1000, count:chunk.length};
  } else if(msg.task_type==='sort'){
    const sr=[...chunk].sort((a,b)=>a-b);
    res={min:sr[0]??0, max:sr[sr.length-1]??0, count:sr.length};
  } else {
    res={count:chunk.length, sample:chunk.slice(0,3).map(x=>btoa(String(x)).slice(0,10))};
  }
  res.elapsed = Math.round((performance.now()-t0)/10)/100;
  await roomSend({ type:'TASK_RESULT', task_id:msg.task_id,
                   from:myId, chunk_index:msg.chunk_index, result:res });
  ulog(`✓ ${msg.task_id} pronto em ${res.elapsed}s`,'OK');
}

function handleTaskResult(msg){
  const tid=msg.task_id; if(!tasks[tid]) return;
  if(taskRes[tid][msg.from]) return; // dedup
  taskRes[tid][msg.from]=msg.result;
  tasks[tid].done++;
  if(members[msg.from]) members[msg.from].tasks_done=(members[msg.from].tasks_done||0)+1;
  if(tasks[tid].done>=tasks[tid].total){
    tasks[tid].status='done'; tasks[tid].finished_at=nowTs();
    ulog(`✅ ${tid} concluída — ${tasks[tid].total} partes recebidas`,'OK');
  }
  broadcastState(); renderRoom();
}

// ════════════════════════════════════════════════════
//  BROADCAST DO ESTADO
// ════════════════════════════════════════════════════
function buildState(){
  const mlist = Object.values(members).map(m=>({...m, online:true}));
  return {
    room_id:   myRoomId,
    room_name: document.getElementById('rname').textContent,
    host_name: myName,
    members:   [{id:myId,name:myName,os:getOS(),is_host:true,
                  cpu_avail:0,ram_avail:0,tasks_done:0,online:true}, ...mlist],
    active_count: mlist.length,
    pool_cpu: Math.round(mlist.reduce((a,m)=>a+m.cpu_avail,0)*10)/10,
    pool_ram: Math.round(mlist.reduce((a,m)=>a+m.ram_avail,0)*100)/100,
    tasks:    Object.values(tasks).slice(-20),
  };
}

async function broadcastState(){
  if(!isHost) return;
  const state = buildState();
  await roomSend({ type:'ROOM_STATE', state });
  renderRoomFromState(state);
}

// ════════════════════════════════════════════════════
//  RENDER — Lobby
// ════════════════════════════════════════════════════
function renderLobby(){
  const rooms = getLobbyRooms();
  const g   = document.getElementById('rgrid');
  const cnt = document.getElementById('room-count');

  if(cnt){
    cnt.textContent = rooms.length;
    cnt.style.display = rooms.length ? '' : 'none';
  }

  if(!rooms.length){
    g.innerHTML='<div class="empty">Nenhuma sala ativa.<br>Crie a primeira!</div>';
    return;
  }
  g.innerHTML = rooms.map(r=>`
    <div class="rc" onclick="clickRoom('${r.id}')">
      <div class="rc-name">
        ${esc(r.name)}
        ${r.has_password?'<span class="badge b-lock">🔒</span>':''}
        ${r.id===myRoomId?'<span class="badge b-mine">minha</span>':''}
      </div>
      <div class="rc-id">${r.id}</div>
      <div class="rc-foot">
        <span><span class="livdot"></span>${r.member_count} cliente(s)</span>
        <span>${esc(r.host_name)}</span>
        <span>${r.created_at}</span>
      </div>
    </div>`).join('');
}

// ════════════════════════════════════════════════════
//  RENDER — Sala
// ════════════════════════════════════════════════════
function renderRoom(){
  if(!myRoomId||!isHost) return;
  renderRoomFromState(buildState());
}

function renderRoomFromState(st){
  if(!st) return;
  document.getElementById('mdev').textContent = st.active_count||0;
  document.getElementById('mcpu').textContent = (st.pool_cpu||0)+'%';
  document.getElementById('mram').textContent = (st.pool_ram||0).toFixed(1)+'GB';
  document.getElementById('bcpu').style.width =
    Math.min((st.pool_cpu||0)/Math.max((st.active_count||1)*100,1)*100,100)+'%';
  document.getElementById('bram').style.width =
    Math.min((st.pool_ram||0)/Math.max((st.active_count||1)*8,1)*100,100)+'%';

  const mg = document.getElementById('mgrid');
  if(!st.members?.length){
    mg.innerHTML='<div class="empty" style="background:var(--paper2)">Aguardando membros...</div>';
  } else {
    mg.innerHTML = st.members.map((m,i)=>{
      const c   = COLS[i%COLS.length];
      const ini = (m.name||'?').slice(0,2).toUpperCase();
      const hst = !!m.is_host;
      const me  = m.id===myId;
      const ico = OSICO[m.os]||'💻';
      return `<div class="mc${hst?' hst':''}">
        <div class="mct">
          <div class="av" style="background:${c}15;color:${c};border:1px solid ${c}30">${ini}</div>
          <div style="flex:1;min-width:0">
            <div class="mnm">
              <div class="sdot ${m.online?'son':'sof'}"></div>
              ${esc(m.name)}
              ${me?'<span style="font-family:var(--mono);font-size:9px;color:var(--muted)">(você)</span>':''}
              ${hst?'<span style="font-size:12px">👑</span>':''}
            </div>
            <div class="mos">${ico} ${m.os||'?'}</div>
          </div>
        </div>
        <div class="mst">
          <div class="msi">
            <div class="msil">CPU livre</div>
            <div class="msiv" style="color:var(--acc)">${m.cpu_avail||0}%</div>
          </div>
          <div class="msi">
            <div class="msil">RAM livre</div>
            <div class="msiv" style="color:var(--acc3)">${(m.ram_avail||0).toFixed(1)}GB</div>
          </div>
          <div class="msi" style="grid-column:1/-1">
            <div class="msil">Tarefas feitas</div>
            <div class="msiv" style="color:var(--acc2)">${m.tasks_done||0}</div>
          </div>
        </div>
      </div>`;
    }).join('');
  }

  const tsec  = document.getElementById('tsec');
  const tlist = document.getElementById('tlist');
  if(!st.tasks?.length){ tsec.style.display='none'; }
  else {
    tsec.style.display='';
    tlist.innerHTML = [...st.tasks].reverse().slice(0,8).map(t=>{
      const p = t.total>0 ? Math.round(t.done/t.total*100) : 0;
      return `<div class="ti">
        <div class="tih">
          <span class="tiid">${t.id}</span>
          <span class="tis ${t.status==='done'?'d':'r'}">
            ${t.status==='done'?'✓ concluída':'⏳ '+p+'%'}
          </span>
        </div>
        <div class="tim">${t.type} · ${t.done}/${t.total} partes · ${t.created_at}</div>
        <div class="tib"><div class="tibf" style="width:${p}%"></div></div>
      </div>`;
    }).join('');
  }
}

// ════════════════════════════════════════════════════
//  MODAL
// ════════════════════════════════════════════════════
function openModal(mode, rid){
  const h=document.getElementById('mtitle'),p=document.getElementById('mdesc');
  const b=document.getElementById('mbody'),ok=document.getElementById('mok');

  if(mode==='create'){
    h.textContent = '✦ Criar sala';
    p.textContent = 'Você será o HOST — outros entram e compartilham CPU e RAM com você em tempo real';
    b.innerHTML = `
      <div class="fld"><label>Seu apelido</label>
        <input id="fn" placeholder="ex: meu-notebook" value="${myName||''}" autocomplete="nickname"></div>
      <div class="fld"><label>Nome da sala</label>
        <input id="fr" placeholder="ex: Lab da Ana" autocomplete="off"></div>
      <div class="fld"><label>Senha (opcional — deixe vazio para sala pública)</label>
        <input id="fp" type="password" autocomplete="new-password"></div>`;
    ok.textContent = 'Criar sala';
    ok.onclick = () => {
      const n=gv('fn'), r=gv('fr'), pw=gv('fp');
      if(!n||!r){ alert('Preencha apelido e nome da sala'); return; }
      closeModal(); createRoom(r,n,pw);
    };
  } else {
    h.textContent = '→ Entrar em sala';
    p.textContent = rid ? `Entrando na sala ${rid}` : 'Informe o ID da sala para entrar';
    b.innerHTML = `
      <div class="fld"><label>Seu apelido</label>
        <input id="fn" placeholder="ex: meu-celular" value="${myName||''}" autocomplete="nickname"></div>
      ${!rid ? `<div class="fld"><label>ID da sala</label>
        <input id="frid" placeholder="ex: MN-AB12CD" autocomplete="off"></div>` : ''}
      <div class="fld"><label>Senha (se necessário)</label>
        <input id="fp" type="password" autocomplete="current-password"></div>`;
    ok.textContent = 'Entrar';
    ok.onclick = () => {
      const n=gv('fn'), r=rid||gv('frid'), pw=gv('fp');
      if(!n||!r){ alert('Preencha apelido e ID da sala'); return; }
      closeModal(); joinRoom(r,n,pw);
    };
  }

  document.getElementById('ov').classList.add('on');
  setTimeout(()=>document.querySelector('#mbody input')?.focus(), 80);
  document.getElementById('mod').onkeydown = e=>{ if(e.key==='Enter') ok.click(); };
}
function closeModal(){ document.getElementById('ov').classList.remove('on'); }

// ════════════════════════════════════════════════════
//  UTILS
// ════════════════════════════════════════════════════
function showView(n){
  document.querySelectorAll('.view').forEach(v=>v.classList.remove('on'));
  document.getElementById('v-'+n).classList.add('on');
}
function setPill(cls,txt){
  const el=document.getElementById('cpill');
  el.className=cls; el.id='cpill'; el.textContent=txt;
}
function ulog(msg,lvl='I'){
  const p=document.getElementById('logbox'); if(!p) return;
  const d=document.createElement('div'); d.className='ll '+lvl;
  d.textContent=`[${new Date().toLocaleTimeString('pt-BR',{hour12:false})}] ${msg}`;
  p.prepend(d); while(p.children.length>80) p.lastChild.remove();
}
function gv(id){ return document.getElementById(id)?.value.trim()||''; }
function esc(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function nowTs(){ return new Date().toLocaleTimeString('pt-BR',{hour12:false}); }
function getOS(){
  const ua=navigator.userAgent;
  if(/android/i.test(ua)) return 'Android';
  if(/iphone|ipad/i.test(ua)) return 'iOS';
  if(/mac/i.test(ua)) return 'macOS';
  if(/win/i.test(ua)) return 'Windows';
  if(/linux/i.test(ua)) return 'Linux';
  return 'Outro';
}
function splitList(lst,n){
  const k=Math.floor(lst.length/n), rem=lst.length%n;
  const parts=[]; let i=0;
  for(let j=0;j<n;j++){ const s=k+(j<rem?1:0); parts.push(lst.slice(i,i+s)); i+=s; }
  return parts;
}
function updateShareUrl(){
  const room = myRoomId ? `?room=${myRoomId}` : '';
  const url  = location.origin + location.pathname + room;
  const el   = document.getElementById('share-url');
  if(el) el.textContent = url;
}
function copyShareUrl(){
  const url = document.getElementById('share-url')?.textContent || location.href;
  navigator.clipboard?.writeText(url)
    .then(()=>ulog('Link copiado! Mande para outros dispositivos.','OK'))
    .catch(()=>alert('Copie o link manualmente: '+url));
}
function copyRid(){
  const rid = document.getElementById('rid-badge')?.textContent || myRoomId || '';
  if(!rid) return;
  const url = location.origin+location.pathname+`?room=${rid}`;
  navigator.clipboard?.writeText(url)
    .then(()=>ulog('Link da sala copiado!','OK'));
}
function clickRoom(rid){ openModal('join', rid); }

// ════════════════════════════════════════════════════
//  START
// ════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', ()=>{
  updateShareUrl();
  init();
  ulog('MeshNet iniciado','OK');
});
</script>
</body>
</html>

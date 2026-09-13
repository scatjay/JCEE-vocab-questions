// 遊戲化引擎 v0（快速堆版，之後迭代）。極小 API，未登入時靜默降級成純 localStorage。
// 用法：<script type="module"> import { JG } from "../game/engine.js"; JG.init({station:"wordwheel"}); </script>
import { initializeApp, getApps, getApp } from "https://www.gstatic.com/firebasejs/10.13.0/firebase-app.js";
import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.13.0/firebase-auth.js";
import { getDatabase, ref, get, set, update, push } from "https://www.gstatic.com/firebasejs/10.13.0/firebase-database.js";

const firebaseConfig = {
  apiKey: "AIzaSyBwPR0oE5VK0eBlqq8JY1B56UXy3R9cyng",
  authDomain: "gen-lang-client-0929530380.firebaseapp.com",
  databaseURL: "https://gen-lang-client-0929530380-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "gen-lang-client-0929530380",
};
const NS = "jceeVocabGame";
const LS_KEY = "jceeGame_v1";

const app = getApps().length ? getApp() : initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getDatabase(app);

function taipeiDay(ts = Date.now()) {
  // 台北無日光節約，UTC+8 固定
  const d = new Date(ts + 8 * 3600 * 1000);
  return d.toISOString().slice(0, 10);
}

function xpForLevel(n) { return Math.round(100 * Math.pow(n, 1.4)); }
function levelFromXp(xp) {
  let n = 1;
  while (xpForLevel(n + 1) <= xp) n++;
  return n;
}

function loadLocal() {
  try { return JSON.parse(localStorage.getItem(LS_KEY)) || {}; } catch (e) { return {}; }
}
function saveLocal(s) {
  try { localStorage.setItem(LS_KEY, JSON.stringify(s)); } catch (e) {}
}

class Engine {
  constructor() {
    this.user = null;
    this.station = null;
    this.session = null; // {mode, startedAt, attempted, correct, items:[]}
    this.local = loadLocal();
    this.local.xp = this.local.xp || 0;
    this.local.streak = this.local.streak || { current: 0, longest: 0, lastActiveDay: null, todayCount: 0 };
    this._hudEl = null;
    onAuthStateChanged(auth, (u) => { this.user = u; this._loadRemoteIfNeeded(); this._renderHud(); });
  }

  init({ station }) {
    this.station = station;
    this._injectHudOnce();
    this._renderHud();
  }

  async _loadRemoteIfNeeded() {
    if (!this.user) return;
    try {
      const snap = await get(ref(db, `${NS}/progress/${this.user.uid}`));
      if (snap.exists()) {
        const remote = snap.val();
        // 遠端是真相來源（跨裝置一致）；本機只是鏡像
        this.local.xp = remote.xp || 0;
        this.local.streak = remote.streak || this.local.streak;
        this.local.badges = remote.badges || {};
        saveLocal(this.local);
      }
    } catch (e) { /* 讀不到就先用本機值，不擋畫面 */ }
    this._renderHud();
  }

  sessionStart({ mode = "free" } = {}) {
    this.session = { mode, station: this.station, startedAt: Date.now(), attempted: 0, correct: 0, items: [] };
  }

  answer({ correct, qid, category, deepLink }) {
    if (!this.session) this.sessionStart({});
    this.session.attempted++;
    if (correct) this.session.correct++;

    const wasWrongBefore = !!(this.local.wrong && this.local.wrong[qid]);
    let gained = correct ? (wasWrongBefore ? 15 : 10) : 2;
    if (correct && wasWrongBefore) {
      this.local.wrong = this.local.wrong || {};
      delete this.local.wrong[qid];
    }
    if (!correct) {
      this.local.wrong = this.local.wrong || {};
      this.local.wrong[qid] = { station: this.station, qid, category, deepLink, missCount: ((this.local.wrong[qid] || {}).missCount || 0) + 1, lastMissAt: Date.now() };
    }

    this.local.xp += gained;
    this._bumpStreak();
    this.session.items.push({ qid, category, correct, gained, deepLink, at: Date.now() });
    saveLocal(this.local);
    this._renderHud(gained, correct);
    return { gained, level: levelFromXp(this.local.xp) };
  }

  _bumpStreak() {
    const today = taipeiDay();
    const s = this.local.streak;
    if (s.lastActiveDay === today) {
      s.todayCount = (s.todayCount || 0) + 1;
    } else {
      // 換日：昨天有沒有達標(>=3)決定連續是否延續
      s.todayCount = 1;
      const yesterday = taipeiDay(Date.now() - 86400000);
      if (s.lastActiveDay === yesterday && (s._prevDayCount || 0) >= 3) {
        s.current = (s.current || 0) + (s._countedYesterday ? 0 : 1);
      } else if (s.lastActiveDay !== today) {
        s.current = 0; // 斷了
      }
      s.lastActiveDay = today;
    }
    if (s.todayCount === 3) {
      s.current = (s.current || 0) + 1;
      s._countedYesterday = true;
      s._prevDayCount = s.todayCount;
    }
    s.longest = Math.max(s.longest || 0, s.current || 0);
  }

  async sessionEnd() {
    if (!this.session) return;
    const sess = this.session;
    sess.endedAt = Date.now();
    sess.durationSec = Math.round((sess.endedAt - sess.startedAt) / 1000);
    this.session = null;

    if (!this.user) return; // 未登入：只留在 localStorage，不寫遠端

    try {
      const uid = this.user.uid;
      await push(ref(db, `${NS}/sessions/${uid}`), {
        station: sess.station, mode: sess.mode,
        startedAt: sess.startedAt, endedAt: sess.endedAt,
        attempted: sess.attempted, correct: sess.correct, durationSec: sess.durationSec,
      });
      await update(ref(db, `${NS}/progress/${uid}`), {
        xp: this.local.xp, level: levelFromXp(this.local.xp), streak: this.local.streak,
      });
      for (const it of sess.items) {
        if (!it.correct) {
          await update(ref(db, `${NS}/wrongItems/${uid}/${it.qid}`), {
            station: sess.station, qid: it.qid, category: it.category || "", deepLink: it.deepLink || "",
            missCount: (this.local.wrong[it.qid] || {}).missCount || 1, lastMissAt: it.at,
          });
        } else if (this.local.wrong && !this.local.wrong[it.qid]) {
          // 這題剛被修好（本機已刪除該筆），標記修復時間
          await update(ref(db, `${NS}/wrongItems/${uid}/${it.qid}`), { repairedAt: it.at });
        }
      }
    } catch (e) { console.warn("JG sessionEnd 寫入失敗（不擋畫面）", e); }
  }

  _injectHudOnce() {
    if (document.getElementById("jg-hud")) return;
    const el = document.createElement("div");
    el.id = "jg-hud";
    el.innerHTML = `<span class="jg-lv"></span><span class="jg-xp"></span><span class="jg-streak"></span>`;
    document.body.appendChild(el);
    this._hudEl = el;
    if (!document.getElementById("jg-hud-css")) {
      const link = document.createElement("link");
      link.id = "jg-hud-css"; link.rel = "stylesheet";
      link.href = new URL("./engine.css", import.meta.url).href;
      document.head.appendChild(link);
    }
  }

  _renderHud(gained, correct) {
    if (!this._hudEl) return;
    const lv = levelFromXp(this.local.xp);
    this._hudEl.querySelector(".jg-lv").textContent = `Lv.${lv}`;
    this._hudEl.querySelector(".jg-xp").textContent = `${this.local.xp} XP`;
    this._hudEl.querySelector(".jg-streak").textContent = `🔥${(this.local.streak && this.local.streak.current) || 0}`;
    if (typeof gained === "number") {
      const toast = document.createElement("div");
      toast.className = "jg-toast" + (correct ? " ok" : "");
      toast.textContent = (correct ? "+" : "+") + gained + " XP";
      this._hudEl.appendChild(toast);
      setTimeout(() => toast.remove(), 1200);
    }
  }
}

export const JG = new Engine();

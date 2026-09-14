// 遊戲化引擎（WP-1）。極小 API，未登入時靜默降級成純 localStorage。
// 用法：<script type="module"> import { JG } from "../game/engine.js"; JG.init({station:"wordwheel"}); </script>
//
// 本檔是在 v0 草稿（190 行）上依 docs/cycle/wp1-2-design.md 補齊的正式交付：
// - Phase 1：sessionId 改用 push() 先取 key、progress/stations 累加、JG.setTrack、
//   _loadRemoteIfNeeded 併回遠端 wrongItems、engine.css。
// - Phase 2：JG.answer 擴充 kcId/errorMode/followedRecommendation、+15 跨場次判定、
//   progress/kc/{kcId}（evaluateKcEvent）、progress/recentAttempts、wrongItems.repairHistory。
// - 計分與熟練度判定的純函式邏輯抽到 ./kc-logic.js（不碰 RTDB/DOM，方便單獨測試）。
import { initializeApp, getApps, getApp } from "https://www.gstatic.com/firebasejs/10.13.0/firebase-app.js";
import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.13.0/firebase-auth.js";
import { getDatabase, ref, get, set, update, push } from "https://www.gstatic.com/firebasejs/10.13.0/firebase-database.js";
import { evaluateKcEvent, computeAnswerGain } from "./kc-logic.js";

const firebaseConfig = {
  apiKey: "AIzaSyBwPR0oE5VK0eBlqq8JY1B56UXy3R9cyng",
  authDomain: "gen-lang-client-0929530380.firebaseapp.com",
  databaseURL: "https://gen-lang-client-0929530380-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "gen-lang-client-0929530380",
};
const NS = "jceeVocabGame";
const LS_KEY = "jceeGame_v1";
const RECENT_ATTEMPTS_LIMIT = 30;
// 離線佇列上限：sessionEnd() 寫 RTDB 失敗時，先把整場 session 存進 localStorage 的
// this.local.pendingSessions，等下次連線成功再補送（見 _queueSession/_flushPendingSessions）。
// 超過上限才捨棄最舊的一場——這是刻意的邊界取捨（見 sessionEnd 附近註解），不是理想解。
const MAX_PENDING_SESSIONS = 20;

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

// Firebase RTDB 的 key 不能含 `. # $ [ ] /`。各站的 qid／kcId 不保證乾淨
// （例如 wordwheel 的 kcId 用 `${station}:${d.k}`，d.k 常見「-tion / -sion」這種帶斜線的字串；
// wordwheel 目前規劃的 qid 是 `${d.k}#${idx}` 帶 `#`）——寫進 RTDB 路徑前一律先轉成安全字元，
// 這也是 §3.2 schema 用 `itemKey` 而不是直接寫 `qid` 當節點名稱的原因。
function pathSafeKey(s) {
  return String(s).replace(/[.#$[\]/]/g, "_");
}

function sessionMsTotal(sess) {
  if (!sess.items.length) return 0;
  let total = 0;
  let prevAt = sess.startedAt;
  for (const it of sess.items) {
    total += Math.max(0, it.at - prevAt);
    prevAt = it.at;
  }
  return total;
}

class Engine {
  constructor() {
    this.user = null;
    this.station = null;
    this.session = null; // {mode, station, startedAt, attempted, correct, items:[], sessionId}
    this.local = loadLocal();
    this.local.xp = this.local.xp || 0;
    this.local.streak = this.local.streak || { current: 0, longest: 0, lastActiveDay: null, todayCount: 0 };
    this.local.pendingSessions = Array.isArray(this.local.pendingSessions) ? this.local.pendingSessions : [];
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
    // 每次連線/重新登入都是一次補送離線佇列的機會（不只靠下一次 sessionEnd）——
    // 斷線常態化的使用者可能久久才重新開站，這裡先補送完再讀遠端，讓下面讀到的
    // progress/wrongItems 是補送後的最新狀態，不會讓 HUD 短暫顯示「進度消失」。
    await this._flushPendingSessions();
    try {
      const uid = this.user.uid;
      const [progressSnap, wrongSnap, recentSnap] = await Promise.all([
        get(ref(db, `${NS}/progress/${uid}`)),
        get(ref(db, `${NS}/wrongItems/${uid}`)),
        get(ref(db, `${NS}/progress/${uid}/recentAttempts`)),
      ]);
      if (progressSnap.exists()) {
        const remote = progressSnap.val();
        // 遠端是真相來源（跨裝置一致）；本機只是鏡像
        this.local.xp = remote.xp || 0;
        this.local.streak = remote.streak || this.local.streak;
        this.local.badges = remote.badges || {};
      }
      // 換裝置/清快取後，wrongItems 一律以遠端現值為準——不然「這題修好了嗎」的判定會失真
      // （assessment-expert 審查第4/7條；驗收標準13）。
      this.local.wrong = wrongSnap.exists() ? wrongSnap.val() : (this.local.wrong || {});
      // WP-9 介面契約 B：JG.getRecentWindow(n) 要合併的「已持久化」那一半，跟 wrongItems 一樣
      // 換裝置/清快取後以遠端現值為準。
      let recentAttempts = recentSnap.exists() ? recentSnap.val() : [];
      if (!Array.isArray(recentAttempts)) recentAttempts = Object.values(recentAttempts || {});
      this.local.recentAttempts = recentAttempts;
      saveLocal(this.local);
    } catch (e) { /* 讀不到就先用本機值，不擋畫面 */ }
    this._renderHud();
  }

  /**
   * WP-9 介面契約 B：回傳最近 n 筆作答，合併「本場尚未 flush 的 session.items」與
   * 「上次 sessionEnd 已寫入 RTDB 的 progress/recentAttempts 快取」，依時間新到舊排序後取前 n 筆
   * （回傳順序依 at 升冪：舊到新，供 evaluateFloorState 直接使用）。
   * 未登入時（this.user===null）只用 this.session.items，跟既有「未登入靜默降級成純
   * localStorage」的整體架構一致。
   */
  getRecentWindow(n = 20) {
    const persisted = Array.isArray(this.local.recentAttempts) ? this.local.recentAttempts : [];
    const inSession = this.session
      ? this.session.items.map((it) => ({
          at: it.at, station: this.station, kcId: it.kcId, correct: it.correct, sessionId: this.session.sessionId,
        }))
      : [];
    const merged = this.user ? [...persisted, ...inSession] : [...inSession];
    merged.sort((a, b) => a.at - b.at);
    return merged.slice(-n);
  }

  /**
   * WP-9 介面契約 D：讀取現有 progress/{uid}/floorState（不存在時回傳 null，呼叫端自行
   * 套用 floor-logic.js 的 emptyFloorState()）。未登入時沒有遠端可讀，回傳 null。
   */
  async getFloorState() {
    if (!this.user) return null;
    try {
      const snap = await get(ref(db, `${NS}/progress/${this.user.uid}/floorState`));
      return snap.exists() ? snap.val() : null;
    } catch (e) {
      console.warn("JG.getFloorState 讀取失敗（不擋畫面）", e);
      return null;
    }
  }

  /** WP-9 介面契約 A：把 evaluateFloorState() 算出的新 floorState 寫回 progress/{uid}/floorState。 */
  setFloorState(floorState) {
    if (!this.user) return;
    update(ref(db, `${NS}/progress/${this.user.uid}`), { floorState }).catch((e) => {
      console.warn("JG.setFloorState 寫入失敗（不擋畫面）", e);
    });
  }

  sessionStart({ mode = "free" } = {}) {
    // sessionId 在這裡就決定（不是等 sessionEnd 才算），因為 JG.answer 的 +15 跨場次判定
    // 需要在作答當下就知道「這是不是同一場」——push() 只是跟伺服器要一把不重複的 key，
    // 不代表真的寫資料（真正落地是在 sessionEnd 用同一把 key set() 進去）。
    // 未登入時沒有 uid 可以要 key，退化用本機亂數字串，一樣具備「同一場都相同、跨場不同」的性質。
    const sessionId = this.user
      ? push(ref(db, `${NS}/sessions/${this.user.uid}`)).key
      : `local_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    this.session = { mode, station: this.station, startedAt: Date.now(), attempted: 0, correct: 0, items: [], sessionId };
  }

  setTrack(track) {
    // 低頻、即時寫，不等 sessionEnd。未登入時沒有 progress/{uid} 可寫，靜默略過。
    if (!this.user) return;
    update(ref(db, `${NS}/progress/${this.user.uid}`), { track }).catch((e) => {
      console.warn("JG.setTrack 寫入失敗（不擋畫面）", e);
    });
  }

  forceStreakCredit({ reason } = {}) {
    // 給 WP-9 floor-hit 掛的入口：把「今天已完成」的判定強制視為 true，
    // 但不改變 session.attempted/correct、不給 XP、不寫 wrongItems/kc/recentAttempts。
    // 做法：沿用既有 _bumpStreak() 的換日/計數骨架本身（一個字都不改），
    // 呼叫到 todayCount 達到跟正常答滿 3 題等價的狀態為止。
    if (this.local.streak.lastActiveDay !== taipeiDay()) this._bumpStreak();
    let guard = 0;
    while ((this.local.streak.todayCount || 0) < 3 && guard < 5) {
      this._bumpStreak();
      guard++;
    }
    saveLocal(this.local);
    if (this.user) {
      update(ref(db, `${NS}/progress/${this.user.uid}`), { streak: this.local.streak }).catch((e) => {
        console.warn("JG.forceStreakCredit 寫入失敗（不擋畫面）", e);
      });
    }
    this._renderHud();
    // reason 目前只用來讓呼叫端表明用意，WP-9 若之後要留存觸發原因，屬於 WP-9 自己的資料節點，
    // 本 WP 不擅自幫它決定要存在哪裡。
    void reason;
  }

  answer({ correct, qid, category, deepLink, kcId, errorMode, followedRecommendation = false }) {
    if (!this.session) this.sessionStart({});

    this.session.attempted++;
    if (correct) this.session.correct++;

    let resolvedKcId = kcId;
    if (!resolvedKcId) {
      resolvedKcId = `${this.station}:${qid}`;
      console.warn(
        `JG.answer: 呼叫時沒有帶 kcId，退化用 "${resolvedKcId}" 頂替——這一題暫時自成一個 KC，` +
        `熟練度判定會失真（不擋畫面，但請盡快讓 ${this.station} 的 adapter 補上 kcId）。`
      );
    }

    const wrongEntry = this.local.wrong && this.local.wrong[qid];
    const { gained, isRepairEvent, wasWrongBefore } = computeAnswerGain({
      correct, wrongEntry, sessionId: this.session.sessionId, followedRecommendation,
    });

    if (!correct) {
      this.local.wrong = this.local.wrong || {};
      this.local.wrong[qid] = {
        station: this.station, qid, category, deepLink,
        missCount: ((this.local.wrong[qid] || {}).missCount || 0) + 1,
        lastMissAt: Date.now(),
        lastMissSessionId: this.session.sessionId,
      };
    } else if (wasWrongBefore) {
      // 不管這次算不算「修復」（跨場次才給+15），只要答對了，本機就不再視為目前答錯中。
      delete this.local.wrong[qid];
    }

    this.local.xp += gained;
    this._bumpStreak();
    this.session.items.push({
      qid, category, correct, gained, deepLink, at: Date.now(),
      station: this.station, kcId: resolvedKcId, errorMode,
      followedRecommendation: !!followedRecommendation, isRepairEvent,
    });
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

    // 先補送先前失敗累積的舊場次，維持時間順序寫入——KC 精熟判定（evaluateKcEvent）
    // 是拿「前一筆狀態」逐次疊代算下一筆，跳過順序或讓新場次搶先寫入會讓舊場次的
    // 精熟計算基準錯亂。
    await this._flushPendingSessions();

    try {
      await this._writeSessionToRemote(sess);
    } catch (e) {
      console.warn(
        "JG sessionEnd 寫入失敗，先存入本機離線佇列，下次連線成功時補送（不擋畫面，不丟棄這場的精熟/錯題進度）",
        e
      );
      this._queueSession(sess);
    }
  }

  /**
   * 把單一場 session 的 RTDB 寫入邏輯（Phase 1 stations 累計、Phase 2 kc/recentAttempts/
   * wrongItems.repairHistory）跑一次。失敗會 throw，由呼叫端（sessionEnd/_flushPendingSessions）
   * 決定要不要排進離線佇列。因為 kcMap/wrongMap/recentAttempts 都是在函式一開頭現撈遠端現值
   * 再疊代，離線佇列補送時只要照佇列順序依序呼叫這支，就會自然疊代出正確的最終狀態
   * ——不需要另外對佇列裡的多筆 session 做「合併/去重」，疊代本身就是最新狀態覆蓋舊狀態。
   */
  async _writeSessionToRemote(sess) {
    const uid = this.user.uid;
    const sessionId = sess.sessionId;
    const updates = {};
    updates[`${NS}/sessions/${uid}/${sessionId}`] = {
      station: sess.station, mode: sess.mode,
      startedAt: sess.startedAt, endedAt: sess.endedAt,
      attempted: sess.attempted, correct: sess.correct, durationSec: sess.durationSec,
    };
    updates[`${NS}/progress/${uid}/xp`] = this.local.xp;
    updates[`${NS}/progress/${uid}/level`] = levelFromXp(this.local.xp);
    updates[`${NS}/progress/${uid}/streak`] = this.local.streak;

    // ---- Phase 1：progress/{uid}/stations/{stationId} 累計 ----
    const stationSnap = await get(ref(db, `${NS}/progress/${uid}/stations/${sess.station}`));
    const prevStation = stationSnap.exists()
      ? stationSnap.val()
      : { attempted: 0, correct: 0, lastAt: 0, msPerItem: 0 };
    const msTotal = sessionMsTotal(sess);
    const newAttempted = (prevStation.attempted || 0) + sess.attempted;
    const newCorrect = (prevStation.correct || 0) + sess.correct;
    const newMsPerItem = newAttempted > 0
      ? Math.round(((prevStation.msPerItem || 0) * (prevStation.attempted || 0) + msTotal) / newAttempted)
      : 0;
    updates[`${NS}/progress/${uid}/stations/${sess.station}`] = {
      attempted: newAttempted, correct: newCorrect, lastAt: sess.endedAt, msPerItem: newMsPerItem,
    };

    // ---- Phase 2：progress/kc/{kcId}、progress/recentAttempts、wrongItems.repairHistory ----
    const [kcSnap, recentSnap, wrongSnap] = await Promise.all([
      get(ref(db, `${NS}/progress/${uid}/kc`)),
      get(ref(db, `${NS}/progress/${uid}/recentAttempts`)),
      get(ref(db, `${NS}/wrongItems/${uid}`)),
    ]);
    const kcMap = kcSnap.exists() ? kcSnap.val() : {};
    let recentAttempts = recentSnap.exists() ? recentSnap.val() : [];
    if (!Array.isArray(recentAttempts)) recentAttempts = Object.values(recentAttempts || {});
    const wrongMap = wrongSnap.exists() ? wrongSnap.val() : {};

    const touchedKc = new Set();
    for (const it of sess.items) {
      const kcKey = pathSafeKey(it.kcId);
      touchedKc.add(kcKey);
      kcMap[kcKey] = evaluateKcEvent(kcMap[kcKey] || null, {
        at: it.at, correct: it.correct, sessionId, station: sess.station, itemId: it.qid,
      });

      recentAttempts.push({ at: it.at, station: sess.station, kcId: it.kcId, correct: it.correct, sessionId });

      const itemKey = pathSafeKey(it.qid);
      const existing = wrongMap[itemKey] || {};
      if (!it.correct) {
        const missCount = (existing.missCount || 0) + 1;
        updates[`${NS}/wrongItems/${uid}/${itemKey}/station`] = sess.station;
        updates[`${NS}/wrongItems/${uid}/${itemKey}/qid`] = it.qid;
        updates[`${NS}/wrongItems/${uid}/${itemKey}/category`] = it.category || "";
        updates[`${NS}/wrongItems/${uid}/${itemKey}/deepLink`] = it.deepLink || "";
        updates[`${NS}/wrongItems/${uid}/${itemKey}/missCount`] = missCount;
        updates[`${NS}/wrongItems/${uid}/${itemKey}/lastMissAt`] = it.at;
        wrongMap[itemKey] = { ...existing, missCount, lastMissAt: it.at };
      } else if (it.isRepairEvent) {
        const history = Array.isArray(existing.repairHistory) ? existing.repairHistory.slice() : [];
        history.push({ repairedAt: it.at, sessionId });
        updates[`${NS}/wrongItems/${uid}/${itemKey}/repairHistory`] = history;
        updates[`${NS}/wrongItems/${uid}/${itemKey}/repairedAt`] = it.at;
        wrongMap[itemKey] = { ...existing, repairHistory: history, repairedAt: it.at };
      }
    }

    while (recentAttempts.length > RECENT_ATTEMPTS_LIMIT) recentAttempts.shift();
    updates[`${NS}/progress/${uid}/recentAttempts`] = recentAttempts;
    for (const kcKey of touchedKc) {
      updates[`${NS}/progress/${uid}/kc/${kcKey}`] = kcMap[kcKey];
    }

    await update(ref(db), updates);
  }

  /**
   * 把一場寫入失敗的 session 存進本機離線佇列（this.local.pendingSessions），
   * 下次連線成功時（_flushPendingSessions）優先補送。同一 sessionId 已在佇列中時直接覆蓋
   * （理論上 sessionEnd 每場只呼叫一次，這裡是保險）。超過 MAX_PENDING_SESSIONS 時捨棄
   * 最舊的一場並 console.warn——這是長時間離線的邊界取捨，不是本次修復要解決的目標
   * （目標是「一般斷線/訊號不穩」不遺失，不是「無限期離線也保證不遺失」）。
   */
  _queueSession(sess) {
    const pending = Array.isArray(this.local.pendingSessions) ? this.local.pendingSessions : [];
    const idx = pending.findIndex((p) => p.sessionId === sess.sessionId);
    if (idx >= 0) pending[idx] = sess; else pending.push(sess);
    while (pending.length > MAX_PENDING_SESSIONS) {
      const dropped = pending.shift();
      console.warn(
        `JG 離線佇列超過上限(${MAX_PENDING_SESSIONS})，捨棄最舊的一場待補送 session（sessionId=${dropped.sessionId}）`
      );
    }
    this.local.pendingSessions = pending;
    saveLocal(this.local);
  }

  /**
   * 依佇列順序（舊到新）依序嘗試把待補送的 session 補寫回 RTDB。任何一筆失敗就停止
   * （保留它與它之後尚未補送的，等下次再試），已成功補送的每寫完一筆就立刻從佇列移除並
   * 存檔——避免「補送到一半又斷線」導致同一筆被重複補送兩次（RTDB 的 update 本身是
   * 冪等覆蓋沒錯，但重複補送等於白白多打兩次遠端請求，且失敗時的錯誤訊息會誤導）。
   */
  async _flushPendingSessions() {
    if (!this.user) return;
    const pending = Array.isArray(this.local.pendingSessions) ? this.local.pendingSessions : [];
    while (pending.length) {
      const sess = pending[0];
      try {
        await this._writeSessionToRemote(sess);
        pending.shift();
        this.local.pendingSessions = pending;
        saveLocal(this.local);
      } catch (e) {
        console.warn("JG 離線佇列補送失敗，暫緩，下次連線再試（進度仍留在本機佇列，未遺失）", e);
        break;
      }
    }
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
// 給 cycle-evaluator／單元測試用（不是公開 API 的一部分，公開 API 只有 JG 本身）。
export { evaluateKcEvent, computeAnswerGain };

// 純函式模組（WP-9 Phase 1）。仿照 ./kc-logic.js 的寫法：不碰 RTDB/DOM，方便 node 直接
// 單元測試，也方便 cycle-evaluator 照著寫 floor_sim.py 或等效測試。
// 對應 docs/cycle/wp9-2-design.md 介面契約 C（evaluateFloorState）與介面契約 A（floorState schema）。

/** 觸底判定所需的滾動視窗大小（介面契約 C 規則 1）。 */
export const FLOOR_WINDOW_SIZE = 20;
/** ≤30% 規則的門檻（介面契約 C 規則 1）。 */
export const FLOOR_MIN_CORRECT_RATIO = 0.30;
/** 連續 8 題錯規則的「8」（介面契約 C 規則 1）。 */
export const FLOOR_LAST_N_ALL_WRONG = 8;
/** 脫離觸底所需的連續答對數（介面契約 C 規則 3）。 */
export const FLOOR_EXIT_STREAK = 5;
/** 24 小時冷卻窗口，單位 ms（介面契約 C 規則 2）。 */
export const FLOOR_COOLDOWN_MS = 24 * 3600 * 1000;

/**
 * progress/{uid}/floorState 不存在時的預設值（介面契約 A／C 開頭所述）。
 * @returns {{active:boolean, firstTriggeredAt:number|null, lastTriggeredAt:number|null,
 *            consecutiveCorrectSinceTrigger:number, triggerCount:number}}
 */
export function emptyFloorState() {
  return {
    active: false,
    firstTriggeredAt: null,
    lastTriggeredAt: null,
    consecutiveCorrectSinceTrigger: 0,
    triggerCount: 0,
  };
}

function correctCount(window) {
  return window.reduce((n, it) => n + (it.correct ? 1 : 0), 0);
}

function last8AllWrong(window) {
  if (window.length < FLOOR_LAST_N_ALL_WRONG) return false;
  const lastN = window.slice(-FLOOR_LAST_N_ALL_WRONG);
  return lastN.every((it) => it.correct === false);
}

/**
 * 純函式：把最近作答視窗套進既有 floorState，算出新的 floorState 與這次要採取的 action。
 * 不碰 RTDB / DOM，輸入輸出都是資料——見 wp9-2-design.md 介面契約 C。
 *
 * @param {object|null} prevFloorState 現有 progress/{uid}/floorState（不存在時傳 null，
 *   等同 emptyFloorState()）
 * @param {Array<{at:number, station:string, kcId:string, correct:boolean, sessionId:string}>} window
 *   JG.getRecentWindow(20) 的回傳值，依 at 升冪排序（舊到新）
 * @param {number} [now=Date.now()]
 * @returns {{floorState:object, action:'trigger_full'|'trigger_short'|'exit'|'none'}}
 */
export function evaluateFloorState(prevFloorState, window, now = Date.now()) {
  const prev = prevFloorState || emptyFloorState();
  const isFloorCondition =
    (window.length >= FLOOR_WINDOW_SIZE && correctCount(window) / window.length <= FLOOR_MIN_CORRECT_RATIO) ||
    last8AllWrong(window);

  if (!prev.active) {
    if (!isFloorCondition) {
      return { floorState: prev, action: "none" };
    }
    const cooledDown = prev.lastTriggeredAt == null || now - prev.lastTriggeredAt >= FLOOR_COOLDOWN_MS;
    const action = cooledDown ? "trigger_full" : "trigger_short";
    const floorState = {
      active: true,
      firstTriggeredAt: prev.firstTriggeredAt || now,
      lastTriggeredAt: now,
      consecutiveCorrectSinceTrigger: 0,
      triggerCount: (prev.triggerCount || 0) + 1,
    };
    return { floorState, action };
  }

  // 已在觸底狀態：逐筆處理 lastTriggeredAt 之後發生的作答（跨任意站，呼應發現 2 的裁決）。
  // 注意：window 每次呼叫都是「當下最新 20 筆」的完整重算，不是只帶入新增的那一筆，
  // 所以這裡必須從 0 重新掃過 since、不能疊加 prev.consecutiveCorrectSinceTrigger——
  // 否則同一批已經算過的作答會被重複疊加，人為灌高連續答對數（曾在自驗時實測到這個 bug：
  // 三次呼叫後 consecutiveCorrectSinceTrigger 變成 1→3→6 而不是真正的 1→2→3）。
  let consecutiveCorrectSinceTrigger = 0;
  const since = window.filter((it) => it.at > prev.lastTriggeredAt);
  for (const it of since) {
    consecutiveCorrectSinceTrigger = it.correct ? consecutiveCorrectSinceTrigger + 1 : 0;
  }

  if (consecutiveCorrectSinceTrigger >= FLOOR_EXIT_STREAK) {
    const floorState = { ...prev, active: false, consecutiveCorrectSinceTrigger };
    return { floorState, action: "exit" };
  }

  const floorState = { ...prev, consecutiveCorrectSinceTrigger };
  return { floorState, action: "trigger_short" };
}

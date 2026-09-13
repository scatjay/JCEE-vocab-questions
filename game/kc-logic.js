// 純函式模組（WP-1 Phase 2）。刻意不 import 任何 Firebase／DOM，方便 cycle-evaluator
// 用 node 直接單元測試（不需要瀏覽器、不需要網路 import）。
// 對應 docs/cycle/wp1-2-design.md 介面契約 E（evaluateKcEvent）與計分規則（computeAnswerGain）。

/** KC 熟練度判定所需的「間隔」門檻：7 天，單位 ms（WP-8 政策8）。 */
export const KC_SPACED_MS = 7 * 24 * 3600 * 1000;
/** progress/{uid}/kc/{kcId}.recentWindow 上限（WP-1 介面契約 C）。 */
export const KC_WINDOW_LIMIT = 10;
/** 連續獨立正確次數達標即視為熟練（WP-8 政策8）。 */
export const KC_MASTERY_STREAK = 3;

/**
 * 純函式：把一次作答事件套進既有 KC 記錄，算出新的 KC 記錄。
 * 不碰 RTDB / DOM，輸入輸出都是資料——見 wp1-2-design.md 介面契約 E。
 *
 * @param {object|null} prevKcRecord 前一次的 progress/{uid}/kc/{kcId} 內容（沒有就傳 null）
 * @param {{at:number, correct:boolean, sessionId:string, station:string, itemId:string}} event
 * @returns {object} 新的 progress/{uid}/kc/{kcId} 內容
 */
export function evaluateKcEvent(prevKcRecord, event) {
  const prev = prevKcRecord || {
    attempted: 0,
    correct: 0,
    recentWindow: [],
    consecutiveSpacedCorrect: 0,
    lastTestedAt: null,
    lastTestedSessionId: null,
    masteredAt: null,
    crossStationVerified: false,
    _stationsInStreak: [],
  };
  const { at, correct, sessionId, station, itemId } = event;

  const attempted = prev.attempted + 1;
  const correctCount = prev.correct + (correct ? 1 : 0);

  const recentWindow = [...(prev.recentWindow || []), { at, correct, itemId, sessionId, station }];
  while (recentWindow.length > KC_WINDOW_LIMIT) recentWindow.shift();

  // 「獨立事件」：距上次作答 ≥7 天 且 sessionId 不同。第一次作答（沒有「上次」可比較）
  // 視為 vacuously true——不然三次都要求跟前一次比較會需要第 4 次才湊得出 3 次獨立事件，
  // 跟驗收標準（三次分屬三個不同 session、間隔 ≥7 天 → 第三次後 masteredAt 成立）對不上。
  const isIndependent =
    prev.lastTestedAt == null
      ? true
      : at - prev.lastTestedAt >= KC_SPACED_MS && sessionId !== prev.lastTestedSessionId;

  let consecutiveSpacedCorrect = prev.consecutiveSpacedCorrect || 0;
  let stationsInStreak = prev._stationsInStreak ? [...prev._stationsInStreak] : [];

  if (!correct) {
    // 獨立事件但答錯，或非獨立事件時答錯 → 歸零（WP-8 政策8字面規則）
    consecutiveSpacedCorrect = 0;
    stationsInStreak = [];
  } else if (isIndependent) {
    consecutiveSpacedCorrect += 1;
    stationsInStreak.push(station);
  }
  // else：非獨立事件且答對 → 不變（同一 session 內同一 KC 被答第二次不算獨立事件）

  let masteredAt = prev.masteredAt ?? null;
  let crossStationVerified = prev.crossStationVerified || false;
  if (consecutiveSpacedCorrect >= KC_MASTERY_STREAK && masteredAt == null) {
    masteredAt = at;
    const last3 = stationsInStreak.slice(-KC_MASTERY_STREAK);
    crossStationVerified = new Set(last3).size >= 2;
  }

  return {
    attempted,
    correct: correctCount,
    recentWindow,
    consecutiveSpacedCorrect,
    lastTestedAt: at,
    lastTestedSessionId: sessionId,
    masteredAt,
    crossStationVerified,
    // 🔴 內部欄位，不在 wp1-2-design.md 介面契約 C 列出的 schema 內：純函式重新評估下一次事件時
    // 需要知道「這一輪連續獨立正確」各自發生在哪些站，才能算 crossStationVerified；
    // 若不想讓這個欄位進 RTDB，呼叫端可以在寫入前自行剔除，見 engine.js 的取捨說明。
    _stationsInStreak: stationsInStreak,
  };
}

/**
 * 純函式：算出這一次作答該得多少 XP，以及是不是一次「跨場次修復」。
 * 不碰 RTDB / DOM。對應 wp1-2-design.md 介面契約 A 的計分規則。
 *
 * @param {{correct:boolean, wrongEntry:({lastMissSessionId?:string}|null|undefined), sessionId:string, followedRecommendation?:boolean}} input
 * @returns {{gained:number, isRepairEvent:boolean, wasWrongBefore:boolean}}
 */
export function computeAnswerGain({ correct, wrongEntry, sessionId, followedRecommendation = false }) {
  const wasWrongBefore = !!wrongEntry;
  let gained;
  let isRepairEvent = false;

  if (!correct) {
    gained = 2;
  } else if (wasWrongBefore) {
    const differentSession = wrongEntry.lastMissSessionId !== sessionId;
    gained = differentSession ? 15 : 10; // 同場次先錯後對：只算一般答對，不給修復加成
    isRepairEvent = differentSession;
  } else {
    gained = 10;
  }

  if (correct && followedRecommendation === true) gained += 2; // WP-8 一致性加成，可與修復加成疊加

  return { gained, isRepairEvent, wasWrongBefore };
}

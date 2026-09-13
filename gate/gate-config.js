// 共用 Firebase 設定 + 登入/審核輔助函式
// 專案：gen-lang-client-0929530380（沿用既有 Firebase 專案，獨立命名空間 jceeVocabGame，
// 跟同專案下其他線的資料互不相通——見 RTDB 規則裡的 jceeVocabGame 節點）
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.13.0/firebase-app.js";
import {
  getAuth, GoogleAuthProvider, signInWithPopup, signOut, onAuthStateChanged,
} from "https://www.gstatic.com/firebasejs/10.13.0/firebase-auth.js";
import {
  getDatabase, ref, get, set, onValue,
} from "https://www.gstatic.com/firebasejs/10.13.0/firebase-database.js";

const firebaseConfig = {
  apiKey: "AIzaSyBwPR0oE5VK0eBlqq8JY1B56UXy3R9cyng",
  authDomain: "gen-lang-client-0929530380.firebaseapp.com",
  databaseURL: "https://gen-lang-client-0929530380-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "gen-lang-client-0929530380",
};

const ADMIN_EMAIL = "scatjay@gmail.com";
const NS = "jceeVocabGame";

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getDatabase(app);

export function userRef(uid) {
  return ref(db, `${NS}/users/${uid}`);
}

export function allUsersRef() {
  return ref(db, `${NS}/users`);
}

export function loginWithGoogle() {
  return signInWithPopup(auth, new GoogleAuthProvider());
}

export function logout() {
  return signOut(auth);
}

export function watchAuth(cb) {
  return onAuthStateChanged(auth, cb);
}

export function isAdmin(user) {
  return !!user && user.email === ADMIN_EMAIL;
}

// 登入後確保審核資料存在；已存在就不覆寫（避免自己把 approved 改回 false 或竄改）
export async function ensureUserRecord(user) {
  const r = userRef(user.uid);
  const snap = await get(r);
  if (!snap.exists()) {
    await set(r, {
      email: user.email,
      displayName: user.displayName || "",
      photoURL: user.photoURL || "",
      approved: false,
      requestedAt: Date.now(),
    });
  }
  return r;
}

export function watchUserRecord(uid, cb) {
  return onValue(userRef(uid), (snap) => cb(snap.val()));
}

export function watchAllUsers(cb) {
  return onValue(allUsersRef(), (snap) => cb(snap.val() || {}));
}

export async function approveUser(uid) {
  const r = ref(db, `${NS}/users/${uid}/approved`);
  await set(r, true);
  await set(ref(db, `${NS}/users/${uid}/approvedAt`), Date.now());
}

export { ADMIN_EMAIL };

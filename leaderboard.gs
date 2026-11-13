// Mr. Mayor leaderboard — paste into the "Mr. Mayor Leaderboard" Google Sheet:
// Extensions > Apps Script, replace everything with this file, then Deploy > New deployment > Web app,
// Execute as: Me, Who has access: Anyone. Put the web-app URL into LB_URL in index.html.
// Rows go to the first sheet: time | name | stars | pts | id | sec (play time in seconds, from round 2 to the end).
// Ranking: more stars first; on equal stars the shorter play time wins; then pts; then who sent first. Delete a row in the Sheet to remove a fake score.

function doGet(e) {
  var n = Math.max(1, Math.min(20, Number(e && e.parameter && e.parameter.n) || 10));
  return out(top_(n));
}

function doPost(e) {
  var d = {};
  try { d = JSON.parse(e.postData.contents); } catch (err) { return out(top_()); }
  var name = String(d.name || '').replace(/[<>]/g, '').trim().slice(0, 16) || 'Mayor';
  if (rude_(name)) name = 'Mayor';
  var stars = Math.max(0, Math.min(8, Math.floor(Number(d.stars) || 0)));
  var pts = Math.max(0, Math.min(300, Math.floor(Number(d.pts) || 0)));
  var id = String(d.id || '').replace(/[^a-z0-9]/gi, '').slice(0, 20);
  var sec = Math.max(0, Math.min(36000, Math.floor(Number(d.sec) || 0)));
  var lock = LockService.getScriptLock();
  lock.waitLock(5000);
  try { sheet_().appendRow([new Date(), name, stars, pts, id, sec]); } finally { lock.releaseLock(); }
  return out(top_(10));
}

// Same simple word list as the game: rude names are stored as "Mayor".
var BAD_ = ['ควย','เหี้ย','สัส','เย็ด','หี','แตด','ดอกทอง','อีดอก','แม่ง','ระยำ','ชิบหาย','เชี่ย','กระหรี่','ส้นตีน','เงี่ยน','หำ','เสือก','สถุน','fuck','shit','bitch','cunt','dick','pussy','asshole','nigg','fag','cock','slut','whore','porn','rape','nazi','hitler','penis','vagina','bastard'];
function rude_(n) {
  var t = String(n).toLowerCase().replace(/[\u200b-\u200d\ufeff]/g, '')
    .replace(/0/g, 'o').replace(/[1!|]/g, 'i').replace(/3/g, 'e').replace(/[4@]/g, 'a').replace(/[5$]/g, 's').replace(/7/g, 't')
    .replace(/[^a-z\u0e00-\u0e7f]/g, '');
  var sq = t.replace(/(.)\1+/g, '$1');
  return BAD_.some(function (w) { return t.indexOf(w) >= 0 || sq.indexOf(w) >= 0; });
}

function sheet_() { return SpreadsheetApp.getActiveSpreadsheet().getSheets()[0]; }

// top: best n rows · total: every score sent · best: how many Best Mayors (8 stars) — board.html shows the last two
function top_(n) {
  var rows = sheet_().getDataRange().getValues().filter(function (r) {
    return r[1] !== '' && r[1] !== 'name';
  });
  var t = function (r) { var v = Number(r[5]); return v > 0 ? v : 1e9; };   // no time recorded = after everyone with a time
  rows.sort(function (a, b) { return (b[2] - a[2]) || (t(a) - t(b)) || (b[3] - a[3]) || (new Date(a[0]) - new Date(b[0])); });
  return { total: rows.length, best: rows.filter(function (r) { return Number(r[2]) >= 8; }).length,
    top: rows.slice(0, n || 10).map(function (r) {
    return { name: String(r[1]), stars: Number(r[2]), pts: Number(r[3]), id: String(r[4]), sec: Number(r[5]) || 0 };
  }) };
}

function out(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

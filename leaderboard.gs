// Mr. Mayor leaderboard — paste into the "Mr. Mayor Leaderboard" Google Sheet:
// Extensions > Apps Script, replace everything with this file, then Deploy > New deployment > Web app,
// Execute as: Me, Who has access: Anyone. Put the web-app URL into LB_URL in index.html.
// Rows go to the first sheet: time | name | stars | pts | id. Delete a row in the Sheet to remove a fake score.

function doGet(e) { return out(top_()); }

function doPost(e) {
  var d = {};
  try { d = JSON.parse(e.postData.contents); } catch (err) { return out(top_()); }
  var name = String(d.name || '').replace(/[<>]/g, '').trim().slice(0, 16) || 'Mayor';
  var stars = Math.max(0, Math.min(8, Math.floor(Number(d.stars) || 0)));
  var pts = Math.max(0, Math.min(300, Math.floor(Number(d.pts) || 0)));
  var id = String(d.id || '').replace(/[^a-z0-9]/gi, '').slice(0, 20);
  var lock = LockService.getScriptLock();
  lock.waitLock(5000);
  try { sheet_().appendRow([new Date(), name, stars, pts, id]); } finally { lock.releaseLock(); }
  return out(top_());
}

function sheet_() { return SpreadsheetApp.getActiveSpreadsheet().getSheets()[0]; }

function top_() {
  var rows = sheet_().getDataRange().getValues().filter(function (r) {
    return r[1] !== '' && r[1] !== 'name';
  });
  rows.sort(function (a, b) { return (b[2] - a[2]) || (b[3] - a[3]) || (new Date(a[0]) - new Date(b[0])); });
  return { top: rows.slice(0, 10).map(function (r) {
    return { name: String(r[1]), stars: Number(r[2]), pts: Number(r[3]), id: String(r[4]) };
  }) };
}

function out(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

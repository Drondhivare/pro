// Test list.html mapping logic
const r = {
  resultId: 1,
  examTitle: 'DBMS Mid-Term Assessment',
  examCode: 'EXAM-DBMS-MID',
  totalMarks: '100.00',
  totalMarksObtained: '50.00',
  percentage: '50.00',
  grade: 'D',
  passStatus: 1,
  publishedAt: '2026-08-11 21:23:17'
};

const totalMarks = Number(r.totalMarks || 0);
const marksObtained = Number(r.totalMarksObtained || 0);
let pctValue = r.percentage != null ? Number(r.percentage) : null;
if (totalMarks > 0 && (pctValue === null || isNaN(pctValue) || Math.abs(pctValue - (marksObtained / totalMarks) * 100) > 0.01)) {
  pctValue = Number(((marksObtained / totalMarks) * 100).toFixed(2));
}
const isPassed = Boolean(r.passStatus != null ? r.passStatus : (totalMarks > 0 && marksObtained >= Number(r.passingMarks || 0)));
const passClass = isPassed ? 'bg-success' : 'bg-danger';
const passLabel = isPassed ? 'PASSED' : 'FAILED';
const pct = pctValue != null ? `${pctValue.toFixed(2)}%` : '--';

console.log('List HTML row rendered values:');
console.log('Percentage & Marks:', `${pct} (${marksObtained.toFixed(2)}/${totalMarks.toFixed(2)})`);
console.log('Grade:', r.grade);
console.log('Status badge:', passLabel);

// Test detail.html scorecard logic
let data = { ...r };
let dTotalMarks = Number(data.totalMarks || 0);
let dMarksObtained = Number(data.totalMarksObtained || 0);
let dPctValue = data.percentage != null ? Number(data.percentage) : null;
if (dTotalMarks > 0 && (dPctValue === null || isNaN(dPctValue) || Math.abs(dPctValue - (dMarksObtained / dTotalMarks) * 100) > 0.01)) {
  dPctValue = Number(((dMarksObtained / dTotalMarks) * 100).toFixed(2));
}
console.log('\nDetail HTML scorecard stats:');
console.log('Total Marks:', dTotalMarks.toFixed(2));
console.log('Marks Obtained:', dMarksObtained.toFixed(2));
console.log('Percentage:', `${dPctValue.toFixed(2)}%`);
console.log('Grade:', `${data.grade} (${passLabel})`);

// Also test defensive fallback if backend returned stale 100.00% with 50/100
let staleData = { ...r, percentage: '100.00' };
let sTotal = Number(staleData.totalMarks || 0);
let sObtained = Number(staleData.totalMarksObtained || 0);
let sPct = staleData.percentage != null ? Number(staleData.percentage) : null;
if (sTotal > 0 && (sPct === null || isNaN(sPct) || Math.abs(sPct - (sObtained / sTotal) * 100) > 0.01)) {
  sPct = Number(((sObtained / sTotal) * 100).toFixed(2));
}
console.log('\nDefensive Fallback Test with stale 100.00% in payload:');
console.log('Calculated percentage is corrected to:', `${sPct.toFixed(2)}%`);
if (sPct !== 50.00) {
  throw new Error('Fallback failed!');
}
console.log('All frontend rendering tests PASSED!');

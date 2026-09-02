document.addEventListener('DOMContentLoaded', ()=> {
  const btn = document.getElementById('contactBtn');
  if (!btn) return;
  btn.addEventListener('click', ()=> {
    // سلوك تجريبي: عرض رسالة تنبيهية
    alert('زر التّواصل التجريبي من Trend Line — هذه تجربة فقط.');
  });
});

// بسيط: فتح/إغلاق نافذة الحجز وتنقل شهادي للآراء
document.addEventListener('DOMContentLoaded',function(){
  const openBtns = document.querySelectorAll('#openBooking, #heroBook, #openBooking2');
  const modal = document.getElementById('bookingModal');
  const close = document.getElementById('closeBooking');
  const form = document.getElementById('bookingForm');

  openBtns.forEach(b=>b && b.addEventListener('click',()=>{
    modal.classList.add('show'); modal.setAttribute('aria-hidden','false');
  }));
  close.addEventListener('click',()=>{ modal.classList.remove('show'); modal.setAttribute('aria-hidden','true'); });
  modal.addEventListener('click',e=>{ if(e.target===modal){ modal.classList.remove('show'); modal.setAttribute('aria-hidden','true'); }});

  form.addEventListener('submit',function(e){
    e.preventDefault();
    alert('تم إرسال الحجز (محاكاة). لن يتم إرسال رسائل فعلية دون موافقة كريم.');
    modal.classList.remove('show'); modal.setAttribute('aria-hidden','true');
  });

  // simple testimonials rotate
  const slides = document.querySelectorAll('.testi');
  let si=0;
  setInterval(()=>{
    slides[si].classList.remove('active');
    si = (si+1)%slides.length;
    slides[si].classList.add('active');
  },4500);
});
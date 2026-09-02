// Simple interactions: language toggle (AR/EN) and form save-as-draft
const langBtn = document.getElementById('langToggle');
let lang = 'ar';
langBtn.addEventListener('click', ()=>{
  if(lang==='ar'){
    document.documentElement.lang='en';
    document.documentElement.dir='ltr';
    lang='en';
    langBtn.textContent='AR';
    // Minimal English content swap (demo)
    document.querySelector('.brand').textContent='MaxFiber';
    document.querySelector('.hero h1').textContent='Durable fiber panels for modern projects';
    document.querySelector('.hero p').textContent='Solutions for cladding, roofing, insulation and industrial use — water, heat and impact resistant.';
    document.querySelector('.btn.primary').textContent='Request a quote';
  } else {
    document.documentElement.lang='ar';
    document.documentElement.dir='rtl';
    lang='ar';
    langBtn.textContent='EN';
    document.querySelector('.brand').textContent='ماكس فيبر';
    document.querySelector('.hero h1').textContent='ألواح فيبر متينة وعملية للمشاريع الحديثة';
    document.querySelector('.hero p').textContent='حلول فيبر مصممة للواجهات، الأسقف، العزل والتطبيقات الصناعية — متاحة بخصائص مقاومة للماء، الحرارة والصدمات.';
    document.querySelector('.btn.primary').textContent='اطلب عرض سعر';
  }
});

// Save form as draft to localStorage (no external sending)
const form = document.getElementById('contactForm');
const sendBtn = document.getElementById('sendBtn');
sendBtn.addEventListener('click', ()=>{
  const data = {
    name: document.getElementById('name').value,
    email: document.getElementById('email').value,
    message: document.getElementById('message').value,
    timestamp: new Date().toISOString()
  };
  localStorage.setItem('maxfiber_draft', JSON.stringify(data));
  alert(lang==='ar'? 'تم حفظ الطلب كمسودة محليًا — لن يُرسل بدون موافقة كريم.' : 'Draft saved locally — will not be sent without Karim\'s approval.');
});

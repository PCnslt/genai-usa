// shared: cursor glow + scroll reveal
(function () {
  const glow = document.getElementById('glow');
  if (glow) {
    let mx = innerWidth / 2, my = innerHeight / 2, gx = mx, gy = my;
    addEventListener('mousemove', e => { mx = e.clientX; my = e.clientY; }, { passive: true });
    (function loop() { gx += (mx - gx) * .07; gy += (my - gy) * .07; glow.style.transform = `translate(${gx}px,${gy}px)`; requestAnimationFrame(loop); })();
  }
  const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { threshold: 0.15 });
  document.querySelectorAll('.reveal').forEach(el => io.observe(el));
})();

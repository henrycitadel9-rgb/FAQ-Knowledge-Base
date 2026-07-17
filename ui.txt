/* ui.js - small microinteractions and entrance animations */
(function(){
    'use strict';

    function prefersReducedMotion(){
        try{
            return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        }catch(e){return false;}
    }

    // Staggered entrance for cards
    function animateCards(){
        if(prefersReducedMotion()) return;
        var cards = document.querySelectorAll('.interface-card[data-animate]');
        cards.forEach(function(card, idx){
            var delay = (parseInt(card.getAttribute('data-animate')) || idx) * 120;
            card.style.transitionDelay = (delay/1000)+'s';
            card.classList.add('animate-in');
        });
    }

    // Simple ripple for buttons/links
    function addRipple(){
        document.addEventListener('click', function(e){
            var el = e.target.closest('.interface-link');
            if(!el) return;
            var rect = el.getBoundingClientRect();
            var circle = document.createElement('span');
            circle.className = 'ripple';
            var size = Math.max(rect.width, rect.height);
            circle.style.width = circle.style.height = size+'px';
            circle.style.left = (e.clientX - rect.left - size/2)+'px';
            circle.style.top = (e.clientY - rect.top - size/2)+'px';
            el.appendChild(circle);
            window.setTimeout(function(){ circle.remove(); }, 500);
        });
    }

    // small nav highlight on scroll/hover
    function init(){
        animateCards();
        addRipple();
    }

    if(document.readyState === 'loading'){
        document.addEventListener('DOMContentLoaded', init);
    }else{
        init();
    }
})();

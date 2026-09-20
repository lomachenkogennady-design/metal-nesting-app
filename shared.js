/* Общий модуль ФАЙЕРПРОМ — связка DXF ↔ КП */
(function(w){
  var KEY = 'fayerprom_dxf_to_kp';
  var PRICE_KEY = 'fayerprom_last_price';
  
  // DXF-модуль сохраняет список деталей
  w.fpPushParts = function(parts) {
    try {
      localStorage.setItem(KEY, JSON.stringify({
        ts: Date.now(),
        items: parts
      }));
      return true;
    } catch(e) { return false; }
  };
  
  // Калькулятор забирает детали
  w.fpPullParts = function() {
    try {
      var raw = localStorage.getItem(KEY);
      if (!raw) return null;
      var data = JSON.parse(raw);
      // если старше 24 часов — игнорируем
      if (Date.now() - data.ts > 86400000) {
        localStorage.removeItem(KEY);
        return null;
      }
      return data.items;
    } catch(e) { return null; }
  };
  
  w.fpClearParts = function() {
    try { localStorage.removeItem(KEY); } catch(e){}
  };
  
  // Запомнить последнюю цену металла для обмена
  w.fpSetPrice = function(price) {
    try { localStorage.setItem(PRICE_KEY, String(price)); } catch(e){}
  };
  w.fpGetPrice = function() {
    try { return parseFloat(localStorage.getItem(PRICE_KEY)) || null; } catch(e){ return null; }
  };
})(window);

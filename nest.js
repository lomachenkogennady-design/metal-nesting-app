/* Модуль раскроя — общий для dxf-tools и index */
(function(w){
  // Полочный алгоритм (shelf / next-fit)
  w.fpNest = function(sw, sh, margin, items) {
    var flat = [];
    items.forEach(function(p){
      var cnt = p.count || p.q || 1;
      for (var i = 0; i < cnt; i++) {
        flat.push({ name: p.name || p.n || 'Деталь', w: p.w || 500, h: p.h || 500 });
      }
    });
    flat.sort(function(a,b){ return (b.w*b.h) - (a.w*a.h); });
    var res = [], sidx = 0, cx = 0, cy = 0, rh = 0;
    var W = sw - margin, H = sh - margin;
    flat.forEach(function(it){
      var w = it.w, h = it.h;
      if (w > W && h <= W && w <= H) { var t = w; w = h; h = t; }
      if (cx + w + margin > W) { cx = 0; cy += rh + margin; rh = 0; }
      if (cy + h + margin > H) { sidx++; cx = 0; cy = 0; rh = 0; }
      res.push({ sheet: sidx, x: cx, y: cy, w: w, h: h, name: it.name });
      cx += w + margin;
      if (h > rh) rh = h;
    });
    return res;
  };
  
  // SVG-карта раскроя (для печати КП)
  w.fpNestSVG = function(res, sw, sh, sheets, maxShow) {
    maxShow = maxShow || 3;
    var show = Math.min(sheets, maxShow);
    var scale = 0.1; // 1 мм = 0.1 px
    var W = sw * scale, H = sh * scale;
    var pad = 10, gap = 20, labelH = 14;
    var totalW = W + pad * 2;
    var totalH = show * (H + labelH + gap) + pad;
    
    var svgPx = 500;
    var aspect = totalH / totalW;
    var svgH = Math.round(svgPx * aspect);
    var svg = '<svg xmlns="http://www.w3.org/2000/svg" width="' + svgPx + '" height="' + svgH + '" viewBox="0 0 ' + totalW + ' ' + totalH + '" style="background:#fff;display:block">';
    svg += '<style>text{font-family:sans-serif;font-size:8px;fill:#333}.det{fill:#3182ce;fill-opacity:.25;stroke:#2b6cb0;stroke-width:.5}</style>';
    
    var oy = pad;
    for (var i = 0; i < show; i++) {
      svg += '<text x="' + pad + '" y="' + (oy + 9) + '" style="font-size:9px;font-weight:600">Лист ' + (i+1) + ' — ' + sw + '×' + sh + ' мм</text>';
      svg += '<rect x="' + pad + '" y="' + (oy + labelH) + '" width="' + W + '" height="' + H + '" fill="#f8fafc" stroke="#3182ce" stroke-width="1"/>';
      
      res.filter(function(r){ return r.sheet === i; }).forEach(function(r) {
        var x = pad + r.x * scale;
        var y = oy + labelH + r.y * scale;
        var w = r.w * scale;
        var h = r.h * scale;
        svg += '<rect class="det" x="' + x.toFixed(1) + '" y="' + y.toFixed(1) + '" width="' + w.toFixed(1) + '" height="' + h.toFixed(1) + '"/>';
        if (w > 25 && h > 10) {
          svg += '<text x="' + (x+2).toFixed(1) + '" y="' + (y+9).toFixed(1) + '">' + (r.name || '').slice(0, 12) + '</text>';
        }
      });
      
      oy += labelH + H + gap;
    }
    if (sheets > show) {
      svg += '<text x="' + pad + '" y="' + (oy + 5) + '" style="font-size:8px;fill:#92400e">... ещё ' + (sheets - show) + ' листов (показаны первые ' + show + ')</text>';
    }
    svg += '</svg>';
    return svg;
  };
  
  // Расчёт статистики
  w.fpNestStats = function(res, sw, sh) {
    var sheets = 0;
    res.forEach(function(r){ if (r.sheet + 1 > sheets) sheets = r.sheet + 1; });
    var totArea = 0;
    res.forEach(function(r){ totArea += (r.w * r.h) / 1e6; });
    var totSheet = sheets * (sw * sh / 1e6);
    var usage = totSheet > 0 ? (totArea / totSheet * 100) : 0;
    return { sheets: sheets, partArea: totArea, sheetArea: totSheet, usage: usage };
  };

  // Обёртка: SVG → img с data URL (для печати)

  w.fpNestIMG = function(res, sw, sh, sheets, maxShow) {
    try {
      maxShow = maxShow || 3;
      var show = Math.min(sheets, maxShow);
      var px = 1000;
      var scale = px / sw;
      var labelH = 30;
      var gap = 40;
      var sheetH = Math.round(sh * scale);
      var totalH = show * (sheetH + labelH + gap) + gap;
      var canvas = document.createElement('canvas');
      canvas.width = px + 40;
      canvas.height = totalH;
      var ctx = canvas.getContext('2d');
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.font = '18px sans-serif';
      ctx.textBaseline = 'top';
      var oy = gap;
      for (var i = 0; i < show; i++) {
        var ox = 20;
        ctx.fillStyle = '#333333';
        ctx.fillText('Лист ' + (i+1) + ' - ' + sw + 'x' + sh + ' мм', ox, oy);
        var sheetY = oy + labelH;
        ctx.fillStyle = '#f8fafc';
        ctx.fillRect(ox, sheetY, px, sheetH);
        ctx.strokeStyle = '#3182ce';
        ctx.lineWidth = 2;
        ctx.strokeRect(ox, sheetY, px, sheetH);
        res.filter(function(r){ return r.sheet === i; }).forEach(function(r){
          var x = ox + r.x * scale;
          var y = sheetY + r.y * scale;
          var w = r.w * scale;
          var h = r.h * scale;
          ctx.fillStyle = 'rgba(49,130,206,0.25)';
          ctx.fillRect(x, y, w, h);
          ctx.strokeStyle = '#2b6cb0';
          ctx.lineWidth = 1.5;
          ctx.strokeRect(x, y, w, h);
          if (w > 60 && h > 20) {
            ctx.fillStyle = '#1a202c';
            ctx.font = '14px sans-serif';
            ctx.fillText((r.name || '').slice(0, 20), x + 4, y + 4);
          }
        });
        oy += labelH + sheetH + gap;
      }
      if (sheets > show) {
        ctx.fillStyle = '#92400e';
        ctx.font = '16px sans-serif';
        ctx.fillText('... ещё ' + (sheets - show) + ' листов', 20, oy);
      }
      var dataUrl = canvas.toDataURL('image/png');
      return '<img src="' + dataUrl + '" style="width:100%;max-width:800px;display:block;margin:8px 0;border:1px solid #ddd">';
    } catch(e) {
      return '<div style="padding:10px;background:#fed7d7;color:#822727">Ошибка карты: ' + e.message + '</div>';
    }
  };
})(window);

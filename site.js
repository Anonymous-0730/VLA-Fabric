(() => {
  'use strict';

  function icon(name) {
    const definition = window.FABRIC_ICONS?.[name];
    if (!definition) return document.createTextNode('');
    function element([tag, attributes, children = []]) {
      const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
      Object.entries(attributes).forEach(([key, value]) => node.setAttribute(key, value));
      children.forEach(child => node.append(element(child)));
      return node;
    }
    const svg = element(definition);
    svg.classList.add('icon');
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('focusable', 'false');
    return svg;
  }
  document.querySelectorAll('[data-icon]').forEach(node => node.replaceWith(icon(node.dataset.icon)));

  // Tabs share keyboard behavior; content remains readable without JavaScript.
  function tabs(selector, activate) {
    const buttons = [...document.querySelectorAll(selector)];
    if (!buttons.length) return;
    function select(button, focus = false) {
      buttons.forEach(item => {
        item.setAttribute('aria-selected', String(item === button));
        item.tabIndex = item === button ? 0 : -1;
      });
      activate(button);
      if (focus) button.focus();
    }
    buttons.forEach((button, index) => {
      button.addEventListener('click', () => select(button));
      button.addEventListener('keydown', event => {
        let next;
        if (event.key === 'ArrowRight') next = (index + 1) % buttons.length;
        if (event.key === 'ArrowLeft') next = (index - 1 + buttons.length) % buttons.length;
        if (event.key === 'Home') next = 0;
        if (event.key === 'End') next = buttons.length - 1;
        if (next !== undefined) {
          event.preventDefault();
          select(buttons[next], true);
        }
      });
    });
    select(buttons.find(button => button.getAttribute('aria-selected') === 'true') || buttons[0]);
  }

  tabs('[data-demo]', button => {
    document.querySelectorAll('.demo-panel').forEach(panel => {
      panel.hidden = panel.id !== button.getAttribute('aria-controls');
      if (panel.hidden) panel.querySelector('video')?.pause();
    });
  });

  const dialog = document.getElementById('figure-dialog');
  if (dialog) {
    document.querySelectorAll('[data-figure]').forEach(button => {
      button.addEventListener('click', () => {
        const img = document.getElementById('dialog-image');
        img.src = button.dataset.figure;
        img.alt = button.querySelector('img').alt;
        dialog.showModal();
        document.documentElement.style.overflow = 'hidden';
      });
    });
    document.getElementById('figure-close').addEventListener('click', () => dialog.close());
    dialog.addEventListener('close', () => { document.documentElement.style.overflow = ''; });
    dialog.addEventListener('click', event => {
      const rect = dialog.getBoundingClientRect();
      if (event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) dialog.close();
    });
  }

  const results = window.FABRIC_RESULTS;
  if (results && document.getElementById('task-charts')) {
    const profiles = [['Raw', '#7a7a7a'], ['Full', '#4c78a8'], ['NSPR-8', '#e07a5f']];
    const tasks = [...new Set(results.cross_task.map(row => row.task))];
    const metrics = {
      traffic_mib: { title: 'Bidirectional traffic (MiB / planning round)', max: 350 },
      critical_mean_ms: { title: 'Communication critical-path mean (ms / planning round)', max: 700 },
      success_pct: { title: 'Task success (%)', max: 100 },
    };
    tabs('[data-metric]', button => {
      const key = button.dataset.metric;
      const metric = metrics[key];
      document.getElementById('chart-unit').textContent = metric.title;
      document.getElementById('cross-task-chart').setAttribute('aria-labelledby', button.id);
      const charts = document.getElementById('task-charts');
      charts.replaceChildren();
      tasks.forEach(task => {
        const rows = results.cross_task.filter(row => row.task === task);
        const group = document.createElement('div');
        group.className = 'task-chart';
        const plot = document.createElement('div');
        plot.className = 'plot';
        plot.setAttribute('role', 'img');
        plot.setAttribute('aria-label', `${task}, ${metric.title}: ${rows.map(row => `${row.profile} ${row[key]}`).join(', ')}`);
        for (const [className, value] of [['axis-top', metric.max], ['axis-bottom', 0]]) {
          const tick = document.createElement('span');
          tick.className = className;
          tick.textContent = value;
          tick.setAttribute('aria-hidden', 'true');
          plot.append(tick);
        }
        profiles.forEach(([name, color]) => {
          const row = rows.find(row => row.profile === name);
          const bar = document.createElement('div');
          bar.className = 'bar';
          bar.style.setProperty('--height', `${row[key] / metric.max * 100}%`);
          bar.style.setProperty('--color', color);
          bar.setAttribute('aria-hidden', 'true');
          const label = document.createElement('span');
          label.className = 'bar-label';
          label.textContent = row[key].toFixed(1);
          bar.append(label);
          plot.append(bar);
        });
        const heading = document.createElement('h4');
        heading.textContent = task;
        const count = document.createElement('span');
        count.textContent = `${rows[0].agents} agents`;
        heading.append(count);
        group.append(plot, heading);
        charts.append(group);
      });
    });
  }

  const canvas = document.getElementById('fabric-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  const toggle = document.getElementById('motion-toggle');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let paused = reduced.matches, visible = true, request = 0, elapsed = 0, previous = 0;
  let width = 0, height = 0, hover = -1;
  const colors = ['#4c78a8', '#698a69', '#e07a5f', '#4c78a8'];
  const edges = [[0, 1], [1, 2], [2, 3], [0, 2], [1, 3], [0, 3]];
  const nodes = () => [.14, .38, .62, .86].map(x => ({x: x * width, y: height * .5}));
  const curvePoint = (a, b, lift, t) => ({
    x: (1 - t) ** 3 * a.x + 3 * (1 - t) ** 2 * t * (a.x + (b.x - a.x) * .28) + 3 * (1 - t) * t * t * (b.x - (b.x - a.x) * .28) + t ** 3 * b.x,
    y: a.y + 3 * t * (1 - t) * lift,
  });
  function draw() {
    ctx.clearRect(0, 0, width, height);
    const points = nodes();
    const nodeWidth = width < 600 ? Math.min(62, width * .17) : 98;
    const nodeHeight = width < 600 ? 56 : 68;
    edges.forEach(([from, to], index) => {
      const a = points[from], b = points[to];
      const lift = (index % 2 ? 1 : -1) * height * (to - from === 3 ? .39 : .28);
      const active = hover < 0 || hover === from || hover === to;
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.bezierCurveTo(a.x + (b.x - a.x) * .28, a.y + lift, b.x - (b.x - a.x) * .28, b.y + lift, b.x, b.y);
      ctx.strokeStyle = active ? '#d1dbe4' : '#eef1f4';
      ctx.lineWidth = 1;
      ctx.stroke();
      for (let packet = 0; packet < 3; packet++) {
        const phase = (elapsed / 4500 + packet / 3 + index * .13) % 1;
        const t = index % 2 ? 1 - phase : phase;
        const p = curvePoint(a, b, lift, t);
        const size = width < 600 ? 4 : 5 + (packet % 2);
        ctx.fillStyle = active ? colors[(index + packet) % colors.length] : '#e7ecef';
        ctx.fillRect(p.x - size / 2, p.y - size / 2, size, size);
      }
    });
    points.forEach((point, index) => {
      ctx.fillStyle = '#ffffff';
      ctx.strokeStyle = hover === index ? colors[index] : '#bcc8d3';
      ctx.lineWidth = hover === index ? 1.6 : 1;
      ctx.beginPath();
      ctx.roundRect(point.x - nodeWidth / 2, point.y - nodeHeight / 2, nodeWidth, nodeHeight, 4);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = colors[index];
      ctx.fillRect(point.x - 11, point.y - nodeHeight / 2, 22, 2);
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.font = `${width < 600 ? 17 : 21}px Georgia, serif`;
      ctx.fillStyle = '#303e49';
      ctx.fillText('VLA', point.x, point.y - 9);
      ctx.font = `${width < 600 ? 10 : 12}px Arial, sans-serif`;
      ctx.fillStyle = '#697681';
      ctx.fillText(`Agent 0${index + 1}`, point.x, point.y + 14);
    });
  }
  function frame(time) {
    request = 0;
    if (previous) elapsed += Math.min(time - previous, 100);
    previous = time;
    draw();
    if (!paused && visible && !document.hidden) request = requestAnimationFrame(frame);
  }
  function schedule() {
    cancelAnimationFrame(request);
    request = 0;
    previous = 0;
    draw();
    if (!paused && visible && !document.hidden) request = requestAnimationFrame(frame);
  }
  function setPaused(value) {
    paused = value;
    toggle.setAttribute('aria-pressed', String(paused));
    toggle.setAttribute('aria-label', paused ? 'Play illustration' : 'Pause illustration');
    toggle.title = toggle.getAttribute('aria-label');
    toggle.replaceChildren(icon(paused ? 'play' : 'pause'));
    schedule();
  }
  new ResizeObserver(() => {
    const rect = canvas.getBoundingClientRect();
    width = rect.width; height = rect.height;
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    schedule();
  }).observe(canvas);
  new IntersectionObserver(entries => { visible = entries[0].isIntersecting; schedule(); }).observe(canvas);
  canvas.addEventListener('pointermove', event => {
    const rect = canvas.getBoundingClientRect();
    hover = nodes().findIndex(point => Math.abs(point.x - (event.clientX - rect.left)) < (width < 600 ? 34 : 52) && Math.abs(point.y - (event.clientY - rect.top)) < 35);
    if (paused) draw();
  });
  canvas.addEventListener('pointerleave', () => { hover = -1; if (paused) draw(); });
  document.addEventListener('visibilitychange', schedule);
  reduced.addEventListener('change', () => setPaused(reduced.matches));
  toggle.addEventListener('click', () => setPaused(!paused));
  toggle.hidden = false;
  setPaused(paused);
})();

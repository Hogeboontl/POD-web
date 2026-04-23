const form = document.getElementById('config-form');
const debounce = (func, wait) => {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
};

// function to send config updates
const updateConfig = (param, value) => {
  fetch('/update_config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ [param]: value })
  }).then(res => {
    if (!res.ok) console.error('Failed to update config');
  });
};

// attach change listeners, this is the lazy approach since the page has no other input or select options, might want to update to pass in correct IDS.
form.querySelectorAll('input').forEach(input => {
  input.addEventListener('blur', (e) => {
    updateConfig(e.target.name, e.target.value);
  });
});

form.querySelectorAll('select').forEach(input => {
  input.addEventListener('input', (e) => {
    updateConfig(e.target.name, e.target.value);
  });
});
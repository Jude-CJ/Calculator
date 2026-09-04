const display = document.querySelector('#display');
const result = document.querySelector('#result');
const hint = document.querySelector('#displayHint');
const count = document.querySelector('#displayCount');
const historyList = document.querySelector('#history');
const history = [];

function updateCount() {
    count.textContent = `${display.value.length} / 100`;
}

function addValue(value) {
    if (display.value.length >= 100) return;
    display.value += value;
    hint.textContent = 'Expression in progress';
    updateCount();
}

function renderHistory() {
    if (!history.length) {
        historyList.innerHTML = '<li class="empty-history">Your latest results will appear here.</li>';
        return;
    }
    historyList.innerHTML = history.map(item => `<li><span class="history-expression">${item.expression}</span><span class="history-result">= ${item.result}</span></li>`).join('');
}

async function calculate() {
    const expression = display.value.trim();
    if (!expression) return;
    hint.textContent = 'Calculating...';
    try {
        const response = await fetch('/api/calc', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ expression }) });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Calculation failed');
        result.textContent = data.result;
        hint.textContent = 'Result';
        history.unshift({ expression: data.expression, result: data.result });
        if (history.length > 6) history.pop();
        renderHistory();
    } catch (error) {
        result.textContent = 'Error';
        hint.textContent = error.message;
    }
}

document.querySelector('.keypad').addEventListener('click', event => {
    const button = event.target.closest('button');
    if (!button) return;
    if (button.dataset.value) addValue(button.dataset.value);
    if (button.dataset.action === 'clear') { display.value = ''; result.textContent = '0'; hint.textContent = 'Ready when you are'; updateCount(); }
    if (button.dataset.action === 'backspace') { display.value = display.value.slice(0, -1); updateCount(); }
    if (button.dataset.action === 'calculate') calculate();
});

display.addEventListener('input', () => { display.value = display.value.replace(/[^0-9+*/%(). -]/g, '').slice(0, 100); updateCount(); });
display.addEventListener('keydown', event => { if (event.key === 'Enter') calculate(); if (event.key === 'Escape') document.querySelector('[data-action="clear"]').click(); });
document.querySelector('#clearHistory').addEventListener('click', () => { history.length = 0; renderHistory(); });
updateCount();

const chat = document.getElementById('chat-form');
const field = document.getElementById('message');
const send = document.getElementById('send');
const conversation = document.getElementById('conversation');
const status = document.getElementById('request-status');
const debug = document.getElementById('debug-panel');
let busy = false;
function configureConversationLinks() {
  conversation.querySelectorAll('a[href]').forEach(link => {
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.title = 'Opens in a new tab';
  });
}
configureConversationLinks();
document.getElementById('debug-toggle').addEventListener('change', event => {
  debug.hidden = !event.target.checked;
});
document.getElementById('show-prompt').addEventListener('click', () => {
  document.getElementById('prompt-dialog').showModal();
});
document.getElementById('close-prompt').addEventListener('click', () => {
  document.getElementById('prompt-dialog').close();
});
function bubble(role, text) {
  const node = document.createElement('div');
  node.className = `bubble ${role}`;
  const label = document.createElement('span');
  label.className = 'role';
  label.textContent = role === 'user' ? 'You' : conversation.dataset.assistantName;
  node.append(label, document.createTextNode(text));
  conversation.append(node);
  conversation.scrollTop = conversation.scrollHeight;
  return node;
}
field.addEventListener('keydown', event => {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    if (!busy) chat.requestSubmit();
  }
});
document.addEventListener('click', event => {
  const example = event.target.closest('[data-message]');
  if (example && !busy) { field.value = example.dataset.message; field.focus(); }
});
document.addEventListener('submit', async event => {
  const form = event.target;
  if (!form.matches('#chat-form, #debug-panel form')) return;
  event.preventDefault();
  if (busy) return;
  const body = new FormData(form);
  body.set('provider', document.getElementById('provider').value);
  if (form === chat && !field.value.trim()) return;
  const submittedMessage = form === chat ? field.value : null;
  busy = true;
  send.disabled = true;
  const started = performance.now();
  if (submittedMessage) { bubble('user', submittedMessage); field.value = ''; }
  field.disabled = true;
  const typing = bubble('assistant', 'Answering…');
  typing.classList.add('typing');
  status.textContent = 'Assistant is answering…';
  const timer = setInterval(() => {
    status.textContent = `Assistant is answering… ${((performance.now() - started) / 1000).toFixed(1)}s`;
  }, 100);
  try {
    const response = await fetch(chat.action, {
      method: 'POST', body,
      headers: {'Accept': 'application/json', 'X-CSRFToken': body.get('csrfmiddlewaretoken')},
      credentials: 'same-origin'
    });
    if (response.redirected && response.url.includes('/accounts/login/')) {
      throw new Error('Your sign-in expired. Sign in again, then return to the chat.');
    }
    if (!response.headers.get('content-type')?.includes('application/json')) {
      throw new Error(`The website returned HTTP ${response.status} instead of a chat reply. Check the server terminal for the error.`);
    }
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `Request failed (HTTP ${response.status}).`);
    const page = new DOMParser().parseFromString(data.html, 'text/html');
    for (const selector of ['#conversation', '#confirmations', '#ticket-list', '#assistant-access', '#request-trace', '#action-audit']) {
      const target = document.querySelector(selector);
      const source = page.querySelector(selector);
      if (target && source) target.innerHTML = source.innerHTML;
    }
    configureConversationLinks();
    document.querySelectorAll('[name="form_token"]').forEach(input => { input.value = data.form_token; });
    document.getElementById('actual-prompts').textContent = data.prompts;
    document.getElementById('prompt-dialog-content').textContent = data.prompts;
    status.textContent = data.error ? 'Request failed. See the explanation in the conversation and Debug.' : `Reply received in ${((performance.now() - started) / 1000).toFixed(1)}s`;
    conversation.scrollTop = conversation.scrollHeight;
  } catch (error) {
    typing.remove();
    bubble('assistant', error.message + ' If you requested a change, check Your tickets before submitting it again.');
    status.textContent = 'Request failed.';
    if (submittedMessage) field.value = submittedMessage;
  } finally {
    clearInterval(timer);
    busy = false;
    send.disabled = false;
    field.disabled = false;
    field.focus();
  }
});
conversation.scrollTop = conversation.scrollHeight;

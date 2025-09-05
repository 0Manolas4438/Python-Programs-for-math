from flask import Flask, request, jsonify, render_template_string
import re
import sympy as sp

app = Flask(__name__)

TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Expression Simplifier — Chat</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
  <style>
    :root{--bg:#0b0f14;--panel:#0f1720;--muted:#9aa6b2;--accent:#7c5cff;--bubble:#0b1220;--user:#263240;--success:#1DB954;}
    *{box-sizing:border-box;font-family:Inter,system-ui,Segoe UI,Roboto,"Helvetica Neue",Arial;}
    html,body{height:100%;margin:0;background:
      radial-gradient(1200px 400px at 10% 10%, rgba(124,92,255,0.08), transparent),
      linear-gradient(180deg, rgba(255,255,255,0.01), rgba(0,0,0,0.02) 60%),var(--bg);color:#e6eef6;}
    .app{max-width:920px;margin:28px auto;padding:18px;border-radius:14px;background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));box-shadow:0 6px 30px rgba(2,6,23,0.7);border:1px solid rgba(255,255,255,0.03);overflow:hidden;}
    header{display:flex;align-items:center;gap:12px;padding:18px 18px 12px;}
    .logo{width:46px;height:46px;border-radius:10px;background:linear-gradient(135deg,var(--accent),#2ab7ff);display:flex;align-items:center;justify-content:center;font-weight:700;color:white;box-shadow:0 6px 18px rgba(124,92,255,0.12), inset 0 -6px 20px rgba(255,255,255,0.03);}
    h1{font-size:18px;margin:0;} p.lead{margin:0;color:var(--muted);font-size:13px;}
    .container{display:flex;gap:18px;padding:18px;}
    .left{flex:1;min-height:380px;background: linear-gradient(180deg, rgba(255,255,255,0.012), rgba(255,255,255,0.008));border-radius:10px;padding:18px;border:1px solid rgba(255,255,255,0.02);display:flex;flex-direction:column;}
    .messages{flex:1;overflow:auto;padding:6px;display:flex;flex-direction:column;gap:10px}
    .msg{max-width:85%;padding:12px 14px;border-radius:12px;line-height:1.45;font-size:14px;white-space:pre-wrap}
    .user{align-self:flex-end;background:linear-gradient(180deg,var(--user),#162433);color:#cfe8ff;border:1px solid rgba(255,255,255,0.02)}
    .bot{align-self:flex-start;background:linear-gradient(180deg,var(--bubble),#0e1722);color:#e8f1ff;border:1px solid rgba(255,255,255,0.02)}
    .bot .step-index{opacity:0.7;font-size:12px;margin-bottom:6px;color:var(--muted)}
    .final{border-left:4px solid var(--success);padding-left:10px}
    .meta{font-size:12px;color:var(--muted);padding:8px 0}
    .input-row{display:flex;gap:10px;margin-top:12px}
    input.equation{flex:1;padding:12px 14px;border-radius:10px;border:1px solid rgba(255,255,255,0.03);background:transparent;color:inherit;outline:none;font-size:14px}
    button.send{background:linear-gradient(90deg,var(--accent),#2ab7ff);border:0;padding:10px 14px;border-radius:10px;color:white;font-weight:600;box-shadow:0 8px 18px rgba(124,92,255,0.14);cursor:pointer}
    .hint{font-size:13px;color:var(--muted);margin-top:12px}
    footer{padding:10px 18px;color:var(--muted);font-size:13px;text-align:center}
    .fade-in{animation:fadeIn .28s ease;}
    @keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
    .small-btn{background:transparent;border:1px solid rgba(255,255,255,0.03);padding:6px 8px;border-radius:8px;color:var(--muted);cursor:pointer}
    .sample{display:inline-block;margin-left:8px;color:var(--accent);cursor:pointer}
  </style>
</head>
<body>
  <div class="app">
    <header>
      <div class="logo">∑</div>
      <div>
        <h1>Expression Simplifier — Chat</h1>
        <p class="lead">Type any math expression to simplify step by step. Example: <code>2*x + 3*x - 4 + 2</code></p>
      </div>
    </header>

    <div class="container">
      <div class="left">
        <div class="messages" id="messages" aria-live="polite"></div>
        <div class="meta">
          <span>Supports integers, fractions, variables, powers, parentheses.</span>
          <button class="small-btn sample" id="sample1">Try sample</button>
        </div>

        <div class="input-row">
          <input id="equation" class="equation" placeholder="e.g. 2*x + 3*x - 4 + 2" />
          <button class="send" id="send">Simplify</button>
        </div>
        <div class="hint">Tip: use * for multiplication and ^ for powers (optional, will convert to **).</div>
      </div>
    </div>

    <footer>Made with ❤️ — shows step-by-step simplification.</footer>
  </div>

<script>
const messages = document.getElementById('messages');
const input = document.getElementById('equation');
const sendBtn = document.getElementById('send');
const sampleBtn = document.getElementById('sample1');

function addMessage(text, who='bot', options={}) {
  const el = document.createElement('div');
  el.className = 'msg fade-in ' + (who==='user' ? 'user' : 'bot') + (options.final ? ' final' : '');
  if (options.index !== undefined) {
    el.innerHTML = '<div class="step-index">Step ' + (options.index+1) + '</div><div class="content">' + escapeHtml(text) + '</div>';
  } else {
    el.textContent = text;
  }
  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight;
  return el;
}

function escapeHtml(unsafe) {
    return unsafe.replace(/[&<>"']/g, function(m) { return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#039;"})[m]; });
}

function typeWriter(el, text, speed=18){ 
  return new Promise(resolve=>{
    el.innerHTML = '';
    const content = el.querySelector ? el.querySelector('.content') || el : el;
    let i = 0;
    function step(){
      if(i <= text.length){
        content.innerHTML = escapeHtml(text.slice(0,i));
        i++;
        messages.scrollTop = messages.scrollHeight;
        setTimeout(step, speed);
      } else {
        resolve();
      }
    }
    step();
  });
}

async function displaySteps(steps, final) {
  for (let i=0;i<steps.length;i++){
    const el = document.createElement('div');
    el.className = 'msg fade-in bot';
    el.innerHTML = '<div class="step-index">Step ' + (i+1) + '</div><div class="content"></div>';
    messages.appendChild(el);
    messages.scrollTop = messages.scrollHeight;
    await typeWriter(el, steps[i], 18);
    await new Promise(r=>setTimeout(r, 220));
  }
  const solEl = document.createElement('div');
  solEl.className = 'msg fade-in bot final';
  solEl.innerHTML = '<div class="step-index">Result</div><div class="content">' + escapeHtml(final) + '</div>';
  messages.appendChild(solEl);
  messages.scrollTop = messages.scrollHeight;
}

async function simplifyExpression(expr) {
  addMessage(expr, 'user');
  const thinking = addMessage('Working...', 'bot');
  sendBtn.disabled = true;
  input.disabled = true;
  try {
    const res = await fetch('/simplify', {
      method:'POST',headers:{'Content-Type':'application/json'},
      body: JSON.stringify({expression:expr})
    });
    const data = await res.json();
    thinking.remove();
    if(data.status==='ok'){
      await displaySteps(data.steps, data.result);
    } else {
      addMessage('Error: ' + (data.message || 'invalid input'), 'bot');
    }
  } catch(err) {
    thinking.remove();
    addMessage('Network or server error. Check console.', 'bot');
    console.error(err);
  } finally {
    sendBtn.disabled = false;
    input.disabled = false;
    input.focus();
  }
}

sendBtn.addEventListener('click', ()=> {
  const eq = input.value.trim();
  if (!eq) return;
  simplifyExpression(eq);
  input.value = '';
});

input.addEventListener('keydown', (e)=>{ if(e.key==='Enter') sendBtn.click(); });

sampleBtn.addEventListener('click', ()=>{
  input.value = '2*x + 3*x - 4 + 2';
  input.focus();
});
</script>
</body>
</html>
"""

# ------------------- Backend -------------------

def preprocess_expr(s: str) -> str:
    s = s.strip()
    s = s.replace('−', '-')
    s = s.replace('^', '**')
    s = re.sub(r'\s+', '', s)
    return s

@app.route("/")
def index():
    return render_template_string(TEMPLATE)

@app.route("/simplify", methods=["POST"])
def simplify():
    data = request.get_json(force=True)
    expr_str = (data.get("expression") or "").strip()
    if not expr_str:
        return jsonify(status="error", message="Empty expression"), 400
    expr_clean = preprocess_expr(expr_str)
    
    try:
        expr = sp.sympify(expr_clean)
    except Exception as e:
        return jsonify(status="error", message=f"Invalid expression ({str(e)})"), 400
    
    steps = []
    current = expr
    # Step 1: expand
    expanded = sp.expand(current)
    if expanded != current:
        steps.append(f"Expand: {expanded}")
        current = expanded
    # Step 2: simplify
    simplified = sp.simplify(current)
    if simplified != current:
        steps.append(f"Simplify: {simplified}")
        current = simplified
    # Step 3: factor if possible
    factored = sp.factor(current)
    if factored != current:
        steps.append(f"Factor: {factored}")
        current = factored
    
    return jsonify(status="ok", steps=[str(s) for s in steps], result=str(current))

if __name__ == "__main__":
    app.run(debug=True)

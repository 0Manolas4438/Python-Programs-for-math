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
  <title>Linear Equation Solver — Chat</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
  <style>
    :root{
      --bg:#0b0f14;
      --panel:#0f1720;
      --muted:#9aa6b2;
      --accent:#7c5cff;
      --bubble:#0b1220;
      --user:#263240;
      --success:#1DB954;
    }
    *{box-sizing:border-box;font-family:Inter,system-ui,Segoe UI,Roboto,"Helvetica Neue",Arial;}
    html,body{height:100%;margin:0;background:
      radial-gradient(1200px 400px at 10% 10%, rgba(124,92,255,0.08), transparent),
      linear-gradient(180deg, rgba(255,255,255,0.01), rgba(0,0,0,0.02) 60%),
      var(--bg); color:#e6eef6;}
    .app{
      max-width:920px;margin:28px auto;padding:18px;border-radius:14px;
      background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
      box-shadow: 0 6px 30px rgba(2,6,23,0.7); border: 1px solid rgba(255,255,255,0.03);
      overflow:hidden;
    }
    header{
      display:flex;align-items:center;gap:12px;padding:18px 18px 12px;
    }
    .logo{
      width:46px;height:46px;border-radius:10px;background:linear-gradient(135deg,var(--accent),#2ab7ff);
      display:flex;align-items:center;justify-content:center;font-weight:700;color:white;
      box-shadow: 0 6px 18px rgba(124,92,255,0.12), inset 0 -6px 20px rgba(255,255,255,0.03);
    }
    h1{font-size:18px;margin:0;}
    p.lead{margin:0;color:var(--muted);font-size:13px;}
    .container{display:flex;gap:18px;padding:18px;}
    .left{
      flex:1;min-height:380px;
      background: linear-gradient(180deg, rgba(255,255,255,0.012), rgba(255,255,255,0.008));
      border-radius:10px;padding:18px;border:1px solid rgba(255,255,255,0.02);
      display:flex;flex-direction:column;
    }
    .messages{flex:1;overflow:auto;padding:6px;display:flex;flex-direction:column;gap:10px}
    .msg{max-width:85%;padding:12px 14px;border-radius:12px;line-height:1.45;font-size:14px;white-space:pre-wrap}
    .user{align-self:flex-end;background:linear-gradient(180deg,var(--user),#162433);color:#cfe8ff;border:1px solid rgba(255,255,255,0.02)}
    .bot{align-self:flex-start;background:linear-gradient(180deg,var(--bubble),#0e1722);color:#e8f1ff;border:1px solid rgba(255,255,255,0.02)}
    .bot .step-index{opacity:0.7;font-size:12px;margin-bottom:6px;color:var(--muted)}
    .final{border-left:4px solid var(--success);padding-left:10px}
    .meta{font-size:12px;color:var(--muted);padding:8px 0}
    .input-row{display:flex;gap:10px;margin-top:12px}
    input.equation{flex:1;padding:12px 14px;border-radius:10px;border:1px solid rgba(255,255,255,0.03);
      background:transparent;color:inherit;outline:none;font-size:14px}
    button.send{background:linear-gradient(90deg,var(--accent),#2ab7ff);border:0;padding:10px 14px;border-radius:10px;color:white;font-weight:600;
      box-shadow: 0 8px 18px rgba(124,92,255,0.14);cursor:pointer}
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
      <div class="logo">Σ</div>
      <div>
        <h1>Linear Solver — chat</h1>
        <p class="lead">Type a single-variable linear equation (any letter as variable). Example: <code>9x+8762 = 283-8x</code></p>
      </div>
    </header>

    <div class="container">
      <div class="left">
        <div class="messages" id="messages" aria-live="polite"></div>

        <div class="meta">
          <span>Only linear equations with one unknown are supported (e.g. ax + b = cx + d). </span>
          <button class="small-btn sample" id="sample1">Try sample</button>
        </div>

        <div class="input-row">
          <input id="equation" class="equation" placeholder="e.g. 9x+8762 = 283-8x" />
          <button class="send" id="send">Solve</button>
        </div>
        <div class="hint">Tip: you can use any letter for the variable (x, y, z...). Use ^ for powers (but solver expects linear equations).</div>
      </div>

    </div>

    <footer>Made with ❤️ — shows step-by-step algebra; supports fractions and integers.</footer>
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
    // minimal escaping so we can safely show plain text
    return unsafe.replace(/[&<>"']/g, function(m) { return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#039;"})[m]; });
}

// typewriter effect for a message element (plain text)
function typeWriter(el, text, speed=18){ 
  return new Promise(resolve=>{
    el.innerHTML = ''; // we'll type into .content if present
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
  // show each step with typing
  for (let i=0;i<steps.length;i++){
    let s = steps[i];
    // create message element
    const el = document.createElement('div');
    el.className = 'msg fade-in bot';
    el.innerHTML = '<div class="step-index">Step ' + (i+1) + '</div><div class="content"></div>';
    messages.appendChild(el);
    messages.scrollTop = messages.scrollHeight;
    await typeWriter(el, s, 18);
    await new Promise(r=>setTimeout(r, 220)); // tiny pause between steps
  }
  // final solution bubble
  const solEl = document.createElement('div');
  solEl.className = 'msg fade-in bot final';
  solEl.innerHTML = '<div class="step-index">Solution</div><div class="content">' + escapeHtml(final) + '</div>';
  messages.appendChild(solEl);
  messages.scrollTop = messages.scrollHeight;
}

async function solve(equation) {
  // show user's message
  addMessage(equation, 'user');
  // show placeholder bot message (thinking)
  const thinking = addMessage('Working...', 'bot');
  sendBtn.disabled = true;
  input.disabled = true;
  try {
    const res = await fetch('/solve', {
      method:'POST',headers:{'Content-Type':'application/json'},
      body: JSON.stringify({equation})
    });
    const data = await res.json();
    thinking.remove();
    if (data.status === 'ok') {
      await displaySteps(data.steps, data.solution);
    } else {
      addMessage('Error: ' + (data.message || 'invalid input'), 'bot');
    }
  } catch (err) {
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
  solve(eq);
  input.value = '';
});

input.addEventListener('keydown', (e)=>{
  if (e.key === 'Enter') {
    sendBtn.click();
  }
});

sampleBtn.addEventListener('click', ()=>{
  input.value = '9x+8762 = 283-8x';
  input.focus();
});
</script>

</body>
</html>
"""

# -------------------
# Backend: parsing & solving
# -------------------

def preprocess_side(s: str) -> str:
    if s is None:
        return s
    s = s.strip()
    # unify minus, caret
    s = s.replace('−', '-')
    s = s.replace('^', '**')
    # remove spaces around operators for easier parsing
    # insert * between number and letter (e.g., 9x -> 9*x)
    s = re.sub(r'(\d)(\s*)(?=[A-Za-z])', r'\1*', s)
    # insert * between a letter/number/closing paren and an opening paren (2(x+1) -> 2*(x+1), x(x+1) -> x*(x+1))
    s = re.sub(r'([A-Za-z0-9\)])\s*\(', r'\1*(', s)
    # insert * between closing paren and variable/number: (x+1)2 -> (x+1)*2, (x+1)x -> (x+1)*x
    s = re.sub(r'\)\s*([A-Za-z0-9])', r')*\1', s)
    # collapse whitespace
    s = re.sub(r'\s+', '', s)
    return s

@app.route("/")
def index():
    return render_template_string(TEMPLATE)

@app.route("/solve", methods=["POST"])
def solve():
    data = request.get_json(force=True)
    eq = (data.get("equation") or "").strip()
    if not eq:
        return jsonify(status="error", message="Empty equation."), 400

    # must have exactly one '='
    if eq.count('=') != 1:
        return jsonify(status="error", message="Please provide a single '=' separating left and right sides."), 400

    left_str, right_str = eq.split('=', 1)

    # try to identify a variable letter from the raw input (first alphabetic character)
    m = re.search(r'[A-Za-z]', eq)
    user_var_hint = m.group(0) if m else None

    lhs_s = preprocess_side(left_str)
    rhs_s = preprocess_side(right_str)

    try:
        lhs = sp.sympify(lhs_s)
        rhs = sp.sympify(rhs_s)
    except Exception as e:
        return jsonify(status="error", message=f"Could not parse expression. Try simpler input. ({str(e)})"), 400

    syms = list(lhs.free_symbols.union(rhs.free_symbols))

    if len(syms) == 0:
        return jsonify(status="error", message="No variable detected. Use a single letter variable (e.g. x)."), 400

    # choose variable: prefer the user first-letter if present
    var = None
    if user_var_hint:
        for s in syms:
            if s.name == user_var_hint:
                var = s
                break
    if var is None:
        # fallback: pick the single symbol if only one, else pick first (but will error later if more than one)
        var = syms[0]

    if len(syms) > 1:
        names = ', '.join([str(s) for s in syms])
        return jsonify(status="error", message=f"Multiple variables detected ({names}). This solver supports one unknown."), 400

    # expand to collect terms
    expr_l = sp.expand(lhs)
    expr_r = sp.expand(rhs)

    # check degree (we only support linear)
    deg = sp.degree(sp.expand(expr_l - expr_r), var)
    if deg is None:
        deg = 0
    if deg > 1:
        return jsonify(status="error", message="Non-linear equation detected (degree > 1). This solver supports linear equations only."), 400

    # coefficients
    left_coeff = sp.expand(expr_l).coeff(var, 1)
    right_coeff = sp.expand(expr_r).coeff(var, 1)
    left_const = sp.expand(expr_l).subs(var, 0)
    right_const = sp.expand(expr_r).subs(var, 0)

    # Steps description (plain-text friendly)
    steps = []

    # Step 1: show original (pretty)
    steps.append(f"Original equation: {sp.srepr(lhs)}  =  {sp.srepr(rhs)}")
    # but give prettier human readable:
    steps.append(f"Rewrite clearly: {sp.expand(lhs)} = {sp.expand(rhs)}")

    # Step 2: collect variable terms to left
    steps.append(f"Collect variable terms on left: subtract ({right_coeff})*{var} from both sides.")
    new_coeff = sp.simplify(left_coeff - right_coeff)
    steps.append(f"Combine like terms: ({left_coeff})*{var} - ({right_coeff})*{var} = ({new_coeff})*{var}")
    # equation now: new_coeff*var + left_const = right_const
    steps.append(f"After moving variable terms: ({new_coeff})*{var} + ({left_const}) = ({right_const})")

    # Step 3: move constants to right
    steps.append(f"Move constants to right: subtract ({left_const}) from both sides.")
    rhs_after = sp.simplify(right_const - left_const)
    steps.append(f"Result: ({new_coeff})*{var} = ({rhs_after})")

    # Solve for variable
    if sp.simplify(new_coeff) == 0:
        # either infinite solutions or no solution
        if sp.simplify(rhs_after) == 0:
            return jsonify(status="error", message="Infinite solutions (identity). Every value of the variable satisfies the equation."), 200
        else:
            return jsonify(status="error", message="No solution (contradiction). The equation is inconsistent."), 200

    solution_expr = sp.simplify(sp.Rational(1,1) * rhs_after / new_coeff)
    solution_pretty = f"{var} = {solution_expr}"

    # final arithmetic step
    steps.append(f"Divide both sides by ({new_coeff}): {var} = ({rhs_after}) / ({new_coeff})")
    steps.append(f"Simplify: {solution_pretty}")

    # Convert steps to plain strings (avoid weird internal sympy repr in client)
    steps_clean = [str(s) for s in steps]

    return jsonify(status="ok", steps=steps_clean, solution=str(solution_pretty))

if __name__ == "__main__":
    app.run(debug=True)

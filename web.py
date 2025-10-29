import json
import os
import time
from flask import Flask, render_template_string, abort, request, url_for


app = Flask(__name__)


def load_last_json():
    last_path = os.path.join(os.path.dirname(__file__), 'last.json')
    if not os.path.exists(last_path):
        abort(404, description='last.json not found')
    with open(last_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_ts(ts):
    try:
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(ts)))
    except Exception:
        return '-'


@app.route('/')
def index():
    data = load_last_json()
    # Expect data['positions'] to be a list of model snapshots
    models = data.get('positions', [])
    
    # Calculate unrealized and total PnL for each model
    for m in models:
        realized_pnl = m.get('realized_pnl', 0.0) or 0.0
        unrealized_pnl = 0.0
        positions = m.get('positions', {})
        for pos in positions.values():
            unrealized_pnl += (pos.get('unrealized_pnl', 0.0) or 0.0)
        m['unrealized_pnl'] = unrealized_pnl
        m['total_pnl'] = realized_pnl + unrealized_pnl
    
    # Sort by realized_pnl descending
    models = sorted(models, key=lambda m: (m.get('realized_pnl') or 0.0), reverse=True)

    # Extract a sorted list of all symbols observed across models for header consistency
    all_symbols = set()
    for m in models:
        for sym in (m.get('positions') or {}).keys():
            all_symbols.add(sym)
    sorted_symbols = sorted(all_symbols)

    # i18n strings
    lang = request.args.get('lang', 'zh')
    is_en = (lang == 'en')
    t = {
        'title': 'Alpha Arena 持仓监控' if not is_en else 'Alpha Arena Positions Monitor',
        'data_time': '数据时间' if not is_en else 'Data Time',
        'auto_refresh': '自动每15秒刷新' if not is_en else 'Auto refresh every 15s',
        'delay': '提示：与官网数据存在约1分钟延时' if not is_en else 'Note: ~1 minute delay vs. official site',
        'model': '模型' if not is_en else 'Model',
        'rpnl': '已实现盈亏' if not is_en else 'Realized PnL',
        'urpnl': '未实现盈亏' if not is_en else 'Unrealized PnL',
        'tpnl': '总盈亏' if not is_en else 'Total PnL',
        'pair': '合约对' if not is_en else 'Pair',
        'qty': '数量' if not is_en else 'Qty',
        'lev': '杠杆' if not is_en else 'Lev',
        'entry': '开仓价' if not is_en else 'Entry',
        'price': '当前价' if not is_en else 'Price',
        'margin': '保证金' if not is_en else 'Margin',
        'upnl': '浮动盈亏' if not is_en else 'U-PnL',
        'cpnl': '平仓盈亏' if not is_en else 'C-PnL',
        'tp': '止盈' if not is_en else 'TP',
        'sl': '止损' if not is_en else 'SL',
        'entry_time': '进入时间' if not is_en else 'Entry Time',
        'file': '文件' if not is_en else 'File',
        'size': '大小' if not is_en else 'Size',
        'toggle': 'English' if not is_en else '中文',
        'contact': '联系方式' if not is_en else 'Contact',
        'nof1': 'nof1.ai' if not is_en else 'nof1.ai',
        'wechat_mp': '公众号:远见拾贝' if not is_en else 'WeChat MP',
        'x': 'X' if is_en else 'X',
        'github': 'Github' if not is_en else 'GitHub',
        'site': '网站' if not is_en else 'Site',
        'disclaimer': '声明：本网站仅供学习和研究使用，不构成投资建议。所有交易决策由用户自行承担风险。作者对任何投资损失不承担责任。如果您发现本网站内容侵犯了您的权益，请联系我们立即处理。' if not is_en else 'Disclaimer: This website is for learning and research only, and does not constitute investment advice. All trading decisions are at your own risk. The author is not responsible for any investment losses. If you find any infringement, please contact us immediately.',
    }

    # HTML template with auto refresh every 15 seconds
    template = r"""
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>持仓监控</title>
  <meta http-equiv="refresh" content="15">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 20px; }
    h1 { font-size: 20px; margin: 0 0 16px; }
    .meta { color: #666; font-size: 12px; margin-bottom: 16px; }
    table { border-collapse: collapse; width: 100%; margin-bottom: 28px; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: right; }
    th { background: #f7f7f7; position: sticky; top: 0; }
    td.sym, th.sym { text-align: left; }
    .pos { color: #111; }
    .neg { color: #b00020; }
    .zero { color: #666; }
    .model { font-size: 16px; margin: 24px 0 8px; }
    .topbar { position: fixed; right: 20px; top: 12px; font-size: 12px; color: #555; }
    .topbar a { color: #0a58ca; text-decoration: none; margin-left: 10px; }
    .spacer { height: 28px; }
  </style>
  <script>
    // In case meta refresh is blocked, fallback to JS reload
    setTimeout(function(){ window.location.reload(); }, 15000);
  </script>
  </head>
<body>
  <div class="topbar">
    {{ t['contact'] }}:
    <a href="https://nof1.ai" target="_blank" rel="noopener">{{ t['nof1'] }}</a>
    <a href="https://www.insightpearl.com/" target="_blank" rel="noopener">{{ t['site'] }}</a>
    <a href="https://x.com/okay456okay" target="_blank" rel="noopener">{{ t['x'] }}</a>
    <a href="https://github.com/okay456okay/nof1.ai.monitor" target="_blank" rel="noopener">{{ t['github'] }}</a>
    <a href="https://www.insightpearl.com/" target="_blank" rel="noopener">{{ t['wechat_mp'] }}</a>
    | <a href="{{ url_for('index', lang='en' if not is_en else 'zh') }}">{{ t['toggle'] }}</a>
  </div>
  <div class="spacer"></div>
  <h1>{{ t['title'] }}</h1>
  <div class="meta">
    {{ t['data_time'] }}：{{ data.get('fetch_time') or data.get('timestamp') }} &nbsp;|&nbsp; {{ t['auto_refresh'] }} &nbsp;|&nbsp; {{ t['delay'] }}
  </div>

  {% for m in models %}
    <div class="model">{{ t['model'] }}：<strong><a href="https://nof1.ai/models/{{ m.get('id') }}" target="_blank" rel="noopener">{{ m.get('id') }}</a></strong> &nbsp; {{ t['rpnl'] }}：{{ '%.2f' % (m.get('realized_pnl', 0.0) or 0.0) }}，{{ t['urpnl'] }}：{{ '%.2f' % (m.get('unrealized_pnl', 0.0) or 0.0) }}，{{ t['tpnl'] }}：{{ '%.2f' % (m.get('total_pnl', 0.0) or 0.0) }}</div>
    <table>
      <thead>
        <tr>
          <th class="sym">{{ t['pair'] }}</th>
          <th>{{ t['qty'] }}</th>
          <th>{{ t['lev'] }}</th>
          <th>{{ t['entry'] }}</th>
          <th>{{ t['price'] }}</th>
          <th>{{ t['margin'] }}</th>
          <th>{{ t['upnl'] }}</th>
          <th>{{ t['cpnl'] }}</th>
          <th>{{ t['tp'] }}</th>
          <th>{{ t['sl'] }}</th>
          <th>{{ t['entry_time'] }}</th>
        </tr>
      </thead>
      <tbody>
        {% set pos_map = m.get('positions') or {} %}
        {% for sym in sorted_symbols %}
          {% set p = pos_map.get(sym) %}
          {% if p %}
            {% set upnl = p.get('unrealized_pnl', 0.0) or 0.0 %}
            {% set cpnl = p.get('closed_pnl', 0.0) or 0.0 %}
            <tr>
              <td class="sym">{{ sym }}</td>
              <td>{{ p.get('quantity') }}</td>
              <td>{{ p.get('leverage') }}</td>
              <td>{{ '%.6g' % (p.get('entry_price') or 0) }}</td>
              <td>{{ '%.6g' % (p.get('current_price') or 0) }}</td>
              <td>{{ '%.2f' % (p.get('margin', 0.0) or 0.0) }}</td>
              <td class="{{ 'pos' if upnl>0 else ('neg' if upnl<0 else 'zero') }}">{{ '%.2f' % upnl }}</td>
              <td class="{{ 'pos' if cpnl>0 else ('neg' if cpnl<0 else 'zero') }}">{{ '%.2f' % cpnl }}</td>
              <td>{% if p.get('exit_plan') %}{{ p['exit_plan'].get('profit_target') }}{% endif %}</td>
              <td>{% if p.get('exit_plan') %}{{ p['exit_plan'].get('stop_loss') }}{% endif %}</td>
              <td>{% set et = p.get('entry_time') %}{{ format_ts(et) if et else '-' }}</td>
            </tr>
          {% else %}
            <tr>
              <td class="sym">{{ sym }}</td>
              <td colspan="11" style="text-align:center;color:#999">—</td>
            </tr>
          {% endif %}
        {% endfor %}
      </tbody>
    </table>
  {% endfor %}

  <div class="meta">{{ t['file'] }}：last.json &nbsp; {{ t['size'] }}：{{ (json_str|length) }} {{ 'bytes' if is_en else '字节' }}</div>

  <div style="margin-top: 40px; padding: 20px; background: #f9f9f9; border-radius: 4px; font-size: 12px; line-height: 1.8; color: #666;">
    {{ t['disclaimer'] }}
  </div>
</body>
</html>
"""

    json_str = json.dumps(data, ensure_ascii=False)
    return render_template_string(
        template,
        data=data,
        models=models,
        sorted_symbols=sorted_symbols,
        json_str=json_str,
        format_ts=format_ts,
        t=t,
        is_en=is_en,
    )


if __name__ == '__main__':
    # Allow host binding via env var if needed
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '5010'))
    debug = os.getenv('FLASK_DEBUG', '0') == '1'
    app.run(host=host, port=port, debug=debug)



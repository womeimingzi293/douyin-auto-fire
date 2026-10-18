from flask import Flask, jsonify, request, send_from_directory
import json
import os
import sys
import subprocess
from datetime import datetime

# 获取资源路径（兼容PyInstaller打包）
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)

# 获取项目根目录（exe所在目录的上级）
if getattr(sys, 'frozen', False):
    # 打包后exe在web目录下，项目根目录是exe所在目录的上级
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(sys.executable)))
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, static_folder='static')

CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')
LOG_PATH = os.path.join(BASE_DIR, 'artifacts', 'daily-run.log')

# 全局运行状态
run_status = {
    'running': False,
    'last_run': None,
    'last_result': None
}

@app.route('/')
def index():
    if getattr(sys, 'frozen', False):
        return send_from_directory(sys._MEIPASS, 'index.html')
    return send_from_directory('.', 'index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return jsonify({'code': 0, 'data': config})
    except Exception as e:
        return jsonify({'code': 1, 'msg': str(e)})

@app.route('/api/config', methods=['POST'])
def save_config():
    try:
        new_config = request.json
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(new_config, f, ensure_ascii=False, indent=2)
        return jsonify({'code': 0, 'msg': '保存成功'})
    except Exception as e:
        return jsonify({'code': 1, 'msg': str(e)})

@app.route('/api/run', methods=['POST'])
def run_now():
    global run_status
    if run_status['running']:
        return jsonify({'code': 1, 'msg': '任务正在运行中，请稍候'})
    
    try:
        run_status['running'] = True
        run_status['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 在后台运行
        def run_task():
            global run_status
            try:
                result = subprocess.run(
                    ['python', 'run.py'],
                    cwd=BASE_DIR,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                run_status['last_result'] = {
                    'success': result.returncode == 0,
                    'output': result.stdout + result.stderr,
                    'end_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            except Exception as e:
                run_status['last_result'] = {
                    'success': False,
                    'output': str(e),
                    'end_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            finally:
                run_status['running'] = False
        
        import threading
        threading.Thread(target=run_task, daemon=True).start()
        
        return jsonify({'code': 0, 'msg': '任务已启动'})
    except Exception as e:
        run_status['running'] = False
        return jsonify({'code': 1, 'msg': str(e)})

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({'code': 0, 'data': run_status})

@app.route('/api/logs', methods=['GET'])
def get_logs():
    try:
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, 'r', encoding='utf-8') as f:
                # 只取最后500行
                lines = f.readlines()[-500:]
                logs = ''.join(lines)
        else:
            logs = '暂无日志'
        return jsonify({'code': 0, 'data': logs})
    except Exception as e:
        return jsonify({'code': 1, 'msg': str(e)})

@app.route('/api/scheduled-task', methods=['GET'])
def get_scheduled_task():
    try:
        result = subprocess.run(
            ['schtasks', '/query', '/tn', '抖音自动续火花', '/fo', 'list'],
            capture_output=True,
            text=True
        )
        return jsonify({'code': 0, 'data': result.stdout})
    except Exception as e:
        return jsonify({'code': 1, 'msg': str(e)})

if __name__ == '__main__':
    print('='*50)
    print('抖音自动续火花 - 管理后台')
    print('访问地址: http://127.0.0.1:5000')
    print('按 Ctrl+C 停止服务')
    print('='*50)
    app.run(host='127.0.0.1', port=5000, debug=False)

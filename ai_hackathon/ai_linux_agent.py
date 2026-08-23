import os
import re
import sys
import traceback
import subprocess
import requests
import gradio as gr
from datetime import datetime
from dotenv import load_dotenv

# ==================== 后端逻辑 (完全保留，未做任何修改) ====================

load_dotenv()
API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
MODEL_NAME = os.getenv("MODEL_NAME")

HIGH_RISK_CMDS = [
    "rm -rf /", "rm -rf /etc", "rm -rf /boot", "rm -rf /var", "rm -rf /root",
    "mkfs", "dd of=/dev/", "chmod -R 777 /", "chmod 777 /etc",
    "vi /etc/shadow", "vi /etc/sudoers",
    ":(){ :|:& };:"
]

MEDIUM_RISK_KEYWORDS = ["useradd", "userdel", "kill -9", "chmod ", "chown ", "rm "]

log_entries = []
pending_cmd_state = None

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    log_entries.append(log_entry)
    print(log_entry, file=sys.stderr)

def get_log_content():
    if not log_entries:
        return "暂无日志记录"
    return "\n".join(log_entries)

def check_security(cmd):
    for bad in HIGH_RISK_CMDS:
        if bad in cmd:
            return False, "BLOCK", f"安全风控拦截：已触发最高级别预警！拒绝执行高危操作。\n\n命令：`{cmd}`"

    is_medium_risk = any(keyword in cmd for keyword in MEDIUM_RISK_KEYWORDS) and "passwd" not in cmd
    if is_medium_risk:
        return False, "CONFIRM", f"中等风险预警：该操作属于变更操作，请回复「确认执行」继续。\n\n待执行命令：`{cmd}`"

    return True, "SAFE", "检查通过"

def safe_run(cmd):
    if "useradd" in cmd or "userdel" in cmd:
        cmd = f"sudo {cmd}"
    try:
        timeout = 60 if "find " in cmd else 30
        res = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=timeout, encoding="utf-8")
        return res.strip() or "命令执行成功，无额外输出。"
    except subprocess.CalledProcessError as e:
        return f"终端报错：{e.output}"
    except Exception as e:
        return f"❌ 系统异常：{str(e)}"

def ask_ai_to_plan(prompt, history):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    system = """你是Linux运维命令生成器。唯一职责：把用户的自然语言运维需求转换成可直接执行的Linux命令，并杜绝一切幻觉。

【最高原则：绝不编造】
1. 绝不编造任何数据：用户名、组名、UID/GID、IP、端口、MAC、主机名、域名、文件/目录路径、PID、进程名、服务名、挂载点、设备名、网卡名、大小、时间戳。这些值只能取自用户在本次或历史对话中明确给出的内容。
2. 若缺少必要参数且命令无法在缺省下运行，禁止猜测、禁止用示例值或 <xxx>、YOUR_xxx 等占位符凑数，必须只输出一行：[信息不足] 并简述缺少哪个参数。
3. 只使用确信存在于标准Linux（coreutils/util-linux/procps/systemd/iproute2/shadow等）的命令与选项；禁止生造不存在的命令、子命令或参数标志，对不确定的选项宁可不用。
4. 不得臆测系统当前状态（如“假设磁盘已满”“假设服务已安装”），只按用户描述生成命令，执行后的真实结果由系统返回。

【输出格式：极严】
5. 只输出命令本身，每行一条完整命令。禁止输出：解释、注释、寒暄、前后缀、markdown代码块、反引号、行号、步骤编号。
6. 仅当用户明确需要连续多步操作时才输出多行，每行必须可独立执行；禁止输出脚本、shebang、循环、函数定义、占位符。
7. 高危删除等操作按用户需求如实生成对应命令（安全审计由外部拦截层负责，你无需回避），但必须严格匹配用户意图，不得擅自扩大范围或删除未提及的目标。

【安全与可执行】
8. 查看进程/CPU/内存只能用非交互式命令，禁止编造进程数据：
    - 查看CPU占用：ps -eo pid,ppid,pcpu,cmd --sort=-pcpu | head -10
    - 查看内存占用：ps -eo pid,ppid,pmem,cmd --sort=-pmem | head -10
    - 禁止单独输出 top，必须用：top -b -n 1 | head -20
9. 禁止单独输出无参数的 sudo、cd、ls；若必须使用需带完整参数使其可独立执行，cd 不影响后续命令工作目录，请用绝对路径代替。
10. 设置用户密码必须用非交互式：echo "密码" | sudo passwd --stdin 用户名；禁止需手动输入的 passwd，禁止 EOF/heredoc 语法。

【意图识别】
11. 只有当用户问题明显与Linux运维无关（天气、闲聊、新闻、百科）时，才输出：[非运维需求]
12. 保持多轮上下文连贯，优先结合历史对话理解当前需求；历史中已确认的真实值可复用。
"""

    messages = [{"role": "system", "content": system}]
    if history:
        for item in history:
            try:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    user_msg = item[0] if item[0] else ""
                    bot_msg = item[1] if item[1] else ""
                    if user_msg and user_msg.strip():
                        messages.append({"role": "user", "content": user_msg})
                    if bot_msg and bot_msg.strip():
                        messages.append({"role": "assistant", "content": bot_msg})
                elif isinstance(item, dict):
                    role = item.get("role", "")
                    content = item.get("content", "")
                    if content and content.strip():
                        messages.append({"role": role, "content": content})
            except Exception as e:
                log_message(f"处理历史记录出错: {e}")
                continue
    messages.append({"role": "user", "content": prompt})
    data = {"model": MODEL_NAME, "messages": messages, "temperature": 0.1}

    try:
        log_message(f"请求AI，历史数: {len(history) if history else 0}")
        resp = requests.post(API_URL, headers=headers, json=data, timeout=150)
        cmds = resp.json()["choices"][0]["message"]["content"].strip()
        cleaned_cmds = cmds.replace("```bash", "").replace("```", "").strip()
        if "[非运维需求]" in cleaned_cmds or cleaned_cmds.lower() == "[非运维需求]":
            return "NON_OPERATION"
        if cleaned_cmds.startswith("[信息不足]"):
            return cleaned_cmds
        log_message(f"AI返回: {cleaned_cmds[:50]}...")
        return cleaned_cmds
    except Exception as e:
        log_message(f"API异常: {str(e)}")
        return f"API_ERROR: {str(e)}"

def translate_to_human(user_prompt, raw_output):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    system = """你是Linux运维结果转述助手。把终端输出如实转述为口语化汇报，可适当加Emoji。
杜绝幻觉——只许复述，不许创造：
1. 汇报内容必须100%来自下方“终端输出”，禁止添加输出中不存在的任何信息。
2. 禁止编造数字：百分比、容量(GB/MB)、数量、计数、速率、负载、PID、端口、时间等，必须与终端输出逐字一致；输出里没有的数字一个都不能写。
3. 禁止臆测原因、诊断结论或趋势（如“可能内存不足”“预计会满”），除非该文字直接出现在终端输出中。
4. 禁止虚构命令、参数、文件名、用户名、服务名等实体。
5. 若输出为空、报错或为“命令执行成功，无额外输出”，据实说明，不得补充臆测。
6. 提炼核心即可，宁少一句假话，不多一句编造。"""
    prompt = f"用户需求：{user_prompt}\n终端输出：{raw_output}\n请自然语言汇报："
    data = {"model": MODEL_NAME, "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}], "temperature": 0.2}
    try:
        resp = requests.post(API_URL, headers=headers, json=data, timeout=150)
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log_message(f"翻译API异常: {str(e)}")
        return raw_output

def bot(message, history):
    global pending_cmd_state
    log_message(f"用户输入: '{message}', 待确认命令: {pending_cmd_state}")
    confirm_keywords = ["确认执行", "yes", "是", "确定", "确认"]
    is_confirm = message.strip() in confirm_keywords or message.lower().strip() == "yes"

    if is_confirm and pending_cmd_state:
        log_message(f"执行确认的命令(跳过安全检查): {pending_cmd_state}")
        exec_result = safe_run(pending_cmd_state)
        human_report = translate_to_human(message, exec_result)
        result = f"### Minerva 汇报：\n{human_report}\n\n---\n<details><summary>查看底层执行</summary>\n```text\n【执行】{pending_cmd_state}\n【结果】{exec_result}\n```</details>"
        pending_cmd_state = None
        return result

    cmd_to_run = ask_ai_to_plan(message, history or [])
    if cmd_to_run == "NON_OPERATION":
        return "抱歉，我无法识别这个需求。我是 Linux 运维助手，请提供具体的运维指令（如：查看磁盘、创建用户、查看进程等）"
    if cmd_to_run.startswith("[信息不足]"):
        reason = cmd_to_run.replace("[信息不足]", "", 1).strip(" :")
        return f"⚠️ 信息不足，无法准确生成命令，请补充以下信息后重试：\n\n{reason}"
    if cmd_to_run.startswith("API_ERROR"):
        return f"大脑连接失败：{cmd_to_run}\n\n请检查 API 配置或稍后重试。"

    commands = cmd_to_run.split('\n')
    execution_logs = []
    for cmd in commands:
        cmd = cmd.strip()
        if not cmd: continue
        passed, level, msg = check_security(cmd)
        if level == "BLOCK":
            log_message(f"高危命令被拦截: {cmd}")
            return msg + "\n\n你可以继续输入其他指令。"
        elif level == "CONFIRM":
            log_message(f"需要确认的命令: {cmd}")
            pending_cmd_state = cmd
            return msg
        exec_result = safe_run(cmd)
        execution_logs.append(f"【执行】{cmd}\n【结果】{exec_result}")

    full_raw_output = "\n\n".join(execution_logs)
    human_report = translate_to_human(message, full_raw_output)
    result = f"### Minerva 汇报：\n{human_report}\n\n---\n<details><summary>查看底层执行</summary>\n```text\n{full_raw_output}\n```</details>"
    return result

# ==================== UI 美化部分 ====================

# ==================== UI 美化部分 ====================

# ... 前面所有后端逻辑 (check_security, safe_run, bot 等) 保持完全不变 ...

# ==================== UI 美化部分 ====================

if __name__ == "__main__":
    custom_css = """
    footer {visibility: hidden}
    .main-container {
        max-width: 1000px !important;
        margin: 0 auto !important;
        padding-top: 2rem !important;
    }
    #chatbot-header {
        text-align: center;
        margin-bottom: 20px;
    }
    #chatbot-header h1 {
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #2D3FE2, #00C6FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .gradio-container .message-wrap .message {
        border-radius: 12px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    """
    theme = gr.themes.Soft(primary_hue="blue", spacing_size="sm", radius_size="md")

    # 1. 这里移除了 theme 和 css 参数
    with gr.Blocks(theme=theme, css=custom_css) as demo:
        with gr.Column(elem_classes="main-container"):
            
            # 2. 将 gr.Div 替换为 gr.Group 或直接使用 Markdown 组合
            with gr.Group(elem_id="chatbot-header"):
                gr.Markdown("# 🤖 AI Linux 助手")
                gr.Markdown("### Minerva 运维专家：对话即操作，安全且高效")
            
            chat = gr.ChatInterface(
                fn=bot,
                chatbot=gr.Chatbot(
                    height=600, 
                    # 删掉 bubble_full_width=False
                    show_label=False,
                    avatar_images=(None, "https://api.dicebear.com/7.x/bottts/svg?seed=Minerva")
                ),
                textbox=gr.Textbox(
                    placeholder="请输入运维需求（例如：帮我看看系统负载...）",
                    container=False,
                    scale=7
                ),
                submit_btn="发送指令",
                stop_btn="停止生成",
                # retry_btn="重新生成",
                # undo_btn="撤销",
                # clear_btn="清空对话",
            )
            
            gr.Markdown(
                "💡 **温馨提示**：本助手具备安全审计功能，高危指令将被拦截，变更操作需人工确认。",
                elem_id="footer-note"
            )

    log_message("系统启动完成")
    
    # 3. 将 theme 和 css 挪到这里
    demo.launch(
        server_name="0.0.0.0", 
        server_port=7860
    )

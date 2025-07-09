# 1_Admin_Panel.py (修正版)
#这是25年7月9日晚在家里添加的注释，目的是测试修改后的代码文件，能否实现从gitee仓库到github仓库的同步
import streamlit as st
import json
import os
from collections import Counter

# --- 配置和数据文件路径 ---
FORM_DEF_FILE = "form_definition.json"
SUBMISSIONS_FILE = "submissions.json"

# --- 辅助函数：加载和保存数据 ---
def load_data(filepath, default_data=[]):
    """从JSON文件加载数据，如果文件不存在则返回默认值"""
    if not os.path.exists(filepath):
        return default_data
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return default_data

def save_data(data, filepath):
    """将数据保存到JSON文件"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- Streamlit 页面主体 ---
st.set_page_config(page_title="管理员后台", layout="wide")
st.title("📊 报名系统 - 管理员后台")

# 使用 session_state 来动态构建表单
if 'questions' not in st.session_state:
    saved_form = load_data(FORM_DEF_FILE, default_data=[{'prompt': '你想报名哪个城市？', 'options': [{'text': '北京', 'quota': 10}, {'text': '上海', 'quota': 5}]}])
    st.session_state.questions = saved_form


# --- 1. 表单设计器 ---
st.header("📝 表单设计器")

# 创建一个唯一的表单区域
with st.form("form_designer"):
    
    # 在表单内部，只放置输入控件
    for i, q in enumerate(st.session_state.questions):
        st.markdown(f"---")
        st.text_input(f"问题 {i+1} 题干", value=q.get('prompt', ''), key=f"q_prompt_{i}")
        
        for j, opt in enumerate(q['options']):
            opt_cols = st.columns([0.8, 0.2])
            opt_cols[0].text_input(f"选项 {j+1} 文字", value=opt.get('text', ''), key=f"q_{i}_opt_text_{j}")
            opt_cols[1].number_input(f"限额", min_value=1, value=opt.get('quota', 10), key=f"q_{i}_opt_quota_{j}")
    
    # 表单唯一的提交按钮
    submitted = st.form_submit_button("💾 保存表单设计")
    if submitted:
        # 当点击“保存”时，从 session_state 读取所有输入框的当前值并更新
        new_questions_data = []
        for i, q in enumerate(st.session_state.questions):
            new_q = {'prompt': st.session_state[f"q_prompt_{i}"], 'options': []}
            for j, opt in enumerate(q['options']):
                new_opt = {
                    'text': st.session_state[f"q_{i}_opt_text_{j}"],
                    'quota': st.session_state[f"q_{i}_opt_quota_{j}"]
                }
                new_q['options'].append(new_opt)
            new_questions_data.append(new_q)
        
        # 为每个选项分配唯一ID
        option_id_counter = 0
        for q in new_questions_data:
            for opt in q['options']:
                opt['id'] = option_id_counter
                option_id_counter += 1
        
        # 更新 session_state 并保存到文件
        st.session_state.questions = new_questions_data
        save_data(st.session_state.questions, FORM_DEF_FILE)
        st.success("表单设计已成功保存！")

# --- 将所有交互式按钮移到表单外部 ---
st.markdown("---")
st.subheader("动态调整结构")

for i, q in enumerate(st.session_state.questions):
    cols = st.columns([0.4, 0.3, 0.3])
    cols[0].write(f"**调整问题 {i+1}：**")
    if cols[1].button(f"➕ 为问题 {i+1} 添加选项", key=f"add_opt_{i}"):
        st.session_state.questions[i]['options'].append({'text': '', 'quota': 10})
        st.rerun() # 立即刷新页面
    if cols[2].button(f"🗑️ 删除问题 {i+1}", key=f"del_q_{i}"):
        st.session_state.questions.pop(i)
        st.rerun() # 立即刷新页面

if st.button("➕ 添加一个新问题"):
    st.session_state.questions.append({'prompt': '', 'options': [{'text': '', 'quota': 10}]})
    st.rerun() # 立即刷新页面

# --- 2. 报名状态查看器 (这部分代码无需修改) ---
st.markdown("---")
st.header("📈 实时报名状态")

form_definition = load_data(FORM_DEF_FILE)
submissions = load_data(SUBMISSIONS_FILE)

if not form_definition:
    st.warning("请先设计并保存一个表单。")
else:
    submission_counts = Counter(submissions)
    
    for i, question in enumerate(form_definition):
        st.subheader(f"问题 {i+1}: {question.get('prompt', '（无题干）')}")
        
        # 使用 st.columns 创建更美观的表格布局
        col1, col2, col3, col4 = st.columns(4)
        col1.markdown("**选项**")
        col2.markdown("**总名额**")
        col3.markdown("**已报名**")
        col4.markdown("**余量**")

        for option in question['options']:
            option_id = option.get('id', -1)
            quota = option.get('quota', 0)
            selected_count = submission_counts.get(option_id, 0)
            remaining = quota - selected_count
            
            col1, col2, col3, col4 = st.columns(4)
            col1.write(option.get('text', ''))
            col2.write(str(quota))
            col3.write(str(selected_count))
            if remaining > 0:
                col4.success(f"**{remaining}**") # 绿色
            else:
                col4.error(f"**{remaining}**") # 红色
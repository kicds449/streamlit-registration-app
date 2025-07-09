# pages/2_User_Form.py
import streamlit as st
import json
import os
from collections import Counter
import time

# --- 配置和数据文件路径 ---
FORM_DEF_FILE = "form_definition.json"
SUBMISSIONS_FILE = "submissions.json"

# --- 辅助函数：与主文件相同 ---
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
st.set_page_config(page_title="在线报名", layout="centered")
st.title("✍️ 在线报名表单")

# 加载表单结构和已提交的数据
form_definition = load_data(FORM_DEF_FILE)
submissions = load_data(SUBMISSIONS_FILE)
submission_counts = Counter(submissions)

if not form_definition:
    st.error("管理员尚未配置报名表单，请稍后再试。")
    st.stop() # 如果没有表单，则停止执行

# 使用 st.form 来包裹所有选项，这样用户可以一次性提交
with st.form("registration_form"):
    
    selections = {} # 用于存储用户的选择

    for i, question in enumerate(form_definition):
        st.subheader(f"{question['prompt']}")

        # 动态生成选项列表，包含实时状态
        option_display_list = []
        option_map = {} # 用于从显示文本映射回选项ID

        for option in question['options']:
            option_id = option['id']
            quota = option['quota']
            selected_count = submission_counts.get(option_id, 0)
            remaining = quota - selected_count
            
            # 核心逻辑：如果名额已满，则在选项后标注，使其无法被选中
            if remaining > 0:
                display_text = f"{option['text']} (总数: {quota}, 余量: {remaining})"
            else:
                display_text = f"{option['text']} [名额已满]"

            option_display_list.append(display_text)
            option_map[display_text] = option_id

        # 使用 st.radio 创建单选题
        # st.radio 本身没有禁用单个选项的功能，我们通过文本提示来解决
        user_choice = st.radio(
            "请选择一项:", 
            options=option_display_list, 
            key=f"q_{i}",
            label_visibility="collapsed" # 隐藏 "请选择一项:" 这个标签
        )
        selections[f"q_{i}"] = user_choice
    
    # 表单的提交按钮
    submit_button = st.form_submit_button("确认提交我的选择")

# --- 处理表单提交 ---
if submit_button:
    # 1. 验证选择
    final_choices = []
    is_valid = True
    for choice_display in selections.values():
        if "[名额已满]" in choice_display:
            st.error(f"您选择的 '{choice_display.split('[')[0].strip()}' 名额已满，请重新选择。")
            is_valid = False
            break
        final_choices.append(option_map[choice_display])
    
    if is_valid:
        # 2. 最终一致性检查 (防止并发提交)
        # 重新加载最新的提交数据
        current_submissions = load_data(SUBMISSIONS_FILE)
        current_counts = Counter(current_submissions)
        
        can_submit = True
        for choice_id in final_choices:
            # 找到该选项的定义
            target_option = next((opt for q in form_definition for opt in q['options'] if opt['id'] == choice_id), None)
            if target_option:
                if current_counts.get(choice_id, 0) >= target_option['quota']:
                    st.error(f"非常抱歉，在您提交的瞬间，选项 '{target_option['text']}' 的最后一个名额被抢走了。请返回并选择其他选项。")
                    can_submit = False
                    break # 只要有一个不满足就停止
        
        if can_submit:
            # 3. 保存数据
            new_submissions = current_submissions + final_choices
            save_data(new_submissions, SUBMISSIONS_FILE)
            st.success("报名成功！您的选择已记录。页面将在3秒后刷新。")
            time.sleep(3) # 短暂暂停，让用户看到成功消息
            st.rerun() # 刷新页面以显示最新状态
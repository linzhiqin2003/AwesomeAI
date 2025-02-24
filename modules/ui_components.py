import streamlit as st
from typing import List, Tuple, Optional
from modules.chat_engine import Message
import time
import html

class ChatUI:
    def __init__(self):
        # 初始化session state
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "current_api" not in st.session_state:
            st.session_state.current_api = None
        if "current_model" not in st.session_state:
            st.session_state.current_model = None
            
    def render_sidebar(self, apis: dict) -> Tuple[str, str]:
        """渲染侧边栏"""
        with st.sidebar:
            st.markdown("""
                <div class="sidebar-header">
                    <h1>🛠️ 设置</h1>
                </div>
            """, unsafe_allow_html=True)
            
            # API选择
            api_name = st.selectbox(
                "选择模型供应商",
                options=list(apis.keys()),
                index=0 if st.session_state.current_api is None 
                else list(apis.keys()).index(st.session_state.current_api),
                format_func=lambda x: x.title()  # 首字母大写
            )
            
            # 模型选择
            models = apis[api_name]["model_list"]
            
            # 为 volcengine 添加特殊处理
            if api_name == "volcengine":
                # 从注释中提取模型名称
                model_names = {}
                for model in models:
                    if '#' in model:
                        model_id, model_name = model.split('#')
                        model_names[model_id.strip()] = model_name.strip()
                
                # 清理model_list中的注释
                clean_models = [m.split('#')[0].strip() for m in models]
                
                model = st.selectbox(
                    "选择模型",
                    options=clean_models,
                    index=clean_models.index(st.session_state.current_model) 
                    if st.session_state.current_model in clean_models 
                    else 0,
                    format_func=lambda x: model_names.get(x, x)  # 使用注释中的名称显示
                )
            else:
                model = st.selectbox(
                    "选择模型",
                    options=models,
                    index=models.index(st.session_state.current_model) 
                    if st.session_state.current_model in models 
                    else 0
                )
            
            # 分隔线
            st.markdown("---")
            
            # 功能按钮
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ 清空对话", use_container_width=True):
                    st.session_state.messages = []
                    st.rerun()
            with col2:
                if st.button("⚙️ 更多设置", use_container_width=True):
                    st.session_state.show_settings = True
                
            return api_name, model

    # 统一转义逻辑
    def escape_content(self,content):
        """递归转义字符串或字典中的 HTML 特殊字符"""
        if isinstance(content, dict):
            return {k: self.escape_content(v) for k, v in content.items()}
        elif isinstance(content, str):
            return html.escape(content)
        return content
                
    def render_message(self,message:Message):
        """
        渲染单条历史消息
        """
        user_avatar = "https://api.dicebear.com/9.x/fun-emoji/svg?seed=Liam"
        assistant_avatar = "https://api.dicebear.com/9.x/bottts/svg?seed=Destiny"
        
        avatar_url = user_avatar if message.role == "user" else assistant_avatar
        content = message.content
        
        # 若为助手消息且内容为字典，则分离思考过程和回答部分
        if message.role == "assistant":
            reasoning = content.get("reasoning","").strip()
            answer = content.get("content", "").strip()
            elapsed = content.get("elapsed", None)  # 耗时秒数，由主流程传入保存
            if reasoning:
                header = "思考完成"
                if elapsed is not None:
                    header += f"（用时{elapsed}秒）"
                thought_html = (
                    f'<details class="assistant-thought" open>'
                    f'<summary>{header}</summary>'
                    f'<p>{reasoning}</p>'
                    f'</details>'
                )
                answer_html = f'<div class="assistant-answer">{answer}</div>'
                message_content = thought_html + answer_html
            else:
                message_content = f'<div class="assistant-answer">{answer}</div>'
        else:
            message_content = html.escape(content)

        message_html = (
            '<div class="message ' + message.role + '">'
            '<div class="avatar"><img src="' + avatar_url + '" alt="avatar"/></div>'
            '<div class="content"><div class="bubble">' +message_content + '</div>'
            '<div class="timestamp">' + time.strftime("%H:%M", time.localtime(message.timestamp)) + '</div>'
            '</div></div>'
        )
        st.markdown(message_html, unsafe_allow_html=True)

    def get_user_input(self) -> Optional[str]:
        """获取用户输入"""
        return st.chat_input("输入消息...")
        
    def render_thinking_animation(self):
        """渲染思考动画"""
        assistant_avatar = "https://api.dicebear.com/9.x/bottts/svg?seed=Destiny"
        
        animation_html = f"""
        <div class="message assistant thinking-container">
            <div class="avatar">
                <img src="{assistant_avatar}" alt="avatar"/>
            </div>
            <div class="content">
                <div class="bubble">
                    <div class="thinking">
                        <div class="dot"></div>
                        <div class="dot"></div>
                        <div class="dot"></div>
                    </div>
                </div>
            </div>
        </div>
        """
        st.markdown(animation_html, unsafe_allow_html=True)
    
    def render_streaming_message(self,content="", reasoning="", elapsed=None, under_reasoning=False,is_reasoner=False):
        """渲染流式响应消息"""
        assistant_avatar = "https://api.dicebear.com/9.x/bottts/svg?seed=Destiny"
        
        if is_reasoner:
            if under_reasoning:
                # 不显示正文内容部分
                header = '<span class="dynamic-thinking">深度思考中...</span>'
                thought_display = (
                    f'<details class="assistant-thought" open>'
                    f'<summary>{header}</summary>'
                    f'<p>{reasoning}</p>'
                    f'</details>'
                )
                answer_display = ""
            else:
                # 流式完成后显示耗时信息，同时显示正文内容部分
                header = f"思考完成（用时{elapsed}秒）"
                thought_display = (
                    f'<details class="assistant-thought" open>'
                    f'<summary>{header}</summary>'
                    f'<p>{reasoning}</p>'
                    f'</details>'
                )
                answer_display = f'<div class="assistant-answer">{content}</div>'
            combined = thought_display + answer_display
        else:
            combined = f'<div class="assistant-answer">{content}</div>'
        
        html_ = (
            '<div class="message assistant">'
            '<div class="avatar"><img src="' + assistant_avatar + '" alt="avatar"/></div>'
            '<div class="content"><div class="bubble">' + combined + '</div></div></div>'
        )
        return html_
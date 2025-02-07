import streamlit as st
from typing import List, Tuple, Optional
from modules.chat_engine import Message
import time

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
            
    def render_message(self, role: str, content: str, timestamp: Optional[float] = None):
        """渲染单条消息"""
        with st.chat_message(role):
            st.markdown(content)
            if timestamp:
                st.caption(f"发送时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}")
                
    def render_messages(self, messages: List[Message]):
        """渲染消息历史"""
        for msg in messages:
            with st.chat_message(msg.role):
                st.markdown(msg.content)
                if msg.timestamp:
                    st.caption(f"发送时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg.timestamp))}")
            
    def get_user_input(self) -> Optional[str]:
        """获取用户输入"""
        return st.chat_input("输入消息...")
        
    def render_streaming(self, role: str, placeholder: str = ""):
        """创建流式输出占位符"""
        with st.chat_message(role):
            return st.empty() 
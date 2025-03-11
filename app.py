import streamlit as st
import time
from modules.api_manager import APIManager
from modules.chat_engine import ChatEngine,Message
from modules.ui_components import ChatUI
import os

os.environ["http_proxy"] = "http://localhost:4780"
os.environ["https_proxy"] = "http://localhost:4780"

# 设置页面配置
st.set_page_config(
    page_title="AwesomeAI",
    page_icon='logo.png',
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "AI Chat Assistant - Your Intelligent Companion"
    }
)

# 加载自定义CSS
with open("config/style.css","r",encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 初始化组件
@st.cache_resource
def get_api_manager():
    return APIManager()

def init_chat_engine():
    if 'chat_engine' not in st.session_state:
        st.session_state.chat_engine = ChatEngine(get_api_manager())
    return st.session_state.chat_engine

def create_layout():
    """创建页面布局"""
    # 顶部导航栏
    st.markdown("""
        <div class="header">
            <div class="header-content">
                <div class="logo-section">
                    <div class="logo-icon">🤖</div>
                    <div class="logo-text">AI Chat</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # 主聊天区域容器
    chat_container = st.container()
    
    return chat_container

def main():
    # 初始化聊天引擎、聊天窗口、侧边栏、用户输入框
    api_manager = get_api_manager()
    chat_engine = init_chat_engine()
    chat_ui = ChatUI()
    
    # 渲染侧边栏并获取选择的API和模型
    api_name, model = chat_ui.render_sidebar(api_manager.get_api_configs())
    
    # 如果API或模型发生变化,更新chat engine
    if (st.session_state.current_api != api_name or 
        st.session_state.current_model != model):
        chat_engine.set_model(api_name, model)
        st.session_state.current_api = api_name
        st.session_state.current_model = model
    
    # 创建消息容器
    message_container = create_layout()
    
    # 初始化session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # 获取用户输入
    user_input = chat_ui.get_user_input_with_upload()
    print(user_input)
    
    # 处理用户输入
    if user_input:
        # 会话状态中添加用户消息
        st.session_state.messages.append(Message(
            role="user",
            content=user_input.text,
            files=user_input.files if user_input.files else None,
            timestamp=time.time()
            ))
        
        # 更新chat engine的消息历史
        chat_engine.clear_history()
    
    # 渲染所有消息
    with message_container:
        # 渲染历史消息
        for message in st.session_state.messages:
            chat_ui.render_message(message)
        
        # 如果有新输入，显示AI响应
        if user_input:
            try:
                # 显示思考动画
                message_placeholder = st.empty()
                with message_placeholder:
                    chat_ui.render_thinking_animation()
                
                # 获取 AI 流式响应
                response_text = {"reasoning": "", "content": ""}
                under_reasoning = False
                is_reasoner = False
                try:
                    print("会话记录：")
                    print(st.session_state.messages)
                    response = chat_engine.get_response(st.session_state.messages)
                    while True:
                        chunk = next(response)
                        if not any(response_text.values()):
                            message_placeholder.empty()
                            message_placeholder = st.empty()
                        
                        chunk_type = chunk["type"]
                        if chunk_type == "reasoning" and not under_reasoning:
                            is_reasoner = True
                            under_reasoning = True
                        elif chunk_type == "content" and under_reasoning:
                            under_reasoning = False
                            response_text["elapsed"] = chunk["elapsed"]

                        response_text[chunk_type] += chunk["content"] if chunk["content"] else ""
                        
                        message_placeholder.markdown(
                            chat_ui.render_streaming_message(
                                content=response_text["content"],
                                reasoning=response_text["reasoning"],
                                is_reasoner=is_reasoner,
                                under_reasoning=under_reasoning,
                                elapsed=response_text.get("elapsed", None)
                            ),
                            unsafe_allow_html=True
                        )

                except StopIteration as e:
                    final_result = e.value
                    st.session_state.messages.append(final_result)
                    message_placeholder.markdown(
                        chat_ui.render_streaming_message(
                            content=final_result.content["content"],
                            reasoning=final_result.content["reasoning"],
                            is_reasoner=is_reasoner,
                            under_reasoning=under_reasoning,
                            elapsed=final_result.content.get("elapsed", None)
                        ),
                        unsafe_allow_html=True
                    ) # 补一帧防抖
                    print("会话记录：")
                    print(st.session_state.messages)

                # 刷新页面
                st.rerun()
                
            except Exception as e:
                message_placeholder.empty()
                st.error(f"发生错误: {str(e)}")

if __name__ == "__main__":
    main() 
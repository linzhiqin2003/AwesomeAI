import streamlit as st
import time
from modules.api_manager import APIManager
from modules.chat_engine import ChatEngine
from modules.ui_components import ChatUI

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
with open("config/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 初始化组件
@st.cache_resource
def get_api_manager():
    return APIManager()

def init_chat_engine():
    if 'chat_engine' not in st.session_state:
        st.session_state.chat_engine = ChatEngine(get_api_manager())
    return st.session_state.chat_engine

def render_message(message):
    """渲染单条历史消息"""
    user_avatar = "https://api.dicebear.com/9.x/fun-emoji/svg?seed=Liam"
    assistant_avatar = "https://api.dicebear.com/9.x/bottts/svg?seed=Destiny"
    
    avatar_url = user_avatar if message["role"] == "user" else assistant_avatar
    content = message["content"]
    
    # 若为助手消息且内容为字典，则分离思考过程和回答部分
    if message["role"] == "assistant" and isinstance(content, dict):
        reasoning = content.get("reasoning", "").strip()
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
        message_content = content

    message_html = (
        '<div class="message ' + message["role"] + '">'
        '<div class="avatar"><img src="' + avatar_url + '" alt="avatar"/></div>'
        '<div class="content"><div class="bubble">' + message_content + '</div>'
        '<div class="timestamp">' + time.strftime("%H:%M", time.localtime(message["timestamp"])) + '</div>'
        '</div></div>'
    )
    st.markdown(message_html, unsafe_allow_html=True)

def render_thinking_animation():
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

def render_streaming_message(content="", reasoning="", elapsed=None, under_reasoning=False,is_reasoner=False):
    """渲染流式响应消息"""
    assistant_avatar = "https://api.dicebear.com/9.x/bottts/svg?seed=Destiny"
    # cursor = "▋" if with_cursor else ""
    
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
            header = f"深度思考完成（用时{elapsed}秒）"
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
    
    html = (
        '<div class="message assistant">'
        '<div class="avatar"><img src="' + assistant_avatar + '" alt="avatar"/></div>'
        '<div class="content"><div class="bubble">' + combined + '</div></div></div>'
    )
    return html

def main():
    # 初始化组件
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
    user_input = chat_ui.get_user_input()
    
    # 处理用户输入
    if user_input:
        # 添加用户消息
        st.session_state.messages.append({
            "role": "user", 
            "content": user_input,
            "timestamp": time.time()
        })
        
        # 更新chat engine的消息历史
        chat_engine.clear_history()
        for msg in st.session_state.messages:
            chat_engine.add_message(msg["role"], msg["content"])
    
    # 渲染所有消息
    with message_container:
        # 渲染历史消息
        for message in st.session_state.messages:
            render_message(message)
        
        # 如果有新输入，显示AI响应
        if user_input:
            try:
                # 开始响应前记录起始时间
                start_time = time.time()
                
                # 显示思考动画
                message_placeholder = st.empty()
                with message_placeholder:
                    render_thinking_animation()
                
                # 获取 AI 流式响应
                response_text = {"reasoning": "", "content": ""}
                under_reasoning = False
                is_reasoner = False
                final_elapsed = None
                for chunk in chat_engine.get_response(user_input):
                    if not any(response_text.values()):
                        message_placeholder.empty()
                        message_placeholder = st.empty()
                    
                    chunk_type = chunk["type"]
                    if chunk_type == "reasoning" and not under_reasoning:
                        under_reasoning = True
                        is_reasoner = True
                    elif chunk_type == "content" and under_reasoning:
                        under_reasoning = False
                        # 完成响应后计算耗时，并构造最终内容
                        current_time = time.time()
                        final_elapsed = round(current_time - start_time)

                    response_text[chunk_type] += chunk["content"]
                    
                    message_placeholder.markdown(
                        render_streaming_message(
                            content=response_text["content"],
                            reasoning=response_text["reasoning"],
                            is_reasoner=is_reasoner,
                            under_reasoning=under_reasoning,
                            elapsed=final_elapsed if final_elapsed else None
                        ),
                        unsafe_allow_html=True
                    )
            
                # final_text = ""
                # if response_text["reasoning"]:
                #     final_text += f'<div class="reasoning-content">{response_text["reasoning"]}</div>'
                # if response_text["content"]:
                #     final_text += response_text["content"]
                
                # message_placeholder.markdown(
                #     render_streaming_message(
                #         content=final_text,
                #         reasoning=response_text["reasoning"],
                #         with_cursor=False,
                #         elapsed=final_elapsed
                #     ),
                #     unsafe_allow_html=True
                # )
                
                # 保存完整内容到 session state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": {
                        "reasoning": response_text["reasoning"],
                        "content": response_text["content"],
                        "elapsed": final_elapsed
                    },
                    "timestamp": time.time()
                })
                
                st.rerun()
                
            except Exception as e:
                message_placeholder.empty()
                st.error(f"发生错误: {str(e)}")

if __name__ == "__main__":
    main() 
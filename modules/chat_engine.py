from dataclasses import dataclass
from typing import List, Generator
import time

@dataclass
class Message:
    role: str
    content: str
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class ChatEngine:
    def __init__(self, api_manager):
        self.api_manager = api_manager
        self.current_api = None
        self.current_model = None
        self.messages: List[Message] = []
    
    def set_model(self, api_name: str, model: str):
        """设置当前使用的API和模型"""
        if not self.api_manager.validate_model(api_name, model) and api_name != "volcengine":
            raise ValueError(f"Invalid model {model} for API {api_name}")
        
        self.current_api = api_name
        self.current_model = model
        
    def add_message(self, role: str, content: str) -> Message:
        """添加新消息到历史记录"""
        message = Message(role=role, content=content)
        self.messages.append(message)
        return message
    
    def get_chat_history(self) -> List[Message]:
        """获取聊天历史"""
        return self.messages
    
    def clear_history(self):
        """清空聊天历史"""
        self.messages = []
        
    def get_response(self, prompt: str) -> Generator[str, None, None]:
        """获取AI响应"""
        if not self.current_api or not self.current_model:
            raise ValueError("API and model must be set before chat")
            
        # 准备消息历史，确保content是字符串
        messages = []
        for msg in self.messages:
            if isinstance(msg.content, dict):
                # 如果content是字典，合并reasoning和content
                content = ""
                if msg.content.get("reasoning"):
                    content += f"推理过程：\n{msg.content['reasoning']}\n\n"
                content += msg.content.get("content", "")
                messages.append({"role": msg.role, "content": content})
            else:
                messages.append({"role": msg.role, "content": msg.content})
        
        # 获取chat client
        client = self.api_manager.create_chat_client(
            self.current_api, 
            self.current_model
        )
        
        # 获取响应
        response = client.chat_completion(messages, stream=True)
        
        # 收集完整响应
        full_response = ""
        reasoning = ""
        
        for chunk in response:
            if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
                reasoning += chunk.choices[0].delta.reasoning_content
                yield {"type": "reasoning", "content": chunk.choices[0].delta.reasoning_content}
            # elif hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
            else:
                full_response += chunk.choices[0].delta.content
                yield {"type": "content", "content": chunk.choices[0].delta.content}
        
        # 添加助手响应到历史
        if reasoning:
            self.add_message("assistant", {
                "reasoning": reasoning,
                "content": full_response
            })
        else:
            self.add_message("assistant", full_response) 
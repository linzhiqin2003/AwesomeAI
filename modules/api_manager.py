import os
import yaml
from typing import Dict, List, Optional
from dataclasses import dataclass
from openai import OpenAI
from functools import lru_cache
import time
import streamlit as st

@dataclass
class APIConfig:
    url: str
    key: str
    model_list: List[str] = None

class ConfigLoader:
    @staticmethod
    def load_config(config_path: str = "config/api_config.yaml") -> Dict:
        """加载API配置"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 替换环境变量
        for api_name, api_config in config['apis'].items():
            if isinstance(api_config.get('key'), str) and '${' in api_config['key']:
                env_var = api_config['key'][2:-1]  # 移除 ${ 和 }
                api_config['key'] = os.getenv(env_var)
                if api_config['key'] is None:
                    raise ValueError(f"Environment variable {env_var} not found for {api_name} API")
        
        return config['apis']
    
    @staticmethod
    def validate_config(config: Dict) -> bool:
        """验证配置是否完整"""
        for api_name, api_config in config.items():
            required_fields = ['url', 'key', 'model_list']
            for field in required_fields:
                if field not in api_config:
                    raise ValueError(f"Missing required field '{field}' in {api_name} config")
                if api_config[field] is None:
                    raise ValueError(f"Field '{field}' cannot be None in {api_name} config")
        return True

class ChatClient:
    """聊天客户端"""
    def __init__(self, api_name: str, model: str, api_manager: 'APIManager'):
        if not api_manager.validate_model(api_name, model) and api_name != "volcengine":
            raise ValueError(f"Model {model} is not supported by {api_name}")
        
        self.api_name = api_name
        self.model = model
        self._client = api_manager.get_client(api_name)
    
    def chat_completion(self, messages: List[Dict], **kwargs) -> Dict:
        """执行聊天补全"""
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs
            )
            return response
        except Exception as e:
            raise Exception(f"Error calling {self.api_name} API: {str(e)}")

class APIManager:
    def __init__(self, config_path: str = "config/api_config.yaml"):
        """初始化API管理器"""
        self._api_configs = self._load_config(config_path)
        self._clients = {}
    
    def _load_config(self, config_path: str) -> dict[str, APIConfig]:
        """加载API配置,进一步封装"""
        config = ConfigLoader.load_config(config_path)
        return {
            name: APIConfig(**config[name])
            for name in config
        }
    
    def get_api_configs(self) -> Dict:
        """获取所有API配置"""
        return {
            name: {
                "url": config.url,
                "key": config.key,
                "model_list": config.model_list
            }
            for name, config in self._api_configs.items()
        }
    
    def get_available_models(self, api_name: str) -> List[str]:
        """获取指定API支持的模型列表"""
        if api_name not in self._api_configs:
            raise ValueError(f"Unknown API: {api_name}")
        return self._api_configs[api_name].model_list or []
    
    @lru_cache(maxsize=None)
    def get_client(self, api_name: str) -> Optional[OpenAI]:
        """获取指定API的客户端实例"""
        if api_name not in self._api_configs:
            raise ValueError(f"Unknown API: {api_name}")
            
        if api_name not in self._clients:
            config = self._api_configs[api_name]
            self._clients[api_name] = OpenAI(
                api_key=config.key,
                base_url=config.url
            )
        
        return self._clients[api_name]
    
    def validate_model(self, api_name: str, model: str) -> bool:
        """验证模型是否支持"""
        available_models = self.get_available_models(api_name)
        return model in available_models

    def create_chat_client(self, api_name: str, model: str) -> 'ChatClient':
        """创建特定API和模型的聊天客户端"""
        return ChatClient(api_name, model, self)

def render_message(message):
    """渲染单条消息"""
    user_avatar = "https://api.dicebear.com/7.x/avataaars/svg?seed=user"
    assistant_avatar = "https://api.dicebear.com/7.x/bottts/svg?seed=assistant"
    
    avatar_url = user_avatar if message["role"] == "user" else assistant_avatar
    
    message_html = f"""
    <div class="message {message['role']}">
        <div class="avatar">
            <img src="{avatar_url}" alt="avatar"/>
        </div>
        <div class="content">
            <div class="bubble-container">
                <div class="bubble">
                    {message['content']}
                </div>
                <div class="timestamp">
                    {time.strftime('%H:%M', time.localtime(message['timestamp']))}
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(message_html, unsafe_allow_html=True)

def render_streaming_message(text, with_cursor=True):
    """渲染流式响应消息"""
    assistant_avatar = "https://api.dicebear.com/7.x/bottts/svg?seed=assistant"
    cursor = "▋" if with_cursor else ""
    
    message_html = f"""
    <div class="message assistant">
        <div class="avatar">
            <img src="{assistant_avatar}" alt="avatar"/>
        </div>
        <div class="content">
            <div class="bubble-container">
                <div class="bubble">
                    {text}{cursor}
                </div>
            </div>
        </div>
    </div>
    """
    return message_html

if __name__ == "__main__":
    api_manager = APIManager()
    chat_client = api_manager.create_chat_client("siliconflow", "deepseek-ai/DeepSeek-R1")
    response = chat_client.chat_completion([{"role": "user", "content": "Hello, how are you?"}],stream=True)
    print(response)
    # print(response.usage.completion_tokens)
    # print(response.usage.prompt_tokens)
    # print(response.usage.total_tokens)
    # for chunk in response:
    #     print(chunk.choices[0].delta.content, end="", flush=True)

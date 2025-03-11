from dataclasses import dataclass
from typing import List, Generator, Union, Optional
import time

@dataclass
class Message:
    role: str
    content: Union[dict,str]
    files : Optional[object] = None
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
        
    def clear_history(self):
        """清空聊天历史"""
        self.messages = []
        
    def get_response(self, messages: List[Message], rag_context: Optional[str] = None) -> Generator[str, None, Message]:
        """获取AI响应"""
        if not self.current_api or not self.current_model:
            raise ValueError("API and model must be set before chat")
            
        # 准备消息历史，确保content是字符串
        # 无论是否有推理内容，只将正文内容放入消息历史中
        context = []
        for msg in messages:
            if isinstance(msg.content, dict):
                context.append({"role": msg.role, "content": msg.content["content"]})
            else:
                context.append({"role": msg.role, "content": msg.content})
        
        # # 如果有RAG上下文，添加系统提示
        # if rag_context and rag_context.strip():
        #     # 添加系统消息，引导模型使用检索到的文档内容
        #     system_message = {
        #         "role": "system", 
        #         "content": f"你是一个能够参考文档的助手。请使用以下检索到的信息帮助回答用户的问题。如果信息不相关，请忽略它。\n\n{rag_context}"
        #     }
            
        #     # 如果已有系统消息，就替换；如果没有，就添加
        #     has_system = False
        #     for i, msg in enumerate(context):
        #         if msg["role"] == "system":
        #             context[i] = system_message
        #             has_system = True
        #             break
            
        #     if not has_system:
        #         context.insert(0, system_message)
        
        # 获取chat client
        client = self.api_manager.create_chat_client(
            self.current_api, 
            self.current_model
        )
        
        # 获取响应
        print("上下文：")
        print(context)
        response = client.chat_completion(context, stream=True)
        
        # 收集完整响应
        full_response = ""
        reasoning = ""
        
        # 处理响应流
        reasoning_elapsed = 0
        recorder = False
        on_reasoning = None
        for chunk in response:
            if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content is not None:
                if not reasoning_elapsed:
                    reasoning_elapsed = -1
                    reasoning_start = time.time()
                reasoning += chunk.choices[0].delta.reasoning_content
                yield {"type": "reasoning", "content": chunk.choices[0].delta.reasoning_content}
            elif hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content and "<think>" in chunk.choices[0].delta.content:
                if not on_reasoning:
                    on_reasoning = True
                if not reasoning_elapsed:
                    reasoning_elapsed = -1
                    reasoning_start = time.time()
            else:
                if on_reasoning:
                    if chunk.choices[0].delta.content == "</think>":
                        on_reasoning = False
                        continue
                    reasoning += chunk.choices[0].delta.content
                    yield {"type": "reasoning", "content": chunk.choices[0].delta.content}
                else:
                    full_response += chunk.choices[0].delta.content if chunk.choices[0].delta.content else ""
                    if reasoning_elapsed:
                        if not recorder:
                            reasoning_elapsed = round(time.time() - reasoning_start)
                            recorder = True
                        yield {"type": "content", "content": chunk.choices[0].delta.content,"elapsed":reasoning_elapsed}
                    else:
                        yield {"type": "content", "content": chunk.choices[0].delta.content}
        
        # 添加助手响应到历史
        return Message(
            role="assistant", 
            content={
                "content":full_response,
                "reasoning":reasoning,
                "elapsed":reasoning_elapsed
                }
            )
    
if __name__ == "__main__":
    from api_manager import APIManager
    api_manager = APIManager()
    chat_engine = ChatEngine(api_manager)
    chat_engine.set_model("volcengine", "ep-20250207110456-k72nb")
    
    gen = chat_engine.get_response([{"role":"user","content":"hi"}])
    try:
        while True:
            print(next(gen))
    except StopIteration as e:
        final_result = e.value
        print("Final result:", final_result)
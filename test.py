from volcenginesdkarkruntime import Ark
import os
import dotenv

dotenv.load_dotenv()

client = Ark(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=os.environ.get("ARK_API_KEY")
)

# Streaming:
print("----- streaming request -----")
stream = client.chat.completions.create(
    model="ep-20250207110456-k72nb",
    messages = [
        # {"role": "system", "content": "你是豆包，是由字节跳动开发的 AI 人工智能助手"},
        {"role": "user", "content": "hi"},
    ],
    stream=True
)
for chunk in stream:
    if not chunk.choices:
        continue
    print(chunk.choices[0])
    print(chunk.choices[0].delta.reasoning_content if hasattr(chunk.choices[0].delta,"reasoning_content") and chunk.choices[0].delta.reasoning_content else chunk.choices[0].delta.content, end="",flush=True)
print()
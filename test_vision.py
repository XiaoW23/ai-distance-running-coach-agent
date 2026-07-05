import os
import base64
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# 1. 加载 .env 文件中的环境变量 (确保里面是 GEMINI 的 Key 和 Base URL)
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") # 哪怕变量名没改，只要里面的 Key 是 AIzaSy... 开头就行
base_url = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")

# 2. 初始化大模型
llm = ChatOpenAI(
    model="gemini-3.5-flash", # 这里声明我们要调用的模型
    openai_api_key=api_key,
    openai_api_base=base_url,
    temperature=0.3
)

# 3. 【核心步骤】定义一个函数：把本地图片文件转换成 Base64 编码字符串
def image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        # 读取二进制数据 -> 进行 Base64 编码 -> 转换成普通字符串
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

# 4. 准备你的测试图片 (确保你项目根目录下有这张图，比如 test.jpg)
image_filename = "0630_speedrun1.jpg" 

if not os.path.exists(image_filename):
    print(f"找不到图片：{image_filename}，请随便随便找张跑鞋或表盘的 jpg 图片放到根目录下！")
else:
    print("正在解析图片并转换为 Base64...")
    base64_image = image_to_base64(image_filename)
    
    # 5. 组装多模态消息：告诉大模型图片的 MIME 类型 (image/jpeg 或 image/png)
    image_data_url = f"data:image/jpeg;base64,{base64_image}"
    
    message = HumanMessage(
        content=[
            {
                "type": "text", 
                "text": "教练，请帮我仔细看看这张图！如果这是跑鞋，请告诉我的磨损情况和足翻类型；如果这是数据表单或表盘，请读出里面的关键数字！"
            },
            {
                "type": "image_url",
                "image_url": {"url": image_data_url}
            }
        ]
    )
    
    print("正在向大模型发送视觉请求，请稍候...")
    # 6. 发起调用
    response = llm.invoke([message])
    
    # 7. 打印最终答复
    print("\n" + "="*50)
    print("AI 教练的诊断结果：")
    print("="*50)
    print(response.content)

print("\n" + "-"*50)
print("【底层物理验身】其实际响应服务器模型 ID 为：")
# 查看 API 真正调用的模型底层名称
print(response.response_metadata.get("model_name") or response.response_metadata.get("model"))
print("-" * 50)
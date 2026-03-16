import openai
import yaml

# 读取配置
with open('settings.yaml', 'r') as f:
    config = yaml.safe_load(f)['openai']

# 设置API
openai.api_key = config['api_key']
openai.api_base = config.get('api_base', 'https://api.openai.com/v1')

# 测试调用
try:
    response = openai.ChatCompletion.create(
        model=config['model'],
        messages=[{"role": "user", "content": "把这句话翻译成英文：当50日均线上穿200日均线时买入"}],
        temperature=0
    )
    print("✅ API调用成功！")
    print("返回：", response.choices[0].message.content)
except Exception as e:
    print("❌ 调用失败：", e)
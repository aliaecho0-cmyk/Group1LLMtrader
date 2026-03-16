# MIT License
# Copyright (c) 2026 Lukas Wesemann
# 
# This file is part of the backtrader_copilot project.
# Original source: https://github.com/LukasWesemann/backtrader_copilot

from langchain.llms import OpenAI
import os
import lorem
import ast
import re
from typing import Optional, Tuple, Dict, Any

"""
The agent that codes out certain tasks.
Acts as the the intermediate layer between bt-copilot and the llm
"""

class SimpleCodingAgent:
    """
    The simple coding agent just fowards the prompts to the LLM. No tests, no iterations.
    Other agents can extend this to more complex, iterative coding strategies.
    """
    def __init__(self, API_KEY, test_mode=False, model="qwen-plus"):
        """
        Constructs a new instance of the simple_coding_agent.
        Args:
            API_KEY: OpenAI API key (兼容阿里云)
            test_mode: If True, returns dummy results instead of calling LLM
            model: 模型名称，默认使用 qwen-plus
        """
        self.API_KEY = API_KEY
        self.test_mode = test_mode
        self.model = model
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def code(self, prompt, temperature=0.2):
        '''
        takes input prompt and returns code-snippet.
        :param prompt: string
        :param temperature: float
        :return: code: string
        '''
        if self.test_mode == False:
            return self.simple_LLMcall(prompt, temperature, self.model)
        else:
            code_snippet = """
class DummyStrategy(bt.Strategy):
    params = (('period', 20),)
    
    def __init__(self):
        self.sma = bt.indicators.SMA(self.data.close, period=self.params.period)
    
    def next(self):
        if not self.position:
            if self.data.close[0] > self.sma[0]:
                self.buy()
        else:
            if self.data.close[0] < self.sma[0]:
                self.sell()
"""
            return code_snippet

    def simple_LLMcall(self, prompt, temperature=0.2, model=None):
        """
        调用阿里云通义千问API
        """
        try:
            from openai import OpenAI
            
            model_name = model or self.model
            
            client = OpenAI(
                api_key=self.API_KEY,
                base_url=self.base_url
            )
            
            messages = [
                {"role": "system", "content": "你是一个量化交易专家，擅长编写backtrader策略。请只返回代码，不要有其他解释。"},
                {"role": "user", "content": prompt}
            ]
            
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=2000
            )
            
            result = response.choices[0].message.content
            result = self._extract_code(result)
            
            return result
            
        except Exception as e:
            print(f"Error in LLM call: {e}")
            return self._get_default_strategy()

    def _extract_code(self, text: str) -> str:
        """从文本中提取代码"""
        code_pattern = r'```(?:python)?\n(.*?)```'
        matches = re.findall(code_pattern, text, re.DOTALL)
        
        if matches:
            return max(matches, key=len).strip()
        
        return text.strip()
    
    def _get_default_strategy(self) -> str:
        """返回默认的安全策略"""
        return '''
class DefaultStrategy(bt.Strategy):
    """默认双均线策略"""
    params = (
        ('fast_period', 10),
        ('slow_period', 30),
    )
    
    def __init__(self):
        self.fast_ma = bt.indicators.SMA(self.data.close, period=self.params.fast_period)
        self.slow_ma = bt.indicators.SMA(self.data.close, period=self.params.slow_period)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
    
    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()
        else:
            if self.crossover < 0:
                self.sell()
'''


class CodeValidator:
    """代码验证器 - 确保生成的代码安全可用"""
    
    @staticmethod
    def validate(code: str) -> Tuple[bool, str]:
        """
        验证代码是否安全
        
        Returns:
            (is_safe, error_message)
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"语法错误: {e}"
        
        # 黑名单：不允许的模块
        blacklist_imports = [
            'os', 'sys', 'subprocess', 'socket', 'requests', 
            'urllib', 'pathlib', 'shutil', 'glob', 'pickle',
            'sqlite3', 'mysql', 'pymongo', 'redis',
            'ctypes', 'win32api', 'winreg', 'threading',
            'multiprocessing', 'asyncio'
        ]
        
        # 黑名单：不允许的函数
        blacklist_functions = [
            'exec', 'eval', 'compile', 'open', 'input', 
            '__import__', 'globals', 'locals', 'vars',
            'getattr', 'setattr', 'delattr', 'exit', 'quit'
        ]
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in blacklist_imports or alias.name.split('.')[0] in blacklist_imports:
                        return False, f"不允许导入模块: {alias.name}"
            
            elif isinstance(node, ast.ImportFrom):
                if node.module and (node.module in blacklist_imports or node.module.split('.')[0] in blacklist_imports):
                    return False, f"不允许导入模块: {node.module}"
            
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in blacklist_functions:
                        return False, f"不允许调用函数: {node.func.id}"
        
        has_strategy = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if 'Strategy' in node.name:
                    has_strategy = True
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == 'Strategy':
                        has_strategy = True
                    elif isinstance(base, ast.Attribute) and base.attr == 'Strategy':
                        has_strategy = True
        
        if not has_strategy:
            return False, "代码必须包含bt.Strategy的子类"
        
        return True, "验证通过"
    
    @staticmethod
    def extract_strategy_class(code: str):
        """
        从代码中提取策略类
        """
        try:
            safe_globals = {
                'bt': __import__('backtrader'),
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'range': range,
                    'isinstance': isinstance,
                    'hasattr': hasattr,
                    'getattr': getattr,
                    'setattr': setattr,
                    'float': float,
                    'int': int,
                    'str': str,
                    'list': list,
                    'dict': dict,
                    'min': min,
                    'max': max,
                    'sum': sum,
                    'abs': abs,
                    'round': round,
                }
            }
            
            exec(code, safe_globals)
            
            for name, obj in safe_globals.items():
                if isinstance(obj, type):
                    try:
                        if hasattr(obj, '__bases__'):
                            for base in obj.__bases__:
                                if base.__name__ == 'Strategy' or (hasattr(base, '__module__') and base.__module__ == 'backtrader'):
                                    return obj
                    except:
                        continue
            
            return None
            
        except Exception as e:
            print(f"提取策略类失败: {e}")
            return None


validator = CodeValidator()
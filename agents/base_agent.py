"""
基础智能体类 - 所有智能体的抽象基类
"""
from abc import ABC, abstractmethod
from openai import OpenAI, AzureOpenAI
import config


def get_llm_client():
    """根据配置返回对应的 LLM 客户端"""
    if config.LLM_PROVIDER == "azure":
        return AzureOpenAI(
            api_key=config.AZURE_OPENAI_API_KEY,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_version=config.AZURE_OPENAI_API_VERSION,
        )
    else:
        return OpenAI(
            api_key=config.OPENAI_API_KEY,
            base_url=config.OPENAI_BASE_URL,
        )


def get_model_name():
    """返回当前使用的模型名称"""
    if config.LLM_PROVIDER == "azure":
        return config.AZURE_OPENAI_DEPLOYMENT
    return config.OPENAI_MODEL


class BaseAgent(ABC):
    """所有智能体的抽象基类"""

    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.client = get_llm_client()
        self.model = get_model_name()
        self.conversation_history: list[dict] = []

    def _call_llm(self, messages: list[dict], temperature: float = 0.7) -> str:
        """调用 LLM 并返回文本响应"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content

    def chat(self, user_message: str, temperature: float = 0.7) -> str:
        """带上下文记忆的对话"""
        if not self.conversation_history:
            self.conversation_history.append(
                {"role": "system", "content": self.system_prompt}
            )
        self.conversation_history.append({"role": "user", "content": user_message})

        reply = self._call_llm(self.conversation_history, temperature)
        self.conversation_history.append({"role": "assistant", "content": reply})
        return reply

    def reset(self):
        """重置对话历史"""
        self.conversation_history = []

    @abstractmethod
    def get_description(self) -> str:
        """返回智能体的功能描述"""
        ...

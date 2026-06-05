"""
文档处理智能体
负责理解和分析上传的医药文档，提取关键信息
"""
from agents.base_agent import BaseAgent
from document_store import DocumentStore
import config


class DocumentAgent(BaseAgent):
    """文档分析智能体 - 理解产品手册、销售策略等文档"""

    def __init__(self, doc_store: DocumentStore):
        super().__init__(
            name="文档分析专家",
            system_prompt=config.DOCUMENT_AGENT_PROMPT,
        )
        self.doc_store = doc_store

    def get_description(self) -> str:
        return "负责解析和理解上传的产品手册、销售策略等医药文档，提取关键信息并生成结构化摘要。"

    def analyze_document(self, file_path: str, file_name: str) -> str:
        """分析上传的文档，返回结构化摘要"""
        doc_info = self.doc_store.add_document(file_path, file_name)

        prompt = f"""请对以下医药文档进行深度分析，生成结构化摘要。

文档名称：{doc_info['file_name']}
文档长度：{doc_info['total_chars']} 字符
分段数量：{doc_info['total_chunks']} 段

文档内容（前 5000 字）：
{doc_info['full_text']}

请按以下结构输出分析结果：

## 📋 文档概述
（一句话概括文档核心内容）

## 💊 产品信息
- 药品名称/通用名：
- 适应症：
- 用法用量：
- 主要不良反应：
- 禁忌症：

## 🏆 核心卖点
（列出 3-5 个差异化竞争优势）

## 📊 关键临床数据
（如有临床研究数据，列出关键结果）

## 💡 销售策略要点
（如文档包含销售策略，提取核心话术和方法）

## ⚠️ 合规注意事项
（需要特别注意的合规要点）
"""
        return self.chat(prompt, temperature=0.3)

    def answer_about_documents(self, question: str) -> str:
        """基于已上传文档回答问题"""
        relevant_docs = self.doc_store.search(question, top_k=5)
        context = "\n\n".join(
            f"[来源: {d['source']}]\n{d['content']}" for d in relevant_docs
        )

        prompt = f"""基于以下文档内容，回答用户的问题。如果文档中没有相关信息，请明确说明。

参考资料：
{context}

用户问题：{question}
"""
        return self.chat(prompt, temperature=0.3)

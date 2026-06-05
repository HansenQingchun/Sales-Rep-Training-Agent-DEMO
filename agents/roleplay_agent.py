"""
角色扮演智能体
模拟科室主任与医药代表进行拜访对话
"""
from agents.base_agent import BaseAgent
from document_store import DocumentStore
import config

# 预设科室主任角色模板
DIRECTOR_PRESETS = {
    "心内科主任_严谨型": {
        "department": "心内科",
        "director_name": "张教授",
        "title": "主任医师/教授/博导",
        "years": "25",
        "specialty": "冠心病介入治疗、心力衰竭管理",
        "personality": "学术严谨，注重循证医学证据，对没有充分数据支持的说法持怀疑态度",
    },
    "肿瘤科主任_务实型": {
        "department": "肿瘤科",
        "director_name": "李主任",
        "title": "主任医师/科室主任",
        "years": "20",
        "specialty": "肺癌靶向治疗、免疫治疗",
        "personality": "务实高效，关注患者实际获益和经济负担，对夸大疗效的说法反感",
    },
    "内分泌科主任_温和型": {
        "department": "内分泌科",
        "director_name": "王主任",
        "title": "主任医师/副教授",
        "years": "18",
        "specialty": "糖尿病综合管理、甲状腺疾病",
        "personality": "温和耐心，愿意倾听，但对关键问题会追问到底",
    },
    "神经内科主任_挑战型": {
        "department": "神经内科",
        "director_name": "赵教授",
        "title": "主任医师/教授",
        "years": "22",
        "specialty": "脑血管病、帕金森病",
        "personality": "直率犀利，喜欢用竞品数据挑战代表，时间观念很强",
    },
    "自定义": None,
}


class RolePlayAgent(BaseAgent):
    """角色扮演智能体 - 模拟科室主任进行拜访训练"""

    def __init__(self, doc_store: DocumentStore):
        super().__init__(
            name="科室主任（角色扮演）",
            system_prompt="",  # 将在 start_session 中动态设置
        )
        self.doc_store = doc_store
        self.session_active = False
        self.turn_count = 0
        self.director_config: dict = {}

    def get_description(self) -> str:
        return "模拟不同性格特点的科室主任，与医药代表进行真实拜访场景的角色扮演对话。"

    def start_session(self, preset_name: str, custom_config: dict | None = None) -> str:
        """开始一次角色扮演会话"""
        if preset_name == "自定义" and custom_config:
            self.director_config = custom_config
        elif preset_name in DIRECTOR_PRESETS and DIRECTOR_PRESETS[preset_name]:
            self.director_config = DIRECTOR_PRESETS[preset_name]
        else:
            self.director_config = DIRECTOR_PRESETS["心内科主任_严谨型"]

        # 构造系统提示词
        system_prompt = config.ROLEPLAY_AGENT_PROMPT.format(**self.director_config)

        # 附加产品知识（让主任了解产品以便提出专业问题）
        product_context = self.doc_store.get_combined_context(max_chars=4000)
        if product_context:
            system_prompt += f"""

---
以下是该医药代表可能推广的产品信息（仅供你作为主任角色参考，用于提出专业问题，不要直接透露你已知道这些信息）：
{product_context}
"""

        self.system_prompt = system_prompt
        self.reset()
        self.session_active = True
        self.turn_count = 0

        # 生成主任的开场反应
        opening = self.chat(
            "医药代表敲门进入你的办公室，请以科室主任的身份做出自然的开场反应。"
            "可以是正在忙碌中抬头看一眼，或者简单打个招呼。保持角色真实感。",
            temperature=0.8,
        )
        return opening

    def respond(self, rep_message: str) -> str:
        """医药代表发言后，主任给出回应"""
        if not self.session_active:
            return "⚠️ 角色扮演会话尚未开始，请先选择主任角色并开始会话。"

        self.turn_count += 1
        if self.turn_count >= config.ROLEPLAY_MAX_TURNS:
            return self._end_session_naturally()

        return self.chat(rep_message, temperature=0.8)

    def _end_session_naturally(self) -> str:
        """自然地结束对话"""
        ending = self.chat(
            "[系统提示: 对话已达到上限轮次，请以符合角色的方式自然地结束这次拜访，"
            "比如暗示自己要去查房、有会议等。]",
            temperature=0.8,
        )
        self.session_active = False
        return ending

    def end_session(self) -> str:
        """手动结束会话"""
        if not self.session_active:
            return "当前没有进行中的角色扮演会话。"
        self.session_active = False
        return "角色扮演会话已结束。"

    def get_conversation_for_evaluation(self) -> list[dict]:
        """导出对话历史供评估智能体使用"""
        # 排除 system 消息和初始开场指令
        filtered = []
        skip_first_user = True
        for msg in self.conversation_history:
            if msg["role"] == "system":
                continue
            if skip_first_user and msg["role"] == "user":
                skip_first_user = False
                continue
            filtered.append(msg)
        return filtered

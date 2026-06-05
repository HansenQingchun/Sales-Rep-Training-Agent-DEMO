"""
医药代表培训多智能体系统 - Streamlit 主界面
"""
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

import config  # noqa: E402 — 需在 load_dotenv() 之后导入
from orchestrator import Orchestrator  # noqa: E402
from agents.roleplay_agent import DIRECTOR_PRESETS  # noqa: E402

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="医药代表培训系统",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 会话状态初始化
# ============================================================
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = Orchestrator()
if "roleplay_messages" not in st.session_state:
    st.session_state.roleplay_messages = []
if "current_questions" not in st.session_state:
    st.session_state.current_questions = []
if "qa_history" not in st.session_state:
    st.session_state.qa_history = []

orch: Orchestrator = st.session_state.orchestrator


# ============================================================
# 辅助函数
# ============================================================
def _parse_batch_qa(text: str) -> list[tuple[str, str]]:
    """解析批量问答输入"""
    pairs = []
    blocks = text.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        q, a = "", ""
        for line in lines:
            stripped = line.strip()
            if stripped.upper().startswith("Q:") or stripped.startswith("问:") or stripped.startswith("问："):
                q = stripped.split(":", 1)[-1].split("：", 1)[-1].strip()
            elif stripped.upper().startswith("A:") or stripped.startswith("答:") or stripped.startswith("答："):
                a = stripped.split(":", 1)[-1].split("：", 1)[-1].strip()
        if q and a:
            pairs.append((q, a))
    return pairs


# ============================================================
# 侧边栏导航
# ============================================================
st.sidebar.title("💊 医药代表培训系统")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "功能模块",
    [
        "📁 文档管理",
        "📝 培训题库",
        "🎭 角色扮演",
        "📊 问答评估",
    ],
    index=0,
)

# 显示已上传文档数
docs = orch.get_uploaded_documents()
st.sidebar.markdown("---")
st.sidebar.metric("已上传文档", len(docs))
if orch.roleplay_active:
    st.sidebar.success("🎭 角色扮演进行中")

# ============================================================
# 📁 文档管理页面
# ============================================================
if page == "📁 文档管理":
    st.header("📁 文档管理")
    st.markdown("上传产品手册、销售策略等文件，系统将自动解析并建立知识库。")

    # 文件上传
    uploaded_files = st.file_uploader(
        "上传文档（支持 PDF、Word、TXT、Markdown、PPT）",
        type=["pdf", "docx", "txt", "md", "pptx"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        for uf in uploaded_files:
            save_path = config.UPLOAD_DIR / uf.name
            save_path.write_bytes(uf.getbuffer())

            with st.spinner(f"正在分析 {uf.name} ..."):
                analysis = orch.upload_document(str(save_path), uf.name)

            st.success(f"✅ {uf.name} 上传并分析完成")
            with st.expander(f"📄 {uf.name} - 分析报告", expanded=True):
                st.markdown(analysis)

    # 已上传文档列表
    st.markdown("---")
    st.subheader("已上传文档")
    if docs:
        for doc in docs:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📄 **{doc['file_name']}**")
            with col2:
                st.caption(f"{doc['total_chars']} 字 · {doc['total_chunks']} 段")
    else:
        st.info("暂无已上传文档，请上传产品手册或销售策略文件。")

    # 文档问答
    st.markdown("---")
    st.subheader("💬 文档问答")
    doc_question = st.text_input("输入关于已上传文档的问题", key="doc_qa_input")
    if doc_question:
        with st.spinner("正在检索文档并生成回答..."):
            answer = orch.ask_about_documents(doc_question)
        st.markdown(answer)


# ============================================================
# 📝 培训题库页面
# ============================================================
elif page == "📝 培训题库":
    st.header("📝 培训题库生成")
    st.markdown("基于已上传的产品资料，自动生成多维度培训问题。")

    col1, col2, col3 = st.columns(3)
    with col1:
        num_q = st.slider("题目数量", 1, 10, 5)
    with col2:
        difficulty = st.selectbox("难度", ["混合", "基础", "进阶", "高级"])
    with col3:
        focus = st.selectbox(
            "重点领域",
            ["综合", "产品知识", "竞品分析", "临床场景", "销售技巧", "合规"],
        )

    if st.button("🎯 生成培训题目", type="primary"):
        with st.spinner("正在生成培训题目..."):
            result = orch.generate_questions(num_q, difficulty, focus)
        st.markdown(result)
        st.session_state.current_questions = result

    # 场景化题目
    st.markdown("---")
    st.subheader("🎬 场景化题目")
    scenario = st.text_area(
        "描述一个具体场景",
        placeholder="例如：拜访心内科主任时，主任提到已经在使用竞品A，对疗效很满意...",
        height=100,
    )
    if scenario and st.button("生成场景题目"):
        with st.spinner("正在生成场景化题目..."):
            result = orch.generate_scenario_questions(scenario)
        st.markdown(result)


# ============================================================
# 🎭 角色扮演页面
# ============================================================
elif page == "🎭 角色扮演":
    st.header("🎭 科室主任拜访模拟")
    st.markdown("选择科室主任角色，开始模拟拜访对话训练。")

    # 角色选择
    if not orch.roleplay_active:
        preset_names = list(DIRECTOR_PRESETS.keys())
        selected_preset = st.selectbox("选择科室主任角色", preset_names)

        custom_cfg = None
        if selected_preset == "自定义":
            st.markdown("##### 自定义主任角色")
            c1, c2 = st.columns(2)
            with c1:
                dept = st.text_input("科室", "消化内科")
                name = st.text_input("姓名", "陈主任")
                title = st.text_input("职称", "主任医师")
            with c2:
                years = st.text_input("从医年限", "15")
                specialty = st.text_input("专业特长", "消化道肿瘤早筛")
                personality = st.text_input(
                    "性格特点", "谨慎保守，偏好经典方案"
                )
            custom_cfg = {
                "department": dept,
                "director_name": name,
                "title": title,
                "years": years,
                "specialty": specialty,
                "personality": personality,
            }
        else:
            preset_info = DIRECTOR_PRESETS.get(selected_preset, {})
            if preset_info:
                st.info(
                    f"**{preset_info['director_name']}** · {preset_info['department']} · "
                    f"{preset_info['title']} · {preset_info['years']}年经验\n\n"
                    f"性格：{preset_info['personality']}"
                )

        if st.button("🎬 开始拜访", type="primary"):
            with st.spinner("正在进入科室..."):
                opening = orch.start_roleplay(selected_preset, custom_cfg)
            st.session_state.roleplay_messages = [
                {"role": "assistant", "content": opening}
            ]
            st.rerun()

    # 对话界面
    if orch.roleplay_active:
        st.info(
            f"🎭 当前角色：**{orch.roleplay_agent.director_config.get('director_name', '主任')}** "
            f"({orch.roleplay_agent.director_config.get('department', '')}科) · "
            f"对话轮次：{orch.roleplay_agent.turn_count}/{config.ROLEPLAY_MAX_TURNS}"
        )

        # 显示对话历史
        for msg in st.session_state.roleplay_messages:
            avatar = "🧑‍⚕️" if msg["role"] == "assistant" else "👔"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

        # 输入框
        user_input = st.chat_input("输入你的回复（医药代表角色）...")
        if user_input:
            st.session_state.roleplay_messages.append(
                {"role": "user", "content": user_input}
            )
            with st.chat_message("user", avatar="👔"):
                st.markdown(user_input)

            with st.spinner("主任正在思考..."):
                reply = orch.roleplay_respond(user_input)
            st.session_state.roleplay_messages.append(
                {"role": "assistant", "content": reply}
            )
            with st.chat_message("assistant", avatar="🧑‍⚕️"):
                st.markdown(reply)

        # 操作按钮
        col_end, col_eval = st.columns(2)
        with col_end:
            if st.button("⏹️ 结束拜访"):
                orch.end_roleplay()
                st.success("拜访已结束。")
                st.rerun()
        with col_eval:
            if st.button("📊 评估本次拜访", type="primary"):
                with st.spinner("正在生成评估报告..."):
                    evaluation = orch.evaluate_roleplay()
                st.markdown("---")
                st.markdown("## 📊 拜访评估报告")
                st.markdown(evaluation)


# ============================================================
# 📊 问答评估页面
# ============================================================
elif page == "📊 问答评估":
    st.header("📊 问答评估")
    st.markdown("输入培训问题和代表回答，获取专业评估和改进建议。")

    tab_single, tab_batch = st.tabs(["单题评估", "批量评估"])

    with tab_single:
        question = st.text_area(
            "培训问题",
            placeholder="例如：请介绍本药品的核心适应症及用法用量",
            height=80,
            key="eval_q",
        )
        answer = st.text_area(
            "代表回答",
            placeholder="输入医药代表对该问题的回答...",
            height=150,
            key="eval_a",
        )
        ref_answer = st.text_area(
            "参考答案（可选）",
            placeholder="输入标准参考答案用于对比评估...",
            height=100,
            key="eval_ref",
        )

        if st.button("📊 开始评估", type="primary"):
            if not question or not answer:
                st.warning("请输入问题和回答。")
            else:
                with st.spinner("正在评估..."):
                    result = orch.evaluate_qa(question, answer, ref_answer)
                st.markdown(result)

                # 保存到历史
                st.session_state.qa_history.append(
                    {
                        "question": question,
                        "answer": answer,
                        "evaluation": result,
                    }
                )

    with tab_batch:
        st.markdown("输入多组问答对，每组用空行分隔。格式：")
        st.code("Q: 问题内容\nA: 回答内容\n\nQ: 下一个问题\nA: 下一个回答", language=None)

        batch_input = st.text_area(
            "批量输入", height=300, key="batch_eval_input"
        )

        if st.button("📊 批量评估") and batch_input:
            pairs = _parse_batch_qa(batch_input)
            if not pairs:
                st.warning("未解析到有效的问答对，请检查格式。")
            else:
                st.info(f"解析到 {len(pairs)} 组问答对，开始评估...")
                for i, (q, a) in enumerate(pairs, 1):
                    with st.expander(f"第 {i} 题", expanded=True):
                        st.markdown(f"**问题：** {q}")
                        st.markdown(f"**回答：** {a}")
                        with st.spinner(f"评估第 {i} 题..."):
                            score = orch.quick_score(q, a)
                        if "error" not in score:
                            cols = st.columns(5)
                            labels = ["准确性", "证据", "沟通", "合规", "价值"]
                            keys = ["accuracy", "evidence", "communication", "compliance", "value_delivery"]
                            for col, label, key in zip(cols, labels, keys):
                                col.metric(label, f"{score[key]['score']}/{score[key]['max']}")
                            st.markdown(f"**总分：{score['total_score']}/{score['total_max']}** · 评级：**{score['grade']}**")
                            st.caption(score.get("brief_feedback", ""))
                        else:
                            st.warning("评分解析失败，原始输出：")
                            st.text(score.get("raw", ""))

    # 评估历史   
    if st.session_state.qa_history:
        st.markdown("---")
        st.subheader("📋 评估历史")
        for i, record in enumerate(reversed(st.session_state.qa_history), 1):
            with st.expander(f"记录 {i}: {record['question'][:50]}..."):
                st.markdown(f"**问题：** {record['question']}")
                st.markdown(f"**回答：** {record['answer']}")
                st.markdown("---")
                st.markdown(record["evaluation"])

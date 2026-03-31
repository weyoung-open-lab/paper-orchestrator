# paper_agent/llm/prompts.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class PromptPack:
    """A maintainable prompt pack."""
    system_en: str
    system_zh: str
    templates_en: Dict[str, str]
    templates_zh: Dict[str, str]


DEFAULT_PROMPTS = PromptPack(
    system_en=(
        "You are an SCI journal paper writing assistant. "
        "Write in a rigorous academic style. "
        "Do NOT fabricate numeric results, experimental conclusions, datasets, citations, or claims. "
        "If information is missing, explicitly say it is missing and list what should be provided."
    ),
    system_zh=(
        "你是一名SCI期刊论文写作助手。请使用严谨学术风格。"
        "严禁编造结果、数值、实验结论、引用。"
        "如果信息不足，请明确说明缺失，并给出可补充内容清单。"
    ),
    templates_en={
        "outline": (
            "Generate a detailed SCI paper outline including: title suggestions, abstract bullets, "
            "Introduction, Related Work, Method, Experiments, Discussion, Conclusion, and References structure.\n\n"
            "Project description:\n{project_description}\n\n"
            "Method/model:\n{model_method}\n\n"
            "Experimental data:\n{experiment_data}\n\n"
            "Output actionable bullet points (5-8+ per section)."
        ),
        "abstract": (
            "Write an SCI Abstract including background, method, dataset/experimental setup, "
            "main contributions, and conclusions/implications. Do not fabricate numeric results.\n\n"
            "Project description:\n{project_description}\n\n"
            "Method/model:\n{model_method}\n\n"
            "Experimental data:\n{experiment_data}\n"
        ),
        "introduction": (
            "Write the Introduction: background/motivation, problem statement, limitations of prior work, "
            "contributions (bulleted), and paper organization. Do not fabricate citations.\n\n"
            "Project description:\n{project_description}\n\n"
            "Method/model:\n{model_method}\n\n"
            "Experimental data:\n{experiment_data}\n"
        ),
        "related_work": (
            "Write Related Work with thematic grouping. Do NOT fabricate references. "
            "If references are missing, list what should be added.\n\n"
            "Project description:\n{project_description}\n\n"
            "Method/model:\n{model_method}\n\n"
            "Seed references (if any):\n{seed_references}\n"
        ),
        "method": (
            "Write Methodology: overall framework, key modules, notation, training/inference procedure, "
            "(optional) complexity analysis, and explicitly note missing details.\n\n"
            "Project description:\n{project_description}\n\n"
            "Method/model:\n{model_method}\n"
        ),
        "experiments": (
            "Write Experiments/Results: dataset description, preprocessing, implementation details, baselines, metrics, "
            "ablation plan, and reproducible settings. Do NOT fabricate numeric results.\n\n"
            "Experimental data:\n{experiment_data}\n\n"
            "Method/model:\n{model_method}\n"
        ),
        "discussion": (
            "Write Discussion: strengths, failure cases, generalization, how to interpret ablation/sensitivity, "
            "limitations and future work. Do NOT fabricate conclusions.\n\n"
            "Project description:\n{project_description}\n\n"
            "Method/model:\n{model_method}\n\n"
            "Experimental data:\n{experiment_data}\n"
        ),
        "conclusion": (
            "Write Conclusion: summarize the work, key contributions, practical value, and future work. "
            "Do NOT fabricate results.\n\n"
            "Project description:\n{project_description}\n\n"
            "Method/model:\n{model_method}\n"
        ),
        "references": (
            "Provide a suggested reference list (>=20 items) based on seed references and the topic. "
            "Do NOT fabricate non-existent papers. If details are missing, output searchable keywords/directions, "
            "and keep seed references verbatim.\n\nSeed references:\n{seed_references}\n"
        ),
        "polish_full": (
            "Polish the full paper for consistency: unify terminology, improve transitions, remove redundancy, "
            "enhance academic writing. Do NOT fabricate results/citations.\n\n{full_paper}\n"
        ),
        "latex_body": (
            "Convert the following paper into LaTeX BODY ONLY (no \\documentclass, no \\begin{document}). "
            "Preserve \\section structure; use proper LaTeX for tables/equations. Do not fabricate content.\n\n{full_paper}\n"
        ),
    },
    templates_zh={
        "outline": (
            "请为一篇SCI论文生成详细论文框架（outline），包括：题目建议、摘要要点、引言、相关工作、方法、实验、讨论、结论、参考文献结构。\n\n"
            "项目描述：\n{project_description}\n\n方法/模型：\n{model_method}\n\n实验数据：\n{experiment_data}\n\n"
            "输出要有可直接写作的章节要点（每章至少5-8条）。"
        ),
        "abstract": (
            "请撰写SCI论文摘要（Abstract），包括研究背景、方法、数据/实验设置、主要贡献、结论与意义。不要编造数值结果。\n\n"
            "项目描述：\n{project_description}\n\n方法/模型：\n{model_method}\n\n实验数据：\n{experiment_data}\n"
        ),
        "introduction": (
            "请撰写SCI论文引言（Introduction），包含：研究背景与动机、问题定义、现有工作不足、本文贡献（列点）、论文结构。不要编造引用。\n\n"
            "项目描述：\n{project_description}\n\n方法/模型：\n{model_method}\n\n实验数据：\n{experiment_data}\n"
        ),
        "related_work": (
            "请撰写相关工作（Related Work），按主题分类总结研究路线、代表性方法与不足。不要编造文献；缺少文献请说明需要补充哪些方向。\n\n"
            "项目描述：\n{project_description}\n\n方法/模型：\n{model_method}\n\n种子参考文献：\n{seed_references}\n"
        ),
        "method": (
            "请撰写方法（Methodology/Method）：整体框架、关键模块、数学符号定义、训练/推理流程、复杂度分析（若可），并明确哪些细节需要补充。\n\n"
            "项目描述：\n{project_description}\n\n方法/模型：\n{model_method}\n"
        ),
        "experiments": (
            "请撰写实验（Experiments/Results）：数据集描述、预处理、实现细节、对比方法、评价指标、消融实验计划、可复现实验设置。不要编造数值结果。\n\n"
            "实验数据：\n{experiment_data}\n\n方法/模型：\n{model_method}\n"
        ),
        "discussion": (
            "请撰写讨论（Discussion）：方法优势、失败案例、泛化性、消融/敏感性分析解读、局限性与未来工作。不要编造结论。\n\n"
            "项目描述：\n{project_description}\n\n方法/模型：\n{model_method}\n\n实验数据：\n{experiment_data}\n"
        ),
        "conclusion": (
            "请撰写结论（Conclusion）：总结工作、贡献点、应用价值与未来工作。不要编造结果。\n\n"
            "项目描述：\n{project_description}\n\n方法/模型：\n{model_method}\n"
        ),
        "references": (
            "请根据种子参考文献与主题给出参考文献列表建议（不少于20条）。不要编造不存在的文献；若信息不足，请输出可检索关键词/方向，并保留种子文献原样。\n\n"
            "种子参考文献：\n{seed_references}\n"
        ),
        "polish_full": (
            "请对以下论文全文进行一致性润色：统一术语、改善逻辑衔接、去除重复表述、提升学术表达。不要编造结果或引用。\n\n{full_paper}\n"
        ),
        "latex_body": (
            "请把下面内容转换成 LaTeX 正文（仅正文，不包含 \\documentclass 和 \\begin{document}），保留 \\section 结构，表格/公式用 LaTeX 语法。不要编造内容。\n\n{full_paper}\n"
        ),
    },
)

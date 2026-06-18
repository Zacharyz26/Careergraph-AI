**CareerGraph AI**

> Current status note: this is a historical product planning document. It
> includes future product ideas such as persistence, resume versions, roadmap
> generation, and export. For the current implemented MVP, see the root
> `README.md`, `docs/architecture.md`, and `docs/api_design.md`.

**AI 简历画像、岗位匹配与求职材料优化 Web App 项目计划书**\
日期：2026 年 6 月 7 日\
作者：Zhuoer Zhang

  ----------------------------------- -------------------------------------------------------------------------------------------------------------------------------------
  **项目定位**                        以简历为中心的 AI Career Agent Web
                                      App。系统通过文档解析、候选人画像、岗位匹配、证据约束改写、版本管理和职业差距规划，帮助学生和初级求职者建立长期可迭代的求职竞争力。

  **最终定位**                        Evidence-grounded, human-in-the-loop, version-controlled resume intelligence platform，而不是简单的 AI resume analyzer。

  **核心用户**                        大学生、转专业学生、国际学生、早期职业求职者，以及需要针对不同岗位方向维护多份简历的用户。

  **MVP 范围**                        上传简历、解析候选人画像、简历诊断、粘贴 JD 匹配、岗位定制改写、用户审批、简历版本保存。

  **明确非目标**                      MVP 不做自动投递、不绕过招聘平台限制、不自动抓取 LinkedIn、不编造用户经历、不承诺录取概率。

  **推荐主技术栈**                    Next.js 16 + React 19 + TypeScript + Vercel AI SDK + FastAPI + OpenAI Agents SDK + PostgreSQL/pgvector + Docling/Unstructured。
  ----------------------------------- -------------------------------------------------------------------------------------------------------------------------------------

  ---------------------------------------------------------------------------------------------------------------
  **最终版核心原则**\
  CareerGraph AI 的所有 AI 建议必须基于 verified
  facts。系统可以帮助用户更清楚、更有针对性地表达已有经历，但不能替用户创造不存在的技能、项目、成绩或工作经历。

  ---------------------------------------------------------------------------------------------------------------

# 目录

1.  项目背景与市场机会

2.  竞品与开源项目借鉴

3.  项目愿景、目标与非目标

4.  用户画像与核心使用场景

5.  产品范围与功能需求

6.  Agent 系统设计

7.  最终技术架构方案

8.  数据模型与 Verified Facts Store

9.  匹配评分与推荐算法

    10\. 文档解析与简历渲染引擎

    11\. 安全、合规、隐私与质量控制

    12\. 可观测性、评估体系与成本控制

    13\. 开发计划与里程碑

    14\. 验收标准与成功指标

    15\. 风险分析与应对策略

    16\. README、作品集与简历呈现方式

    17\. 参考资源

# 1. 项目背景与市场机会

学生和早期职业求职者在求职中通常面临三个问题：第一，不知道自己的简历最适合哪些岗位方向；第二，无法把岗位描述中的要求转化为具体、可信、可执行的简历优化动作；第三，缺少一个持续管理简历版本、岗位匹配结果和能力差距的系统。现有工具多集中在简历模板、ATS
关键词匹配、cover letter
生成或自动填表，但很少把"候选人能力画像""岗位匹配""证据约束改写"和"长期职业路线"做成完整闭环。

CareerGraph AI 的机会在于将简历从静态 PDF
转化为结构化职业资产。用户上传简历后，系统会构建 candidate
profile，识别技能、项目、经历、教育背景、职业方向和薄弱环节；当用户导入岗位
JD
后，系统会计算匹配度、解释匹配和缺口，并生成基于事实来源的改写建议。最终，系统通过版本管理和
roadmap 帮助用户持续迭代简历，而不是一次性给出泛泛建议。

  -----------------------------------------------------------------------
  **项目判断**\
  该项目既有真实用户价值，也适合作为 full-stack AI / agent engineering /
  applied LLM 项目展示。它能体现文档解析、结构化抽取、embedding
  匹配、agent
  workflow、human-in-the-loop、版本管理、评估与可观测性等能力。

  -----------------------------------------------------------------------

# 2. 竞品与开源项目借鉴

最终版计划书明确借鉴现有成功项目，但不直接复刻。CareerGraph AI
的差异化不是"又一个简历打分器"，而是把简历作为长期职业图谱的入口，并用
verified facts 控制 AI 改写质量。

  ----------------------- ---------------------------------------------------- ------------------------------------------------------------------------------
  **项目/产品**           **可借鉴点**                                         **CareerGraph AI 的差异化**

  Resume Matcher          上传 master resume、粘贴 JD、生成 AI 修改建议、cover 在 JD 匹配基础上加入候选人画像、多岗位方向分析、verified
                          letter、导出 PDF；验证了"JD 驱动简历优化"的需求。    facts、长期版本管理和职业差距 roadmap。

  OpenResume              开源 resume builder + parser；强调 ATS               借鉴 ATS-readable 输出与 parser 思路，但增加 AI 证据约束改写和岗位匹配。
                          可读性和结构化简历生成体验。                         

  Reactive Resume /       隐私友好、自托管、模板化简历生成、版本化简历内容。   把简历模板和版本管理与 AI 匹配、岗位建议、修改审批结合。
  开源简历生成器                                                               

  Teal                    Job tracker、简历 builder、JD                        强化"简历版本---岗位---匹配分数---修改记录---反馈"的闭环，并提供解释型匹配和
                          关键词分析、为不同岗位创建多份简历。                 roadmap。

  Simplify Copilot        自动填表、tailored resume/cover letter、申请追踪。   MVP 不做自动投递，只将自动填表作为 V3 参考；优先做简历智能化和
                                                                               human-in-the-loop。

  Browser-use / Stagehand 为 AI agent                                          V2 可用于岗位 JD 导入；MVP 避免爬虫和平台限制风险。
  / Firecrawl 类工具      提供网页浏览、抓取、解析或浏览器自动化能力。         
  ----------------------- ---------------------------------------------------- ------------------------------------------------------------------------------

  -----------------------------------------------------------------------
  **竞品结论**\
  Resume Matcher 证明"简历 + JD 匹配"可行；OpenResume/Reactive Resume
  证明"简历生成与 ATS 可读性"重要；Teal/Simplify 证明"job tracker +
  多版本材料"有商业价值。CareerGraph AI 应综合这些方向，但以
  evidence-grounded resume intelligence 为核心差异化。

  -----------------------------------------------------------------------

# 3. 项目愿景、目标与非目标

## 3.1 项目愿景

CareerGraph AI
的愿景是成为学生和早期职业求职者的"简历操作系统"。它不只是帮助用户写一份简历，而是帮助用户理解自己当前的职业竞争力、最适合的岗位方向、简历与目标岗位之间的差距，以及下一步最值得补强的技能和项目。

## 3.2 项目目标

-   把 PDF/DOCX 简历转化为结构化 candidate profile 和 verified facts。

-   对简历进行多维度诊断，指出
    ATS、关键词、经历表达、项目深度、量化结果和岗位定位问题。

-   支持用户粘贴 JD
    或导入岗位链接，解析岗位要求并计算岗位---简历匹配度。

-   生成基于事实来源的简历 bullet、summary、skills section 和 cover
    letter 建议。

-   通过 human-in-the-loop 审批机制让用户接受、编辑或拒绝 AI 建议。

-   保存不同岗位方向的简历版本、修改记录、匹配记录和改写依据。

-   根据目标岗位反推出技能、项目和学习路线，形成职业差距 roadmap。

## 3.3 非目标

-   MVP 不做自动投递和自动提交申请。

-   MVP 不自动抓取或自动化 LinkedIn 等平台，也不绕过任何网站限制。

-   系统不保证用户获得面试或 offer。匹配分数只表示简历与 JD
    的相似度和覆盖度。

-   系统不允许编造经历、技能、奖项、指标、工作年限或教育背景。

-   系统不替代职业顾问或法律/移民建议。涉及 work
    authorization、visa、sponsorship
    等内容只做表单结构化记录，不做法律判断。

# 4. 用户画像与核心使用场景

  ----------------------- --------------------------------------------------- ------------------------------------------------------------
  **用户类型**            **典型痛点**                                        **产品价值**

  大学生/实习求职者       不知道简历适合 AI、Data、SWE 还是                   自动建立画像，展示不同岗位方向匹配度，并给出具体修改动作。
                          Backend；不知道如何针对 JD 修改。                   

  转专业/跨方向求职者     经历分散，难以证明自己适合新方向。                  将课程、项目、实习转化为目标岗位相关证据，指出缺失能力。

  国际学生                简历格式、ATS、工作授权问题复杂；需要多版本材料。   提供结构化
                                                                              profile、常见申请信息管理、版本化简历和岗位匹配解释。

  早期职业求职者          工作经历少，项目表达弱，缺少量化结果。              帮助重写 bullet、突出项目技术深度和岗位相关性。
  ----------------------- --------------------------------------------------- ------------------------------------------------------------

## 4.1 核心用户旅程

10. 用户上传基础简历 PDF/DOCX。

11. 系统解析文档，生成 candidate profile 和 verified facts。

12. 系统诊断简历质量，输出多维评分和 top fixes。

13. 用户选择目标岗位方向，或粘贴一个岗位 JD。

14. 系统解析 JD，计算匹配度，解释 matched evidence 和 missing
    requirements。

15. 系统生成定制版简历建议，逐条展示原文、建议、原因、风险和事实来源。

16. 用户接受、编辑或拒绝建议。

17. 系统生成新简历版本，保存 change log，并可导出 ATS-readable
    DOCX/PDF。

18. 系统根据缺口生成 30/60/90 天 roadmap。

# 5. 产品范围与功能需求

## 5.1 MVP 功能范围

  ----------------- ------------------------------------------------------ ----------------- --------------------------------------
  **模块**          **功能说明**                                           **优先级**        **验收结果**

  Resume Upload &   支持 PDF/DOCX                                          P0                上传后 60 秒内生成可编辑画像。
  Parsing           上传，抽取文本、章节、教育、技能、经历、项目，并生成                     
                    profile。                                                                

  Verified Facts    把简历中的每条事实保存为                               P0                每条建议都能追溯到一个或多个 fact_id。
  Store             fact_id，后续所有改写建议必须引用来源。                                  

  Resume Diagnostic ATS 兼容性、关键词覆盖、bullet                         P0                输出评分、原因、top fixes。
                    质量、项目强度、量化结果、岗位定位等评分。                               

  JD Import &       支持粘贴 JD，解析 required skills、preferred           P0                输出结构化 JD JSON。
  Parsing           skills、职责、学历、年限、地点等。                                       

  Hybrid Matching   规则过滤 + 技能匹配 + embedding similarity + LLM       P0                输出匹配分数、证据、缺口、建议动作。
  Engine            evidence reasoning。                                                     

  Tailoring         生成 bullet、summary、skills section、cover letter     P0                逐条可接受/编辑/拒绝。
  Suggestions       建议。                                                                   

  Resume Version    保存不同目标岗位版本、修改记录、关联 JD 和匹配分数。   P1                用户可回看版本差异和导出结果。
  Manager                                                                                    

  Roadmap Agent     根据目标岗位缺口生成 30/60/90 天学习和项目补强路线。   P1                输出可执行任务列表。
  ----------------- ------------------------------------------------------ ----------------- --------------------------------------

## 5.2 后续版本范围

  ----------------------- ----------------------- ------------------------------------------------------
  **版本**                **新增能力**            **说明**

  V2                      Job Match Board         支持保存岗位、批量匹配、岗位列表排序、匹配历史分析。

  V2                      Job Link Import         支持用户粘贴 Greenhouse/Lever/company career page
                                                  链接，系统提取 JD。可评估 Firecrawl。

  V2                      GitHub Profile Analyzer 读取用户项目 README
                                                  或用户粘贴项目内容，判断项目能否支撑简历 bullet。

  V2                      Evaluation Dashboard    监控 parsing accuracy、match calibration、rewrite
                                                  acceptance rate、hallucination rate。

  V3                      Chrome Extension        从网页保存 JD 到 CareerGraph AI，不自动提交申请。

  V3                      Application Assistant   可选自动填写表单草稿，但必须停在 submit
                                                  前并等待用户审批。
  ----------------------- ----------------------- ------------------------------------------------------

## 5.3 关键界面设计

-   Profile 页面：展示教育、技能、项目、经历、目标岗位方向、强项和弱项。

-   Resume Score Dashboard：展示简历评分雷达图、top
    issues、可执行修改建议。

-   Role Fit Explorer：展示 AI Intern、Data Analyst、SWE Intern、Backend
    Intern 等方向匹配度。

-   Job Match 页面：展示岗位匹配分数、matched keywords、missing
    keywords、建议使用的简历版本。

-   Tailor Resume 页面：左右对比 original vs suggested，并显示 source
    evidence、risk level 和 approval buttons。

-   Roadmap 页面：展示基于目标岗位的 30/60/90 天技能和项目补强计划。

# 6. Agent 系统设计

最终版采用"workflow agent + specialist tools"的设计。MVP
不追求多个完全自治 agent 相互聊天，而是由一个可审计的 orchestrator
调用多个专用工具，保证输出可控、可恢复、可追踪。

## 6.1 Agent 编排原则

-   LLM
    负责理解、抽取、解释和生成；后端代码负责状态、验证、评分、权限和持久化。

-   所有结构化输出必须通过 Pydantic schema 验证。

-   所有简历改写建议必须引用 verified facts，不能无来源生成。

-   所有会修改用户简历内容的动作必须经过 human-in-the-loop 审批。

-   Agent run 必须记录
    trace、模型、token、耗时、输入输出摘要、工具调用和失败原因。

## 6.2 Specialist Agents / Tools

  ----------------- -------------------------------------------------- ------------------------ ------------------------
  **Agent/Tool**    **职责**                                           **输入**                 **输出**

  Document          解析 PDF/DOCX，保留章节结构、阅读顺序和文本块。    resume_file              resume_blocks, raw_text,
  Ingestion Tool                                                                                layout_metadata

  Resume Parser     抽取教育、经历、项目、技能、证书、个人信息。       resume_blocks            candidate_profile_json
  Agent                                                                                         

  Verified Facts    把简历内容拆成事实单元并赋予 fact_id。             profile + blocks         verified_facts\[\]
  Builder                                                                                       

  Resume Critic     诊断简历质量和岗位定位。                           profile + facts          scores + issues + fixes
  Agent                                                                                         

  JD Parser Agent   解析岗位描述，抽取要求、职责、技能、年限、地点。   job_description          job_profile_json

  Match Scoring     计算匹配分数和证据解释。                           candidate_profile +      match_result_json
  Engine                                                               job_profile + facts      

  Tailoring Agent   生成基于事实的 bullet/summary/skills/cover letter  job_profile + facts +    suggestions\[\]
                    建议。                                             current_resume           

  Human Review      管理接受、编辑、拒绝、重新生成流程。               suggestions +            approved_changes
  Controller                                                           user_actions             

  Version Manager   创建简历版本、记录 change log、绑定目标岗位。      approved_changes         resume_version

  Roadmap Agent     将岗位缺口转为学习/项目补强计划。                  missing_requirements +   roadmap
                                                                       profile                  
  ----------------- -------------------------------------------------- ------------------------ ------------------------

## 6.3 MVP Orchestration Flow

START\
-\> upload_resume\
-\> document_ingestion\
-\> parse_resume_profile\
-\> build_verified_facts\
-\> diagnose_resume\
-\> user_imports_job_description\
-\> parse_job_description\
-\> run_hard_filters\
-\> compute_hybrid_match_score\
-\> generate_evidence_based_suggestions\
-\> human_review_gate\
-\> accept: create_resume_version\
-\> edit: update_suggestion_and_save\
-\> reject: archive_suggestion\
-\> export_resume_docx_pdf\
-\> update_roadmap\
END

## 6.4 Agent Framework Decision

  -----------------------------------------------------------------------
  **最终选择**\
  MVP 主框架采用 OpenAI Agents
  SDK，因为它适合工具调用、结构化输出、guardrails、human-in-the-loop 和
  tracing。LangGraph 作为 V2/V3 备选，用于更复杂的
  long-running、stateful、多岗位批量匹配和多 agent 状态管理。

  -----------------------------------------------------------------------

  ----------------------- ----------------------- ------------------------------------------------------------
  **框架**                **适用阶段**            **选择理由**

  OpenAI Agents SDK       MVP 主选                适合应用自主管理 orchestration、tool execution、approval 和
                                                  state；支持 guardrails、human review 和 tracing。

  LangGraph               V2/V3 备选              适合长流程、复杂状态、失败恢复、多 agent handoff 和长期 job
                                                  tracker。

  自定义 FastAPI workflow 基础兜底                核心业务逻辑可以先用函数和数据库状态实现，避免过早复杂化。
  ----------------------- ----------------------- ------------------------------------------------------------

# 7. 最终技术架构方案

## 7.1 推荐架构总览

Frontend: Next.js 16 + React 19 + TypeScript\
- Tailwind CSS + shadcn/ui\
- Vercel AI SDK for streaming AI UI and tool-call-aware states\
- TanStack Query for API state\
- Zod for client-side schema validation\
\
Backend: FastAPI + Python 3.12/3.13\
- Pydantic v2 for structured outputs and validation\
- SQLAlchemy 2 + Alembic for data models and migrations\
- Celery/RQ + Redis for async parsing, embedding, and batch matching\
\
Agent Layer:\
- OpenAI Agents SDK as MVP orchestrator\
- LangGraph evaluated for V2 long-running workflows\
- Guardrails, human approval, tracing, model/provider abstraction\
\
Data Layer:\
- PostgreSQL as primary database\
- pgvector for embeddings\
- S3-compatible object storage for resumes, exports, and logs\
\
Document Layer:\
- Docling or Unstructured as robust parser\
- PyMuPDF and python-docx as fallback\
- Template-based DOCX/PDF resume rendering\
\
Observability:\
- agent_runs table, structured logs, token/cost tracking\
- OpenAI tracing or LangSmith/OpenTelemetry-style tracing

## 7.2 技术栈清单

  ----------------------- ----------------------- ------------------------------------------------
  **层级**                **最终推荐技术**        **说明**

  Frontend                Next.js 16 + React 19 + 现代 AI SaaS 前端，便于构建 dashboard
                          TypeScript              和复杂交互。

  UI                      Tailwind CSS +          快速构建专业、统一、可维护的界面组件。
                          shadcn/ui               

  AI UI                   Vercel AI SDK           支持流式输出、tool calling UI 状态、provider
                                                  abstraction。

  Backend                 FastAPI + Python        适合 AI 后端、文件解析、算法和异步任务。
                          3.12/3.13               

  Validation              Pydantic v2 + Zod       前后端 schema 验证，减少 LLM JSON 输出错误。

  ORM                     SQLAlchemy 2 + Alembic  稳定数据库建模和迁移。

  Database                PostgreSQL + pgvector   关系数据 + embedding similarity
                                                  在一个数据库中完成。

  Queue                   Redis + Celery/RQ       处理文档解析、embedding
                                                  生成、批量匹配等耗时任务。

  Agent                   OpenAI Agents SDK       MVP agent
                                                  orchestration、tools、guardrails、human
                                                  review、tracing。

  Alternative Agent       LangGraph               V2 长流程、多状态、多 agent 工作流。

  LLM                     OpenAI API + optional   OpenAI 作为主模型，Gemini 作为备选 provider。
                          Gemini                  

  Local Mode              Ollama optional         开发测试或隐私模式可选，不作为 MVP 必须项。

  Document Parsing        Docling / Unstructured  更稳健处理 PDF/DOCX、表格、阅读顺序、OCR。

  Fallback Parsing        PyMuPDF / python-docx   轻量、快速、低成本备用方案。

  Web Extraction V2       Firecrawl optional      用于岗位网页转 Markdown/structured
                                                  JD，不用于绕过平台限制。

  Export                  DOCX template + PDF     从结构化 resume JSON 生成 ATS-readable 简历。
                          renderer                

  Observability           OpenAI tracing /        调试 agent、监控质量、记录成本和失败原因。
                          LangSmith / structured  
                          logs                    

  Deployment              Vercel +                前端与后端分离，数据库托管，适合个人项目上线。
                          Render/Fly/Railway +    
                          Neon/Supabase           
  ----------------------- ----------------------- ------------------------------------------------

## 7.3 组件边界

-   Frontend 不直接调用 LLM API，所有 AI 调用从后端发起，以保护 API key
    和统一审计。

-   Backend 暴露 REST/streaming API：upload resume、parse status、match
    JD、generate suggestions、approve changes、export version。

-   Agent layer 不直接写数据库；通过 service layer
    写入，保证数据验证和权限控制。

-   Document processing 可以异步执行，上传后返回
    job_id，前端显示解析进度。

-   Embedding 只在简历事实块和 JD 块更新时重新生成，避免重复成本。

# 8. 数据模型与 Verified Facts Store

Verified Facts Store
是本项目的核心专业设计。它将简历中的每条可验证事实保存为结构化对象，所有
AI 改写建议必须引用事实来源。这样可以降低 hallucination
风险，并让用户知道 AI 为什么这么改。

## 8.1 核心数据库表

  ----------------------- ------------------------ ---------------------------
  **表名**                **核心字段**             **用途**

  users                   id, email, name,         用户基础信息。
                          created_at               

  resumes                 id, user_id, file_url,   原始简历文件和解析文本。
                          raw_text,                
                          parser_version,          
                          created_at               

  resume_blocks           id, resume_id,           文档解析后的章节/文本块。
                          section_type, text,      
                          page, order_index,       
                          layout_meta              

  candidate_profiles      id, user_id, resume_id,  结构化候选人画像。
                          profile_json,            
                          confidence_json          

  verified_facts          id, user_id, resume_id,  可追溯事实库。
                          fact_type, section,      
                          text, source_block_id,   
                          verified_by_user,        
                          confidence               

  jobs                    id, user_id, title,      导入或保存的岗位。
                          company, source, url,    
                          raw_description,         
                          parsed_job_json          

  matches                 id, user_id, resume_id,  岗位---简历匹配结果。
                          job_id, final_score,     
                          component_scores_json,   
                          explanation_json         

  suggestions             id, resume_id, job_id,   AI 修改建议和审批状态。
                          original_text,           
                          suggested_text,          
                          source_fact_ids,         
                          risk_level, status       

  resume_versions         id, user_id,             已保存简历版本。
                          base_resume_id,          
                          version_name,            
                          target_role,             
                          content_json,            
                          change_log_json          

  agent_runs              id, user_id, run_type,   Agent 调用和可观测性记录。
                          model, status, trace_id, 
                          token_usage, cost,       
                          latency_ms,              
                          error_summary            
  ----------------------- ------------------------ ---------------------------

## 8.2 Verified Fact JSON 示例

{\
\"fact_id\": \"proj_001_bullet_02\",\
\"source\": \"resume\",\
\"section\": \"Projects\",\
\"fact_type\": \"project_experience\",\
\"text\": \"Built a FastAPI backend for an AI health assistant
integrating Gemini API.\",\
\"source_block_id\": \"block_034\",\
\"verified_by_user\": true,\
\"confidence\": 0.92\
}

## 8.3 Suggestion JSON 示例

{\
\"suggestion_id\": \"sug_128\",\
\"original_text\": \"Built backend APIs for a health assistant app.\",\
\"suggested_text\": \"Developed FastAPI backend services for an
AI-powered health assistant, integrating Gemini API with medication
reminder and health log workflows.\",\
\"source_fact_ids\": \[\"proj_001_bullet_02\"\],\
\"target_job_id\": \"job_078\",\
\"reason\": \"Makes API design, AI integration, and product workflow
explicit for AI software roles.\",\
\"risk_level\": \"low\",\
\"requires_user_confirmation\": false,\
\"status\": \"pending_review\"\
}

## 8.4 数据原则

-   原始文件、解析文本、结构化画像、事实库和简历版本分层存储。

-   AI 建议不直接覆盖原始简历，只创建 pending suggestions。

-   用户接受建议后才生成新版本。

-   每个版本都必须保存 change log、目标岗位、关联 JD 和
    source_fact_ids。

-   用户可以删除文件和账号数据；删除时需要清理对象存储和数据库记录。

# 9. 匹配评分与推荐算法

匹配系统不能让 LLM 直接"拍脑袋打分"。最终版采用多阶段 hybrid
scoring：硬性过滤、特征抽取、规则和 embedding 评分、LLM
证据解释、人工数据校准。

## 9.1 Scoring Pipeline

Stage 1: Hard Filters\
- role type mismatch: internship vs full-time\
- seniority mismatch: entry-level vs 5+ years\
- location / remote mismatch\
- required degree or graduation window mismatch\
\
Stage 2: Structured Feature Extraction\
- required_skills, preferred_skills, tools, frameworks\
- responsibilities, domain keywords, seniority signals\
- education, work authorization, language requirements\
\
Stage 3: Hybrid Scoring\
- exact skill keyword coverage\
- normalized skill taxonomy match\
- embedding similarity between JD blocks and resume facts\
- project-to-responsibility relevance\
- education and role-fit rules\
\
Stage 4: Evidence Reasoning\
- LLM explains matched evidence and missing requirements\
- LLM cannot override hard filters or fabricate facts\
\
Stage 5: Calibration\
- compare scores with human labels\
- adjust weights per target role

## 9.2 初始权重设计

  ----------------------- ----------------------- --------------------------------------------------
  **评分项**              **权重**                **说明**

  Skill Keyword Coverage  25%                     JD required/preferred skills
                                                  与简历技能、项目、经历中的技能覆盖。

  Semantic Similarity     20%                     使用 embeddings 比较 JD
                                                  职责与简历事实块的语义相似度。

  Experience Relevance    18%                     实习/工作经历是否能支撑岗位职责。

  Project Relevance       17%                     项目是否体现岗位需要的技术、复杂度和领域相关性。

  Education & Course Fit  10%                     专业、课程、学历、毕业时间与岗位要求是否匹配。

  Career Goal /           10%                     目标方向、地点、岗位类型与用户偏好是否一致。
  Preference Fit                                  
  ----------------------- ----------------------- --------------------------------------------------

## 9.3 输出格式

{\
\"final_score\": 82,\
\"confidence\": \"medium-high\",\
\"component_scores\": {\
\"skill_keyword_coverage\": 86,\
\"semantic_similarity\": 80,\
\"experience_relevance\": 76,\
\"project_relevance\": 88,\
\"education_fit\": 84,\
\"preference_fit\": 75\
},\
\"matched_evidence\": \[\
{\"requirement\": \"Python\", \"source_fact_id\": \"skill_004\"},\
{\"requirement\": \"FastAPI\", \"source_fact_id\":
\"proj_001_bullet_02\"}\
\],\
\"missing_requirements\": \[\"Docker\", \"AWS\", \"model
evaluation\"\],\
\"recommended_action\": \"Apply after tailoring project bullets\",\
\"resume_sections_to_improve\": \[\"Projects\", \"Skills\"\]\
}

# 10. 文档解析与简历渲染引擎

## 10.1 Document Ingestion Layer

简历 PDF
经常存在双栏、表格、图标、非线性阅读顺序和字体问题。最终版不只使用
PyMuPDF/python-docx，而是引入 Document Ingestion Layer：优先使用 Docling
或 Unstructured 进行结构化解析，必要时使用 PyMuPDF/python-docx 作为轻量
fallback。

  ----------------------- ------------------------------------------ ----------------------------------------
  **组件**                **职责**                                   **MVP 使用方式**

  Docling / Unstructured  将 PDF/DOCX 转换为                         优先方案，用于提高复杂简历解析稳定性。
                          Markdown、结构化块、阅读顺序和表格信息。   

  PyMuPDF                 快速读取普通 PDF 文本。                    fallback 或开发阶段使用。

  python-docx             读取 DOCX 段落和表格。                     DOCX fallback。

  OCR optional            处理扫描版或图片型简历。                   MVP 可提示用户上传可选中文本 PDF，OCR 放
                                                                     V2。
  ----------------------- ------------------------------------------ ----------------------------------------

## 10.2 Resume Rendering Engine

CareerGraph AI 不应只给文字建议，还需要能将已审批内容输出为 ATS-readable
简历。最终版加入 Resume Rendering Engine：以 resume JSON
为单一事实来源，通过模板生成 DOCX，再转为 PDF。

Resume JSON\
-\> template selection\
-\> section ordering\
-\> bullet rendering\
-\> DOCX generation\
-\> PDF export\
-\> ATS readability check\
-\> version record saved

-   支持 Base Resume、AI Intern Resume、Data Analyst Resume、SWE Intern
    Resume 等版本。

-   每个版本保存模板、目标岗位、修改记录和关联 JD。

-   导出结果应避免图片化文本、过度图标、复杂表格和不可读排版。

-   模板优先保证 ATS 可读性，其次才是视觉设计。

# 11. 安全、合规、隐私与质量控制

## 11.1 Guardrails

  ----------------------------------- -----------------------------------------------------------------------
  **风险**                            **控制措施**

  简历内容 hallucination              所有建议必须引用
                                      source_fact_ids；高风险建议必须要求用户确认；禁止自动添加不存在技能。

  错误匹配分数误导用户                匹配分数解释为 JD 覆盖度和相似度，不承诺面试概率。

  敏感个人信息泄露                    文件私有存储；API key
                                      后端保存；日志不记录完整简历原文；用户可删除数据。

  平台规则风险                        MVP 不自动爬取 LinkedIn，不自动投递，不绕过验证码或登录限制。

  AI 建议质量不稳定                   引入 schema validation、fact grounding、用户审批、rewrite acceptance
                                      rate 评估。

  成本失控                            缓存解析结果和 embeddings；小模型用于抽取，大模型用于最终改写；记录
                                      token 成本。
  ----------------------------------- -----------------------------------------------------------------------

## 11.2 Human-in-the-loop 审批

所有可能改变简历内容的 AI 输出都必须进入 pending 状态。用户可以
Accept、Edit、Reject 或
Regenerate。只有被用户接受或编辑确认后的内容才能进入 resume version。

Suggestion states:\
pending_review -\> accepted -\> included_in_version\
pending_review -\> edited -\> accepted -\> included_in_version\
pending_review -\> rejected -\> archived\
pending_review -\> regenerate_requested -\> pending_review

## 11.3 隐私与数据最小化

-   只收集完成产品功能所需的数据。

-   LLM 日志中默认不保存完整简历原文，只保存摘要、hash、run metadata。

-   用户可删除原始文件、解析结果、版本和岗位记录。

-   开发环境使用 mock resumes 和公开
    JD，不使用真实用户隐私数据进行调试。

-   若未来做多人使用，应增加认证、访问控制、加密存储和隐私政策。

# 12. 可观测性、评估体系与成本控制

## 12.1 Agent Observability

  ----------------------------------- --------------------------------------------------------------------------------
  **指标/日志**                       **说明**

  agent_runs                          记录
                                      run_type、model、status、trace_id、token_usage、latency、cost、error_summary。

  tool_calls                          记录每次 tool 输入输出摘要、耗时和失败原因。

  parsing_errors                      记录文档解析失败、章节识别失败、低置信度字段。

  suggestion_outcomes                 记录用户接受、编辑、拒绝、重新生成比例。

  match_feedback                      记录用户认为匹配结果是否准确，用于后续校准。

  cost dashboard                      按用户、run type、模型统计 token 和成本。
  ----------------------------------- --------------------------------------------------------------------------------

## 12.2 Evaluation Dataset

为了让项目超过普通 demo 水平，应在开发阶段构建小型评估集。

  ----------------- ----------------- ---------------------------------------------- ------------------------------------
  **评估对象**      **建议规模**      **标注方式**                                   **指标**

  简历解析          30 份简历         人工检查教育、经历、技能、项目抽取是否正确。   字段准确率、遗漏率、低置信度比例。

  JD 解析           100 个岗位描述    人工检查 required/preferred                    解析准确率、JSON validation pass
                                      skills、职责、学历等字段。                     rate。

  匹配评分          300 个 resume-JD  人工标注 low/medium/high fit。                 分类准确率、排序相关性、false
                    pairs                                                            positive/negative。

  改写建议          100 条 bullet     人工标注 accept/edit/reject 和是否             接受率、编辑率、hallucination
                    rewrite           hallucination。                                violation rate。

  端到端体验        10 个真实用户任务 观察上传、匹配、改写、导出完成情况。           任务成功率、耗时、用户满意度。
  ----------------- ----------------- ---------------------------------------------- ------------------------------------

## 12.3 成本控制策略

-   缓存 parsed resume、parsed JD、embeddings 和 match result。

-   使用较小模型做结构化抽取，用较强模型做最终改写和复杂 reasoning。

-   批量生成 embeddings，避免同一事实块重复 embedding。

-   对长 JD 和长简历先分块摘要，再进入匹配流程。

-   设置每个用户每日分析次数和 token 预算。

-   在 agent_runs 中记录每次调用成本，为后续优化模型选择提供依据。

# 13. 开发计划与里程碑

  ----------------- ----------------- -------------------------------------- ----------------------------
  **阶段**          **时间**          **主要任务**                           **交付物**

  Phase 0: 项目准备 第 1 周           确定技术栈、初始化 repo、设计数据库    GitHub repo、README
                                      schema、准备 mock                      初版、数据库迁移、设计稿。
                                      resumes/JDs、建立基础 UI。             

  Phase 1: Resume   第 2-3 周         实现上传、文档解析、candidate          上传流程、profile
  Parsing & Profile                   profile、verified                      页面、facts 数据表。
                                      facts、解析结果编辑。                  

  Phase 2: Resume   第 4 周           实现简历评分、top issues、role fit     评分 dashboard、诊断报告。
  Diagnostic                          explorer 初版。                        

  Phase 3: JD       第 5-6 周         实现 JD 粘贴、岗位解析、hybrid         JD import、match result
  Parsing &                           scoring、匹配解释。                    页面。
  Matching                                                                   

  Phase 4:          第 7-8 周         实现基于 facts                         Tailor Resume
  Tailoring & HITL                    的改写建议、审批流程、suggestion       页面、审批卡片。
                                      状态机。                               

  Phase 5:          第 9 周           实现 resume version manager、change    多版本简历、导出文件。
  Versioning &                        log、DOCX/PDF 导出。                   
  Export                                                                     

  Phase 6: Roadmap  第 10 周          实现 roadmap agent、评估集、质量指标   Roadmap 页面、评估报告。
  & Evaluation                        dashboard。                            

  Phase 7: Polish & 第 11-12 周       UI                                     可访问
  Deployment                          打磨、错误处理、隐私控制、部署、demo   demo、最终文档、演示视频。
                                      数据、最终 README。                    
  ----------------- ----------------- -------------------------------------- ----------------------------

## 13.1 MVP 任务拆分

-   Backend：FastAPI 项目结构、Auth
    mock、文件上传、对象存储、本地开发环境。

-   Database：users、resumes、resume_blocks、verified_facts、jobs、matches、suggestions、resume_versions、agent_runs。

-   Document：Docling/Unstructured 集成、fallback parser、section
    classifier。

-   LLM：Pydantic schemas、prompt templates、structured output
    validation、retry strategy。

-   Matching：skill taxonomy、embedding service、score
    weights、explanation generator。

-   Frontend：upload page、profile page、diagnostic page、JD match
    page、tailoring page、version page。

-   Export：resume JSON to DOCX/PDF，模板至少 1 个 ATS-friendly 版本。

-   QA：mock data、unit tests、integration tests、manual evaluation
    sheet。

# 14. 验收标准与成功指标

## 14.1 MVP 验收标准

  ----------------------------------- --------------------------------------------------------------
  **类别**                            **验收标准**

  功能完整性                          用户可以上传简历、生成 profile、粘贴
                                      JD、获得匹配分数、查看修改建议、审批建议、生成新版本并导出。

  事实约束                            100% 简历改写建议包含 source_fact_ids；无来源建议必须标记为
                                      needs_user_confirmation。

  解析质量                            普通单栏/双栏 PDF 和 DOCX
                                      至少能抽取主要章节、技能、教育、经历、项目。

  匹配解释                            每个匹配结果必须包含 matched evidence、missing
                                      requirements、recommended action。

  用户控制                            AI 不自动覆盖简历；所有修改都由用户 accept/edit/reject。

  性能                                普通简历解析和诊断在 60 秒内完成；单个 JD 匹配在 30 秒内完成。

  可观测性                            每次 agent run 记录 token、模型、耗时、状态和错误摘要。

  导出                                至少支持一个 ATS-friendly DOCX/PDF
                                      模板，导出内容与用户审批版本一致。
  ----------------------------------- --------------------------------------------------------------

## 14.2 成功指标

  ----------------------------------- -----------------------------------
  **指标**                            **目标值**

  JSON schema validation pass rate    \>= 95%

  Resume parsing critical field       \>= 85%
  accuracy                            

  JD parsing critical field accuracy  \>= 85%

  Rewrite hallucination violation     \<= 2%
  rate                                

  User suggestion acceptance/edit     \>= 60% accepted or edited
  rate                                

  Match explanation usefulness rating \>= 4/5 in pilot feedback

  End-to-end MVP task success rate    \>= 90% for supported file types

  Average cost per full analysis      tracked and optimized; target below
                                      project budget threshold
  ----------------------------------- -----------------------------------

# 15. 风险分析与应对策略

  ----------------------- ------------------------ -----------------------------------------------------
  **风险**                **影响**                 **应对策略**

  复杂 PDF 解析失败       无法建立准确画像和       使用 Docling/Unstructured；提供手动编辑
                          facts。                  profile；低置信度字段提示用户确认。

  LLM 输出 JSON 不稳定    后端处理失败。           使用 Pydantic/Zod schema、retry、repair
                                                   prompt、字段默认值和错误提示。

  AI 改写编造经历         严重影响用户信任。       Verified Facts Store、source_fact_ids、risk
                                                   level、人工审批、hallucination eval。

  匹配分数不准            误导用户投递方向。       使用 hard
                                                   filters、可解释权重、人工标注评估集和用户反馈校准。

  范围膨胀                项目无法按期完成。       MVP 只做粘贴 JD，不做自动投递；岗位发现、Chrome
                                                   extension、autofill 放 V2/V3。

  API 成本过高            项目难以持续使用。       缓存、模型分层、token budget、成本
                                                   dashboard、local/Ollama optional。

  隐私风险                用户简历包含敏感信息。   最小化日志、删除功能、对象存储权限、API key
                                                   后端管理。

  部署复杂                影响 demo 可用性。       前端 Vercel，后端 Render/Fly/Railway，数据库
                                                   Neon/Supabase；本地 Docker Compose 兜底。
  ----------------------- ------------------------ -----------------------------------------------------

# 16. README、作品集与简历呈现方式

## 16.1 README 描述

CareerGraph AI is an evidence-grounded, human-in-the-loop resume
intelligence platform.\
It converts resumes into structured candidate profiles, evaluates resume
quality across career tracks, matches resumes with job descriptions
using a hybrid scoring engine, and generates source-grounded resume
improvements for each target role.\
\
The system combines document parsing, verified fact extraction,
embeddings, rule-based scoring, LLM reasoning, human approval, resume
version management, and ATS-readable export.

## 16.2 简历项目 bullet 示例

Built CareerGraph AI, an AI-native resume intelligence platform that
parses PDF/DOCX resumes into structured candidate profiles and verified
fact stores, enabling evidence-grounded resume rewriting without
hallucinated qualifications.\
\
Implemented a hybrid job-resume matching engine combining rule-based
filters, skill taxonomy matching, embedding similarity, and LLM-based
evidence reasoning to rank job fit and explain missing requirements.\
\
Designed a human-in-the-loop resume tailoring workflow with suggestion
approval states, source fact citations, versioned resume outputs, and
ATS-readable DOCX/PDF export.\
\
Developed observability and evaluation components for agent runs,
tracking token usage, latency, parsing errors, rewrite acceptance rates,
and hallucination violation metrics.

## 16.3 Demo 展示重点

-   上传一份基础简历，展示系统如何解析 profile 和 verified facts。

-   粘贴一个 AI Intern 或 Data Analyst JD，展示结构化 JD 和匹配结果。

-   展示 matched evidence、missing requirements 和 recommended resume
    actions。

-   展示 AI 改写建议如何引用 source_fact_id，并由用户审批。

-   接受若干建议后生成新 resume version，并导出 DOCX/PDF。

-   展示 agent_runs dashboard，体现工程可观测性。

# 17. 参考资源

以下资源用于确定最终版计划书中的产品边界、竞品借鉴和技术架构方向。

  ----------------- ----------------- ----------------------------------------- ------------------------------------------------------------------
  **编号**          **资源**          **用途**                                  **链接**

  R1                Resume Matcher    开源 AI 简历匹配与 JD 定制项目。          https://github.com/srbhr/Resume-Matcher

  R2                OpenResume        开源 resume builder 与 resume             https://github.com/xitanggg/open-resume
                                      parser，强调 ATS 可读性。                 

  R3                Teal              商业化 resume builder、job tracker        https://www.tealhq.com/
                                      与岗位匹配产品。                          

  R4                Simplify Copilot  自动填表、tailored resume/cover letter 和 https://simplify.jobs/copilot
                                      job tracker 产品。                        

  R5                OpenAI Agents SDK Agent                                     https://developers.openai.com/api/docs/guides/agents
                                      orchestration、tools、guardrails、human   
                                      review 和 tracing 参考。                  

  R6                OpenAI Agents SDK Human-in-the-loop approval 工作流参考。   https://openai.github.io/openai-agents-python/human_in_the_loop/
                    HITL                                                        

  R7                LangGraph         Long-running, stateful agent workflow     https://docs.langchain.com/oss/python/langgraph/overview
                                      参考。                                    

  R8                Vercel AI SDK     AI UI、streaming、tool calling 和         https://ai-sdk.dev/docs/introduction
                                      provider abstraction 参考。               

  R9                Docling           复杂文档解析和结构化文档转换参考。        https://www.docling.ai/

  R10               Unstructured      AI-ready 文档解析、chunking 和 enrichment https://unstructured.io/
                                      参考。                                    

  R11               Firecrawl         V2 岗位网页提取和 AI agent web context    https://www.firecrawl.dev/
                                      参考。                                    
  ----------------- ----------------- ----------------------------------------- ------------------------------------------------------------------

  -----------------------------------------------------------------------
  **最终结论**\
  CareerGraph AI 的最终版计划不应被描述为"AI
  简历打分器"。更准确的描述是：一个以 verified facts 为基础、由
  human-in-the-loop 控制、支持多版本简历和岗位匹配闭环的 AI Resume
  Intelligence Platform。

  -----------------------------------------------------------------------

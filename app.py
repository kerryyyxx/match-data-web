import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import chardet

# 页面配置
st.set_page_config(
    page_title="高级数据对齐大师",
    page_icon="⚡",
    layout="wide"  # 宽屏模式
)

# ===== 侧边栏：大白话说明书 =====
with st.sidebar:
    st.header("⚡ 快捷工具箱")

    with st.container(border=True):
        st.markdown("### 💡 本版视觉优化")
        st.markdown("""
        - 🟠 **橙色** 代表你的**数据库/总表**
        - 🔵 **蓝色** 代表你的**待补全列表**
        - 增加了卡片式布局，界面更清爽
        """)

    st.markdown("---")
    if st.button("🔄 彻底重置并清空缓存", use_container_width=True, type="secondary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# 初始化session state
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'large_df' not in st.session_state:
    st.session_state.large_df = None
if 'small_df' not in st.session_state:
    st.session_state.small_df = None
if 'match_results' not in st.session_state:
    st.session_state.match_results = None
if 'pending_matches' not in st.session_state:
    st.session_state.pending_matches = []
if 'current_match_index' not in st.session_state:
    st.session_state.current_match_index = 0


def detect_encoding(file):
    raw = file.read(10000)
    file.seek(0)
    result = chardet.detect(raw)
    return result['encoding'] or 'utf-8'


def read_file_with_encoding(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            encoding = detect_encoding(uploaded_file)
            try:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding=encoding)
            except:
                for enc in ['utf-8', 'gbk', 'gb2312', 'latin1']:
                    try:
                        uploaded_file.seek(0)
                        df = pd.read_csv(uploaded_file, encoding=enc)
                        break
                    except:
                        continue
        else:
            df = pd.read_excel(uploaded_file)
        return df
    except Exception as e:
        st.error(f"文件读取失败：{str(e)}")
        return None


# ===== 顶部全局步骤条 =====
st.title("⚡ 高级数据匹配与多列搬运工具")

step_cols = st.columns(3)
with step_cols[0]:
    st.markdown("### :orange[1. 上传文件]" if st.session_state.step == 1 else "### 1. 上传文件")
    st.progress(1.0 if st.session_state.step >= 1 else 0.0)
with step_cols[1]:
    st.markdown("### :blue[2. 对齐规则]" if st.session_state.step == 2 else "### 2. 对齐规则")
    st.progress(1.0 if st.session_state.step >= 2 else 0.0)
with step_cols[2]:
    st.markdown("### :green[3. 核对与下载]" if st.session_state.step == 3 else "### 3. 核对与下载")
    st.progress(1.0 if st.session_state.step >= 3 else 0.0)

st.markdown("---")

# ===== 步骤1：上传文件 =====
if st.session_state.step == 1:
    st.markdown("### 📁 第一步：把你的两个表格传上来")
    st.caption("支持 Excel (.xlsx) 和 CSV (.csv) 格式。文件只会留在你的浏览器本地处理，安全保密。")
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("#### 🟠 1号大文件（数据总数据库）")
            st.markdown("信息最全的底表，我们要从这里**查数据**并搬运你想要的部分。")
            large_file = st.file_uploader("点击或拖拽上传总表", type=['xlsx', 'csv'], key='large_uploader',
                                          label_visibility="collapsed")
            if large_file:
                df = read_file_with_encoding(large_file)
                if df is not None:
                    st.session_state.large_df = df
                    st.metric(label="成功加载总表行数", value=f"{len(df)} 行")
                    with st.expander("🔍 预览前5行数据内容"):
                        st.dataframe(df.head(5), use_container_width=True)

    with col2:
        with st.container(border=True):
            st.markdown("#### 🔵 2号小文件（待查询/待补全列表）")
            st.markdown("你想更新的目标表，我们要往这里**填入新列**。")
            small_file = st.file_uploader("点击或拖拽上传目标表", type=['xlsx', 'csv'], key='small_uploader',
                                          label_visibility="collapsed")
            if small_file:
                df = read_file_with_encoding(small_file)
                if df is not None:
                    st.session_state.small_df = df
                    st.metric(label="成功加载目标表行数", value=f"{len(df)} 行")
                    with st.expander("🔍 预览前5行数据内容"):
                        st.dataframe(df.head(5), use_container_width=True)

    if st.session_state.large_df is not None and st.session_state.small_df is not None:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("进入下一步：设置对齐规则 ➔", use_container_width=True, type="primary"):
            st.session_state.step = 2
            st.rerun()

# ===== 步骤2：设置匹配规则 =====
if st.session_state.step == 2:
    st.markdown("### ⚙️ 第二步：连线思考，告诉工具怎么对齐")
    st.caption("就像Excel里的VLOOKUP一样，我们需要指定两张表靠什么字段连接，以及要搬运什么过去。")
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("#### 🟠 建立连接纽带")
            large_key = st.selectbox(
                "👉 拿 1号大文件 里的哪一列去和对方比对？",
                st.session_state.large_df.columns.tolist(),
                help="通常是唯一标识，比如姓名、工号、身份证、手机号等"
            )
            small_key = st.selectbox(
                "👉 对应 2号小文件 里的哪一列？",
                st.session_state.small_df.columns.tolist(),
                help="两张表用来比对的这一列内容格式最好一致"
            )

    with col2:
        with st.container(border=True):
            st.markdown("#### 🎒🎅选择要搬运的内容")
            large_results = st.multiselect(
                "👉 你想从 1号大文件 里把哪几列的数据抓过来？",
                st.session_state.large_df.columns.tolist(),
                default=[st.session_state.large_df.columns.tolist()[1]] if len(
                    st.session_state.large_df.columns) > 1 else None,
                help="你可以勾选一个或者很多个列，它们未来会变成小文件里的新列"
            )

    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("#### 🛠️ 细节强迫症选项（默认开启，一般不用动）")
        c1, c2 = st.columns(2)
        with c1:
            strip_spaces = st.checkbox("🧼 自动去除单元格前后的空格", value=True,
                                       help="防止因为‘张三 ’多了一个看不见的空格而匹配不上")
        with c2:
            ignore_case = st.checkbox("🔤 忽略英文字母大小写", value=False, help="让 ZHANGSAN 和 zhangsan 算同一个人")

    st.markdown("---")

    if not large_results:
        st.warning("⚠️ 别忘了：你必须至少选择一个想抓过来的结果列，否则没法干活哦。")
    else:
        if st.button("开始执行全量比对 🚀", type="primary", use_container_width=True):
            st.session_state.step = 3
            st.session_state.match_params = {
                'large_key': large_key,
                'large_results': large_results,
                'small_key': small_key,
                'strip_spaces': strip_spaces,
                'ignore_case': ignore_case
            }
            st.session_state.match_results = None
            st.rerun()

    if st.button("← 返回上一步修改上传的文件", use_container_width=True, type="secondary"):
        st.session_state.step = 1
        st.rerun()

# ===== 步骤3：执行匹配与人工核对 =====
if st.session_state.step == 3:
    st.markdown("### 🔄 第三步：数据碰撞与智能核对")

    # 首次进入，后台静默计算
    if st.session_state.match_results is None:
        # 使用现代化 st.status 组件展现底层逻辑
        with st.status("🚀 引擎启动，正在进行深度交叉比对...", expanded=True) as status:
            params = st.session_state.match_params
            large_df = st.session_state.large_df.copy()
            small_df = st.session_state.small_df.copy()


            def clean_text(x):
                if pd.isna(x): return x
                x = str(x)
                if params['strip_spaces']: x = x.strip()
                if params['ignore_case']: x = x.lower()
                return x


            st.write("🧼 正在洗涤两边的数据主键（去空格/转大小写）...")
            large_df['_key_clean'] = large_df[params['large_key']].apply(clean_text)
            small_df['_key_clean'] = small_df[params['small_key']].apply(clean_text)

            matches = []
            pending = []
            total = len(small_df)

            st.write("🧩 正在挨个扫描数据进行拼图对齐...")
            for idx, row in small_df.iterrows():
                clean_key = row['_key_clean']
                matched_rows = large_df[large_df['_key_clean'] == clean_key]

                if len(matched_rows) == 0:
                    matches.append({'index': idx, 'status': 'not_found', 'data': None})
                elif len(matched_rows) == 1:
                    res_data = matched_rows.iloc[0][params['large_results']].to_dict()
                    matches.append({'index': idx, 'status': 'matched', 'data': res_data})
                else:
                    candidates = []
                    for _, cand_row in matched_rows.iterrows():
                        candidates.append({
                            'all_data': cand_row.to_dict(),
                            'extract_data': cand_row[params['large_results']].to_dict()
                        })
                    pending.append({
                        'index': idx,
                        'name': row[params['small_key']],
                        'candidates': candidates
                    })
                    matches.append({'index': idx, 'status': 'pending', 'data': None})

            st.session_state.match_results = matches
            st.session_state.pending_matches = pending
            st.session_state.current_match_index = 0
            status.update(label="✨ 比对计算全部完成！", state="complete")
            st.rerun()

    # 如果有重名，卡片式弹窗核对
    if st.session_state.pending_matches:
        current_idx = st.session_state.current_match_index
        total_pending = len(st.session_state.pending_matches)
        current_task = st.session_state.pending_matches[current_idx]

        st.markdown(f"#### ⚠️ 抓到重名数据！请帮人工甄别")
        st.info(
            f"在总表里找到了多个叫 **{current_task['name']}** 的记录。目前处理第 {current_idx + 1} / {total_pending} 个重名。")

        with st.container(border=True):
            st.markdown(f"### 🔍 待确认的查询名字：:red[{current_task['name']}]")
            st.markdown("**下面是系统在 1号大文件 里翻出来的这几个人，请根据他们的其他特征选出正确的一位：**")

            options = []
            for i, cand in enumerate(current_task['candidates']):
                info_summary = " | ".join(
                    [f"【{k}】{v}" for k, v in cand['all_data'].items() if k != '_key_clean' and pd.notna(v)])
                options.append(f"选项 {i + 1} ➔ {info_summary}")

            choice = st.radio("请点选正确的那一行：", options, index=0)
            choice_idx = options.index(choice)

            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("确认此人，继续 ➔", use_container_width=True, type="primary"):
                    target_idx = current_task['index']
                    selected_data = current_task['candidates'][choice_idx]['extract_data']
                    for m in st.session_state.match_results:
                        if m['index'] == target_idx:
                            m['status'] = 'matched'
                            m['data'] = selected_data
                            break

                    if current_idx + 1 < total_pending:
                        st.session_state.current_match_index += 1
                    else:
                        st.session_state.pending_matches = []
                    st.rerun()

            with col2:
                if st.button("这个人我也不确定，先跳过 ⏭️", use_container_width=True):
                    if current_idx + 1 < total_pending:
                        st.session_state.current_match_index += 1
                    else:
                        st.session_state.pending_matches = []
                    st.rerun()

    # 全部搞定，华丽展示并提供下载
    elif st.session_state.match_results:
        st.balloons()  # 庆祝气球
        st.success("🎉 数据对齐及多列补全全部收工！")

        # 统计面板
        matched_count = len([m for m in st.session_state.match_results if m['status'] == 'matched'])
        not_found_count = len([m for m in st.session_state.match_results if m['status'] == 'not_found'])

        m_cols = st.columns(3)
        m_cols[0].metric("✨ 成功补全数据", f"{matched_count} 行")
        m_cols[1].metric("🔍 未找到匹配（留空）", f"{not_found_count} 行")
        m_cols[2].metric("📊 目标表总计", f"{len(st.session_state.match_results)} 行")

        # 还原表格
        final_df = st.session_state.small_df.copy()
        target_cols = st.session_state.match_params['large_results']

        for col in target_cols:
            final_df[col] = None

        for m in st.session_state.match_results:
            if m['status'] == 'matched' and m['data'] is not None:
                for col in target_cols:
                    final_df.at[m['index'], col] = m['data'].get(col)

        st.markdown("<br>#### 📋 新表格前 10 行效果预览")
        st.dataframe(final_df.head(10), use_container_width=True)

        # 下载卡片
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("### 📥 成果导出")
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                final_df.to_excel(writer, index=False, sheet_name='对齐补全结果')

            st.download_button(
                label="💥 点击下载完美补全后的 Excel 表格 💥",
                data=output.getvalue(),
                file_name="匹配结果_已补全.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary"
            )

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 重新做一张新表", use_container_width=True, type="secondary"):
            for key in ['step', 'match_results', 'pending_matches', 'match_params']:
                if key in st.session_state: del st.session_state[key]
            st.rerun()

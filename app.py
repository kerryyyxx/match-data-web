import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import chardet

# 页面配置
st.set_page_config(
    page_title="数据匹配工具",
    page_icon="🔍"
)

# ===== 侧边栏：大白话使用说明 =====
with st.sidebar:
    st.header("📖 使用说明（大白话版）")

    with st.expander("🎯 这工具是干啥的", expanded=True):
        st.markdown("""
        **简单说**：就是Excel里VLOOKUP功能的升级版

        比如你有：
        - 📄 **大文件**：公司所有人的信息（姓名、手机号、身份证、部门...）
        - 📄 **小文件**：今天要联系的客户名单（只有姓名）

        这工具能自动从小文件里的姓名，去大文件里找到对应的手机号填上
        """)

    with st.expander("📁 第一步：上传文件"):
        st.markdown("""
        **大文件**（数据总表）
        - 就是那个啥都有的表
        - 比如全公司人员名单

        **小文件**（待查询列表）
        - 就是你想查的那批人
        - 比如今天要打电话的客户
        """)

    with st.expander("⚙️ 第二步：告诉工具怎么查"):
        st.markdown("""
        **大文件里**：
        - 用哪一列去查？（通常是姓名、工号、身份证）
        - 想提取哪一列的结果？（通常是手机号、邮箱）

        **小文件里**：
        - 拿哪一列去问？（比如也是姓名）
        - 结果放在哪一列？（可以写个新列名）

        **高级选项**（一般不用动）：
        - 去空格：把"张 三"变成"张三"再查
        - 忽略大小写："ZHANG SAN"和"zhang san"算一样的
        """)

    with st.expander("🔄 第三步：处理同名的人"):
        st.markdown("""
        如果遇到重名的（比如两个叫张三的）：

        工具会停下来问你"选哪个？"

        它会显示这俩人其他的信息（比如身份证号、部门），
        你根据这些信息选对的那个人就行。

        选完继续往下查
        """)

    with st.expander("📥 最后：下载结果"):
        st.markdown("""
        匹配完会生成一个Excel文件：

        你的小文件里会多出一列，就是查到的结果

        没查到的人会空着
        """)

    with st.expander("⚠️ 常见问题"):
        st.markdown("""
        **Q：查出来怎么是空的？**
        - 大文件里没这个人
        - 或者名字写法不一样（比如大文件是"张三"，你写的是"张 三"）
        - 可以试试高级选项里的"去空格"

        **Q：怎么有好几个同名的人？**
        - 正常，说明大文件里确实有重名的
        - 工具会弹出来让你选，选对的就行

        **Q：支持什么格式？**
        - Excel (.xlsx)
        - CSV (.csv)

        **Q：卡住了怎么办？**
        - 关掉重新打开
        - 或者点"重新开始"
        """)

    st.markdown("---")
    st.caption("有问题随时重来，数据不会丢")

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
    """检测文件编码"""
    raw = file.read(10000)
    file.seek(0)
    result = chardet.detect(raw)
    return result['encoding'] or 'utf-8'


def read_file_with_encoding(uploaded_file):
    """读取上传的文件（自动处理编码）"""
    try:
        if uploaded_file.name.endswith('.csv'):
            encoding = detect_encoding(uploaded_file)
            try:
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


# 页面标题
st.title("🔍 数据匹配工具")
st.markdown("---")

# 步骤1：上传文件
if st.session_state.step == 1:
    st.header("📁 步骤1：上传文件")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("大文件（数据总表）")
        large_file = st.file_uploader("上传包含完整信息的文件", type=['xlsx', 'csv'], key='large_uploader')
        if large_file:
            df = read_file_with_encoding(large_file)
            if df is not None:
                st.session_state.large_df = df
                st.success(f"已加载：{len(df)}行，{len(df.columns)}列")
                with st.expander("预览"):
                    st.dataframe(df.head(5), use_container_width=True)

    with col2:
        st.subheader("小文件（待查询列表）")
        small_file = st.file_uploader("上传需要查询的文件", type=['xlsx', 'csv'], key='small_uploader')
        if small_file:
            df = read_file_with_encoding(small_file)
            if df is not None:
                st.session_state.small_df = df
                st.success(f"已加载：{len(df)}行，{len(df.columns)}列")
                with st.expander("预览"):
                    st.dataframe(df.head(5), use_container_width=True)

    if st.session_state.large_df is not None and st.session_state.small_df is not None:
        st.markdown("---")
        if st.button("下一步 ➡️", use_container_width=True):
            st.session_state.step = 2
            st.rerun()

# 步骤2：设置匹配规则
if st.session_state.step == 2:
    st.header("⚙️ 步骤2：设置匹配规则")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("大文件")
        large_key = st.selectbox(
            "用哪一列去匹配？（比如姓名、工号、身份证）",
            st.session_state.large_df.columns.tolist(),
            key="large_key"
        )
        large_result = st.selectbox(
            "要提取哪一列的数据？（比如手机号、邮箱）",
            st.session_state.large_df.columns.tolist(),
            key="large_result"
        )

    with col2:
        st.subheader("小文件")
        small_key = st.selectbox(
            "用哪一列作为查询条件？（比如也是姓名）",
            st.session_state.small_df.columns.tolist(),
            key="small_key"
        )

        # 结果存放位置
        result_col_name = st.text_input(
            "结果存放在哪一列？",
            value="匹配结果",
            help="输入新列名，或选择已有列名"
        )

    # 高级选项
    with st.expander("高级选项（一般不用动）"):
        strip_spaces = st.checkbox("匹配前去除空格", value=True, help="比如把'张 三'变成'张三'再查，避免因为空格查不到")
        ignore_case = st.checkbox("忽略大小写", value=False, help="比如'ZHANG SAN'和'zhang san'算一样的")
        duplicate_action = st.selectbox(
            "遇到同名时",
            ["标记待核对（推荐）", "取第一个", "全部列出"],
            index=0,
            help="选'标记待核对'：遇到重名的会弹出来让你选，最保险"
        )

    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("开始匹配 🚀", type="primary", use_container_width=True):
            st.session_state.step = 3
            st.session_state.match_params = {
                'large_key': large_key,
                'large_result': large_result,
                'small_key': small_key,
                'result_col': result_col_name,
                'strip_spaces': strip_spaces,
                'ignore_case': ignore_case,
                'duplicate_action': duplicate_action
            }
            st.rerun()

    # 返回按钮
    if st.button("← 返回上一步", use_container_width=True):
        st.session_state.step = 1
        st.rerun()

# 步骤3：执行匹配
if st.session_state.step == 3:
    st.header("🔄 步骤3：执行匹配")

    # 首次匹配
    if st.session_state.match_results is None:
        with st.spinner("正在匹配数据..."):
            large_df = st.session_state.large_df.copy()
            small_df = st.session_state.small_df.copy()

            large_key = st.session_state.match_params['large_key']
            large_result = st.session_state.match_params['large_result']
            small_key = st.session_state.match_params['small_key']
            strip_spaces = st.session_state.match_params['strip_spaces']
            ignore_case = st.session_state.match_params['ignore_case']


            # 清洗函数
            def clean_text(x):
                if pd.isna(x):
                    return x
                x = str(x)
                if strip_spaces:
                    x = x.strip()
                if ignore_case:
                    x = x.lower()
                return x


            # 应用清洗
            large_df['_key_clean'] = large_df[large_key].apply(clean_text)
            small_df['_key_clean'] = small_df[small_key].apply(clean_text)

            matches = []
            pending = []

            total = len(small_df)
            progress_bar = st.progress(0)
            status_text = st.empty()

            for idx, row in small_df.iterrows():
                status_text.text(f"处理中：{idx + 1}/{total}")
                progress_bar.progress((idx + 1) / total)

                clean_key = row['_key_clean']
                matched_rows = large_df[large_df['_key_clean'] == clean_key]

                if len(matched_rows) == 0:
                    matches.append({
                        'index': idx,
                        'status': 'not_found',
                        'result': None
                    })
                elif len(matched_rows) == 1:
                    matches.append({
                        'index': idx,
                        'status': 'matched',
                        'result': matched_rows.iloc[0][large_result]
                    })
                else:
                    # 同名情况
                    candidates = []
                    for _, cand_row in matched_rows.iterrows():
                        # 收集额外信息（身份证、学校等，如果有的话）
                        extra_info = {}
                        for col in large_df.columns:
                            if col not in [large_key, large_result, '_key_clean']:
                                extra_info[col] = cand_row[col]

                        candidates.append({
                            'result': cand_row[large_result],
                            'extra': extra_info
                        })

                    pending.append({
                        'index': idx,
                        'name': row[small_key],
                        'candidates': candidates
                    })

                    matches.append({
                        'index': idx,
                        'status': 'pending',
                        'result': None
                    })

            progress_bar.empty()
            status_text.empty()

            st.session_state.match_results = matches
            st.session_state.pending_matches = pending
            st.session_state.current_match_index = 0

            st.rerun()

    # 处理同名
    if st.session_state.pending_matches:
        st.warning(f"发现 {len(st.session_state.pending_matches)} 条同名记录需要确认")

        # 显示当前处理进度
        st.progress((st.session_state.current_match_index + 1) / len(st.session_state.pending_matches))

        current = st.session_state.pending_matches[st.session_state.current_match_index]

        st.markdown("---")
        st.markdown(f"### 第 {st.session_state.current_match_index + 1}/{len(st.session_state.pending_matches)} 条")
        st.markdown(f"**查询条件：{current['name']}**")

        st.markdown("**找到多个匹配，请选择正确的一个：**")

        # 显示候选
        options = []
        for i, cand in enumerate(current['candidates']):
            # 格式化额外信息
            extra_parts = []
            for k, v in cand['extra'].items():
                if pd.notna(v) and str(v).strip():
                    extra_parts.append(f"{k}:{v}")
            extra_str = " | ".join(extra_parts) if extra_parts else ""

            option_text = f"{i + 1}. {cand['result']}"
            if extra_str:
                option_text += f" ({extra_str})"
            options.append(option_text)

        selected = st.radio("选择", options, key="pending_select", label_visibility="collapsed")
        selected_idx = options.index(selected)

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("✅ 确认选择", use_container_width=True):
                # 更新匹配结果
                for match in st.session_state.match_results:
                    if match['index'] == current['index']:
                        match['status'] = 'matched'
                        match['result'] = current['candidates'][selected_idx]['result']
                        break

                # 移动到下一个
                if st.session_state.current_match_index < len(st.session_state.pending_matches) - 1:
                    st.session_state.current_match_index += 1
                    st.rerun()
                else:
                    st.session_state.pending_matches = []
                    st.rerun()

        with col2:
            if st.button("⏭️ 暂时跳过", use_container_width=True):
                if st.session_state.current_match_index < len(st.session_state.pending_matches) - 1:
                    st.session_state.current_match_index += 1
                    st.rerun()

    # 显示结果
    if len(st.session_state.pending_matches) == 0 and st.session_state.match_results:
        st.success("✅ 匹配完成！")

        # 统计
        matched = len([m for m in st.session_state.match_results if m['status'] == 'matched'])
        not_found = len([m for m in st.session_state.match_results if m['status'] == 'not_found'])

        col1, col2, col3 = st.columns(3)
        col1.metric("成功匹配", matched)
        col2.metric("未找到", not_found)
        col3.metric("总计", len(st.session_state.match_results))

        # 生成结果
        result_df = st.session_state.small_df.copy()
        result_col = st.session_state.match_params['result_col']
        result_df[result_col] = None

        for match in st.session_state.match_results:
            if match['status'] == 'matched':
                result_df.at[match['index'], result_col] = match['result']

        st.markdown("---")
        st.subheader("结果预览")
        st.dataframe(result_df.head(10), use_container_width=True)

        # 下载
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            result_df.to_excel(writer, index=False, sheet_name='匹配结果')

        st.markdown("---")
        st.download_button(
            label="📥 下载结果文件",
            data=output.getvalue(),
            file_name="匹配结果.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        # 重新开始
        st.markdown("---")
        if st.button("🔄 重新开始", use_container_width=True):
            for key in ['step', 'large_df', 'small_df', 'match_results', 'pending_matches', 'current_match_index',
                        'match_params']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
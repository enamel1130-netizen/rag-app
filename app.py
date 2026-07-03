import os
from dotenv import load_dotenv
import streamlit as st
import pandas as pd

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

import streamlit as st
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))

# ===== 設定 =====
PARTS_FILE = "parts_master.xlsx"      # ① 元データ（人間が編集する部品マスタ）
DB_DIR = "chroma_db"                  # ② 検索用DBの保存フォルダ（ディスクに永続化）

# ===== ページ設定 =====
st.set_page_config(page_title="部品価格AI", page_icon="🔧")
st.title("🔧 部品価格チャットボット")
st.caption("部品マスタ(Excel)をもとにAIが価格を回答します")


def load_parts_as_documents(path: str) -> list[Document]:
    """部品マスタExcelを読み込み、1行＝1ドキュメントの形に変換する"""
    df = pd.read_excel(path)
    documents = []
    for _, row in df.iterrows():
        text = (
            f"部品名：{row['部品名']}　型番：{row['型番']}　"
            f"価格：{row['価格(円)']}円　用途：{row['用途']}　"
            f"互換品：{row['互換品']}　メモ：{row['メモ']}"
        )
        documents.append(Document(page_content=text))
    return documents


# ===== ① RAGの初期化（重い処理はキャッシュして1回だけ実行） =====
@st.cache_resource
def setup_chain():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    needs_rebuild = True  # まず「作り直しが必要」と仮定する

    if os.path.exists(DB_DIR):
        # ExcelとDBフォルダ、どちらが新しいか比較する
        excel_mtime = os.path.getmtime(PARTS_FILE)      # Excelの最終編集時刻
        db_mtime = os.path.getmtime(DB_DIR)              # DBフォルダの最終更新時刻
        if db_mtime >= excel_mtime:
            needs_rebuild = False  # DBの方が新しい（or同じ）→作り直し不要

    if needs_rebuild:
        # Excelから読み込んでDBを作り直し、ディスクに保存する
        import shutil
        if os.path.exists(DB_DIR):
            shutil.rmtree(DB_DIR)  # 古いDBを削除してから作り直す
        documents = load_parts_as_documents(PARTS_FILE)
        vectorstore = Chroma.from_documents(
            documents, embeddings, persist_directory=DB_DIR
        )
    else:
        # 変更がないので、保存済みのDBをそのまま読み込む（高速）
        vectorstore = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)

    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    llm = ChatGroq(model="llama-3.1-8b-instant")

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "あなたは部品の価格を案内するアシスタントです。"
         "以下の部品情報をもとに、質問に答えてください。"
         "情報に該当する部品がない場合は、正直に「該当する部品が見つかりません」と答えてください。\n\n{context}"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ])

    # chat_historyはinvoke時に外から渡すので、ここではダミーのRunnablePassthroughを使う
    chain = (
        {
            "context": (lambda x: x["question"]) | retriever,
            "question": lambda x: x["question"],
            "chat_history": lambda x: x["chat_history"],
        }
        | prompt
        | llm
    )
    return chain


chain = setup_chain()

# ===== ② 履歴の保存場所（Streamlitはst.session_stateを使う） =====
if "messages" not in st.session_state:
    st.session_state.messages = []  # 画面表示用（role, content）
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # LangChain用（HumanMessage/AIMessage）

# ===== ③ これまでの会話を画面に表示 =====
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ===== ④ 入力欄 =====
user_input = st.chat_input("質問を入力してください...")

if user_input:
    # ユーザーの発言を画面に表示＋保存
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # AIの回答を生成
    with st.chat_message("assistant"):
        with st.spinner("考え中..."):
            result = chain.invoke({
                "question": user_input,
                "chat_history": st.session_state.chat_history,
            })
            answer = result.content
            st.markdown(answer)

    # 履歴に追加（画面表示用 / LangChain用の両方）
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.chat_history.append(HumanMessage(content=user_input))
    st.session_state.chat_history.append(AIMessage(content=answer))

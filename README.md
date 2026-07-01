# 部品価格チャットボット

## このアプリについて
部品マスタ（Excel）をもとに、AIが部品の価格を回答するチャットボットです。

## デモ
https://rag-app-nbh8z2z6nbzdxhxmuv8zry.streamlit.app/

## 使用技術
- Python
- Streamlit
- LangChain
- Chroma（ベクトルデータベース）
- Groq（LLM）
- HuggingFace Embeddings

## 機能
- Excelファイルから、部品データを読み込む
- 自然な言葉で、部品の価格を検索できる
- 会話の履歴を、記憶して、文脈を理解する
- Excelを更新すると、自動的に、データベースを更新する
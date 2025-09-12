import janus
import time
import os
import requests
import faiss
import pickle
from sentence_transformers import SentenceTransformer

# ===== 設定 =====
JANUS_HOST = "http://localhost:8000"
JANUS_TOKEN = "janus_c4ce1635dd72153eab29f6c0c87ac7fab67d878a67560f045c0e7ca133559580"
AI_CHANNEL_NAME = "ai-serch"

# LMStudio API設定
LMSTUDIO_API = "http://localhost:1234/v1/chat/completions"
LMSTUDIO_MODEL = "local-model"

# 埋め込みモデル
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# FAISSデータ保存先
FAISS_INDEX_PATH = "./rag_index.faiss"
DOCS_PATH = "./rag_docs.pkl"

# BOT自身のID（固定で入れる）
BOT_ID = "auth0|68c051a0716fe7384425473f"

# ===== Janusクライアント初期化 =====
client = janus.Client(
    host=JANUS_HOST,
    token=JANUS_TOKEN,
    use_server_token=True
)

# ===== AIチャンネル確認/作成 =====
channels = client.get_channels()
ai_channel = next((c for c in channels if c.name == AI_CHANNEL_NAME), None)
if not ai_channel:
    ai_channel = client.create_channel(
        name=AI_CHANNEL_NAME,
        type="text",
        description="AI検索用チャンネル"
    )
print(f"AIチャンネル: {ai_channel.name} (ID: {ai_channel.id})")

# ===== メッセージ全取得 =====
def fetch_all_messages(channel_id, batch_size=200):
    all_messages = []
    last_seen = 0
    while True:
        messages = client.get_messages(channel_id, limit=batch_size)
        if not messages:
            break
        messages = sorted(messages, key=lambda m: m.id)
        new_msgs = [m for m in messages if m.id > last_seen]
        if not new_msgs:
            break
        all_messages.extend(new_msgs)
        last_seen = new_msgs[-1].id
        if len(messages) < batch_size:
            break
    return all_messages

# ===== RAG更新 =====
def update_rag_data():
    docs = []
    channels = client.get_channels()
    for ch in channels:
        if ch.id == ai_channel.id:
            continue
        messages = fetch_all_messages(ch.id)
        for m in messages:
            docs.append(f"{m.author.id}: {m.content}")
    if not docs:
        print("メッセージがありません")
        return
    embeddings = embedder.encode(docs, convert_to_numpy=True)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    faiss.write_index(index, FAISS_INDEX_PATH)
    with open(DOCS_PATH, "wb") as f:
        pickle.dump(docs, f)
    print("RAGデータ更新完了")

# ===== RAG検索 =====
def rag_search(query, top_k=5):
    if not os.path.exists(FAISS_INDEX_PATH):
        return "データがありません"
    index = faiss.read_index(FAISS_INDEX_PATH)
    with open(DOCS_PATH, "rb") as f:
        docs = pickle.load(f)
    q_emb = embedder.encode([query], convert_to_numpy=True)
    D, I = index.search(q_emb, top_k)
    results = [docs[i] for i in I[0] if i < len(docs)]
    return "\n".join(results)

# ===== LMStudio問い合わせ =====
def ask_llm(query, context=""):
    headers = {"Content-Type": "application/json"}
    data = {
        "model": LMSTUDIO_MODEL,
        "messages": [
            {"role": "system", "content": "あなたは知識検索アシスタントです。"},
            {"role": "user", "content": f"質問: {query}\n\n参考情報:\n{context}"}
        ]
    }
    res = requests.post(LMSTUDIO_API, headers=headers, json=data)
    return res.json()["choices"][0]["message"]["content"]

# ===== 初回RAG作成 =====
update_rag_data()

# ===== 起動時の最新IDを記録 =====
messages = client.get_messages(ai_channel.id, limit=1)
last_id = messages[0].id if messages else 0

# ===== メインループ =====
while True:
    messages = client.get_messages(ai_channel.id, limit=5)
    messages = sorted(messages, key=lambda m: m.id)
    for msg in messages:
        if msg.id <= last_id:
            continue
        # BOT自身の発言は無視
        if msg.author.id == BOT_ID:
            continue
        if msg.content.startswith("!s "):
            query = msg.content[3:].strip()
            print(f"検索リクエスト: {query}")
            context = rag_search(query)
            answer = ask_llm(query, context)
            client.send_message(ai_channel.id, f"Q: {query}\nA: {answer}")
        elif msg.content == "!update":
            update_rag_data()
            client.send_message(ai_channel.id, "RAGデータを更新したよ。")
    if messages:
        last_id = max(last_id, max(m.id for m in messages))
    time.sleep(5)

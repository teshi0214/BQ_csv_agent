import requests
import json
from datetime import datetime

API_KEY = "sk-65a0271d495f40fbbeef3d3844cb704e"
BASE_URL = "https://open-webui-522847804541.us-central1.run.app"
headers = {"Authorization": f"Bearer {API_KEY}"}

def export_feedbacks():
    # 1. フィードバック取得
    print("=" * 60)
    print("1. フィードバックデータを取得中...")
    print("=" * 60)
    
    feedbacks = requests.get(f"{BASE_URL}/api/v1/evaluations/feedbacks/all", headers=headers).json()
    print(f"取得件数: {len(feedbacks)} 件\n")
    
    rows = []
    for fb in feedbacks:
        chat_id = fb["meta"]["chat_id"]
        message_id = fb["meta"]["message_id"]
        
        print("-" * 60)
        print(f"フィードバックID: {fb['id']}")
        print(f"チャットID: {chat_id}")
        print(f"メッセージID: {message_id}")
        
        # 2. チャット内容取得
        print("\n2. チャット内容を取得中...")
        chat = requests.get(f"{BASE_URL}/api/v1/chats/{chat_id}", headers=headers).json()
        
        # 3. プロンプトと回答を抽出
        messages = chat["chat"]["messages"]
        user_prompt = ""
        assistant_response = ""
        
        for i, msg in enumerate(messages):
            if msg["id"] == message_id:
                assistant_response = msg["content"]
                if i > 0:
                    user_prompt = messages[i-1]["content"]
        
        # タイムスタンプを読みやすい形式に変換
        created_at = datetime.fromtimestamp(fb["created_at"]).strftime('%Y-%m-%d %H:%M:%S')
        
        row = {
            "feedback_id": fb["id"],
            "chat_id": chat_id,
            "message_id": message_id,
            "rating": fb["data"]["rating"],
            "rating_detail": fb["data"].get("details", {}).get("rating"),
            "model_id": fb["data"]["model_id"],
            "user_prompt": user_prompt,
            "assistant_response": assistant_response,
            "user_id": fb["user"]["id"],
            "user_name": fb["user"]["name"],
            "user_email": fb["user"]["email"],
            "comment": fb["data"].get("comment", ""),
            "reason": fb["data"].get("reason", ""),
            "tags": fb["data"].get("tags", []),
            "created_at": created_at
        }
        rows.append(row)
        
        # 結果を表示
        print("\n" + "=" * 60)
        print("📊 抽出結果")
        print("=" * 60)
        print(f"👤 ユーザー: {row['user_name']} ({row['user_email']})")
        print(f"🤖 モデル: {row['model_id']}")
        print(f"⭐ 評価: {'👍 Good' if row['rating'] == 1 else '👎 Bad'} (詳細スコア: {row['rating_detail']})")
        print(f"📅 日時: {row['created_at']}")
        print(f"\n💬 ユーザーのプロンプト:")
        print(f"   {row['user_prompt']}")
        print(f"\n🤖 AIの回答:")
        print(f"   {row['assistant_response'][:200]}{'...' if len(row['assistant_response']) > 200 else ''}")
        if row['comment']:
            print(f"\n📝 コメント: {row['comment']}")
        print("-" * 60)
    
    # 最終サマリー
    print("\n" + "=" * 60)
    print("📋 BigQueryにエクスポートするデータ (JSON形式)")
    print("=" * 60)
    print(json.dumps(rows, indent=2, ensure_ascii=False))
    
    return rows

if __name__ == "__main__":
    rows = export_feedbacks()
    print(f"\n✅ 合計 {len(rows)} 件のフィードバックを取得しました")





#https://generativelanguage.googleapis.com/v1beta/openai
#API

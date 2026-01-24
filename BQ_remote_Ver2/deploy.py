#!/usr/bin/env python3
"""
deploy.py - BigQuery MCP Agent を Agent Engine にデプロイするスクリプト

使用方法:
    python deploy.py [--project PROJECT_ID] [--region REGION] [--display-name NAME]

例:
    python deploy.py
    python deploy.py --project my-project --region us-central1
    python deploy.py --display-name "BQ Agent v2"
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path


def get_project_id() -> str:
    """プロジェクトIDを取得"""
    # 1. 引数から
    # 2. 環境変数から
    # 3. gcloud config から
    
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("PROJECT_ID")
    
    if not project_id:
        try:
            result = subprocess.run(
                ["gcloud", "config", "get", "project"],
                capture_output=True,
                text=True,
                check=True
            )
            project_id = result.stdout.strip()
        except subprocess.CalledProcessError:
            pass
    
    return project_id


def get_project_number(project_id: str) -> str:
    """プロジェクト番号を取得"""
    try:
        result = subprocess.run(
            ["gcloud", "projects", "describe", project_id, "--format=value(projectNumber)"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ プロジェクト番号の取得に失敗: {e}")
        sys.exit(1)


def setup_service_account_permissions(project_id: str, project_number: str) -> None:
    """サービスアカウントに必要な権限を付与"""
    service_account = f"service-{project_number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
    
    roles = [
        "roles/bigquery.dataViewer",
        "roles/bigquery.jobUser",
        "roles/mcp.toolUser",
    ]
    
    print(f"\n📋 サービスアカウントに権限を付与中...")
    print(f"   サービスアカウント: {service_account}")
    
    for role in roles:
        print(f"   付与中: {role}")
        try:
            subprocess.run(
                [
                    "gcloud", "projects", "add-iam-policy-binding", project_id,
                    f"--member=serviceAccount:{service_account}",
                    f"--role={role}",
                    "--quiet"
                ],
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️  {role} の付与に失敗（既に付与済みの可能性あり）")


def deploy_agent(project_id: str, region: str, agent_dir: str, display_name: str = None, staging_bucket: str = None) -> str:
    """ADK Agent を Agent Engine にデプロイ"""
    
    cmd = [
        "adk", "deploy", "agent_engine",
        f"--project={project_id}",
        f"--region={region}",
    ]
    
    if display_name:
        cmd.append(f"--display_name={display_name}")
    
    if staging_bucket:
        cmd.append(f"--staging_bucket={staging_bucket}")
    
    cmd.append(agent_dir)
    
    print(f"\n🚀 Agent Engine にデプロイ中...")
    print(f"   コマンド: {' '.join(cmd)}")
    print()
    
    try:
        # 出力をリアルタイムで表示しつつ、内容もキャプチャ
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        output_lines = []
        for line in process.stdout:
            print(line, end='')
            output_lines.append(line)
        
        process.wait()
        output = ''.join(output_lines)
        
        # "Deploy failed" が含まれていたら失敗
        if "Deploy failed" in output or process.returncode != 0:
            print(f"\n❌ デプロイに失敗しました")
            return None
        
        return "success"
    except subprocess.CalledProcessError as e:
        print(f"❌ デプロイに失敗しました")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="BigQuery MCP Agent を Agent Engine にデプロイ"
    )
    parser.add_argument(
        "--project", "-p",
        help="Google Cloud プロジェクトID"
    )
    parser.add_argument(
        "--region", "-r",
        default="us-central1",
        help="デプロイ先リージョン (デフォルト: us-central1)"
    )
    parser.add_argument(
        "--display-name", "-n",
        help="エージェントの表示名"
    )
    parser.add_argument(
        "--skip-permissions",
        action="store_true",
        help="サービスアカウント権限設定をスキップ"
    )
    parser.add_argument(
        "--agent-dir",
        default="./bq_agent",
        help="エージェントディレクトリ (デフォルト: ./bq_agent)"
    )
    parser.add_argument(
        "--staging-bucket", "-b",
        help="GCSステージングバケット (例: gs://my-bucket)"
    )
    
    args = parser.parse_args()
    
    # ヘッダー表示
    print("=" * 50)
    print("BigQuery MCP Agent - Agent Engine デプロイ")
    print("=" * 50)
    
    # プロジェクトID取得
    project_id = args.project or get_project_id()
    if not project_id:
        print("❌ プロジェクトIDが指定されていません")
        print("   --project オプションで指定するか、環境変数 GOOGLE_CLOUD_PROJECT を設定してください")
        sys.exit(1)
    
    print(f"\n📁 プロジェクト: {project_id}")
    print(f"📍 リージョン: {args.region}")
    print(f"📂 エージェントディレクトリ: {args.agent_dir}")
    
    # ステージングバケットの設定
    staging_bucket = args.staging_bucket or os.environ.get("STAGING_BUCKET")
    if not staging_bucket:
        # デフォルトバケット名を生成
        staging_bucket = f"gs://{project_id}-adk-staging"
        print(f"🪣 ステージングバケット: {staging_bucket} (自動生成)")
        
        # バケットが存在しない場合は作成
        bucket_name = staging_bucket.replace("gs://", "")
        try:
            check_result = subprocess.run(
                ["gcloud", "storage", "buckets", "describe", staging_bucket],
                capture_output=True,
                text=True
            )
            if check_result.returncode != 0:
                print(f"   バケットを作成中...")
                subprocess.run(
                    ["gcloud", "storage", "buckets", "create", staging_bucket, 
                     f"--project={project_id}", f"--location={args.region}"],
                    check=True
                )
                print(f"   ✅ バケット作成完了")
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️  バケット作成に失敗: {e}")
    else:
        print(f"🪣 ステージングバケット: {staging_bucket}")
    
    # エージェントディレクトリの存在確認
    agent_path = Path(args.agent_dir)
    if not agent_path.exists():
        print(f"❌ エージェントディレクトリが見つかりません: {args.agent_dir}")
        sys.exit(1)
    
    if not (agent_path / "agent.py").exists():
        print(f"❌ agent.py が見つかりません: {agent_path / 'agent.py'}")
        sys.exit(1)
    
    # プロジェクト番号取得
    project_number = get_project_number(project_id)
    print(f"🔢 プロジェクト番号: {project_number}")
    
    # サービスアカウント権限設定
    if not args.skip_permissions:
        setup_service_account_permissions(project_id, project_number)
    else:
        print("\n⏭️  サービスアカウント権限設定をスキップ")
    
    # デプロイ実行
    result = deploy_agent(
        project_id=project_id,
        region=args.region,
        agent_dir=args.agent_dir,
        display_name=args.display_name,
        staging_bucket=staging_bucket
    )
    
    if result:
        print("\n" + "=" * 50)
        print("✅ デプロイ完了！")
        print("=" * 50)
        print("\n次のステップ:")
        print("  1. Cloud Console で Agent Engine を確認")
        print("  2. Gemini Enterprise で OAuth 設定を行う（必要な場合）")
        print(f"\n確認コマンド:")
        print(f"  gcloud ai reasoning-engines list --project={project_id} --region={args.region}")
    else:
        print("\n❌ デプロイに失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()

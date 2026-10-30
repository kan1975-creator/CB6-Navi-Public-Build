# CB6 Jules 双方向ブリッジ（隔離実装）

## 状態
コード・GitHub Actions workflow の候補を作成済み。GitHubへの登録、Jules API呼出、Actions起動は未実施。APIキー不要の構文検査のみ実施。

## 安全構造
- READは手動起動のみ。Jules APIのセッション・活動履歴を取得し、Runner一時領域にのみ保存。公開リポジトリのArtifactへ原始証拠をアップロードしない。
- SENDは手動起動のみ。`cb6-jules-send-approval` EnvironmentのRequired reviewersが設定済みであることが前提。本人が実際の指示内容を確認して承認する。指示のUTF-8バイト列SHA-256が一致しなければ送信しない。
- SEND Workflowを登録する**前に** Environment保護を設定すること。保護なしで登録・実行してはいけない。
- Jules APIの`sendMessage`は指示送信であり、Jules側の作業実行やGitHub変更を絶対に防止する機能ではない。安全な指示内容・Jules側権限の制限も必要。
- `approvePlan`、PR自動作成、GitHub push、Registry昇格、ビルドは実装しない。
- READの詳細原始証拠はRunner消滅後に残らない。恒久保存は非公開保管先と権限設定を別途用意する必要がある。

## Androidでの導入順
1. Jules設定画面 `https://jules.google.com/settings` でAPIキーを取得（ChatGPTへ貼らない）。
2. GitHub対象リポジトリの Settings → Secrets and variables → Actions → New repository secret で `JULES_API_KEY` を登録。
3. Settings → Environments に `cb6-jules-send-approval` を作成し、Required reviewers を本人だけに設定。**自分自身がレビュー可能か、利用プランで環境保護が有効か確認**。できなければSENDは登録しない。
4. `.github/workflows/` の2つと `tools/jules_bridge.py` を専用ブランチで登録する。**この登録は未実施。** GitHubのworkflow_dispatchはデフォルトブランチ登録等の条件を満たす必要がある。
5. READを限定1回試行してAPI上のセッションIDが使えることを確認。GitHub Actionsの課金・利用枠を事前確認。
6. SENDは承認保護が実効確認できた後だけ利用。指示本文をGitHub Actions入力に貼り、SHA-256を計算し、保護された実行を本人が承認。

## 未解決事項
- Jules WebのセッションID `8061497760758145992` がAPIで有効かは未確認。
- GitHub公開リポジトリでEnvironment Required reviewersを利用できるか・本人自己承認できるかは未確認。
- GitHub ActionsおよびJules APIの無料枠は未確認。追加課金0円は保証しない。
- GitHub Actions入力はログ・実行履歴に残り得るため、秘密情報を送信しないこと。
- この構成だけではChatGPTへの自動プッシュ通知・自動レビューは成立しない。GitHub連携から必要時に結果を取得するか、別の通知機構が必要。

API仕様参照: https://jules.google/docs/api/reference/sessions / https://jules.google/docs/api/reference/activities/

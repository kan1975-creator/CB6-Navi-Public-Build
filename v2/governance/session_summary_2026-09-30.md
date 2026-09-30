# Session Summary — 2026-09-30

- GitHub の `cb6-v2-clean` 最新 HEAD を唯一の正規状態として扱い、チャット上の自己申告は Evidence としない。
- 作業開始時に HEAD を取得し、commit/push 直前にも再取得する。開始 HEAD と不一致なら古い作業を push せず、最新 HEAD へ再同期する。
- 進捗報告は **進めて推奨 / 待ち / スマホ操作が必要** の3分類を使用する。
- **進めて推奨**: ChatGPT/GitHub 側で安全に継続できる作業がある状態。チャット指示待ちだけを理由に停止しない。
- **待ち**: Actions、GitHub 取得経路など外部結果待ちの状態。必ず「目安時間」「次の確認タイミング」「待機中にできる対応の有無」を併記し、待機中も競合しない静的解析・Evidence確認を進める。
- **スマホ操作が必要**: 実機 CB6 でしか取得できない Evidence やユーザー操作が次工程に必須の状態。必要な操作・取得対象を具体的に通知する。
- 修正 commit が必要な場合は、適用中の承認ルール（`OPS-USER-APPROVAL-BEFORE-FIX-001` または正式な後継ルール）に従い、変更内容を具体化して必要な個別承認を得てから実装する。
- `GOVERNANCE-V3-ACTIVE-METHOD-REVISION` はユーザー採用済み。正しい最新 HEAD に安全に適用するため、HEAD を証明できない間の commit/push 保留は採用取消しを意味しない。
- 通知・過去の進捗報告は stale state になり得る。ユーザーが「進捗は？」と確認した際は、過去の通知をそのまま再利用せず、最新 HEAD・関連 Actions・必要な raw log/Evidence を再取得して現在状態を判定する。
- Signal 0件問題を最優先課題とする。ただし Governance/HEAD 整合性を確立している間、Signal 側のコード・style・patch は **読み取り専用** とし、変更しない。
- Signal 調査は GitHub 上の客観的 Evidence を優先し、入力取得 → patch適用 → 生成物 → runtime のどこで最初に0件へ遮断されるかを証明する。
- Actions 成功時は Artifact/Evidence を確認し、失敗時は raw log を解析して原因を特定する。許可された修正は最小変更 → Gate → HEAD再確認 → commit/push → 再Build の順で行う。

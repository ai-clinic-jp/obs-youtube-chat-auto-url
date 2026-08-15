# YouTube Chat Auto URL for OBS Studio

OBSでYouTubeライブを開始したとき、**コメント表示用ブラウザソースのURLを自動更新するOBS Pythonスクリプト**です。

毎回ライブ配信のVideo IDをコピーして、

```text
https://www.youtube.com/live_chat?is_popout=1&v=VIDEO_ID
```

の `VIDEO_ID` を手動で差し替える作業をなくします。

## 特徴

- **配信開始だけで自動更新**
- **YouTubeチャンネルURLの入力不要**
- **YouTube側からライブ配信を検索しない**
- **Google API / OAuth 不要**
- **OBSが現在選択している `broadcast_id` を直接利用**
- 手動テストボタンあり

## 仕組み

このスクリプトは、YouTubeのチャンネルページやHTMLから「現在ライブ中の動画」を探しません。

OBS StudioでYouTubeアカウントを連携し、「配信の管理」から配信枠を選択すると、OBS内部のStreaming Service設定に現在の配信ID（`broadcast_id`）が保持されます。

このスクリプトは配信開始イベントを検知し、その `broadcast_id` を直接取得してブラウザソースのURLを書き換えます。

```text
OBSで配信枠を選択
        ↓
「配信開始」
        ↓
OBS内部の broadcast_id を取得
        ↓
YouTubeライブチャットURLを生成
        ↓
ブラウザソースのURLを自動更新
```

## 必要環境

- OBS Studio
- OBSとYouTubeアカウントを連携していること
- OBSの「配信の管理」からYouTube配信枠を選択していること
- コメント表示用のブラウザソース

> ストリームキーのみを手動設定している環境では `broadcast_id` を取得できない可能性があります。

## インストール

1. `youtube_chat_auto_url.py` をダウンロード
2. OBS Studioを起動
3. `ツール` → `スクリプト`
4. `Python設定` でOBSが利用するPythonを設定
5. `+` ボタンから `youtube_chat_auto_url.py` を追加
6. 「コメント表示ブラウザソース」でコメント欄に使っているブラウザソースを選択

## 使い方

通常どおりOBSの「配信の管理」でYouTube配信枠を選択し、**「配信開始」**を押すだけです。

配信開始後、ブラウザソースのURLが自動的に次の形式へ更新されます。

```text
https://www.youtube.com/live_chat?is_popout=1&v=現在のVideoID
```

配信開始直後にOBS内部へ配信IDがまだ反映されていない場合に備え、1秒おきに最大10回まで自動再試行します。

## 手動テスト

OBSの `ツール` → `スクリプト` から、

**「今すぐURL更新をテスト」**

を押すと、現在OBSで選択している配信のVideo IDを取得してブラウザソースを更新できます。

配信開始前でも、OBSの「配信の管理」で配信枠が選択されていれば動作確認に使えます。

## トラブルシューティング

### Video IDを取得できない

次を確認してください。

- OBSとYouTubeアカウントを連携している
- OBSの「配信の管理」で配信枠を選択している
- ストリームキーのみの手動設定ではない

### コメント欄が更新されない

- スクリプト設定で正しいブラウザソースを選択しているか確認
- OBSの `ツール` → `スクリプト` → `スクリプトログ` を確認
- 「今すぐURL更新をテスト」を実行して動作確認

## 動作確認

2026年8月、Windows版OBS Studio + YouTubeアカウント連携環境で動作確認しています。

OBSやYouTube側の仕様変更により、将来動作しなくなる可能性があります。

## ライセンス

MIT License

## 免責事項

このツールはYouTube、Google、OBS Projectとは無関係の非公式ツールです。

本ソフトウェアは無保証です。利用は自己責任でお願いします。


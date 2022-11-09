# 環境変数一覧

NUCOSen Broadcastが読み取る環境変数の一覧。

| 環境変数名 | 説明 |
| :--: | :-- |
| CATEGORY | 生放送タイトル最初の「【】」内に入る文字 |
| COMMUNITY | 放送対象のcoから始まるコミュニティID |
| TAGS | 生放送の枠に付与されるタグ。半角コンマ（,）区切り |
| REQTAGS | 放送対象の動画のタグ。半角コンマ（,）区切り |
| NICO_ID | ニコニコアカウントのメールアドレス |
| NICO_PW | （機密）ニコニコアカウントのパスワード |
| NICO_TFA | （機密）ニコニコアカウントの2段階認証を突破するための鍵 |
| LOGGING_DISCORD_WEBHOOK | （機密）ログの送信先。DiscordのウェブフックURL |
| QUEUE_URL | 放送待ちデータベースのURL |
| REQUEST_URL | リクエスト受理待ちデータベースのURL |
| DB_KEY | （機密）データベースのアクセス鍵 |
| NG_TAGS | 放送自主規制の対象。タグ単位。半角コンマ（,）区切り |
| IGNORE_QUOTABLE_CHECK | （臨時）指定すると、動画引用可能チェックを無視する |

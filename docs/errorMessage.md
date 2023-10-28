# エラーメッセージの構造

## Discordログ

Discordに送信されるエラーメッセージは、以下のフォーマットで表記されています。

```text
エラーレベル エラーを受理したロガー名 (エラーが発生した関数名)
エラーの内容
```

ロガーとはエラーを処理するためのシステムです。一部の例外を除き、NUCOSen Broadcastでは、パッケージ名とモジュール名をドット区切りでつなげたものを命名しています。なお、モジュール名の.pyは省略されます。

一例：

```text
WARNING @ nucosen.nucosen (run)
エラーメッセージ
```

↓

nucosenパッケージ内、nucosen.pyモジュールのrun関数から発せられたWARNINGレベルのエラー。

### 例外

例外として、リトライの際はパッケージ名・モジュール名に続いて関数名もドット区切りで連結します。
これは、リトライ処理がエラーを起こした関数の外で行われることから、正常に関数名を取得できないためです。

一例：

```text
WARNING @ nucosen.live.getLives (__retry_internal)
エラーメッセージ, retrying in 1 seconds...
```

↓

nucosenパッケージ内、live.pyモジュールのgetLives関数から発せられたWARNINGレベルのエラー。

# エラーメッセージ一覧

xは任意の数字を指します。

| Code | 原因 | 対処 |
| :---: | :--- | :--- |
| 4xx | HTTP/HTTPS通信に失敗した | 自動的にリトライするまで待つか、再起動してください。 |
| 5xx | HTTP/HTTPS通信に失敗した | 自動的にリトライするまで待つか、通信相手がダウンしていないか（メンテナンス情報等がないか）確認してください。 |
| C0L | 現枠・次枠のどちらか、または両方が見つからなかった | どちらも枠がない状態で起動した場合にも発生します。その場合はデーモンによる再起動を待つか、手動で再起動してください。<br>再起動後も発生する場合は、手動で枠の予約を行ってください。 |
| E0x | 動画IDが想定される形式と違った | 正しい動画IDの場合、手動でエンキューしてください。<br>そうでない場合は、リクエストAPIのフィルターが正常に作動していない可能性があります。 |
| E10 | これから予約する枠の放送開始時刻を決めることができなかった | 翌日の朝10時開始で枠を予約しています。現枠が終了するまでに手動で枠の予約を行ってください。 |
| E20 | 枠の予約に失敗した | メンテナンス前の枠予約に失敗しました。<br>処理は続行します。手動で予約を行ってください。 |
| E21 | 枠の予約に失敗した | メンテナンス後の枠予約に失敗しました。<br>E20の後に起きた場合は続いて致命的エラーが発生するかもしれません。<br>次のメンテナンスが24時間以上の場合、このエラーは仕様です。手動で予約を行ってください。 |
| E30 | 引用中の動画を途中停止した | すぐに放送を再開する場合は、再起動してください。<br>メンテナンス作業を行う場合は、3分以内に完了するか、放送停止措置をとってください。<br>同じ動画をもう一度放送する場合は、3分以内に優先エンキューを行った後に再起動してください。<br>約3分で自動的に放送は復帰します。<br>（MAINTENANCE_VIDEO_ID設定を使用している場合、作業時間はメンテナンス動画の長さ） |
| E40 | 抽選候補に適切な動画がなかった | リクエストAPIのフィルターを点検してください。<br>データベースへの不正アクセスがなかったか点検してください。 |
| Lxx | 通信セッションが使用できなかった | 自動で再ログインします。<br>繰り返し発生する場合は、configファイルまたは環境変数を確認し、正しいログイン情報に修正してください。 |
| W0L | 現枠・次枠の両方が見つからなかった | どちらも枠がない状態で起動した場合にも発生します。その場合は対応する必要はありません。<br>繰り返し発生する場合は予約の検出に問題があります。すぐに停止してエラー情報を報告してください。 |
| W10 | 引用を拒否された | 枠開始直後の場合は無視できます（放送前引用での拒否）。<br>INFOレベルで通信ログが残されています。繰り返し発生する場合は、ログに記載されている警告文に従ってください。 |
| W20 | 枠の予約に失敗した | このエラーに続いて数字3桁のWARNINGが発出されるため、その内容に従ってください。<br>もしくは手動で枠の予約を行ってください。 |
| W21 | 不要な枠予約をスキップ | メンテ前の枠取りをスキップしました。この処理が誤りである場合は手動で枠取りを行ってください。 |
| W30 | 古いAPIの呼び出し | オプションにより、古いAPIの呼び出しが指定されています。このAPIは過去に動作しなくなったことがあります。<br>意図して古いAPIを指定している場合は無視して構いません。 |
| V00 | ニコニコへのログインに失敗した | 環境変数を確認してください。<br>メールアドレス・パスワードが正しい場合、二段階認証の生成コードが間違っている可能性があります |
| V0E | 必要な環境変数が得られなかった | configファイルを確かめてください。<br>デーモンの設定を確かめてください。<br>環境変数を設定してください。 |
| V10 | 予約直後にも関わらず、放送予定の枠がない | 手動で予約を実施してください。<br>予約が成立しているにも関わらずエラーが発生する場合は、再起動してください。<br>それでも治らない場合、ニコニコのサーバーがダウンしていないか確認してください。 |
| V20 | 引用直前で動画が引用不能であることが判明した | （エラー処理を記述していないためクラッシュ） |
| V3x | ランダムセレクションの選出に失敗 | 自動で再試行します。<br>同じタグで繰り返し発生する場合は、そのタグで投稿された引用可能動画が少なすぎる可能性があります。 |
| V40 | 二段階認証に失敗した | 自動で再ログインします。<br>繰り返し発生する場合は、configファイルまたは環境変数を確認し、正しいログイン情報に修正してください。 |

# src/utility/messages.py

class HeianMessages:
    """朝廷（システム）内で発せられる言霊（ログメッセージ）の目録"""

    # --- 大納言（StateManager / RedisClient）関連 ---
    STATE_VIOLATION = "【掟破り】政務 '{task_id}' にて許可されざる状態遷移（{old_status} → {new_status}）が試みられました。"
    TASK_RETRY = "【やり直し】政務 '{task_id}' が失敗いたしました。リトライ回数: {count}/{limit}"
    TASK_FAILED = "【無念】政務 '{task_id}' は限界（リトライ上限）に達しました。FAILEDといたします。"
    TASK_UPDATED = "【詔勅更新】政務 '{task_id}' が '{status}' の状態となり申した。"
    MESSAGE_SENT = "【伝令】{sender_id} より {receiver_id} 宛に '{msg_type}' の文が送られました。"

    # --- 官職（BaseAgent）全般 ---
    AGENT_ATTENDANCE = "【出仕】{role} '{agent_id}' が朝廷に出仕し、待機を開始いたしました。"
    AGENT_RETIRE = "【退朝】{agent_id} はお役目を終え、退出いたします。"
    AGENT_WAKEUP = "【狼煙検知】{agent_id}: '{event_type}' の狼煙を確認。文箱を改めまする。"
    AGENT_RECEIVED = "【受領】{agent_id}: '{sender_id}' より '{msg_type}' の文を受け取りました。"
    AGENT_ERROR = "【異常事態】{agent_id}: 政務中に不測の事態が発生いたしました。({error})"
    AGENT_STATUS_CHANGE = "【状態変化】{agent_id} が '{status}' となり申した。"

    # --- 頭弁（Tonoben）専用 ---
    TONOBEN_IGNORE = "【頭弁】承知できぬ用件ゆえ、静観いたしまする。({msg_type})"
    TONOBEN_ORDER_RECEIVED = "【頭弁】関白殿下より詔勅を賜りました。「{instruction}」...これより政務を分解いたしまする。"
    TONOBEN_DECOMPOSED = "【頭弁】思考完了。政務を {count} つのタスクに分解いたしました。"
    TONOBEN_ASSIGN_COMPLETE = "【頭弁】すべての舎人への割り振りが完了いたしました。（実行ID: {execution_id}）"
    TONOBEN_ERROR = "【頭弁エラー】政務の分解中に不測の事態が発生いたしました。: {error}"

    # --- 舎人・防壁（SafeIO）関連 ---
    IO_VIOLATION = "不敬なる越権行為（許可されていない領域へのアクセス）を検知いたしました。"
    IO_NOT_FOUND = "ご指定の巻物（ファイル）が見つかりませぬ。"
    IO_READ_SUCCESS = "読み込みに成功いたしました。"
    IO_WRITE_SUCCESS = "書き込みに成功いたしました。"
    IO_READ_ERROR = "読み込み中に不測の事態が発生: {error}"
    IO_WRITE_ERROR = "書き込み中に不測の事態が発生: {error}"

    # --- system (main.py) ---
    SYSTEM_STARTUP = "=== Kanpakuシステム起動 ==="
    REDIS_CHECK = "Redis接続を確認中..."
    STATE_MANAGER_INIT = "StateManager初期化中..."
    TONOBEN_STARTUP = "頭弁起動中..."
    TONOBEN_ATTENDANCE = "頭弁出席宣言中..."
    SAMPLE_AGENT_STARTUP = "Sample起動中..."
    EVENT_LOOP_START = "イベントループ開始..."
    EVENT_LOOP_STOP = "イベントループ停止..."
    SYSTEM_STOP = "Kanpakuシステム停止..."
    SYSTEM_STARTUP_ERROR = "システム起動エラー: {error}"
    UNKNOWN_COMMAND = "未知のコマンド。'help'でヘルプを表示します。"
    HELP_COMMANDS = """
Available commands:
  help              - このヘルプを表示する
  exit              - システムを停止する
  order             - 頭弁にテスト指示を送信する
  order <instruction> - カスタム指示を送信する
"""
    HEAD_WITH_ORDER = " 詔勅付き: {instruction}"
    ORDER_PROCESSING_COMPLETE = "詔勅処理完了"
    ORDER_PROCESSING_ERROR = "詔勅処理中にエラーが発生: {error}"
    CUSTOM_ORDER_SENT = "カスタム指示を頭弁に送信: {instruction}"
    ORDER_PROCESSING_DONE = "指示処理完了"

    # --- Additional StateManager messages ---
    LOCK_ACQUIRED = " ロック取得 '{target_path}' by {lock.locked_by}"
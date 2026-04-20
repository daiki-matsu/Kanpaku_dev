import pytest
import time
import threading
from models.message import Message
from db.redis_client import RedisClient

class TestInboxAndPubSub:
    """官職間の通信網（InboxとPub/Sub）のテスト"""
    
    def test_inbox_persistence(self, redis_client, sample_message):
        """Inboxの確実性：システム停止後もメッセージが残存すること"""
        # メッセージをInboxに投函
        redis_client.push_inbox(sample_message.receiver_id, sample_message)
        
        # 直接Redisを確認してメッセージが保存されていることを検証
        inbox_key = f"inbox:{sample_message.receiver_id}"
        messages = redis_client.client.lrange(inbox_key, 0, -1)
        
        assert len(messages) == 1
        saved_message = Message.model_validate_json(messages[0])
        assert saved_message.message_id == sample_message.message_id
        assert saved_message.sender_id == sample_message.sender_id
        assert saved_message.receiver_id == sample_message.receiver_id
        assert saved_message.message_type == sample_message.message_type
    
    def test_fifo_order(self, redis_client):
        """FIFO (First In First Out) confirmation"""
        # Post multiple messages in correct order for FIFO behavior
        messages = []
        for i in range(3):
            msg = Message(
                sender_id="tonoben",
                receiver_id="toneri_1",
                message_type="TASK_ASSIGNED",
                task_id=f"test_task_{i+1}",
                content={"order": i}
            )
            messages.append(msg)
            redis_client.push_inbox("toneri_1", msg)
        
        # FIFOで取り出せることを確認
        retrieved_messages = []
        for _ in range(3):
            msg = redis_client.pop_inbox("toneri_1")
            if msg:
                retrieved_messages.append(msg)
        
        assert len(retrieved_messages) == 3
        
        # 投函した順番通りに取り出せることを確認
        for i, msg in enumerate(retrieved_messages):
            assert msg.message_type == "TASK_ASSIGNED"
            assert msg.task_id == f"test_task_{i+1}"
            assert msg.content.get("order", 0) == i
        
        # すべてのメッセージを取り出した後は空であることを確認
        empty_msg = redis_client.pop_inbox("toneri_1")
        assert empty_msg is None
    
    def test_pubsub_notification(self, redis_client, sample_message):
        """Pub/Subの即時性：通知が即座に配信されること"""
        notification_received = threading.Event()
        received_data = None
        
        def subscriber():
            """別スレッドでPub/Sub通知を待機"""
            pubsub = redis_client.get_pubsub()
            channel = f"notify:{sample_message.receiver_id}"
            pubsub.subscribe(channel)
            
            try:
                # 通知を待機（最大5秒）
                start_time = time.time()
                while time.time() - start_time < 5.0:
                    message = pubsub.get_message(timeout=0.1)
                    if message and message['type'] == 'message':
                        nonlocal received_data
                        received_data = message['data']
                        notification_received.set()
                        break
                    time.sleep(0.01)
            finally:
                pubsub.close()
        
        # サブスクライバースレッドを起動
        subscriber_thread = threading.Thread(target=subscriber)
        subscriber_thread.start()
        
        # 少し待ってからメッセージを送信
        time.sleep(0.1)
        channel = f"notify:{sample_message.receiver_id}"
        redis_client.publish_notification(channel, sample_message.message_type)
        
        # 通知が受信されるのを待機（最大5秒）
        assert notification_received.wait(timeout=5.0), "Pub/Sub通知が5秒以内に受信されませんでした"
        assert received_data == sample_message.message_type
        
        subscriber_thread.join(timeout=1.0)
    
    def test_send_message_integration(self, state_manager, sample_message):
        """StateManager.send_message() の統合テスト"""
        # メッセージを送信
        state_manager.send_message(sample_message)
        
        # Inboxにmessageが保存されていることを確認
        inbox_message = state_manager.redis.pop_inbox(sample_message.receiver_id)
        assert inbox_message is not None
        assert inbox_message.message_type == sample_message.message_type
        assert inbox_message.sender_id == sample_message.sender_id
        assert inbox_message.receiver_id == sample_message.receiver_id
        
        # Pub/Subチャンネルに通知が送信されていることを確認
        # （直接Pub/Subをテストするのは複雑なため、ここではInboxの保存を主な検証対象とする）
        channel = f"notify:{sample_message.receiver_id}"
        
        # 別のメッセージでPub/Subの動作を確認
        test_message = Message(
            sender_id="test_sender",
            receiver_id="test_receiver",
            message_type="TEST_NOTIFICATION"
        )
        
        notification_received = threading.Event()
        
        def notification_listener():
            pubsub = state_manager.redis.get_pubsub()
            pubsub.subscribe(f"notify:test_receiver")
            try:
                start_time = time.time()
                while time.time() - start_time < 3.0:
                    msg = pubsub.get_message(timeout=0.1)
                    if msg and msg['type'] == 'message':
                        notification_received.set()
                        break
                    time.sleep(0.01)
            finally:
                pubsub.close()
        
        listener_thread = threading.Thread(target=notification_listener)
        listener_thread.start()
        
        time.sleep(0.1)
        state_manager.send_message(test_message)
        
        assert notification_received.wait(timeout=3.0), "通知が受信されませんでした"
        listener_thread.join(timeout=1.0)
    
    def test_multiple_agents_communication(self, state_manager):
        """複数のエージェント間の通信テスト"""
        agents = ["toneri_1", "toneri_2", "toneri_3"]
        message_ids = {}
        
        # 各エージェントにメッセージを送信
        for i, agent_id in enumerate(agents):
            msg = Message(
                sender_id="tonoben",
                receiver_id=agent_id,
                message_type="TASK_ASSIGNED",
                task_id=f"test_task_{i+1}",
                content={"instruction": f"{agent_id} no shiji"}
            )
            message_ids[agent_id] = msg.message_id
            state_manager.send_message(msg)
        
        # 各エージェントが自分のメッセージを受け取れることを確認
        for i, agent_id in enumerate(agents):
            received_msg = state_manager.redis.pop_inbox(agent_id)
            assert received_msg is not None
            assert received_msg.receiver_id == agent_id
            assert received_msg.message_type == "TASK_ASSIGNED"
            assert received_msg.task_id == f"test_task_{i+1}"
            assert received_msg.message_id == message_ids[agent_id]
        
        # すべてのメッセージが取り出された後、Inboxが空であることを確認
        for agent_id in agents:
            empty_msg = state_manager.redis.pop_inbox(agent_id)
            assert empty_msg is None

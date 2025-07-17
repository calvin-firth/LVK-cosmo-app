from gcn_kafka import Consumer


consumer = Consumer(client_id='3i856lfjrpqe3d8nh8fbbmbt9r',
                    client_secret='1vkcja4n67fjlcck7bbo1apqpv9g0c453ng221njon0pgn2dlr9u')

print(consumer.list_topics().topics)

# Subscribe to topics and receive alerts
consumer.subscribe(['gcn.classic.text.FERMI_GBM_FIN_POS',
                    'gcn.classic.text.LVC_INITIAL'])
while True:
    print("In while")
    for message in consumer.consume(timeout=1):
        if message.error():
            print(message.error())
            continue
        # Print the topic and message ID
        print(f'topic={message.topic()}, offset={message.offset()}')
        value = message.value()
        print(value)

consumer.consume()
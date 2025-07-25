from gcn_kafka import Consumer
import json

consumer = Consumer(client_id='3i856lfjrpqe3d8nh8fbbmbt9r',
                                        client_secret='1vkcja4n67fjlcck7bbo1apqpv9g0c453ng221njon0pgn2dlr9u',
                                        domain='gcn.nasa.gov')
consumer.subscribe(['igwn.gwalert'])

print("Connected")

while True:
    for message in consumer.consume(timeout=1):
        if message.error():
            print(message.error())
            continue
        # Print the topic and message ID
        print(f'topic={message.topic()}, offset={message.offset()}')
        value = message.value()
        print(value)
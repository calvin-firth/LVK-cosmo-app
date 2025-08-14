from gcn_kafka import Consumer
import time
import threading
import redis
import json
import icarogw
from analyze_event_utils import analyze_event
import traceback

def poll_events():
    while True:
        try:
            if not connected:
                try:
                    consumer = Consumer(client_id='3i856lfjrpqe3d8nh8fbbmbt9r',
                                        client_secret='1vkcja4n67fjlcck7bbo1apqpv9g0c453ng221njon0pgn2dlr9u',
                                        domain='gcn.nasa.gov')
                    consumer.subscribe(['igwn.gwalert'])
                    connected = consumer.list_topics() is not None
                    print("Reconnected")
                    #r.hset("Status", "Connected", "True")
                except:
                    print("Still disconnected")
                    continue
            connected = consumer.list_topics() is not None
            for message in consumer.consume(timeout=1):
                print("in for loop")
                if message.error():
                    print(message.error())
                    continue
                # Print the topic and message ID
                print(f'topic={message.topic()}, offset={message.offset()}')
                alert = json.loads(message.value())
                try:
                    print("Got message " + str(alert['superevent_id']),flush=True)
                except:
                    print("Got message, couldn't print", flush = True)
                    traceback.print_exc()

                if alert['superevent_id'][0] == 'S':
                    r.rpush("queue:waiting", json.dumps(alert)) #Use all events for testing
            if connected:
                r.hset("Status","Last Check",time.time())
        except:
            print("Kafka disconnected")
            #r.hset("Status","Connected","False")
            connected = False

        time.sleep(5)

def process_queue():
    while True:
        print("process queue loop")
        pop = r.blpop("queue:waiting", timeout=5)
        #print("after pop")
        if pop is not None:
            _, result = pop
            print("Succesfully popped item from queue",flush=True)
        else:
            continue
        try:
            result = json.loads(result)
        except:
            print("Couldn't load " + str(result))
            continue
        try:
            if result['alert_type'] == 'EARLYWARNING' or result['alert_type'] == 'PRELIMINARY':
                continue
            elif result['alert_type'] == 'INITIAL':
                alert_id = result['superevent_id']
                if alert_id not in r.smembers("events:all"):
                    r.hset("Status", "Currently Analyzing",alert_id + " Initial skymap")
                    r.hset(alert_id, "status", "Analysis in process")
                    '''try:
                        from analyze_event_utils import analyze_event
                        print("Import succesful")
                    except:
                        print("Import failed")'''
                    try:
                        # Do actual analysis
                        r.sadd("events:all", alert_id)
                        print("Right before analyze_event",flush=True)
                        analyze_event(alert_id,result['event']['skymap'],cat,empty_cat,r=r)
                        r.hset(alert_id,"status","Initial analysis complete")
                    except:
                        r.hset(alert_id, "status", "Initial analysis failed")
                        print("Analysis failed")
                        traceback.print_exc()
                    finally:
                        r.hset("Status","Currently Analyzing","None")
                else:
                    print("Got initial alert for event already in event list")
            elif result['alert_type'] == 'UPDATE':
                alert_id = result['superevent_id']
                r.hset(alert_id, "status", "Running updated analysis")
                r.hset("Status", "Currently Analyzing", alert_id + " Initial skymap")
                if alert_id in r.smembers("events:all"):
                    try:
                        # Do actual analysis
                        analyze_event(alert_id,result.get('event', {}).pop('skymap'),cat,empty_cat,r=r)
                        r.hset(alert_id, "status", "Analysis updated " + time.ctime())
                    except:
                        r.hset(alert_id, "status", "Update failed at " + time.ctime())
                    finally:
                        r.hset("Status", "Currently Analyzing", "None")
                else:
                    print("Update received for event not in event list")
            elif result['alert_type'] == 'RETRACTION':
                alert_id = result['superevent_id']
                if alert_id in r.smembers("events:all"):
                    r.hset(alert_id, "status", "Retracted")
                else:
                    print("Alert retracted not in list")
            else:
                print("Alert type not recognized!")
                continue
        except:
            print("Hit process queue exception")

if __name__ == "__main__":
    ##LOAD CATALOG FIRST
    from joblib import Memory

    # Store the cache in a temporary or project folder
    memory = Memory(".cache", verbose=1)  # will store cached results here

    @memory.cache
    def load_catalog():
        print("Loading catalog...")
        outcat = icarogw.catalog.icarogw_catalog('/mnt/c/Users/Calvi/2025 IREU Sapienza/icaro_gladep.hdf5', 'K-band',
                                                 'eps-1')
        outcat.load_from_hdf5_file()
        print("Catalog loaded, making copy...")
        import copy

        cat = copy.deepcopy(outcat)
        outcat.make_me_empty()
        empty_cat = outcat
        print("Empty catalog made.")
        return cat,empty_cat


    cat,empty_cat = load_catalog()
    print("Catalog loading done.")

    r = redis.Redis.from_url("rediss://default:AWTjAAIjcDE0ODhlMDIxZTEwNDg0Y2NmOTM5YTliZWI4ZTE0OGI5ZHAxMA@internal-sawfly-25827.upstash.io:6379",decode_responses=True,retry_on_timeout=True)

    consumer = Consumer(client_id='3i856lfjrpqe3d8nh8fbbmbt9r',
                        client_secret='1vkcja4n67fjlcck7bbo1apqpv9g0c453ng221njon0pgn2dlr9u',domain='gcn.nasa.gov')
    consumer.subscribe(['igwn.gwalert'])

    try:
        connected = consumer.list_topics()
        r.hset("Status", "Connected", "True")
        print("Connection successful")
    except:
        r.hset("Status", "Connected", "False")

    t1 = threading.Thread(target=poll_events, daemon=True)
    t2 = threading.Thread(target=process_queue, daemon=True)

    t1.start()
    t2.start()

    t1.join()
    t2.join()
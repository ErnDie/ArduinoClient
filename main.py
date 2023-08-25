#! /usr/bin/env python3

import json

from crosslab.soa_services.webcam import WebcamService__Producer, GstTrack

import arduino_connection
import asyncio

from crosslab.api_client import APIClient
from crosslab.soa_client.device_handler import DeviceHandler
from crosslab.soa_services.message import MessageServiceEvent
from crosslab.soa_services.message import MessageService__Producer, MessageService__Consumer


async def main_async():
    # read config from file
    with open("config.json", "r") as configfile:
        conf = json.load(configfile)

    # debug; delete for prod
    print(conf)

    deviceHandler = DeviceHandler()

    # Webcam Service
    pipeline_new = (" ! ").join(
                [
                    "v4l2src device=/dev/video0",
                    "'image/jpeg,width=640,height=480,framerate=30/1'",
                    "v4l2jpegdec",
                    "v4l2h264enc",
                    "'video/x-h264,level=(string)4'",
                ])
    #pipeline = "v4l2src device=/dev/video0 ! videoconvert ! video/x-raw,format=I420 ! x264enc speed-preset=ultrafast tune=zerolatency"
    webcamService = WebcamService__Producer(GstTrack(pipeline_new), "webcam")
    deviceHandler.add_service(webcamService)

    # Message Service
    messageServiceProducer = MessageService__Producer("messageP")
    deviceHandler.add_service(messageServiceProducer)

    messageServiceConsumer = MessageService__Consumer("messageC")

    async def onMessage(message: MessageServiceEvent):
        print("Received Message of type", message["message_type"])
        print("Message content:", message["message"])
        message_parts = message["message"].split(';')
        led_message = message_parts[0]
        protocol = message_parts[1]
        if (protocol == "TCP"):
            print("Send message (TCP)")
            response = arduino_connection.TCPRequest(led_message)
            print(f"Response: {response}")
            await messageServiceProducer.sendMessage(response, "info")
        if (protocol == "UDP"):
            response = arduino_connection.UDPRequest(led_message)
            await messageServiceProducer.sendMessage(response, "info")

    messageServiceConsumer.on("message", onMessage)
    deviceHandler.add_service(messageServiceConsumer)

    url = conf["auth"]["deviceURL"]

    async with APIClient(url) as client:
        client.set_auth_token(conf["auth"]["deviceAuthToken"])
        deviceHandlerTask = asyncio.create_task(
            deviceHandler.connect("{url}/devices/{did}".format(
                url=conf["auth"]["deviceURL"],
                did=conf["auth"]["deviceID"]
            ), client)
        )

        await deviceHandlerTask


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

#! /usr/bin/env python3

import json

import asyncio

import requests

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

    # --------------------------------------------------------------#
    #   I/O                                                         #
    # --------------------------------------------------------------#
    # message service: errors
    messageServiceProducer = MessageService__Producer("message")
    deviceHandler.add_service(messageServiceProducer)

    messageServiceConsumer = MessageService__Consumer("message")

    async def onMessage(message: MessageServiceEvent):
        print("Received Message of type", message["message_type"])
        print("Message content:", message["message"])

        # send get request to arduino
        response = requests.get(url, params={"led": message["message"]})
        if response.status_code == 200:
            await messageServiceProducer.sendMessage("Success, LED was turned " + message["message"], 'info')
        else:
            await messageServiceProducer.sendMessage("Something went wrong: " + message["message"], 'error')

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

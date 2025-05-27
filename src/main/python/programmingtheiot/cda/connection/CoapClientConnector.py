#####
# 
# This class is part of the Programming the Internet of Things project.
# 
# It is provided as a simple shell to guide the student and assist with
# implementation for the Programming the Internet of Things exercises,
# and designed to be modified by the student as needed.
#

import logging
import socket
import asyncio
import traceback

from aiocoap import *

from programmingtheiot.cda.connection.IRequestResponseClient import IRequestResponseClient

from programmingtheiot.data.DataUtil import DataUtil

import programmingtheiot.common.ConfigConst as ConfigConst
from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum
from programmingtheiot.common.IDataMessageListener import IDataMessageListener
from programmingtheiot.cda.connection.IRequestResponseClient import IRequestResponseClient

class CoapClientConnector(IRequestResponseClient):
	"""
	Shell representation of class for student implementation.
	
	"""
	
	def __init__(self, dataMsgListener: IDataMessageListener = None):
		self.config = ConfigUtil()
		self.dataMsgListener = dataMsgListener
		self.enableConfirmedMsgs = False
		self.coapClient = None
		self.observeRequests = {}

		self.host = self.config.getProperty(
			ConfigConst.COAP_GATEWAY_SERVICE,
			ConfigConst.HOST_KEY,
			ConfigConst.DEFAULT_HOST
		)
		self.port = self.config.getInteger(
			ConfigConst.COAP_GATEWAY_SERVICE,
			ConfigConst.PORT_KEY,
			ConfigConst.DEFAULT_COAP_PORT
		)
		self.uriPath = f"coap://{self.host}:{self.port}/"

		logging.info(f"\tHost:Port: {self.host}:{self.port}")

		self.includeDebugLogDetail = True

		try:
			tmpHost = socket.gethostbyname(self.host)
			if tmpHost:
				self.host = tmpHost
				self._initClient()
			else:
				logging.error("Can't resolve host: " + self.host)
		except socket.gaierror:
			logging.info("Failed to resolve host: " + self.host)

	def _initClient(self):
		asyncio.get_event_loop().run_until_complete(self._initClientContext())

	async def _initClientContext(self):
		try:
			logging.info("Creating CoAP client for URI path: " + self.uriPath)
			self.coapClient = await Context.create_client_context()
			logging.info("Client context created.")
		except Exception as e:
			logging.error("Failed to create CoAP client context.", exc_info=True)

	def sendDiscoveryRequest(self, timeout: int = IRequestResponseClient.DEFAULT_TIMEOUT) -> bool:
		logging.info("sendDiscoveryRequest() called.")
		return False

	def sendDeleteRequest(self, resource: ResourceNameEnum = None, name: str = None,
                          enableCON: bool = False, timeout: int = IRequestResponseClient.DEFAULT_TIMEOUT) -> bool:
		logging.info("sendDeleteRequest() called.")
		return False
	
	def sendGetRequest(self, resource: ResourceNameEnum = None, name: str = None,
                       enableCON: bool = False, timeout: int = IRequestResponseClient.DEFAULT_TIMEOUT) -> bool:
		logging.info("sendGetRequest() called.")
		return False

	def sendPostRequest(self, resource: ResourceNameEnum = None, name: str = None,
                        enableCON: bool = False, payload: str = None,
                        timeout: int = IRequestResponseClient.DEFAULT_TIMEOUT) -> bool:
		logging.info("sendPostRequest() called.")
		return False

	def sendPutRequest(self, resource: ResourceNameEnum = None, name: str = None,
                       enableCON: bool = False, payload: str = None,
                       timeout: int = IRequestResponseClient.DEFAULT_TIMEOUT) -> bool:
		logging.info("sendPutRequest() called.")
		return False

	def setDataMessageListener(self, listener: IDataMessageListener = None) -> bool:
		logging.info("setDataMessageListener() called.")
		self.dataMsgListener = listener
		return True

	def startObserver(self, resource: ResourceNameEnum = None, name: str = None,
                      ttl: int = IRequestResponseClient.DEFAULT_TTL) -> bool:
		logging.info("startObserver() called.")
		return False

	def stopObserver(self, resource: ResourceNameEnum = None, name: str = None,
                     timeout: int = IRequestResponseClient.DEFAULT_TIMEOUT) -> bool:
		logging.info("stopObserver() called.")
		return False

	def _createResourcePath(self, resource: ResourceNameEnum = None, name: str = None) -> str:
		resourcePath = ""
		hasResource = False

		if resource:
			resourcePath += resource.value
			hasResource = True

		if name:
			if hasResource:
				resourcePath += "/"
			resourcePath += name

		return resourcePath
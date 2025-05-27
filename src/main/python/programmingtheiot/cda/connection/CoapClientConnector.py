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
from programmingtheiot.data.ActuatorData import ActuatorData

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
		logging.info("Discovering remote resources...")
		return self.sendGetRequest(
			resource=None,
			name=".well-known/core",
			enableCON=False,
			timeout=timeout
		)

	def sendDeleteRequest(self, resource: ResourceNameEnum = None, name: str = None,
                      enableCON: bool = False, timeout: int = IRequestResponseClient.DEFAULT_TIMEOUT) -> bool:
		if resource or name:
			resourcePath = self._createResourcePath(resource, name)
			fullUri = f"{self.uriPath}{resourcePath}"

			logging.info("Issuing Async DELETE to path: " + fullUri)

			asyncio.get_event_loop().run_until_complete(
				self._handleDeleteRequest(
					resourcePath=fullUri,
					enableCON=enableCON
				)
			)
			return True
		else:
			logging.warning("Can't issue Async DELETE - no path or path list provided.")
			return False
		
	async def _handleDeleteRequest(self, resourcePath: str = None, enableCON: bool = False):
		try:
			msgType = CON if enableCON else NON

			msg = Message(mtype=msgType, code=Code.DELETE, uri=resourcePath)
			req = self.coapClient.request(msg)
			responseData = await req.response

			self._onDeleteResponse(responseData)

		except Exception as e:
			logging.warning("Failed to process DELETE request for path: " + resourcePath)
			traceback.print_exception(type(e), e, e.__traceback__)

	def _onDeleteResponse(self, response):
		if not response:
			logging.warning('DELETE response invalid. Ignoring.')
			return

		logging.info('DELETE response received: %s', response.payload.decode("utf-8"))
	
	def sendGetRequest(self, resource: ResourceNameEnum = None, name: str = None,
					enableCON: bool = False, timeout: int = IRequestResponseClient.DEFAULT_TIMEOUT) -> bool:
		if resource or name:
			resourcePath = self._createResourcePath(resource, name)
			fullUri = f"{self.uriPath}{resourcePath}"

			logging.info(f"Issuing Async GET to path: {fullUri}")
			asyncio.get_event_loop().run_until_complete(
				self._handleGetRequest(resourcePath=fullUri, enableCON=enableCON)
			)
			return True
		else:
			logging.warning("Can't issue Async GET - no path or path list provided.")
			return False

	async def _handleGetRequest(self, resourcePath: str = None, enableCON: bool = False):
		try:
			msgType = CON if enableCON else NON
			msg = Message(mtype=msgType, code=Code.GET, uri=resourcePath)

			req = self.coapClient.request(msg)
			responseData = await req.response

			self._onGetResponse(responseData)

		except Exception as e:
			logging.warning(f"Failed to process GET request for path: {resourcePath}")
			traceback.print_exception(type(e), e, e.__traceback__)


	def _onGetResponse(self, response):
		if not response:
			logging.warning('Async GET response invalid. Ignoring.')
			return

		logging.info('Async GET response received.')

		jsonData = response.payload.decode("utf-8")
		logging.debug(f"Raw payload: {jsonData}")

		# Try to extract the data type from the URI path
		if len(response.opt.uri_path) >= 2:
			dataType = response.opt.uri_path[2]

			if dataType == ConfigConst.ACTUATOR_CMD:
				logging.info("ActuatorData received: %s", jsonData)

				try:
					ad = DataUtil().jsonToActuatorData(jsonData)

					if self.dataMsgListener:
						self.dataMsgListener.handleActuatorCommandMessage(ad)
				except Exception as e:
					logging.warning("Failed to decode actuator data. Ignoring: %s", jsonData)
					traceback.print_exception(type(e), e, e.__traceback__)
					return
			else:
				logging.info("Response data received. Payload: %s", jsonData)
		else:
			logging.info("Response data received. Payload: %s", jsonData)

	

	def sendPostRequest(self, resource: ResourceNameEnum = None, name: str = None,
						enableCON: bool = False, payload: str = None,
						timeout: int = IRequestResponseClient.DEFAULT_TIMEOUT) -> bool:
		if resource or name:
			resourcePath = self._createResourcePath(resource, name)
			fullUri = f"{self.uriPath}{resourcePath}"

			logging.info("Issuing Async POST to path: " + fullUri)

			asyncio.get_event_loop().run_until_complete(
				self._handlePostRequest(
					resourcePath=fullUri,
					payload=payload,
					enableCON=enableCON
				)
			)
			return True
		else:
			logging.warning("Can't issue Async POST - no path or path list provided.")
			return False
		
	async def _handlePostRequest(self, resourcePath: str = None, payload: str = None, enableCON: bool = False):
		try:
			msgType = CON if enableCON else NON
			payloadBytes = payload.encode("utf-8") if payload else b""

			msg = Message(mtype=msgType, payload=payloadBytes, code=Code.POST, uri=resourcePath)
			req = self.coapClient.request(msg)
			responseData = await req.response

			self._onPostResponse(responseData)

		except Exception as e:
			logging.warning("Failed to process POST request for path: " + resourcePath)
			traceback.print_exception(type(e), e, e.__traceback__)

	def _onPostResponse(self, response):
		if not response:
			logging.warning('POST response invalid. Ignoring.')
			return

		logging.info('POST response received: %s', response.payload.decode("utf-8"))


	def sendPutRequest(self, resource: ResourceNameEnum = None, name: str = None,
                   enableCON: bool = False, payload: str = None,
                   timeout: int = IRequestResponseClient.DEFAULT_TIMEOUT) -> bool:
		if resource or name:
			resourcePath = self._createResourcePath(resource, name)
			fullUri = f"{self.uriPath}{resourcePath}"

			logging.info("Issuing Async PUT to path: " + fullUri)

			asyncio.get_event_loop().run_until_complete(
				self._handlePutRequest(
					resourcePath=fullUri,
					payload=payload,
					enableCON=enableCON
				)
			)
			return True
		else:
			logging.warning("Can't issue Async PUT - no path or path list provided.")
			return False
		
	async def _handlePutRequest(self, resourcePath: str = None, payload: str = None, enableCON: bool = False):
		try:
			msgType = CON if enableCON else NON
			payloadBytes = payload.encode("utf-8") if payload else b""

			msg = Message(mtype=msgType, payload=payloadBytes, code=Code.PUT, uri=resourcePath)
			req = self.coapClient.request(msg)
			responseData = await req.response

			self._onPutResponse(responseData)

		except Exception as e:
			logging.warning("Failed to process PUT request for path: " + resourcePath)
			traceback.print_exception(type(e), e, e.__traceback__)

	def _onPutResponse(self, response):
		if not response:
			logging.warning('PUT response invalid. Ignoring.')
			return

		logging.info('PUT response received: %s', response.payload.decode("utf-8"))


	def setDataMessageListener(self, listener: IDataMessageListener = None) -> bool:
		logging.info("setDataMessageListener() called.")
		self.dataMsgListener = listener
		return True

	def startObserver(self, resource: ResourceNameEnum = None, name: str = None,
                  ttl: int = IRequestResponseClient.DEFAULT_TTL) -> bool:
		if resource or name:
			resourcePath = self._createResourcePath(resource, name)

			if resourcePath in self.observeRequests:
				logging.warning("Already observing resource %s. Ignoring start observe request.", resourcePath)
				return False

			asyncio.get_event_loop().run_until_complete(
				asyncio.ensure_future(self._handleStartObserveRequest(resourcePath))
			)
			return True
		else:
			logging.warning("Can't issue Async OBSERVE - GET - no path or path list provided.")
			return False

	def stopObserver(self, resource: ResourceNameEnum = None, name: str = None,
                 timeout: int = IRequestResponseClient.DEFAULT_TIMEOUT) -> bool:
		if resource or name:
			resourcePath = self._createResourcePath(resource, name)

			if resourcePath not in self.observeRequests:
				logging.warning("Resource %s not being observed. Ignoring stop observe request.", resourcePath)
				return False

			asyncio.get_event_loop().run_until_complete(
				self._handleStopObserveRequest(resourcePath)
			)
			return True
		else:
			logging.warning("Can't cancel OBSERVE - no path provided.")
			return False
		
	async def _handleStartObserveRequest(self, resourcePath: str = None):
		logging.info('Handle start observe invoked: ' + resourcePath)

		fullUri = f"{self.uriPath}{resourcePath}"
		msg = Message(code=Code.GET, uri=fullUri, observe=0)
		req = self.coapClient.request(msg)

		self.observeRequests[resourcePath] = req

		try:
			responseData = await req.response
			self._onGetResponse(responseData)

			async for responseData in req.observation:
				self._onGetResponse(responseData)
		except Exception as e:
			logging.warning("Failed to execute OBSERVE - GET. Recovering...")
			traceback.print_exception(type(e), e, e.__traceback__)
			await self._handleStopObserveRequest(resourcePath, ignoreErr=True)

	async def _handleStopObserveRequest(self, resourcePath: str = None, ignoreErr: bool = False):
		if resourcePath in self.observeRequests:
			logging.info('Handle stop observe invoked: ' + resourcePath)

			try:
				observeRequest = self.observeRequests[resourcePath]
				observeRequest.observation.cancel()
			except Exception as e:
				if not ignoreErr:
					logging.warning("Failed to cancel OBSERVE - GET: " + resourcePath)

			try:
				del self.observeRequests[resourcePath]
			except Exception as e:
				if not ignoreErr:
					logging.warning("Failed to remove observable from list: " + resourcePath)
		else:
			logging.warning('Resource not currently under observation. Ignoring: ' + resourcePath)

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
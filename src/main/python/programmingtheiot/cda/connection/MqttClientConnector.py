#####
# 
# This class is part of the Programming the Internet of Things project.
# 
# It is provided as a simple shell to guide the student and assist with
# implementation for the Programming the Internet of Things exercises,
# and designed to be modified by the student as needed.
#

import ssl
import logging
import paho.mqtt.client as mqttClient

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.data.DataUtil import DataUtil
from programmingtheiot.common.IDataMessageListener import IDataMessageListener
from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum

from programmingtheiot.cda.connection.IPubSubClient import IPubSubClient

class MqttClientConnector(IPubSubClient):
	"""
	Shell representation of class for student implementation.
	
	"""

	def __init__(self, clientID: str = None):
		"""
		Default constructor. This will set remote broker information and client connection
		information based on the default configuration file contents.
		
		@param clientID Defaults to None. Can be set by caller. If this is used, it's
		critically important that a unique, non-conflicting name be used so to avoid
		causing the MQTT broker to disconnect any client using the same name. With
		auto-reconnect enabled, this can cause a race condition where each client with
		the same clientID continuously attempts to re-connect, causing the broker to
		disconnect the previous instance.
		"""
		self.config = ConfigUtil()

		self.dataMsgListener = None

		self.host = self.config.getProperty(ConfigConst.MQTT_GATEWAY_SERVICE, 
									  		ConfigConst.HOST_KEY, 
											ConfigConst.DEFAULT_HOST
											)

		self.port = self.config.getInteger(ConfigConst.MQTT_GATEWAY_SERVICE, 
									 		ConfigConst.PORT_KEY, 
											ConfigConst.DEFAULT_MQTT_PORT
											)
		
		self.keepAlive = self.config.getInteger(ConfigConst.MQTT_GATEWAY_SERVICE, 
										  		ConfigConst.KEEP_ALIVE_KEY, 
												ConfigConst.DEFAULT_KEEP_ALIVE
												)
		
		self.defaultQos = self.config.getInteger(ConfigConst.MQTT_GATEWAY_SERVICE, 
										   		ConfigConst.DEFAULT_QOS_KEY, 
												ConfigConst.DEFAULT_QOS)
		

		self.enableEncriptation = self.config.getBoolean(ConfigConst.MQTT_GATEWAY_SERVICE,
													ConfigConst.ENABLE_CRYPT_KEY, 
													)
		
		self.pemFileName = self.config.getProperty(ConfigConst.MQTT_GATEWAY_SERVICE,
											 		ConfigConst.CERT_FILE_KEY
													)	
		
		self.mqttClient = None
		
		# Establece clientID
		if clientID:
			self.clientID = clientID

		else:
			self.clientID = self.config.getProperty(ConfigConst.CONSTRAINED_DEVICE, 
										   			ConfigConst.DEVICE_LOCATION_ID_KEY
													)
		
		# Valida clientID
		if not self.clientID or len(self.clientID.strip()) == 0:
			raise ValueError("Client ID must be non-empty")

		# Info logging
		logging.info('\tMQTT Client ID: ' + self.clientID)
		logging.info('\tMQTT Broker Host: ' + self.host)
		logging.info('\tMQTT Broker Port: ' + str(self.port))
		logging.info('\tMQTT Keep Alive: ' + str(self.keepAlive))


	def connectClient(self) -> bool:
		if not self.mqttClient:
			self.mqttClient = mqttClient.Client(client_id=self.clientID, clean_session=True)

			try:
				if self.enableEncryption:
					logging.info("Enabling TLS encryption...")

					self.port = self.config.getInteger(
						ConfigConst.MQTT_GATEWAY_SERVICE,
						ConfigConst.SECURE_PORT_KEY,
						ConfigConst.DEFAULT_MQTT_SECURE_PORT
					)

					self.mqttClient.tls_set(
						self.pemFileName,
						tls_version=ssl.PROTOCOL_TLS_CLIENT
					)
			except Exception as e:
				logging.warning(f"Failed to enable TLS encryption. Using unencrypted connection. Error: {e}")

			self.mqttClient.on_connect = self.onConnect
			self.mqttClient.on_disconnect = self.onDisconnect
			self.mqttClient.on_message = self.onMessage
			self.mqttClient.on_publish = self.onPublish
			self.mqttClient.on_subscribe = self.onSubscribe

		if not self.mqttClient.is_connected():
			logging.info('MQTT client connecting to broker at host: ' + self.host)
			self.mqttClient.connect(self.host, self.port, self.keepAlive)
			self.mqttClient.loop_start()
			return True
		else:
			logging.warning('MQTT client is already connected. Ignoring connect request.')
			return False
		

	def disconnectClient(self) -> bool:
		if self.mqttClient and self.mqttClient.is_connected():
			logging.info('Disconnecting MQTT client from broker: ' + self.host)
			self.mqttClient.loop_stop()
			self.mqttClient.disconnect()
			return True
		else:
			logging.warning('MQTT client already disconnected. Ignoring.')
			return False
			

	def onConnect(self, client, userdata, flags, rc):
		logging.info('MQTT client connected to broker: ' + str(client))

		# Suscribirse directamente desde aquí
		self.mqttClient.subscribe(
			topic = ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE.value,
			qos = self.defaultQos
		)
		self.mqttClient.message_callback_add(
			sub = ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE.value,
			callback = self.onActuatorCommandMessage
		)


	def onDisconnect(self, client, userdata, rc):
		logging.info('MQTT client disconnected from broker: ' + str(client))


	def onMessage(self, client, userdata, msg):
		payload = msg.payload

		if payload:
			decodedMsg = payload.decode("utf-8")
			logging.info(f'MQTT message received on topic {msg.topic} with payload: {decodedMsg}')
			
			if self.dataMsgListener:
				from programmingtheiot.data.DataUtil import DataUtil
				from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum

				if msg.topic == ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE.value:
					actuatorData = DataUtil().jsonToActuatorData(decodedMsg)
					self.dataMsgListener.handleActuatorCommandMessage(actuatorData)
				else:
					self.dataMsgListener.handleIncomingMessage(ResourceNameEnum.getEnumFromTopicName(msg.topic), decodedMsg)
		else:
			logging.info('MQTT message received with no payload: ' + str(msg))


	def onPublish(self, client, userdata, mid):
		logging.info('MQTT message published: ' + str(client))


	def onSubscribe(self, client, userdata, mid, granted_qos):
		logging.info('MQTT client subscribed: ' + str(client))
	

	def onActuatorCommandMessage(self, client, userdata, msg):
		logging.info('[Callback] Actuator command message received. Topic: %s.', msg.topic)

		if self.dataMsgListener:
			try:
				actuatorData = DataUtil().jsonToActuatorData(msg.payload.decode('utf-8'))
				self.dataMsgListener.handleActuatorCommandMessage(actuatorData)
			except:
				logging.exception("Failed to convert incoming actuation command payload to ActuatorData: ")
	

	def publishMessage(self, resource: ResourceNameEnum = None, msg: str = None, qos: int = ConfigConst.DEFAULT_QOS) -> bool:
		# check validity of resource (topic)
		if not resource:
			logging.warning('No topic specified. Cannot publish message.')
			return False

		# check validity of message
		if not msg:
			logging.warning('No message specified. Cannot publish message to topic: ' + resource.value)
			return False

		# check validity of QoS - set to default if necessary
		if qos < 0 or qos > 2:
			qos = ConfigConst.DEFAULT_QOS
			logging.info('Invalid QoS level. Using default: ' + str(qos))

		# publish message, and wait for publish to complete before returning
		msgInfo = self.mqttClient.publish(topic = resource.value, payload = msg, qos = qos)
		#msgInfo.wait_for_publish()

		return True


	def subscribeToTopic(self, resource: ResourceNameEnum = None, callback = None, qos: int = ConfigConst.DEFAULT_QOS) -> bool:
		# check validity of resource (topic)
		if not resource:
			logging.warning('No topic specified. Cannot subscribe.')
			return False

		# check validity of QoS - set to default if necessary
		if qos < 0 or qos > 2:
			qos = ConfigConst.DEFAULT_QOS
			logging.info('Invalid QoS level. Using default: ' + str(qos))

		# subscribe to topic
		logging.info('Subscribing to topic %s', resource.value)
		self.mqttClient.subscribe(resource.value, qos)

		# set callback if provided
		if callback:
			self.mqttClient.message_callback_add(resource.value, callback)

		return True


	def unsubscribeFromTopic(self, resource: ResourceNameEnum = None) -> bool:
		# check validity of resource (topic)
		if not resource:
			logging.warning('No topic specified. Cannot unsubscribe.')
			return False

		logging.info('Unsubscribing from topic %s', resource.value)
		self.mqttClient.unsubscribe(resource.value)

		return True
	

	def setDataMessageListener(self, listener: IDataMessageListener = None) -> bool:
		if listener:
			self.dataMsgListener = listener
			return True

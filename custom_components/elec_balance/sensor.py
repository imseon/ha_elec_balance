"""Platform for sensor integration."""
from homeassistant.helpers.entity import Entity
import os
import logging
import json


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    add_entities([ElecBalanceSensor()])


class ElecBalanceSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self):
        """Initialize the sensor."""
        result = self.readBalance()
        self._state = result['balance']
        self._attrs = result

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'Elec Balance'

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        return self._attrs

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return '元'

    def readBalance(self):
        dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(dir, 'balance')
        balance = {'balance': '0.00'}
        try:
            with open(file_path, 'r') as f:
                balance = f.read()
                if balance:
                    balance = json.loads(balance)
        except:
            pass
        return balance

    def update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        result = self.readBalance()
        self._state = result['balance']
        self._attrs = result

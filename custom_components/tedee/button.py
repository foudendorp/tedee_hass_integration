import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from aiotedee import TedeeClientException

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for lock in coordinator.data.values():
        if lock.is_enabled_pullspring:
            entities.append(TedeeUnlatchButton(lock, coordinator))
            entities.append(TedeeUnlockUnlatchButton(lock, coordinator))

    async_add_entities(entities)

class TedeeUnlatchButton(CoordinatorEntity, ButtonEntity):
    """Button to only pull the spring (does not unlock if locked)"""
    def __init__(self, lock, coordinator):
        _LOGGER.debug("Setting up ButtonEntity for %s", lock.lock_name)
        super().__init__(coordinator)
        self._lock = lock
        self._attr_has_entity_name = True
        self._attr_name = "Unlatch"
        self._attr_unique_id = f"{lock.lock_id}-unlatch-button"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._lock.lock_id)},
            name=self._lock.lock_name,
            manufacturer="tedee",
            model=self._lock.lock_type
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._lock = self.coordinator.data[self._lock.lock_id]
        self.async_write_ha_state()
        

    async def async_press(self, **kwargs) -> None:
        try:
            self._lock.state = 4
            self.async_write_ha_state()
            await self.coordinator._tedee_client.pull(self._lock.lock_id)
            await self.coordinator.async_request_refresh()
        except (TedeeClientException, Exception) as ex:
            _LOGGER.debug("Error while unlatching the door through button: %s", ex)
            raise HomeAssistantError(ex) from ex
        

class TedeeUnlockUnlatchButton(CoordinatorEntity, ButtonEntity):
    """Button to unlock and pull the spring / only pull the spring if unlocked"""
    def __init__(self, lock, coordinator):
        _LOGGER.debug("Setting up ButtonEntity for %s", lock.lock_name)
        super().__init__(coordinator)
        self._lock = lock
        self._attr_has_entity_name = True
        self._attr_name = "Unlock & Unlatch"
        self._attr_unique_id = f"{lock.lock_id}-unlockunlatch-button"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._lock.lock_id)},
            name=self._lock.lock_name,
            manufacturer="tedee",
            model=self._lock.lock_type
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._lock = self.coordinator.data[self._lock.lock_id]
        self.async_write_ha_state()
        

    async def async_press(self, **kwargs) -> None:
        try:
            self._lock.state = 4
            self.async_write_ha_state()
            await self.coordinator._tedee_client.open(self._lock.lock_id)
            await self.coordinator.async_request_refresh()
        except (TedeeClientException, Exception) as ex:
            _LOGGER.debug("Error while opening the door through button: %s", ex)
            raise HomeAssistantError(ex) from ex
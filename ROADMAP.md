# Roadmap: Teltonika RMS Integration

This roadmap outlines the planned features and improvements for the Teltonika RMS Home Assistant integration. Priorities may shift based on user feedback and RMS API changes.

## 🚧 In Progress / Up Next
- [ ] **Official HACS Inclusion:** Remove the need for custom repository addition by getting added to the default HACS store.
- [ ] **PoE Control:** Complete the implementation of `switch` entities to remotely toggle PoE power on supported switch ports (e.g., TSW202) directly from Home Assistant.
- [ ] **Data Usage Sensors:** Expose daily/monthly mobile data usage statistics per SIM card.

## 📅 Planned (Short to Medium Term)
- [ ] **Wi-Fi Toggle:** Ability to enable/disable specific Wi-Fi access points or SSIDs.
- [ ] **Firmware Update Action:** Trigger the firmware update process directly via the `update` entity in Home Assistant.
- [ ] **Mobile Connection Control:** Switch to remotely enable/disable the mobile data connection.
- [ ] **SIM Switching:** Service or selector to switch between SIM 1 and SIM 2 for dual-SIM routers (like RUTX50).
- [ ] **SMS Integration:** Expose a notification service to send SMS messages via the router's SIM card.

## 🔮 Exploring (Long Term)
- [ ] **Home Assistant Core:** Eventually refactor and submit to Home Assistant Core as an official integration.
- [ ] **Webhooks / Push Updates:** Explore if RMS supports webhooks for instant state changes to reduce API polling.

---
*If you have a feature request that is not on this list, please [open an issue](https://github.com/derliebemarcus/teltonika_rms/issues) on GitHub!*

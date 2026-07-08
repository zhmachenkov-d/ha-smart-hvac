# LADRC on Critical Zone air temperature with OpenTherm water setpoint

The HVAC App splits multi-zone coordination from control: the Multi-Zone Coordinator selects the Critical Zone (largest positive Zone Error) and passes its air temperature and reference setpoint to an ADRC Controller running LADRC. The controller commands Set Water Temperature on the Plant via a Home Assistant number entity — not zone thermostat setpoints.

Outdoor temperature enters as additive Weather Feedforward (linear baseline) on top of the LADRC tracking term. When no Zone has Heating Demand (all zone errors ≤ 0), the App writes **0** to Set Water Temperature, bypasses LADRC output, and resets observer state. When the Critical Zone changes, the ESO re-initializes from the new zone's measured temperature so observer state is not carried across rooms.

This differs from Huang et al. (2018), who control a single AHU zone by adjusting coil water **flow**; here the actuator is OpenTherm **water temperature** for a shared boiler serving multiple Zones. Gains are configurable starting points, not copy-paste from the paper.

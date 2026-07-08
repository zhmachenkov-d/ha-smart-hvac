# Exclusive Session against production Home Assistant

Dev AppDaemon talks to the house's production Home Assistant over the LAN. To avoid two runtimes commanding the same OpenTherm / climate entities, the Production AppDaemon add-on is stopped for the whole session, then started again afterward. A dedicated lab HA was rejected for now; dual-run with discipline alone was rejected as unsafe for HVAC.

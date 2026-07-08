# Smart HVAC

Python automations that control heating, ventilation, and air conditioning through Home Assistant, hosted by AppDaemon.

## Language

**App**:
A Python automation that runs inside AppDaemon and acts on Home Assistant entities to control HVAC behavior.
_Avoid_: Script, automation (HA automation), integration, add-on

**AppDaemon**:
The sandboxed Python execution environment that loads and runs Apps. This project consumes AppDaemon; it does not develop it.
_Avoid_: Framework, HA core, add-on (as a synonym for AppDaemon or for an App)

**Home Assistant**:
The home automation platform whose entities, services, and events Apps observe and control.
_Avoid_: HAOS, supervisor (unless referring specifically to those products)

**Production Add-on**:
The Home Assistant AppDaemon add-on that normally hosts the house's Apps.
_Avoid_: Prod container, live AD (as the only name)

**Exclusive Session**:
A development period in which the Production Add-on is stopped so a local AppDaemon is the sole runtime talking to Home Assistant for those Apps.
_Avoid_: Dual-run, parallel AD (those are failures of an Exclusive Session)

**Zone**:
A controllable heating area of the house that participates in shared boiler demand. A Zone has a temperature reading and one or more Home Assistant thermostats (climate entities).
_Avoid_: Room (unless a Zone is exactly one room), entity

**Plant**:
The boiler and primary water circuit that supplies heat to Zones, commanded via OpenTherm.
_Avoid_: HVAC system (too broad), heater (ambiguous with zone emitters)

**Set Water Temperature**:
The OpenTherm boiler water setpoint the App commands on the Plant (the boiler's target water temperature via OpenTherm).
_Avoid_: Room setpoint, climate temperature (those are Zone air targets), mixer setpoint

**Zone Error**:
The difference between a Zone's thermostat setpoint and that Zone's current temperature (how far the Zone is from its comfort target).
_Avoid_: Demand (until defined), delta (ambiguous)

**Critical Zone**:
The Zone currently selected as having the largest Zone Error; it drives Plant demand for that control step.
_Avoid_: Master zone, primary room

**Outdoor Temperature**:
The measured outdoor air temperature used when calculating an appropriate Set Water Temperature.
_Avoid_: Weather, forecast (unless forecast is explicitly in scope)

**Multi-Zone Coordinator**:
The part of the HVAC App that picks the Critical Zone from all Zones and turns its need (plus Outdoor Temperature) into a desired Plant water temperature.
_Avoid_: Thermostat, scheduler (unless that is all it does)

**ADRC Controller**:
The part of the HVAC App that uses Active Disturbance Rejection Control in relation to Set Water Temperature (exact role relative to the Multi-Zone Coordinator is still under discussion). Depth: `knowledge/concepts/adrc.md`.
_Avoid_: PID (unless explicitly choosing PID instead), weather compensation (related idea, different algorithm)

**LADRC**:
Linear Active Disturbance Rejection Control — linear ESO plus linear outer loop; a practical form of ADRC (not yet decided as this project's ADRC Controller implementation). Depth: `knowledge/concepts/ladrc.md`.
_Avoid_: PID (related baseline, different algorithm), nonlinear ADRC (related parent idea)

**MADRC**:
Modified Active Disturbance Rejection Control — ADRC/LADRC with an inertia compensator delaying the ESO’s command input so it stays synchronized with a high-order lag plant (not yet decided for this project). Depth: `knowledge/concepts/madrc.md`.
_Avoid_: Smith predictor (related delay idea, different structure), plain LADRC (no command-path compensator)

**Extended State Observer**:
The ADRC/LADRC observer that estimates the measured output and an extra state for total disturbance. Depth: `knowledge/concepts/extended-state-observer.md`.
_Avoid_: Kalman filter (different observer family unless explicitly choosing it)

## Example dialogue

> **Dev:** When I change the thermostat schedule logic, am I editing Home Assistant or an App?
> **Expert:** An App. Home Assistant exposes the climate entity; the App decides when and how to call it.
> **Dev:** So AppDaemon is part of what we ship?
> **Expert:** No — AppDaemon is the runtime that hosts our Apps. We pin and configure it; we don't maintain its source here.
> **Dev:** Can I start AppDaemon in the Dev Container while the Production Add-on is still running?
> **Expert:** No. That isn't an Exclusive Session — both would drive the same entities. Stop the add-on first, then run locally.
> **Dev:** Two Zones want heat; which one moves the boiler?
> **Expert:** The Critical Zone — the one with the largest Zone Error. The Multi-Zone Coordinator uses that Zone (and Outdoor Temperature) when deciding water temperature. The App still owns ADRC as well; how those two parts share the OpenTherm write is a separate decision.
> **Dev:** Is Set Water Temperature the same as a Zone thermostat setpoint?
> **Expert:** No. Zone thermostats set air temperature targets. Set Water Temperature is the OpenTherm boiler water setpoint.

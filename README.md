Stiebel Eltron HTTP is a Home Assistant integration that connects and scrapes your local Stiebel Eltron ISG webserver to retrieve data from your heat pump system, as HA sensors.

It is not meant to be a climate entity and thus cannot set the temperatures, change the modes, etc. See the official HA integration for that - but you'll need to find a way to activate Modbus on your ISG.

NB: both integrations can run in the same HA instance.

# Needed hardware

- A [Stiebel Eltron heat pump](https://www.stiebel-eltron.com/en/home/products-solutions/renewables/heat_pump.html)
- A [Stiebel Eltron Internet Service Gateway (ISG)](https://www.stiebel-eltron.com/en/home/products-solutions/renewables/controller_energymanagement/isg-web/isg-web.html), connected to your heat pump and your network

# Available data

- Room temperature
- Room relative humidity
- Outside temperature
- Total heating produced
- Total energy consumption

# ovfiets-gbfs

Transform OV-fiets data into GBFS. There is a "global" OV-fiets GBFS and a per zone export. The difference is the pricing, you could bring back your bike at any zone for a surplus tariff.

## Installation
1. Install universal https://github.com/StichtingOpenGeo/universal
2. Install python3 and pyzmq
3. Create the folder /home/projects/gbfs.openov.nl/htdocs/ovfiets
4. Create the users ovfiets and universal, shell "nologin".
5. Install the systemd service files for universal-ovfiets, ovfiets-gbfs and ovfiets-gbfs, enable and start them.

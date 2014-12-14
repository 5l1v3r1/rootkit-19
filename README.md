rootkit
=======

Note: Just messing around with game mechanics for now.

Rootkit is intended to be a Play-By-Email (PBeM) game. 

* Games have multiple players.
* Players have multiple Servers.
* Servers are identified by unique IP address (###.###.###.###)
* Servers have weaknesses. 
* Players don't know which weaknesses their servers have.
* Opponents don't know which weaknesses the other player's servers have. 
* Players don't know the IP address of their opponent's servers.
* Each turn is called a "cycle".
* Players can instruct their servers to run programs. 
* Players can execute one program per server per cycle. 
* Some program take many cycles to complete.
* Some programs take effect immediately when executed (eg: Power Off) 
* Some programs take effect at the end of the cyle. (eg: Power On)
* Credits can be used to buy new programs, hardware and knowledge. 
* Everyone starts with three servers. 

Players are hackers and trying to take down or take over the other servers.

Players have tools to help with their hacking.

Right now they have:
* `nmap` to scan for other servers. The broader your search, the longer it takes. 
* `probe` to scan a server for weaknesses (including your own)
* `mine` to mine for credits

Eventually, I'll add things you can buy with your credits.

* Firewalls
* CPU/Memory/Network upgrades (faster scans/mining/etc)
* Better hacking software
* Patches to repair weaknesses
* Intrusion detection software
* Viruses you can install to hijack other servers. 

Other commands I'm thinking about are:
* `udp` - blasts out a UDP multicast message to all servers. These can be used to talk to other players, but also to instruct your viruses to perform special operations. 

Currently, I'm trying to finalize the turn resolution steps. Things are a little messy in there right now. 

The current approach is:
* `pre-cycle` - things that are done when the cycle starts. All servers run their pre-cycle step first. 
* `post-cycle` - things that are done at the end of the cycle. Usually this is a noop. 
* `completed` - things that are done when the program finishes up. This is where the real work is done. Remember that programs could take several cycles to complete. 

More to come ... patches welcome.




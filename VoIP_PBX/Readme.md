# First steps with Asterisk

## Disclaimer
This info has been taken from asterisk's [wiki](https://wiki.asterisk.org/) unless otherwise noted.

## Runnig asterisk
You can run asterisk by invoking:

```bash
asterisk -cvvvvv # Run asterisk with a CLI attached and vervosity level 5
asterisk         # Run asterisk in the background. We can attach to it later on
astrisk -rvvvvv  # Attach a CLI to an already running asterisk instance 
```

Stoping it can by done by:

```bash
asterisk -rx 'core stop gracefully' # If not currently on asterisk's CLI
coder stop gracefully               # If on asterisk's CLI
```

Exiting the CLI is done by pressing `CTRL + C`.

### Running it as a service
In order to run it as a service you can get the following unit file into `/etc/systemd/system` and use `systemd`'s utilities with `systemctl`. Just be sure to correct file permissions on each of asterisk's dependencies as the user and group running the instance will be `asterisk:asterisk`. The file has been taken from [here](https://github.com/johannbg/systemd-units/blob/master/projects/asterisk/service/asterisk.service).

## Playing back an audio file
Asterisk uses **applications** to do stuff. We are going to use the `Playback()` app to play an audio file back to the caller when he/she dials `100`. To do so we need to take care of several things:

### Setting up `/etc/asterisk/extensions.conf`
The contents are not yeat crystal clear to me...

```ini
[from-internal]
exten = 100,1,Answer()
same = n,Wait(1)
; same = n,Playback(hello-world)
same = n,Playback(/home/vagrant/estefania)
same = n,Hangup()
```

We'll let asterisk anwswer the call and pplayback the provided file. If we use a standalone name asterisk will look for files under `/var/lib/asterisk/sounds/en/`. We can, as seen, provide absolute paths **without** the file extension. We can also see how the **SIP** clients should dial `100` to access this service.

Asterisk likes to play `.gsm` files. This audio codec provides us with low-quality compressed audio. The files can be generated from `.wav` files using good old `sox`. Just run:

```bash
sox input.xxx output.gsm
```

Where `xxx` is the input extension. You can then record any files you want and use them! Be careful though as converting a file to `.gsm` and back again introduces a great deal of noise...

### Adding users through `/etc/asterisk/pjsip.conf`
This file helps us define the transport protocol to use as well as *PBX* users:

```ini
[transport_udp]
type = transport
protocol = udp
; Bind (a.k.a listen on) to every interface
bind = 0.0.0.0

; Config extracted from https://wiki.asterisk.org/wiki/display/AST/Creating+SIP+Accounts
; Check https://wiki.asterisk.org/wiki/display/AST/PJSIP+Configuration+Sections+and+Relationships for info in user config!

; Templates for the necessary config sections

[endpoint_internal](!)
type = endpoint
context = from-internal
disallow = all
allow = ulaw

[auth_userpass](!)
type = auth
auth_type = userpass

[aor_dynamic](!)
type = aor
max_contacts = 1

; Instantiate those templates. If not overwritten the defaults are inherited!

[spike](endpoint_internal)
auth = spike_auth
aors = spike_aor
[spike_auth](auth_userpass)
username = spike
password = spike
[spike_aor](aor_dynamic)

[jin](endpoint_internal)
auth = jin_auth
aors = jin_aor
[jin_auth](auth_userpass)
username = jin
password = jin
[jin_aor](aor_dynamic)
```

A **SIP** client connecting to us should use the following data:
1. Username -> `spike`
2. Password -> `spike`
3. Server -> `Asterisk's Host IP`

You should see that the user registers itself automatically.

### Making the call
Depending on your **SIP** client you'll need to make the call in one way or another. I used Android's default phone app and had to manually ask it to use my **SIP** profile rather than the **SIM** card to make any calls. Be sure to be connected to the LAN where your asterisk instance is running!

### Differentiating called number, user and caller ID
When modifying `pjsip.conf` we are defining the accounts that any given softphone is going to use. We should note that the numbers we make the calls to are actually defined in `extensions.conf` through the so called extension number. That's where we map extension number to registered username. We can also add a caller ID that will be returned to the calling phone as additional info!
